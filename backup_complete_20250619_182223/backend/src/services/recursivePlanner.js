/**
 * Recursive Planner Service with Langwatch Integration
 * 
 * Módulo que implementa un sistema de planificación recursiva con:
 * - Recuperación de intentos previos desde memoryService
 * - Llamadas al LLM con contexto de intentos anteriores
 * - Evaluación con rewardShell
 * - Inyección de contradicción explícita en fallos múltiples
 * - Monitoreo completo con Langwatch
 * - Retorno de reply, tokens, attempts, score
 * 
 * @module recursivePlanner
 */

import { getContext, saveStep, saveReward } from './memoryService.js';
import { evaluateOutput } from './rewardShell.js';
import { createRecursiveTracker, isLangwatchEnabled } from '../middleware/langwatchMiddleware.js';
import logger from '../utils/logger.js';

/**
 * Configuración por defecto para el recursive planner
 */
const DEFAULT_CONFIG = {
  maxRetries: 3,
  scoreThreshold: 0.8,
  paradoxThreshold: 2, // Después de cuántos fallos inyectar contradicción
  tokenLimit: 4000,
  timeoutMs: 30000
};

/**
 * Ejecuta una tarea de razonamiento con retry recursivo e inyección de paradoja
 * 
 * @param {string} prompt - El prompt base a ejecutar
 * @param {string} sessionId - ID de sesión para tracking
 * @param {string} taskTag - Tag único de memoria para esta tarea
 * @param {object} options - Opciones de configuración
 * @param {object} llmInstance - Instancia del LLM a utilizar
 * @returns {object} Resultado final con reply, tokens, attempts, score
 */
export async function recursiveSolve(prompt, sessionId, taskTag, options = {}, llmInstance = null) {
  const config = { ...DEFAULT_CONFIG, ...options };
  const startTime = Date.now();
  
  // Inicializar tracker de Langwatch
  let langwatchTracker = null;
  if (isLangwatchEnabled()) {
    langwatchTracker = createRecursiveTracker(sessionId, taskTag, prompt);
    logger.info('🔍 Langwatch tracker inicializado para recursive solve');
  }
  
  try {
    logger.info(`🔄 Iniciando recursive solve para sesión ${sessionId}, tag: ${taskTag}`);
    
    // Recuperar contexto e intentos previos
    const contextResult = await getContext(sessionId, taskTag);
    let previousAttempts = [];
    
    if (contextResult.success && contextResult.context?.attempts) {
      previousAttempts = contextResult.context.attempts;
      logger.info(`📚 Recuperados ${previousAttempts.length} intentos previos`);
    }
    
    let currentAttempt = 0;
    let bestResult = null;
    let bestScore = 0;
    let allAttempts = [...previousAttempts];
    let totalTokens = 0;
    
    // Ciclo de intentos con mejora iterativa
    while (currentAttempt <= config.maxRetries) {
      const attemptStartTime = Date.now();
      
      try {
        logger.info(`🎯 Intento ${currentAttempt + 1}/${config.maxRetries + 1} para ${taskTag}`);
        
        // Construir prompt con contexto de intentos previos
        const enhancedPrompt = buildEnhancedPrompt(
          prompt, 
          allAttempts, 
          currentAttempt, 
          config.paradoxThreshold
        );
        
        // Detectar si se activará contradicción explícita
        const willTriggerContradiction = currentAttempt >= config.paradoxThreshold;
        if (willTriggerContradiction && langwatchTracker) {
          const failedAttempts = allAttempts.filter(a => a.score < config.scoreThreshold);
          await langwatchTracker.trackContradictionTrigger(
            currentAttempt + 1, 
            enhancedPrompt, 
            failedAttempts
          );
        }
        
        // Llamar al LLM
        const llmResult = await callLLMWithRetry(enhancedPrompt, llmInstance, config);
        
        if (!llmResult.success) {
          throw new Error(`LLM call failed: ${llmResult.error}`);
        }
        
        const { reply, tokens } = llmResult;
        totalTokens += tokens || 0;
        
        // Guardar el paso en memoria
        const stepResult = await saveStep(sessionId, {
          stepName: `recursive_attempt_${currentAttempt + 1}`,
          stepType: 'recursive_planning',
          agentUsed: 'recursivePlanner',
          input: enhancedPrompt,
          output: reply,
          metadata: {
            attemptNumber: currentAttempt + 1,
            taskTag,
            tokensUsed: tokens,
            duration: Date.now() - attemptStartTime,
            contradictionTriggered: willTriggerContradiction
          }
        });
        
        if (!stepResult.success) {
          logger.warn(`⚠️ No se pudo guardar el paso: ${stepResult.error}`);
        }
        
        // Evaluar el resultado con rewardShell
        const evaluationResult = await evaluateOutput(reply, prompt, {
          sessionId,
          stepId: stepResult.stepId,
          attemptNumber: currentAttempt + 1,
          previousAttempts: allAttempts
        });
        
        if (!evaluationResult.success) {
          throw new Error(`Evaluation failed: ${evaluationResult.error}`);
        }
        
        const { score, feedback, retry } = evaluationResult.evaluation;
        
        // Guardar la recompensa
        await saveReward(sessionId, {
          stepId: stepResult.stepId,
          score,
          feedback,
          retryRecommended: retry,
          metadata: {
            attemptNumber: currentAttempt + 1,
            taskTag,
            evaluationType: 'recursive_planning'
          }
        });
        
        // Trackear intento en Langwatch
        if (langwatchTracker) {
          await langwatchTracker.trackAttempt(
            currentAttempt + 1,
            enhancedPrompt,
            reply,
            score,
            feedback,
            tokens,
            Date.now() - attemptStartTime
          );
        }
        
        // Agregar intento actual a la lista
        allAttempts.push({
          attempt: currentAttempt + 1,
          prompt: enhancedPrompt,
          reply,
          score,
          feedback: feedback?.summary || '',
          timestamp: new Date().toISOString(),
          tokens
        });
        
        logger.info(`📊 Intento ${currentAttempt + 1} completado. Score: ${score.toFixed(3)}`);
        
        // Verificar si alcanzamos el umbral de calidad
        if (score >= config.scoreThreshold) {
          logger.info(`✅ Umbral de calidad alcanzado (${score.toFixed(3)} >= ${config.scoreThreshold})`);
          bestResult = {
            reply,
            score,
            feedback,
            attemptNumber: currentAttempt + 1,
            tokens
          };
          break;
        }
        
        // Mantener el mejor resultado hasta ahora
        if (score > bestScore) {
          bestScore = score;
          bestResult = {
            reply,
            score,
            feedback,
            attemptNumber: currentAttempt + 1,
            tokens
          };
        }
        
        currentAttempt++;
        
        // Verificar timeout
        if (Date.now() - startTime > config.timeoutMs) {
          logger.warn(`⏰ Timeout alcanzado para ${taskTag}`);
          break;
        }
        
      } catch (attemptError) {
        logger.error(`❌ Error en intento ${currentAttempt + 1}:`, attemptError);
        
        // Agregar intento fallido a la lista
        allAttempts.push({
          attempt: currentAttempt + 1,
          prompt: 'Error en la ejecución',
          reply: `Error: ${attemptError.message}`,
          score: 0,
          feedback: 'Intento fallido debido a error técnico',
          timestamp: new Date().toISOString(),
          tokens: 0,
          error: true
        });
        
        currentAttempt++;
      }
    }
    
    // Guardar contexto actualizado
    await saveContextUpdate(sessionId, taskTag, allAttempts);
    
    const totalDuration = Date.now() - startTime;
    
    // Preparar resultado final
    const finalResult = {
      reply: bestResult?.reply || 'No se pudo generar una respuesta satisfactoria',
      score: bestScore,
      feedback: bestResult?.feedback || { summary: 'Proceso completado sin alcanzar umbral óptimo' },
      attempts: allAttempts,
      totalAttempts: allAttempts.length,
      bestAttemptNumber: bestResult?.attemptNumber || 0,
      totalTokens,
      totalDuration,
      thresholdReached: bestScore >= config.scoreThreshold
    };
    
    // Finalizar tracking en Langwatch
    if (langwatchTracker) {
      await langwatchTracker.finalize(finalResult);
      logger.info('🔍 Langwatch tracking finalizado para recursive solve');
    }
    
    logger.info(`🏁 Recursive solve completado para ${taskTag}. Mejor score: ${bestScore.toFixed(3)}`);
    
    return {
      success: true,
      result: finalResult,
      metadata: {
        sessionId,
        taskTag,
        config,
        startTime: new Date(startTime).toISOString(),
        endTime: new Date().toISOString()
      }
    };
    
  } catch (error) {
    logger.error(`💥 Error crítico en recursive solve para ${taskTag}:`, error);
    
    // Finalizar tracking en Langwatch con error
    if (langwatchTracker) {
      try {
        const errorResult = {
          reply: 'Error en el proceso de planificación recursiva',
          score: 0,
          feedback: { summary: `Error: ${error.message}` },
          attempts: [],
          totalAttempts: 0,
          bestAttemptNumber: 0,
          totalTokens: 0,
          totalDuration: Date.now() - startTime,
          thresholdReached: false
        };
        await langwatchTracker.finalize(errorResult);
        logger.info('🔍 Langwatch tracking finalizado con error');
      } catch (trackingError) {
        logger.warn('⚠️ Error finalizando tracking en Langwatch:', trackingError);
      }
    }
    
    return {
      success: false,
      error: error.message,
      result: {
        reply: 'Error en el proceso de planificación recursiva',
        score: 0,
        feedback: { summary: `Error: ${error.message}` },
        attempts: [],
        totalAttempts: 0,
        bestAttemptNumber: 0,
        totalTokens: 0,
        totalDuration: Date.now() - startTime,
        thresholdReached: false
      },
      metadata: {
        sessionId,
        taskTag,
        error: error.message
      }
    };
  }
}

/**
 * Construye un prompt mejorado con contexto de intentos previos
 * 
 * @param {string} originalPrompt - Prompt original
 * @param {Array} attempts - Lista de intentos previos
 * @param {number} currentAttempt - Número del intento actual
 * @param {number} paradoxThreshold - Umbral para inyección de contradicción
 * @returns {string} Prompt mejorado
 */
function buildEnhancedPrompt(originalPrompt, attempts, currentAttempt, paradoxThreshold) {
  let enhancedPrompt = originalPrompt;
  
  // Si hay intentos previos, incluir contexto
  if (attempts.length > 0) {
    const recentAttempts = attempts.slice(-3); // Últimos 3 intentos para evitar prompts muy largos
    
    enhancedPrompt = `CONTEXTO DE INTENTOS PREVIOS:
${recentAttempts.map((attempt, index) => 
  `Intento ${attempt.attempt || index + 1} (Score: ${attempt.score?.toFixed(2) || 'N/A'}):
  Respuesta: ${attempt.reply}
  Feedback: ${attempt.feedback}
  ---`
).join('\n')}

TAREA ACTUAL:
${originalPrompt}

INSTRUCCIONES:
- Analiza los intentos previos y sus puntuaciones
- Identifica qué funcionó bien y qué necesita mejorar
- Genera una respuesta que supere las limitaciones anteriores`;
  }
  
  // Inyección de contradicción explícita después del umbral
  if (currentAttempt >= paradoxThreshold) {
    const failedAttempts = attempts.filter(a => a.score < 0.8);
    
    enhancedPrompt = `ANÁLISIS CRÍTICO REQUERIDO:

Has fallado ${failedAttempts.length} veces en esta tarea. Tus intentos previos fueron:

${failedAttempts.map((attempt, index) => 
  `FALLO ${index + 1}:
  Tu respuesta: "${attempt.reply}"
  Score obtenido: ${attempt.score?.toFixed(2) || '0.00'}
  Por qué falló: ${attempt.feedback}
  ---`
).join('\n')}

CONTRADICCIÓN EXPLÍCITA:
Claramente tu enfoque anterior no funcionó. Debes:

1. EXPLICAR específicamente por qué fallaron tus intentos anteriores
2. IDENTIFICAR los errores conceptuales o de ejecución
3. PROPONER un enfoque completamente diferente
4. IMPLEMENTAR la solución con una metodología nueva

TAREA ORIGINAL:
${originalPrompt}

REQUISITO CRÍTICO: No repitas los mismos errores. Si no puedes explicar por qué fallaste antes, no podrás tener éxito ahora.`;
  }
  
  return enhancedPrompt;
}

/**
 * Llama al LLM con manejo de errores y reintentos
 * 
 * @param {string} prompt - Prompt a enviar
 * @param {object} llmInstance - Instancia del LLM
 * @param {object} config - Configuración
 * @returns {object} Resultado de la llamada
 */
async function callLLMWithRetry(prompt, llmInstance, config) {
  const maxLLMRetries = 2;
  
  for (let retry = 0; retry <= maxLLMRetries; retry++) {
    try {
      if (!llmInstance) {
        throw new Error('No LLM instance provided');
      }
      
      // Truncar prompt si es muy largo
      const truncatedPrompt = prompt.length > config.tokenLimit * 3 
        ? prompt.substring(0, config.tokenLimit * 3) + '\n\n[PROMPT TRUNCATED DUE TO LENGTH]'
        : prompt;
      
      const response = await llmInstance.invoke(truncatedPrompt);
      
      return {
        success: true,
        reply: response.content || response.text || response,
        tokens: response.usage?.total_tokens || response.tokens || prompt.length / 4 // Estimación
      };
      
    } catch (error) {
      logger.warn(`⚠️ LLM call attempt ${retry + 1} failed:`, error.message);
      
      if (retry === maxLLMRetries) {
        return {
          success: false,
          error: `LLM call failed after ${maxLLMRetries + 1} attempts: ${error.message}`,
          reply: null,
          tokens: 0
        };
      }
      
      // Esperar antes del siguiente intento
      await new Promise(resolve => setTimeout(resolve, 1000 * (retry + 1)));
    }
  }
}

/**
 * Guarda la actualización del contexto en memoria
 * 
 * @param {string} sessionId - ID de sesión
 * @param {string} taskTag - Tag de la tarea
 * @param {Array} attempts - Lista de intentos
 */
async function saveContextUpdate(sessionId, taskTag, attempts) {
  try {
    const contextData = {
      taskTag,
      attempts,
      lastUpdated: new Date().toISOString(),
      totalAttempts: attempts.length,
      bestScore: Math.max(...attempts.map(a => a.score || 0))
    };
    
    // Aquí podrías implementar una función específica en memoryService
    // Por ahora, guardamos como un paso especial
    await saveStep(sessionId, {
      stepName: 'context_update',
      stepType: 'context_management',
      agentUsed: 'recursivePlanner',
      output: JSON.stringify(contextData),
      metadata: {
        taskTag,
        contextUpdate: true
      }
    });
    
  } catch (error) {
    logger.warn(`⚠️ No se pudo guardar actualización de contexto:`, error);
  }
}

/**
 * Función de utilidad para ejecutar múltiples tareas recursivas en paralelo
 * 
 * @param {Array} tasks - Lista de tareas a ejecutar
 * @param {string} sessionId - ID de sesión
 * @param {object} llmInstance - Instancia del LLM
 * @param {object} options - Opciones globales
 * @returns {object} Resultados de todas las tareas
 */
export async function recursiveSolveMultiple(tasks, sessionId, llmInstance, options = {}) {
  const startTime = Date.now();
  
  try {
    logger.info(`🔄 Iniciando recursive solve múltiple para ${tasks.length} tareas`);
    
    const results = await Promise.allSettled(
      tasks.map((task, index) => 
        recursiveSolve(
          task.prompt,
          sessionId,
          task.tag || `task_${index}`,
          { ...options, ...task.options },
          llmInstance
        )
      )
    );
    
    const successful = results.filter(r => r.status === 'fulfilled' && r.value.success);
    const failed = results.filter(r => r.status === 'rejected' || !r.value.success);
    
    logger.info(`✅ Recursive solve múltiple completado: ${successful.length}/${tasks.length} exitosas`);
    
    return {
      success: true,
      results: results.map(r => r.status === 'fulfilled' ? r.value : { success: false, error: r.reason }),
      summary: {
        total: tasks.length,
        successful: successful.length,
        failed: failed.length,
        totalDuration: Date.now() - startTime
      }
    };
    
  } catch (error) {
    logger.error(`💥 Error en recursive solve múltiple:`, error);
    
    return {
      success: false,
      error: error.message,
      results: [],
      summary: {
        total: tasks.length,
        successful: 0,
        failed: tasks.length,
        totalDuration: Date.now() - startTime
      }
    };
  }
}

export default {
  recursiveSolve,
  recursiveSolveMultiple,
  DEFAULT_CONFIG
};

