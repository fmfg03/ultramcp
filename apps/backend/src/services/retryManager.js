/**
 * Retry Manager Service
 * 
 * Este servicio maneja la lógica de reintentos automáticos cuando
 * el reward shell determina que se necesita mejorar el resultado.
 * Limita a 2 reintentos por tarea para evitar bucles infinitos.
 * 
 * @module retryManager
 */

import { logger } from '../utils/logger.js';
import { updateStep, saveStep, STEP_TYPES, STATUS } from './memoryService.js';

/**
 * Configuración de reintentos
 */
const RETRY_CONFIG = {
  MAX_RETRIES: 2,
  RETRY_DELAY_MS: 1000,
  EXPONENTIAL_BACKOFF: true,
  RETRY_SCORE_THRESHOLD: 0.6
};

/**
 * Tipos de estrategias de retry
 */
const RETRY_STRATEGIES = {
  SIMPLE: 'simple',           // Retry simple con el mismo prompt
  ENHANCED: 'enhanced',       // Retry con prompt mejorado basado en feedback
  ALTERNATIVE: 'alternative', // Retry con agente alternativo
  DECOMPOSED: 'decomposed'    // Retry dividiendo la tarea en pasos más pequeños
};

/**
 * Razones comunes de retry
 */
const RETRY_REASONS = {
  LOW_QUALITY: 'low_quality',
  INCOMPLETE: 'incomplete',
  INCORRECT: 'incorrect',
  ERROR: 'error',
  TIMEOUT: 'timeout'
};

/**
 * Clase principal del Retry Manager
 */
class RetryManager {
  constructor() {
    this.activeRetries = new Map(); // sessionId -> retryInfo
    this.retryHistory = new Map();  // sessionId -> Array<retryAttempt>
  }

  /**
   * Determina si se debe realizar un retry
   * @param {Object} evaluation - Evaluación del reward shell
   * @param {Object} context - Contexto de la sesión
   * @returns {Object} Decisión de retry
   */
  shouldRetry(evaluation, context) {
    try {
      const sessionId = context.sessionId;
      const currentRetries = this.getCurrentRetryCount(sessionId);
      
      // Verificar límite de reintentos
      if (currentRetries >= RETRY_CONFIG.MAX_RETRIES) {
        logger.info('RetryManager: Límite de reintentos alcanzado', {
          sessionId,
          currentRetries,
          maxRetries: RETRY_CONFIG.MAX_RETRIES
        });
        
        return {
          shouldRetry: false,
          reason: 'max_retries_reached',
          currentRetries,
          maxRetries: RETRY_CONFIG.MAX_RETRIES
        };
      }

      // Verificar si el reward shell recomienda retry
      if (!evaluation.retry) {
        logger.info('RetryManager: Reward shell no recomienda retry', {
          sessionId,
          score: evaluation.score,
          qualityLevel: evaluation.qualityLevel
        });
        
        return {
          shouldRetry: false,
          reason: 'quality_acceptable',
          score: evaluation.score,
          qualityLevel: evaluation.qualityLevel
        };
      }

      // Verificar umbral de puntuación
      if (evaluation.score >= RETRY_CONFIG.RETRY_SCORE_THRESHOLD) {
        logger.info('RetryManager: Puntuación por encima del umbral de retry', {
          sessionId,
          score: evaluation.score,
          threshold: RETRY_CONFIG.RETRY_SCORE_THRESHOLD
        });
        
        return {
          shouldRetry: false,
          reason: 'score_above_threshold',
          score: evaluation.score,
          threshold: RETRY_CONFIG.RETRY_SCORE_THRESHOLD
        };
      }

      // Determinar estrategia de retry
      const strategy = this.determineRetryStrategy(evaluation, context, currentRetries);
      
      logger.info('RetryManager: Retry recomendado', {
        sessionId,
        strategy,
        currentRetries: currentRetries + 1,
        score: evaluation.score
      });

      return {
        shouldRetry: true,
        strategy,
        retryCount: currentRetries + 1,
        reason: this.determineRetryReason(evaluation),
        delayMs: this.calculateRetryDelay(currentRetries)
      };

    } catch (error) {
      logger.error('RetryManager: Error determinando retry', {
        error: error.message,
        sessionId: context.sessionId
      });
      
      return {
        shouldRetry: false,
        reason: 'error',
        error: error.message
      };
    }
  }

  /**
   * Ejecuta un retry con la estrategia determinada
   * @param {Object} retryDecision - Decisión de retry
   * @param {Object} originalContext - Contexto original
   * @param {Function} executeFunction - Función a ejecutar para el retry
   * @returns {Object} Resultado del retry
   */
  async executeRetry(retryDecision, originalContext, executeFunction) {
    try {
      const sessionId = originalContext.sessionId;
      const retryCount = retryDecision.retryCount;
      
      logger.info('RetryManager: Iniciando retry', {
        sessionId,
        retryCount,
        strategy: retryDecision.strategy
      });

      // Registrar intento de retry
      this.registerRetryAttempt(sessionId, retryDecision);

      // Aplicar delay si está configurado
      if (retryDecision.delayMs > 0) {
        await this.delay(retryDecision.delayMs);
      }

      // Guardar paso de retry
      const stepData = {
        sessionId,
        stepType: STEP_TYPES.RETRY,
        stepName: `retry_attempt_${retryCount}`,
        agentUsed: 'retryManager',
        inputData: {
          strategy: retryDecision.strategy,
          reason: retryDecision.reason,
          originalScore: originalContext.lastEvaluation?.score
        },
        status: STATUS.RUNNING
      };

      const stepResult = await saveStep(stepData);
      const stepId = stepResult.step.id;

      try {
        // Modificar contexto según la estrategia
        const modifiedContext = await this.applyRetryStrategy(
          retryDecision.strategy,
          originalContext,
          retryDecision
        );

        // Ejecutar función con contexto modificado
        const result = await executeFunction(modifiedContext);

        // Actualizar paso como exitoso
        await updateStep(stepId, {
          status: STATUS.SUCCESS,
          outputData: { result },
          completedAt: new Date().toISOString(),
          durationMs: Date.now() - new Date(stepResult.step.started_at).getTime()
        });

        logger.info('RetryManager: Retry completado exitosamente', {
          sessionId,
          retryCount,
          strategy: retryDecision.strategy
        });

        return {
          success: true,
          result,
          retryInfo: {
            count: retryCount,
            strategy: retryDecision.strategy,
            reason: retryDecision.reason
          }
        };

      } catch (executeError) {
        // Actualizar paso con error
        await updateStep(stepId, {
          status: STATUS.ERROR,
          errorMessage: executeError.message,
          completedAt: new Date().toISOString(),
          durationMs: Date.now() - new Date(stepResult.step.started_at).getTime()
        });

        throw executeError;
      }

    } catch (error) {
      logger.error('RetryManager: Error ejecutando retry', {
        sessionId: originalContext.sessionId,
        retryCount: retryDecision.retryCount,
        error: error.message
      });

      return {
        success: false,
        error: error.message,
        retryInfo: {
          count: retryDecision.retryCount,
          strategy: retryDecision.strategy,
          reason: retryDecision.reason
        }
      };
    }
  }

  /**
   * Determina la estrategia de retry más apropiada
   * @param {Object} evaluation - Evaluación actual
   * @param {Object} context - Contexto de la sesión
   * @param {number} currentRetries - Número actual de reintentos
   * @returns {string} Estrategia de retry
   */
  determineRetryStrategy(evaluation, context, currentRetries) {
    // En el primer retry, usar estrategia enhanced
    if (currentRetries === 0) {
      return RETRY_STRATEGIES.ENHANCED;
    }

    // En el segundo retry, usar estrategia alternativa o decomposed
    if (currentRetries === 1) {
      // Si la completitud es baja, descomponer la tarea
      if (evaluation.evaluations?.completeness?.score < 0.5) {
        return RETRY_STRATEGIES.DECOMPOSED;
      }
      // Si la calidad técnica es baja, usar agente alternativo
      return RETRY_STRATEGIES.ALTERNATIVE;
    }

    // Fallback a estrategia simple
    return RETRY_STRATEGIES.SIMPLE;
  }

  /**
   * Determina la razón del retry basada en la evaluación
   * @param {Object} evaluation - Evaluación del reward shell
   * @returns {string} Razón del retry
   */
  determineRetryReason(evaluation) {
    if (evaluation.score < 0.3) {
      return RETRY_REASONS.LOW_QUALITY;
    }
    
    if (evaluation.evaluations?.completeness?.score < 0.5) {
      return RETRY_REASONS.INCOMPLETE;
    }
    
    if (evaluation.evaluations?.objectiveFulfillment?.score < 0.5) {
      return RETRY_REASONS.INCORRECT;
    }
    
    return RETRY_REASONS.LOW_QUALITY;
  }

  /**
   * Aplica la estrategia de retry modificando el contexto
   * @param {string} strategy - Estrategia a aplicar
   * @param {Object} context - Contexto original
   * @param {Object} retryDecision - Decisión de retry
   * @returns {Object} Contexto modificado
   */
  async applyRetryStrategy(strategy, context, retryDecision) {
    const modifiedContext = { ...context };

    switch (strategy) {
      case RETRY_STRATEGIES.SIMPLE:
        // No modificar el contexto, usar el mismo prompt
        break;

      case RETRY_STRATEGIES.ENHANCED:
        // Mejorar el prompt con feedback específico
        modifiedContext.enhancedPrompt = this.buildEnhancedPrompt(
          context.originalRequest,
          context.lastEvaluation
        );
        break;

      case RETRY_STRATEGIES.ALTERNATIVE:
        // Cambiar el agente o modelo LLM
        modifiedContext.alternativeAgent = true;
        modifiedContext.preferredModel = this.selectAlternativeModel(context);
        break;

      case RETRY_STRATEGIES.DECOMPOSED:
        // Dividir la tarea en pasos más pequeños
        modifiedContext.decomposedTasks = await this.decomposeTasks(
          context.executionPlan,
          context.lastEvaluation
        );
        break;
    }

    // Agregar información de retry al contexto
    modifiedContext.retryInfo = {
      count: retryDecision.retryCount,
      strategy,
      reason: retryDecision.reason,
      previousScore: context.lastEvaluation?.score
    };

    return modifiedContext;
  }

  /**
   * Construye un prompt mejorado basado en el feedback
   * @param {string} originalRequest - Solicitud original
   * @param {Object} evaluation - Evaluación anterior
   * @returns {string} Prompt mejorado
   */
  buildEnhancedPrompt(originalRequest, evaluation) {
    let enhancedPrompt = originalRequest;

    if (evaluation?.feedback?.improvements?.length > 0) {
      enhancedPrompt += '\n\nMejoras necesarias basadas en evaluación anterior:\n';
      evaluation.feedback.improvements.forEach((improvement, index) => {
        enhancedPrompt += `${index + 1}. ${improvement}\n`;
      });
    }

    if (evaluation?.feedback?.recommendations?.length > 0) {
      enhancedPrompt += '\nRecomendaciones específicas:\n';
      evaluation.feedback.recommendations.forEach((rec, index) => {
        enhancedPrompt += `${index + 1}. ${rec}\n`;
      });
    }

    enhancedPrompt += '\n\nPor favor, aborda específicamente estos puntos en tu respuesta.';

    return enhancedPrompt;
  }

  /**
   * Selecciona un modelo alternativo para el retry
   * @param {Object} context - Contexto actual
   * @returns {string} Modelo alternativo
   */
  selectAlternativeModel(context) {
    const currentModel = context.modelUsed || 'openai';
    
    // Rotar entre modelos disponibles
    const modelRotation = {
      'openai': 'anthropic',
      'anthropic': 'google',
      'google': 'openai'
    };

    return modelRotation[currentModel] || 'anthropic';
  }

  /**
   * Descompone las tareas en pasos más pequeños
   * @param {Object} executionPlan - Plan de ejecución original
   * @param {Object} evaluation - Evaluación anterior
   * @returns {Array} Tareas descompuestas
   */
  async decomposeTasks(executionPlan, evaluation) {
    // Identificar tareas que fallaron o tuvieron baja puntuación
    const problematicTasks = executionPlan.subtasks.filter(task => {
      // Lógica para identificar tareas problemáticas
      return true; // Simplificado por ahora
    });

    // Dividir cada tarea problemática en subtareas más pequeñas
    const decomposedTasks = [];
    
    for (const task of problematicTasks) {
      const subtasks = this.splitTaskIntoSubtasks(task);
      decomposedTasks.push(...subtasks);
    }

    return decomposedTasks;
  }

  /**
   * Divide una tarea en subtareas más pequeñas
   * @param {Object} task - Tarea a dividir
   * @returns {Array} Subtareas
   */
  splitTaskIntoSubtasks(task) {
    // Implementación simplificada
    return [
      {
        ...task,
        id: `${task.id}_part_1`,
        description: `Primera parte: ${task.description}`,
        priority: task.priority
      },
      {
        ...task,
        id: `${task.id}_part_2`,
        description: `Segunda parte: ${task.description}`,
        priority: task.priority + 0.1
      }
    ];
  }

  /**
   * Calcula el delay para el retry con backoff exponencial
   * @param {number} retryCount - Número de retry actual
   * @returns {number} Delay en milisegundos
   */
  calculateRetryDelay(retryCount) {
    if (!RETRY_CONFIG.EXPONENTIAL_BACKOFF) {
      return RETRY_CONFIG.RETRY_DELAY_MS;
    }

    return RETRY_CONFIG.RETRY_DELAY_MS * Math.pow(2, retryCount);
  }

  /**
   * Obtiene el número actual de reintentos para una sesión
   * @param {string} sessionId - ID de la sesión
   * @returns {number} Número de reintentos
   */
  getCurrentRetryCount(sessionId) {
    const retryHistory = this.retryHistory.get(sessionId) || [];
    return retryHistory.length;
  }

  /**
   * Registra un intento de retry
   * @param {string} sessionId - ID de la sesión
   * @param {Object} retryDecision - Decisión de retry
   */
  registerRetryAttempt(sessionId, retryDecision) {
    if (!this.retryHistory.has(sessionId)) {
      this.retryHistory.set(sessionId, []);
    }

    const retryHistory = this.retryHistory.get(sessionId);
    retryHistory.push({
      timestamp: new Date().toISOString(),
      retryCount: retryDecision.retryCount,
      strategy: retryDecision.strategy,
      reason: retryDecision.reason
    });

    // Actualizar información activa
    this.activeRetries.set(sessionId, {
      currentRetries: retryDecision.retryCount,
      lastRetryTime: new Date().toISOString(),
      strategy: retryDecision.strategy
    });
  }

  /**
   * Obtiene el historial de reintentos para una sesión
   * @param {string} sessionId - ID de la sesión
   * @returns {Array} Historial de reintentos
   */
  getRetryHistory(sessionId) {
    return this.retryHistory.get(sessionId) || [];
  }

  /**
   * Limpia el historial de reintentos para una sesión
   * @param {string} sessionId - ID de la sesión
   */
  clearRetryHistory(sessionId) {
    this.retryHistory.delete(sessionId);
    this.activeRetries.delete(sessionId);
  }

  /**
   * Obtiene estadísticas de reintentos
   * @returns {Object} Estadísticas
   */
  getRetryStats() {
    const stats = {
      activeSessions: this.activeRetries.size,
      totalSessions: this.retryHistory.size,
      averageRetries: 0,
      strategyUsage: {},
      reasonDistribution: {}
    };

    let totalRetries = 0;
    
    for (const [sessionId, history] of this.retryHistory.entries()) {
      totalRetries += history.length;
      
      history.forEach(attempt => {
        // Contar estrategias
        stats.strategyUsage[attempt.strategy] = 
          (stats.strategyUsage[attempt.strategy] || 0) + 1;
        
        // Contar razones
        stats.reasonDistribution[attempt.reason] = 
          (stats.reasonDistribution[attempt.reason] || 0) + 1;
      });
    }

    stats.averageRetries = stats.totalSessions > 0 ? 
      totalRetries / stats.totalSessions : 0;

    return stats;
  }

  /**
   * Función de utilidad para delay
   * @param {number} ms - Milisegundos a esperar
   * @returns {Promise} Promise que se resuelve después del delay
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Instancia singleton del RetryManager
const retryManager = new RetryManager();

export default retryManager;
export { 
  RetryManager, 
  RETRY_CONFIG, 
  RETRY_STRATEGIES, 
  RETRY_REASONS 
};

