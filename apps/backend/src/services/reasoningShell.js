/**
 * Reasoning Shell Service
 * 
 * Este servicio recibe el input del usuario y lo procesa para:
 * - Dividir la tarea en subtareas o pasos manejables
 * - Decidir qué agente (Builder, Judge, etc.) ejecuta cada paso
 * - Retornar una lista estructurada de instrucciones
 * 
 * @module reasoningShell
 */

import { logger } from '../utils/logger.js';

/**
 * Tipos de agentes disponibles en el sistema
 */
const AGENT_TYPES = {
  BUILDER: 'builder',
  JUDGE: 'judge',
  FINALIZER: 'finalizer',
  RESEARCHER: 'researcher',
  VALIDATOR: 'validator'
};

/**
 * Tipos de tareas que el sistema puede manejar
 */
const TASK_TYPES = {
  WEB_DEVELOPMENT: 'web_development',
  DATA_ANALYSIS: 'data_analysis',
  CONTENT_CREATION: 'content_creation',
  API_INTEGRATION: 'api_integration',
  RESEARCH: 'research',
  VALIDATION: 'validation'
};

/**
 * Analiza el input del usuario y determina el tipo de tarea
 * @param {string} userInput - Input del usuario
 * @returns {string} Tipo de tarea identificado
 */
function analyzeTaskType(userInput) {
  const input = userInput.toLowerCase();
  
  // Patrones para identificar tipos de tareas
  const patterns = {
    [TASK_TYPES.WEB_DEVELOPMENT]: [
      'website', 'web app', 'frontend', 'backend', 'html', 'css', 'javascript',
      'react', 'vue', 'angular', 'api', 'server', 'database'
    ],
    [TASK_TYPES.DATA_ANALYSIS]: [
      'analyze', 'data', 'chart', 'graph', 'statistics', 'csv', 'excel',
      'visualization', 'report', 'metrics'
    ],
    [TASK_TYPES.CONTENT_CREATION]: [
      'write', 'create content', 'article', 'blog', 'documentation',
      'copy', 'text', 'content'
    ],
    [TASK_TYPES.API_INTEGRATION]: [
      'api', 'integration', 'connect', 'webhook', 'service', 'endpoint'
    ],
    [TASK_TYPES.RESEARCH]: [
      'research', 'find', 'search', 'investigate', 'gather information',
      'study', 'analyze'
    ]
  };

  // Buscar coincidencias con los patrones
  for (const [taskType, keywords] of Object.entries(patterns)) {
    if (keywords.some(keyword => input.includes(keyword))) {
      return taskType;
    }
  }

  // Tipo por defecto si no se encuentra coincidencia
  return TASK_TYPES.WEB_DEVELOPMENT;
}

/**
 * Divide una tarea en subtareas basado en su tipo
 * @param {string} userInput - Input original del usuario
 * @param {string} taskType - Tipo de tarea identificado
 * @returns {Array} Lista de subtareas
 */
function decomposeTask(userInput, taskType) {
  const subtasks = [];

  switch (taskType) {
    case TASK_TYPES.WEB_DEVELOPMENT:
      subtasks.push(
        {
          id: 'research_requirements',
          description: 'Analizar y definir los requerimientos del proyecto web',
          agent: AGENT_TYPES.RESEARCHER,
          priority: 1,
          dependencies: []
        },
        {
          id: 'design_architecture',
          description: 'Diseñar la arquitectura y estructura del proyecto',
          agent: AGENT_TYPES.BUILDER,
          priority: 2,
          dependencies: ['research_requirements']
        },
        {
          id: 'implement_frontend',
          description: 'Implementar la interfaz de usuario',
          agent: AGENT_TYPES.BUILDER,
          priority: 3,
          dependencies: ['design_architecture']
        },
        {
          id: 'implement_backend',
          description: 'Implementar la lógica del servidor y APIs',
          agent: AGENT_TYPES.BUILDER,
          priority: 4,
          dependencies: ['design_architecture']
        },
        {
          id: 'validate_implementation',
          description: 'Validar que la implementación cumple los requerimientos',
          agent: AGENT_TYPES.VALIDATOR,
          priority: 5,
          dependencies: ['implement_frontend', 'implement_backend']
        },
        {
          id: 'finalize_project',
          description: 'Finalizar el proyecto y preparar entrega',
          agent: AGENT_TYPES.FINALIZER,
          priority: 6,
          dependencies: ['validate_implementation']
        }
      );
      break;

    case TASK_TYPES.DATA_ANALYSIS:
      subtasks.push(
        {
          id: 'gather_data',
          description: 'Recopilar y preparar los datos para análisis',
          agent: AGENT_TYPES.RESEARCHER,
          priority: 1,
          dependencies: []
        },
        {
          id: 'analyze_data',
          description: 'Realizar análisis estadístico y identificar patrones',
          agent: AGENT_TYPES.BUILDER,
          priority: 2,
          dependencies: ['gather_data']
        },
        {
          id: 'create_visualizations',
          description: 'Crear gráficos y visualizaciones de los datos',
          agent: AGENT_TYPES.BUILDER,
          priority: 3,
          dependencies: ['analyze_data']
        },
        {
          id: 'validate_results',
          description: 'Validar la precisión y relevancia de los resultados',
          agent: AGENT_TYPES.VALIDATOR,
          priority: 4,
          dependencies: ['create_visualizations']
        },
        {
          id: 'generate_report',
          description: 'Generar reporte final con conclusiones',
          agent: AGENT_TYPES.FINALIZER,
          priority: 5,
          dependencies: ['validate_results']
        }
      );
      break;

    case TASK_TYPES.CONTENT_CREATION:
      subtasks.push(
        {
          id: 'research_topic',
          description: 'Investigar el tema y recopilar información relevante',
          agent: AGENT_TYPES.RESEARCHER,
          priority: 1,
          dependencies: []
        },
        {
          id: 'create_outline',
          description: 'Crear estructura y esquema del contenido',
          agent: AGENT_TYPES.BUILDER,
          priority: 2,
          dependencies: ['research_topic']
        },
        {
          id: 'write_content',
          description: 'Escribir el contenido siguiendo el esquema',
          agent: AGENT_TYPES.BUILDER,
          priority: 3,
          dependencies: ['create_outline']
        },
        {
          id: 'review_content',
          description: 'Revisar calidad, coherencia y precisión del contenido',
          agent: AGENT_TYPES.JUDGE,
          priority: 4,
          dependencies: ['write_content']
        },
        {
          id: 'finalize_content',
          description: 'Aplicar correcciones finales y formatear',
          agent: AGENT_TYPES.FINALIZER,
          priority: 5,
          dependencies: ['review_content']
        }
      );
      break;

    default:
      // Flujo genérico para tareas no específicas
      subtasks.push(
        {
          id: 'analyze_request',
          description: 'Analizar y entender la solicitud del usuario',
          agent: AGENT_TYPES.RESEARCHER,
          priority: 1,
          dependencies: []
        },
        {
          id: 'execute_task',
          description: 'Ejecutar la tarea principal',
          agent: AGENT_TYPES.BUILDER,
          priority: 2,
          dependencies: ['analyze_request']
        },
        {
          id: 'validate_output',
          description: 'Validar que el resultado cumple las expectativas',
          agent: AGENT_TYPES.VALIDATOR,
          priority: 3,
          dependencies: ['execute_task']
        },
        {
          id: 'finalize_result',
          description: 'Finalizar y entregar el resultado',
          agent: AGENT_TYPES.FINALIZER,
          priority: 4,
          dependencies: ['validate_output']
        }
      );
  }

  return subtasks;
}

/**
 * Estima la complejidad de una tarea basado en el input del usuario
 * @param {string} userInput - Input del usuario
 * @param {Array} subtasks - Lista de subtareas generadas
 * @returns {Object} Estimación de complejidad
 */
function estimateComplexity(userInput, subtasks) {
  const inputLength = userInput.length;
  const subtaskCount = subtasks.length;
  
  // Factores de complejidad
  let complexityScore = 0;
  
  // Basado en longitud del input
  if (inputLength > 500) complexityScore += 3;
  else if (inputLength > 200) complexityScore += 2;
  else complexityScore += 1;
  
  // Basado en número de subtareas
  complexityScore += Math.floor(subtaskCount / 2);
  
  // Palabras clave que indican complejidad
  const complexKeywords = [
    'integration', 'database', 'authentication', 'real-time',
    'scalable', 'microservices', 'api', 'deployment'
  ];
  
  const foundComplexKeywords = complexKeywords.filter(keyword => 
    userInput.toLowerCase().includes(keyword)
  );
  
  complexityScore += foundComplexKeywords.length;
  
  // Determinar nivel de complejidad
  let level;
  if (complexityScore <= 3) level = 'low';
  else if (complexityScore <= 6) level = 'medium';
  else level = 'high';
  
  return {
    score: complexityScore,
    level,
    estimatedTime: level === 'low' ? '15-30 min' : 
                   level === 'medium' ? '30-60 min' : '60+ min',
    factors: {
      inputLength,
      subtaskCount,
      complexKeywords: foundComplexKeywords
    }
  };
}

/**
 * Función principal del Reasoning Shell
 * Procesa el input del usuario y genera un plan de ejecución estructurado
 * 
 * @param {string} userInput - Input original del usuario
 * @param {Object} context - Contexto adicional (sesión, preferencias, etc.)
 * @returns {Object} Plan de ejecución estructurado
 */
export async function processUserInput(userInput, context = {}) {
  try {
    logger.info('ReasoningShell: Procesando input del usuario', { 
      inputLength: userInput.length,
      sessionId: context.sessionId 
    });

    // 1. Analizar tipo de tarea
    const taskType = analyzeTaskType(userInput);
    logger.info('ReasoningShell: Tipo de tarea identificado', { taskType });

    // 2. Descomponer en subtareas
    const subtasks = decomposeTask(userInput, taskType);
    logger.info('ReasoningShell: Subtareas generadas', { 
      subtaskCount: subtasks.length 
    });

    // 3. Estimar complejidad
    const complexity = estimateComplexity(userInput, subtasks);
    logger.info('ReasoningShell: Complejidad estimada', { complexity });

    // 4. Generar plan de ejecución
    const executionPlan = {
      id: `plan_${Date.now()}`,
      timestamp: new Date().toISOString(),
      originalInput: userInput,
      taskType,
      complexity,
      subtasks,
      context,
      metadata: {
        totalSteps: subtasks.length,
        estimatedDuration: complexity.estimatedTime,
        requiredAgents: [...new Set(subtasks.map(task => task.agent))],
        createdBy: 'reasoningShell',
        version: '1.0.0'
      }
    };

    logger.info('ReasoningShell: Plan de ejecución generado exitosamente', {
      planId: executionPlan.id,
      totalSteps: executionPlan.metadata.totalSteps
    });

    return {
      success: true,
      plan: executionPlan,
      message: 'Plan de ejecución generado exitosamente'
    };

  } catch (error) {
    logger.error('ReasoningShell: Error procesando input del usuario', {
      error: error.message,
      stack: error.stack,
      userInput: userInput.substring(0, 100) + '...'
    });

    return {
      success: false,
      error: error.message,
      message: 'Error al procesar el input del usuario'
    };
  }
}

/**
 * Valida si un plan de ejecución es válido
 * @param {Object} plan - Plan de ejecución a validar
 * @returns {Object} Resultado de la validación
 */
export function validateExecutionPlan(plan) {
  const errors = [];

  if (!plan.id) errors.push('Plan ID es requerido');
  if (!plan.originalInput) errors.push('Input original es requerido');
  if (!plan.taskType) errors.push('Tipo de tarea es requerido');
  if (!plan.subtasks || !Array.isArray(plan.subtasks)) {
    errors.push('Subtareas deben ser un array');
  } else if (plan.subtasks.length === 0) {
    errors.push('Debe haber al menos una subtarea');
  }

  // Validar cada subtarea
  plan.subtasks?.forEach((subtask, index) => {
    if (!subtask.id) errors.push(`Subtarea ${index}: ID es requerido`);
    if (!subtask.description) errors.push(`Subtarea ${index}: Descripción es requerida`);
    if (!subtask.agent) errors.push(`Subtarea ${index}: Agente es requerido`);
    if (typeof subtask.priority !== 'number') {
      errors.push(`Subtarea ${index}: Prioridad debe ser un número`);
    }
  });

  return {
    isValid: errors.length === 0,
    errors
  };
}

export { AGENT_TYPES, TASK_TYPES };

