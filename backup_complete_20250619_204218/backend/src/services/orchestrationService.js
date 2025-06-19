/**
 * Orchestration Service - Refactorizado con Recursive Planner y Langwatch
 * 
 * Este servicio refactorizado utiliza los nuevos reasoning y reward shells
 * junto con el recursive planner para proporcionar una orquestación clara 
 * y trazabilidad completa con mejora iterativa y monitoreo con Langwatch.
 * 
 * @module orchestrationService
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";

// Importar los nuevos servicios
import { processUserInput, validateExecutionPlan, AGENT_TYPES } from './reasoningShell.js';
import { evaluateOutput } from './rewardShell.js';
import { recursiveSolve, recursiveSolveMultiple } from './recursivePlanner.js';
import { 
  createSession, 
  saveStep, 
  updateStep, 
  saveReward, 
  getContext, 
  saveExecutionPlan,
  updateSessionStatus,
  STATUS,
  STEP_TYPES 
} from './memoryService.js';

// Importar middleware de Langwatch
import { 
  createOrchestrationTracker, 
  isLangwatchEnabled,
  initializeLangwatch 
} from '../middleware/langwatchMiddleware.js';

// Servicios existentes
import mcpBrokerService from './mcpBrokerService.js';
import ModelRouterService from './modelRouterService.js';
import AppError from '../utils/AppError.js';
import { retryOperation } from '../utils/retryUtils.js';
import logger from '../utils/logger.js';

const modelRouter = new ModelRouterService();

// Inicializar Langwatch al cargar el módulo
initializeLangwatch();

/**
 * Estado del agente refactorizado con soporte para recursive planner
 */
const agentState = {
  // Identificadores de sesión y contexto
  sessionId: { value: null },
  userId: { value: null },
  
  // Input y procesamiento inicial
  originalRequest: { value: null },
  executionPlan: { value: null },
  
  // Estado de ejecución
  currentStep: { value: null },
  completedSteps: { value: (x, y) => (x ?? []).concat(y), default: () => [] },
  
  // Outputs y evaluaciones
  builderOutput: { value: null },
  currentEvaluation: { value: null },
  
  // Control de flujo y recursive planner
  shouldRetry: { value: false, default: () => false },
  retryCount: { value: 0, default: () => 0 },
  maxRetries: { value: 2, default: () => 2 },
  useRecursivePlanner: { value: false, default: () => false },
  recursivePlannerResults: { value: null },
  
  // Estado final
  finalResult: { value: null },
  error: { value: null },
  
  // Metadatos
  startTime: { value: null },
  endTime: { value: null },
  totalDuration: { value: null }
};

/**
 * Instancias de LLM
 */
const llmInstances = {};

/**
 * Configuración del recursive planner
 */
const RECURSIVE_PLANNER_CONFIG = {
  enableForComplexTasks: true,
  complexityThreshold: 4, // Usar recursive planner para tareas con complejidad >= 4
  enableForFailedTasks: true,
  failureThreshold: 0.6, // Usar recursive planner si score < 0.6
  maxRecursiveRetries: 3,
  recursiveScoreThreshold: 0.8
};

/**
 * Inicializa una instancia de LLM
 */
const initializeLlm = (provider, model, apiKeyEnvVar, temperature = 0.7) => {
  if (!process.env[apiKeyEnvVar]) {
    logger.warn(`${apiKeyEnvVar} no configurado. Modelos ${provider} no disponibles.`);
    return null;
  }
  
  try {
    let instance;
    const options = { 
      modelName: model, 
      temperature: temperature, 
      apiKey: process.env[apiKeyEnvVar] 
    };
    
    switch (provider.toLowerCase()) {
      case "openai": 
        instance = new ChatOpenAI(options); 
        break;
      case "anthropic": 
        instance = new ChatAnthropic(options); 
        break;
      case "google": 
        instance = new ChatGoogleGenerativeAI(options); 
        break;
      default:
        throw new Error(`Proveedor LLM no soportado: ${provider}`);
    }
    
    logger.info(`LLM inicializado: ${provider}/${model}`);
    return instance;
  } catch (error) {
    logger.error(`Error inicializando LLM ${provider}/${model}:`, error);
    return null;
  }
};

/**
 * Inicializa todas las instancias de LLM
 */
const initializeAllLlms = () => {
  llmInstances.openai = initializeLlm("openai", "gpt-4", "OPENAI_API_KEY");
  llmInstances.anthropic = initializeLlm("anthropic", "claude-3-sonnet-20240229", "ANTHROPIC_API_KEY");
  llmInstances.google = initializeLlm("google", "gemini-pro", "GOOGLE_API_KEY");
};

/**
 * Obtiene la mejor instancia de LLM disponible
 */
const getBestLlmInstance = () => {
  return llmInstances.anthropic || llmInstances.openai || llmInstances.google || null;
};

/**
 * Determina si se debe usar el recursive planner
 */
const shouldUseRecursivePlanner = (executionPlan, previousEvaluation = null) => {
  // Usar para tareas complejas
  if (RECURSIVE_PLANNER_CONFIG.enableForComplexTasks && 
      executionPlan?.complexity?.score >= RECURSIVE_PLANNER_CONFIG.complexityThreshold) {
    logger.info('🔄 Usando recursive planner por alta complejidad', {
      complexityScore: executionPlan.complexity.score
    });
    return true;
  }
  
  // Usar para tareas que fallaron previamente
  if (RECURSIVE_PLANNER_CONFIG.enableForFailedTasks && 
      previousEvaluation?.score < RECURSIVE_PLANNER_CONFIG.failureThreshold) {
    logger.info('🔄 Usando recursive planner por score bajo', {
      previousScore: previousEvaluation.score
    });
    return true;
  }
  
  return false;
};

/**
 * Nodo: Inicialización de sesión
 */
async function initializeSession(state) {
  try {
    logger.info('OrchestrationService: Inicializando sesión');
    
    const sessionData = {
      userId: state.userId,
      originalInput: state.originalRequest,
      taskType: 'general', // Se determinará en el reasoning shell
      metadata: {
        startTime: new Date().toISOString(),
        userAgent: state.userAgent || 'unknown',
        recursivePlannerEnabled: RECURSIVE_PLANNER_CONFIG.enableForComplexTasks
      }
    };
    
    const sessionResult = await createSession(sessionData);
    if (!sessionResult.success) {
      throw new Error(`Error creando sesión: ${sessionResult.error}`);
    }
    
    return {
      ...state,
      sessionId: sessionResult.session.id,
      startTime: new Date().toISOString()
    };
    
  } catch (error) {
    logger.error('OrchestrationService: Error en inicialización de sesión', { error: error.message });
    return {
      ...state,
      error: error.message
    };
  }
}

/**
 * Nodo: Reasoning Shell - Procesamiento y planificación
 */
async function reasoningNode(state) {
  try {
    logger.info('OrchestrationService: Ejecutando reasoning shell', { 
      sessionId: state.sessionId 
    });
    
    // Guardar paso de reasoning
    const stepData = {
      sessionId: state.sessionId,
      stepType: STEP_TYPES.REASONING,
      stepName: 'reasoning_analysis',
      agentUsed: 'reasoningShell',
      inputData: { originalRequest: state.originalRequest },
      status: STATUS.RUNNING
    };
    
    const stepResult = await saveStep(stepData);
    if (!stepResult.success) {
      throw new Error(`Error guardando paso: ${stepResult.error}`);
    }
    
    const stepId = stepResult.step.id;
    
    // Procesar input con reasoning shell
    const reasoningResult = await processUserInput(state.originalRequest, {
      sessionId: state.sessionId,
      userId: state.userId
    });
    
    if (!reasoningResult.success) {
      // Actualizar paso con error
      await updateStep(stepId, {
        status: STATUS.ERROR,
        errorMessage: reasoningResult.error,
        completedAt: new Date().toISOString()
      });
      throw new Error(`Error en reasoning shell: ${reasoningResult.error}`);
    }
    
    // Validar plan de ejecución
    const validation = validateExecutionPlan(reasoningResult.plan);
    if (!validation.isValid) {
      await updateStep(stepId, {
        status: STATUS.ERROR,
        errorMessage: `Plan inválido: ${validation.errors.join(', ')}`,
        completedAt: new Date().toISOString()
      });
      throw new Error(`Plan de ejecución inválido: ${validation.errors.join(', ')}`);
    }
    
    // Guardar plan de ejecución
    await saveExecutionPlan({
      sessionId: state.sessionId,
      planData: reasoningResult.plan,
      complexityScore: reasoningResult.plan.complexity?.score,
      estimatedDuration: reasoningResult.plan.complexity?.estimatedTime
    });
    
    // Determinar si usar recursive planner
    const useRecursive = shouldUseRecursivePlanner(reasoningResult.plan);
    
    const stepDuration = Date.now() - new Date(stepResult.step.started_at).getTime();
    
    // Trackear paso en Langwatch
    if (state.orchestrationTracker) {
      await state.orchestrationTracker.trackStep(
        'reasoning_analysis',
        'reasoning',
        state.originalRequest,
        reasoningResult.plan,
        stepDuration,
        {
          useRecursivePlanner: useRecursive,
          complexityScore: reasoningResult.plan.complexity?.score,
          subtasksCount: reasoningResult.plan.subtasks?.length
        }
      );
    }
    
    // Actualizar paso como completado
    await updateStep(stepId, {
      status: STATUS.SUCCESS,
      outputData: { 
        plan: reasoningResult.plan,
        useRecursivePlanner: useRecursive
      },
      completedAt: new Date().toISOString(),
      durationMs: stepDuration
    });
    
    logger.info('OrchestrationService: Reasoning completado exitosamente', {
      sessionId: state.sessionId,
      planId: reasoningResult.plan.id,
      subtasks: reasoningResult.plan.subtasks.length,
      useRecursivePlanner: useRecursive
    });
    
    return {
      ...state,
      executionPlan: reasoningResult.plan,
      useRecursivePlanner: useRecursive,
      completedSteps: [...(state.completedSteps || []), stepResult.step]
    };
    
  } catch (error) {
    logger.error('OrchestrationService: Error en reasoning node', { 
      sessionId: state.sessionId,
      error: error.message 
    });
    return {
      ...state,
      error: error.message
    };
  }
}

/**
 * Nodo: Builder con Recursive Planner - Ejecución de tareas mejorada
 */
async function builderNode(state) {
  try {
    logger.info('OrchestrationService: Ejecutando builder', { 
      sessionId: state.sessionId,
      useRecursivePlanner: state.useRecursivePlanner
    });
    
    if (!state.executionPlan) {
      throw new Error('No hay plan de ejecución disponible');
    }
    
    const plan = state.executionPlan;
    const builderOutput = {
      sessionId: state.sessionId,
      planId: plan.id,
      results: [],
      completedSteps: [],
      errors: [],
      warnings: [],
      recursivePlannerResults: null
    };
    
    // Si se debe usar recursive planner, ejecutar tareas con mejora iterativa
    if (state.useRecursivePlanner) {
      const recursiveResults = await executeWithRecursivePlanner(state, plan);
      builderOutput.recursivePlannerResults = recursiveResults;
      
      if (recursiveResults.success) {
        // Usar los resultados del recursive planner
        builderOutput.results = recursiveResults.results;
        builderOutput.completedSteps = recursiveResults.completedSteps;
      } else {
        // Fallback a ejecución normal si recursive planner falla
        logger.warn('Recursive planner falló, usando ejecución normal', {
          error: recursiveResults.error
        });
        await executeNormalFlow(state, plan, builderOutput);
      }
    } else {
      // Ejecución normal sin recursive planner
      await executeNormalFlow(state, plan, builderOutput);
    }
    
    logger.info('OrchestrationService: Builder completado', {
      sessionId: state.sessionId,
      resultsCount: builderOutput.results.length,
      errorsCount: builderOutput.errors.length,
      usedRecursivePlanner: state.useRecursivePlanner
    });
    
    return {
      ...state,
      builderOutput,
      recursivePlannerResults: builderOutput.recursivePlannerResults
    };
    
  } catch (error) {
    logger.error('OrchestrationService: Error en builder node', { 
      sessionId: state.sessionId,
      error: error.message 
    });
    return {
      ...state,
      error: error.message
    };
  }
}

/**
 * Ejecuta tareas usando el recursive planner
 */
async function executeWithRecursivePlanner(state, plan) {
  try {
    logger.info('🔄 Ejecutando con recursive planner', {
      sessionId: state.sessionId,
      subtasks: plan.subtasks.length
    });
    
    const llmInstance = getBestLlmInstance();
    if (!llmInstance) {
      throw new Error('No hay instancias de LLM disponibles para recursive planner');
    }
    
    // Preparar tareas para recursive planner
    const recursiveTasks = plan.subtasks.map(subtask => ({
      prompt: buildSubtaskPrompt(subtask, state.originalRequest, plan),
      tag: `subtask_${subtask.id}`,
      options: {
        maxRetries: RECURSIVE_PLANNER_CONFIG.maxRecursiveRetries,
        scoreThreshold: RECURSIVE_PLANNER_CONFIG.recursiveScoreThreshold,
        paradoxThreshold: 2
      }
    }));
    
    // Ejecutar tareas con recursive planner
    const recursiveResult = await recursiveSolveMultiple(
      recursiveTasks,
      state.sessionId,
      llmInstance,
      {
        maxRetries: RECURSIVE_PLANNER_CONFIG.maxRecursiveRetries,
        scoreThreshold: RECURSIVE_PLANNER_CONFIG.recursiveScoreThreshold
      }
    );
    
    if (!recursiveResult.success) {
      throw new Error(`Recursive planner falló: ${recursiveResult.error}`);
    }
    
    // Procesar resultados
    const results = [];
    const completedSteps = [];
    
    for (let i = 0; i < plan.subtasks.length; i++) {
      const subtask = plan.subtasks[i];
      const recursiveRes = recursiveResult.results[i];
      
      if (recursiveRes.success) {
        results.push({
          subtaskId: subtask.id,
          agent: subtask.agent,
          response: recursiveRes.result.reply,
          score: recursiveRes.result.score,
          attempts: recursiveRes.result.totalAttempts,
          timestamp: new Date().toISOString(),
          recursivePlanner: true
        });
        
        completedSteps.push({
          id: subtask.id,
          status: 'completed',
          score: recursiveRes.result.score,
          attempts: recursiveRes.result.totalAttempts
        });
      } else {
        results.push({
          subtaskId: subtask.id,
          agent: subtask.agent,
          response: `Error en recursive planner: ${recursiveRes.error}`,
          score: 0,
          attempts: 0,
          timestamp: new Date().toISOString(),
          error: true
        });
        
        completedSteps.push({
          id: subtask.id,
          status: 'failed',
          error: recursiveRes.error
        });
      }
    }
    
    return {
      success: true,
      results,
      completedSteps,
      recursiveResults: recursiveResult,
      summary: recursiveResult.summary
    };
    
  } catch (error) {
    logger.error('Error en executeWithRecursivePlanner:', error);
    return {
      success: false,
      error: error.message,
      results: [],
      completedSteps: []
    };
  }
}

/**
 * Ejecuta el flujo normal sin recursive planner
 */
async function executeNormalFlow(state, plan, builderOutput) {
  // Ejecutar cada subtarea del plan de forma normal
  for (const subtask of plan.subtasks) {
    try {
      logger.info('OrchestrationService: Ejecutando subtarea normal', { 
        subtaskId: subtask.id,
        agent: subtask.agent 
      });
      
      // Guardar paso de ejecución
      const stepData = {
        sessionId: state.sessionId,
        stepType: STEP_TYPES.EXECUTION,
        stepName: subtask.id,
        agentUsed: subtask.agent,
        inputData: { subtask },
        status: STATUS.RUNNING
      };
      
      const stepResult = await saveStep(stepData);
      const stepId = stepResult.step.id;
      
      // Ejecutar subtarea según el agente
      let result;
      switch (subtask.agent) {
        case AGENT_TYPES.BUILDER:
          result = await executeBuilderTask(subtask, state);
          break;
        case AGENT_TYPES.RESEARCHER:
          result = await executeResearchTask(subtask, state);
          break;
        case AGENT_TYPES.JUDGE:
          result = await executeJudgeTask(subtask, state);
          break;
        default:
          result = await executeGenericTask(subtask, state);
      }
      
      // Actualizar paso
      await updateStep(stepId, {
        status: result.success ? STATUS.SUCCESS : STATUS.ERROR,
        outputData: result,
        errorMessage: result.success ? null : result.error,
        completedAt: new Date().toISOString(),
        durationMs: Date.now() - new Date(stepResult.step.started_at).getTime()
      });
      
      if (result.success) {
        builderOutput.results.push({
          subtaskId: subtask.id,
          agent: subtask.agent,
          response: result.response,
          timestamp: new Date().toISOString()
        });
        
        builderOutput.completedSteps.push({
          id: subtask.id,
          status: 'completed'
        });
      } else {
        builderOutput.errors.push({
          subtaskId: subtask.id,
          agent: subtask.agent,
          error: result.error,
          timestamp: new Date().toISOString()
        });
      }
      
    } catch (error) {
      logger.error('OrchestrationService: Error ejecutando subtarea', {
        subtaskId: subtask.id,
        error: error.message
      });
      
      builderOutput.errors.push({
        subtaskId: subtask.id,
        agent: subtask.agent,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
}

/**
 * Construye un prompt para una subtarea específica
 */
function buildSubtaskPrompt(subtask, originalRequest, plan) {
  return `CONTEXTO GENERAL:
Solicitud original del usuario: "${originalRequest}"

PLAN DE EJECUCIÓN:
Tipo de tarea: ${plan.taskType}
Complejidad: ${plan.complexity?.level} (${plan.complexity?.score}/5)

SUBTAREA ESPECÍFICA:
ID: ${subtask.id}
Descripción: ${subtask.description}
Agente asignado: ${subtask.agent}
Prioridad: ${subtask.priority}

INSTRUCCIONES:
${subtask.instructions || 'Ejecuta esta subtarea de la mejor manera posible, considerando el contexto general y los objetivos del usuario.'}

CRITERIOS DE ÉXITO:
- La respuesta debe ser específica y actionable
- Debe contribuir al objetivo general de la solicitud
- Debe ser coherente con el plan de ejecución
- Debe proporcionar valor tangible al usuario

Genera una respuesta completa y de alta calidad para esta subtarea.`;
}

/**
 * Nodo: Reward Shell - Evaluación mejorada
 */
async function rewardNode(state) {
  try {
    logger.info('OrchestrationService: Ejecutando reward shell', { 
      sessionId: state.sessionId 
    });
    
    if (!state.builderOutput) {
      throw new Error('No hay output del builder para evaluar');
    }
    
    // Guardar paso de evaluación
    const stepData = {
      sessionId: state.sessionId,
      stepType: STEP_TYPES.EVALUATION,
      stepName: 'reward_evaluation',
      agentUsed: 'rewardShell',
      inputData: { 
        builderOutput: state.builderOutput,
        originalRequest: state.originalRequest,
        recursivePlannerUsed: state.useRecursivePlanner
      },
      status: STATUS.RUNNING
    };
    
    const stepResult = await saveStep(stepData);
    const stepId = stepResult.step.id;
    
    // Evaluar output con reward shell
    const evaluationResult = await evaluateOutput(
      state.builderOutput, 
      state.originalRequest,
      {
        sessionId: state.sessionId,
        executionPlan: state.executionPlan,
        recursivePlannerResults: state.recursivePlannerResults
      }
    );
    
    if (!evaluationResult.success) {
      await updateStep(stepId, {
        status: STATUS.ERROR,
        errorMessage: evaluationResult.error,
        completedAt: new Date().toISOString()
      });
      throw new Error(`Error en reward shell: ${evaluationResult.error}`);
    }
    
    const evaluation = evaluationResult.evaluation;
    
    // Guardar recompensa
    await saveReward(state.sessionId, {
      stepId,
      score: evaluation.score,
      feedback: evaluation.feedback,
      retryRecommended: evaluation.retry,
      metadata: {
        evaluationType: 'final_evaluation',
        recursivePlannerUsed: state.useRecursivePlanner,
        qualityLevel: evaluation.qualityLevel
      }
    });
    
    // Actualizar paso como completado
    await updateStep(stepId, {
      status: STATUS.SUCCESS,
      outputData: { evaluation },
      completedAt: new Date().toISOString(),
      durationMs: Date.now() - new Date(stepResult.step.started_at).getTime()
    });
    
    // Determinar si se necesita retry con recursive planner
    const needsRecursiveRetry = !state.useRecursivePlanner && 
                               evaluation.retry && 
                               evaluation.score < RECURSIVE_PLANNER_CONFIG.failureThreshold &&
                               state.retryCount < state.maxRetries;
    
    logger.info('OrchestrationService: Reward shell completado', {
      sessionId: state.sessionId,
      score: evaluation.score,
      retry: evaluation.retry,
      needsRecursiveRetry
    });
    
    return {
      ...state,
      currentEvaluation: evaluation,
      shouldRetry: evaluation.retry,
      useRecursivePlanner: needsRecursiveRetry || state.useRecursivePlanner,
      completedSteps: [...(state.completedSteps || []), stepResult.step]
    };
    
  } catch (error) {
    logger.error('OrchestrationService: Error en reward node', { 
      sessionId: state.sessionId,
      error: error.message 
    });
    return {
      ...state,
      error: error.message
    };
  }
}

/**
 * Funciones de ejecución de tareas específicas
 */
async function executeBuilderTask(subtask, state) {
  try {
    // Implementar lógica específica del builder
    const response = `Builder ejecutó: ${subtask.description}`;
    return { success: true, response };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function executeResearchTask(subtask, state) {
  try {
    // Implementar lógica específica de investigación
    const response = `Investigación completada: ${subtask.description}`;
    return { success: true, response };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function executeJudgeTask(subtask, state) {
  try {
    // Implementar lógica específica del judge
    const response = `Evaluación completada: ${subtask.description}`;
    return { success: true, response };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function executeGenericTask(subtask, state) {
  try {
    // Implementar lógica genérica
    const response = `Tarea genérica completada: ${subtask.description}`;
    return { success: true, response };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Nodo: Finalización
 */
async function finalizationNode(state) {
  try {
    logger.info('OrchestrationService: Finalizando sesión', { 
      sessionId: state.sessionId 
    });
    
    const endTime = new Date().toISOString();
    const totalDuration = new Date(endTime).getTime() - new Date(state.startTime).getTime();
    
    // Actualizar estado de sesión
    await updateSessionStatus(state.sessionId, {
      status: state.error ? STATUS.ERROR : STATUS.SUCCESS,
      completedAt: endTime,
      metadata: {
        totalDuration,
        finalScore: state.currentEvaluation?.score,
        retryCount: state.retryCount,
        recursivePlannerUsed: state.useRecursivePlanner,
        error: state.error
      }
    });
    
    const finalResult = {
      sessionId: state.sessionId,
      success: !state.error,
      builderOutput: state.builderOutput,
      evaluation: state.currentEvaluation,
      totalDuration,
      retryCount: state.retryCount,
      recursivePlannerUsed: state.useRecursivePlanner,
      recursivePlannerResults: state.recursivePlannerResults,
      error: state.error
    };
    
    logger.info('OrchestrationService: Sesión finalizada', {
      sessionId: state.sessionId,
      success: !state.error,
      score: state.currentEvaluation?.score,
      duration: totalDuration
    });
    
    return {
      ...state,
      finalResult,
      endTime,
      totalDuration
    };
    
  } catch (error) {
    logger.error('OrchestrationService: Error en finalización', { 
      sessionId: state.sessionId,
      error: error.message 
    });
    return {
      ...state,
      error: error.message
    };
  }
}

/**
 * Función de decisión para el flujo
 */
function shouldRetry(state) {
  if (state.error) return END;
  if (!state.shouldRetry) return END;
  if (state.retryCount >= state.maxRetries) return END;
  return "builderNode";
}

/**
 * Crear el grafo de estado
 */
const createOrchestrationGraph = () => {
  const workflow = new StateGraph(agentState);
  
  // Agregar nodos
  workflow.addNode("initializeSession", initializeSession);
  workflow.addNode("reasoningNode", reasoningNode);
  workflow.addNode("builderNode", builderNode);
  workflow.addNode("rewardNode", rewardNode);
  workflow.addNode("finalizationNode", finalizationNode);
  
  // Definir flujo
  workflow.setEntryPoint("initializeSession");
  workflow.addEdge("initializeSession", "reasoningNode");
  workflow.addEdge("reasoningNode", "builderNode");
  workflow.addEdge("builderNode", "rewardNode");
  workflow.addConditionalEdges("rewardNode", shouldRetry, {
    "builderNode": "builderNode",
    [END]: "finalizationNode"
  });
  workflow.addEdge("finalizationNode", END);
  
  return workflow.compile();
};

/**
 * Función principal de orquestación con Langwatch
 */
export async function orchestrateTask(request, options = {}) {
  let orchestrationTracker = null;
  
  try {
    logger.info('OrchestrationService: Iniciando orquestación de tarea');
    
    // Inicializar tracker de Langwatch para orquestación
    if (isLangwatchEnabled()) {
      const sessionId = options.sessionId || `session_${Date.now()}`;
      orchestrationTracker = createOrchestrationTracker(sessionId, request);
      logger.info('🔍 Langwatch orchestration tracker inicializado');
    }
    
    const graph = createOrchestrationGraph();
    
    const initialState = {
      originalRequest: request,
      userId: options.userId || 'anonymous',
      maxRetries: options.maxRetries || 2,
      userAgent: options.userAgent,
      orchestrationTracker // Pasar tracker al estado
    };
    
    const result = await graph.invoke(initialState);
    
    // Finalizar tracking de orquestación
    if (orchestrationTracker) {
      await orchestrationTracker.finalize(result.finalResult);
      logger.info('🔍 Langwatch orchestration tracking finalizado');
    }
    
    logger.info('OrchestrationService: Orquestación completada', {
      sessionId: result.sessionId,
      success: !result.error
    });
    
    return {
      success: !result.error,
      sessionId: result.sessionId,
      result: result.finalResult,
      error: result.error
    };
    
  } catch (error) {
    logger.error('OrchestrationService: Error en orquestación', { error: error.message });
    
    // Finalizar tracking con error
    if (orchestrationTracker) {
      try {
        await orchestrationTracker.finalize({
          success: false,
          error: error.message
        });
        logger.info('🔍 Langwatch orchestration tracking finalizado con error');
      } catch (trackingError) {
        logger.warn('⚠️ Error finalizando orchestration tracking:', trackingError);
      }
    }
    
    throw new AppError(`Error en orquestación: ${error.message}`, 500);
  }
}

// Exportar funciones y configuraciones
export {
  initializeAllLlms,
  getBestLlmInstance,
  RECURSIVE_PLANNER_CONFIG,
  agentState,
  llmInstances
};

export default {
  orchestrateTask,
  initializeAllLlms,
  getBestLlmInstance,
  RECURSIVE_PLANNER_CONFIG
};

