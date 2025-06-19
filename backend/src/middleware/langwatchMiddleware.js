/**
 * Langwatch Middleware
 * 
 * Middleware para auditar y monitorear el sistema recursivo de planificación
 * con Langwatch, proporcionando visibilidad completa del proceso de mejora iterativa
 * 
 * @module langwatchMiddleware
 */

import { LangWatch } from 'langwatch';
import logger from '../utils/logger.js';

/**
 * Configuración de Langwatch
 */
const LANGWATCH_CONFIG = {
  apiKey: process.env.LANGWATCH_API_KEY,
  endpoint: process.env.LANGWATCH_ENDPOINT || 'https://app.langwatch.ai',
  projectId: process.env.LANGWATCH_PROJECT_ID || 'mcp-recursive-system',
  environment: process.env.NODE_ENV || 'development',
  
  // Configuración específica para recursive planner
  trackRecursiveAttempts: true,
  trackScoreProgression: true,
  trackContradictionTriggers: true,
  trackPatternAnalysis: true,
  
  // Configuración de sampling
  samplingRate: parseFloat(process.env.LANGWATCH_SAMPLING_RATE) || 1.0,
  
  // Configuración de alertas
  alertOnLowScore: true,
  alertOnHighRetryCount: true,
  alertOnStagnation: true,
  
  // Configuración de métricas
  enableCustomMetrics: true,
  enablePerformanceTracking: true,
  enableErrorTracking: true
};

/**
 * Instancia de Langwatch
 */
let langwatchClient = null;

/**
 * Inicializa el cliente de Langwatch
 */
export function initializeLangwatch() {
  try {
    if (!LANGWATCH_CONFIG.apiKey) {
      logger.warn('🔍 LANGWATCH_API_KEY no configurado. Monitoring deshabilitado.');
      return false;
    }
    
    langwatchClient = new LangWatch({
      apiKey: LANGWATCH_CONFIG.apiKey,
      endpoint: LANGWATCH_CONFIG.endpoint,
      projectId: LANGWATCH_CONFIG.projectId,
      environment: LANGWATCH_CONFIG.environment
    });
    
    logger.info('🔍 Langwatch inicializado correctamente', {
      projectId: LANGWATCH_CONFIG.projectId,
      environment: LANGWATCH_CONFIG.environment
    });
    
    return true;
  } catch (error) {
    logger.error('❌ Error inicializando Langwatch:', error);
    return false;
  }
}

/**
 * Verifica si Langwatch está disponible
 */
export function isLangwatchEnabled() {
  return langwatchClient !== null;
}

/**
 * Middleware para trackear sesiones de recursive planner
 */
export class RecursivePlannerTracker {
  constructor(sessionId, taskTag, originalPrompt) {
    this.sessionId = sessionId;
    this.taskTag = taskTag;
    this.originalPrompt = originalPrompt;
    this.traceId = `recursive_${sessionId}_${taskTag}_${Date.now()}`;
    this.attempts = [];
    this.startTime = Date.now();
    this.metadata = {
      sessionId,
      taskTag,
      originalPrompt: originalPrompt.substring(0, 500) + '...',
      startTime: new Date().toISOString()
    };
    
    if (isLangwatchEnabled()) {
      this.initializeTrace();
    }
  }
  
  /**
   * Inicializa el trace en Langwatch
   */
  async initializeTrace() {
    try {
      if (!langwatchClient) return;
      
      await langwatchClient.trace.start({
        traceId: this.traceId,
        userId: this.sessionId,
        metadata: {
          ...this.metadata,
          type: 'recursive_planning',
          component: 'recursivePlanner'
        },
        tags: ['recursive-planner', 'mcp-system', this.taskTag]
      });
      
      logger.debug('🔍 Langwatch trace iniciado', { traceId: this.traceId });
    } catch (error) {
      logger.warn('⚠️ Error iniciando trace en Langwatch:', error);
    }
  }
  
  /**
   * Trackea un intento individual
   */
  async trackAttempt(attemptNumber, prompt, response, score, feedback, tokens, duration) {
    try {
      const attempt = {
        attemptNumber,
        prompt: prompt.substring(0, 1000) + (prompt.length > 1000 ? '...' : ''),
        response: response.substring(0, 1000) + (response.length > 1000 ? '...' : ''),
        score,
        feedback: feedback?.summary || feedback,
        tokens,
        duration,
        timestamp: new Date().toISOString()
      };
      
      this.attempts.push(attempt);
      
      if (!langwatchClient) return;
      
      // Crear span para este intento
      const spanId = `attempt_${attemptNumber}_${Date.now()}`;
      
      await langwatchClient.span.create({
        traceId: this.traceId,
        spanId,
        name: `Recursive Attempt ${attemptNumber}`,
        type: 'llm',
        input: prompt,
        output: response,
        metadata: {
          attemptNumber,
          score,
          feedback,
          tokens,
          duration,
          taskTag: this.taskTag,
          isRecursiveAttempt: true
        },
        metrics: {
          score,
          tokens,
          duration,
          attemptNumber
        },
        tags: [
          'recursive-attempt',
          `attempt-${attemptNumber}`,
          score >= 0.8 ? 'high-score' : score >= 0.6 ? 'medium-score' : 'low-score'
        ]
      });
      
      // Trackear progresión de score
      await this.trackScoreProgression();
      
      logger.debug('🔍 Intento trackeado en Langwatch', {
        traceId: this.traceId,
        attemptNumber,
        score,
        tokens
      });
      
    } catch (error) {
      logger.warn('⚠️ Error trackeando intento en Langwatch:', error);
    }
  }
  
  /**
   * Trackea cuando se activa la contradicción explícita
   */
  async trackContradictionTrigger(attemptNumber, contradictionPrompt, previousFailures) {
    try {
      if (!langwatchClient) return;
      
      const spanId = `contradiction_${attemptNumber}_${Date.now()}`;
      
      await langwatchClient.span.create({
        traceId: this.traceId,
        spanId,
        name: `Contradiction Trigger - Attempt ${attemptNumber}`,
        type: 'reasoning',
        input: contradictionPrompt,
        metadata: {
          attemptNumber,
          previousFailures: previousFailures.length,
          contradictionTriggered: true,
          taskTag: this.taskTag,
          failureAnalysis: previousFailures.map(f => ({
            attempt: f.attempt,
            score: f.score,
            feedback: f.feedback
          }))
        },
        tags: [
          'contradiction-trigger',
          'critical-analysis',
          'failure-recovery',
          `failures-${previousFailures.length}`
        ]
      });
      
      // Crear evento personalizado
      await langwatchClient.event.create({
        traceId: this.traceId,
        type: 'contradiction_triggered',
        data: {
          attemptNumber,
          previousFailures: previousFailures.length,
          taskTag: this.taskTag,
          timestamp: new Date().toISOString()
        }
      });
      
      logger.info('🔍 Contradicción explícita trackeada', {
        traceId: this.traceId,
        attemptNumber,
        previousFailures: previousFailures.length
      });
      
    } catch (error) {
      logger.warn('⚠️ Error trackeando contradicción en Langwatch:', error);
    }
  }
  
  /**
   * Trackea la progresión de scores
   */
  async trackScoreProgression() {
    try {
      if (!langwatchClient || this.attempts.length < 2) return;
      
      const scores = this.attempts.map(a => a.score);
      const isImproving = scores[scores.length - 1] > scores[scores.length - 2];
      const averageScore = scores.reduce((a, b) => a + b, 0) / scores.length;
      const scoreVariance = this.calculateVariance(scores);
      
      await langwatchClient.metric.record({
        traceId: this.traceId,
        name: 'score_progression',
        value: scores[scores.length - 1],
        metadata: {
          isImproving,
          averageScore,
          scoreVariance,
          totalAttempts: this.attempts.length,
          scoreHistory: scores,
          taskTag: this.taskTag
        }
      });
      
      // Detectar estancamiento
      if (this.attempts.length >= 3) {
        const lastThreeScores = scores.slice(-3);
        const isStagnant = Math.max(...lastThreeScores) - Math.min(...lastThreeScores) < 0.1;
        
        if (isStagnant && LANGWATCH_CONFIG.alertOnStagnation) {
          await this.createAlert('score_stagnation', {
            message: 'Score progression stagnant for 3 attempts',
            scores: lastThreeScores,
            taskTag: this.taskTag
          });
        }
      }
      
    } catch (error) {
      logger.warn('⚠️ Error trackeando progresión de scores:', error);
    }
  }
  
  /**
   * Finaliza el tracking de la sesión recursiva
   */
  async finalize(finalResult) {
    try {
      const endTime = Date.now();
      const totalDuration = endTime - this.startTime;
      
      if (!langwatchClient) return;
      
      // Finalizar trace
      await langwatchClient.trace.end({
        traceId: this.traceId,
        output: finalResult.reply,
        metadata: {
          ...this.metadata,
          finalScore: finalResult.score,
          totalAttempts: finalResult.totalAttempts,
          bestAttemptNumber: finalResult.bestAttemptNumber,
          totalTokens: finalResult.totalTokens,
          totalDuration,
          thresholdReached: finalResult.thresholdReached,
          endTime: new Date().toISOString()
        },
        metrics: {
          finalScore: finalResult.score,
          totalAttempts: finalResult.totalAttempts,
          totalTokens: finalResult.totalTokens,
          totalDuration,
          efficiency: finalResult.score / finalResult.totalAttempts // Score per attempt
        },
        tags: [
          finalResult.thresholdReached ? 'success' : 'partial-success',
          `attempts-${finalResult.totalAttempts}`,
          finalResult.score >= 0.8 ? 'high-quality' : 'needs-improvement'
        ]
      });
      
      // Crear métricas de resumen
      await this.createSummaryMetrics(finalResult, totalDuration);
      
      // Crear alertas si es necesario
      await this.createFinalAlerts(finalResult);
      
      logger.info('🔍 Sesión recursiva finalizada en Langwatch', {
        traceId: this.traceId,
        finalScore: finalResult.score,
        totalAttempts: finalResult.totalAttempts,
        duration: totalDuration
      });
      
    } catch (error) {
      logger.warn('⚠️ Error finalizando tracking en Langwatch:', error);
    }
  }
  
  /**
   * Crea métricas de resumen
   */
  async createSummaryMetrics(finalResult, totalDuration) {
    try {
      if (!langwatchClient) return;
      
      const metrics = [
        {
          name: 'recursive_session_score',
          value: finalResult.score,
          tags: ['final-score', this.taskTag]
        },
        {
          name: 'recursive_session_attempts',
          value: finalResult.totalAttempts,
          tags: ['attempt-count', this.taskTag]
        },
        {
          name: 'recursive_session_duration',
          value: totalDuration,
          tags: ['duration', this.taskTag]
        },
        {
          name: 'recursive_session_tokens',
          value: finalResult.totalTokens,
          tags: ['token-usage', this.taskTag]
        },
        {
          name: 'recursive_session_efficiency',
          value: finalResult.score / finalResult.totalAttempts,
          tags: ['efficiency', this.taskTag]
        }
      ];
      
      for (const metric of metrics) {
        await langwatchClient.metric.record({
          traceId: this.traceId,
          ...metric,
          metadata: {
            sessionId: this.sessionId,
            taskTag: this.taskTag,
            timestamp: new Date().toISOString()
          }
        });
      }
      
    } catch (error) {
      logger.warn('⚠️ Error creando métricas de resumen:', error);
    }
  }
  
  /**
   * Crea alertas finales si es necesario
   */
  async createFinalAlerts(finalResult) {
    try {
      if (!langwatchClient) return;
      
      // Alerta por score bajo
      if (LANGWATCH_CONFIG.alertOnLowScore && finalResult.score < 0.6) {
        await this.createAlert('low_final_score', {
          message: `Final score below threshold: ${finalResult.score}`,
          score: finalResult.score,
          attempts: finalResult.totalAttempts,
          taskTag: this.taskTag
        });
      }
      
      // Alerta por muchos reintentos
      if (LANGWATCH_CONFIG.alertOnHighRetryCount && finalResult.totalAttempts > 5) {
        await this.createAlert('high_retry_count', {
          message: `High retry count: ${finalResult.totalAttempts} attempts`,
          attempts: finalResult.totalAttempts,
          finalScore: finalResult.score,
          taskTag: this.taskTag
        });
      }
      
    } catch (error) {
      logger.warn('⚠️ Error creando alertas finales:', error);
    }
  }
  
  /**
   * Crea una alerta en Langwatch
   */
  async createAlert(type, data) {
    try {
      if (!langwatchClient) return;
      
      await langwatchClient.alert.create({
        traceId: this.traceId,
        type,
        severity: type.includes('low_score') ? 'warning' : 'info',
        message: data.message,
        data: {
          ...data,
          sessionId: this.sessionId,
          timestamp: new Date().toISOString()
        }
      });
      
      logger.warn(`🚨 Alerta creada en Langwatch: ${type}`, data);
      
    } catch (error) {
      logger.warn('⚠️ Error creando alerta en Langwatch:', error);
    }
  }
  
  /**
   * Calcula la varianza de un array de números
   */
  calculateVariance(numbers) {
    const mean = numbers.reduce((a, b) => a + b, 0) / numbers.length;
    const squaredDiffs = numbers.map(num => Math.pow(num - mean, 2));
    return squaredDiffs.reduce((a, b) => a + b, 0) / numbers.length;
  }
}

/**
 * Middleware para trackear operaciones del orchestration service
 */
export class OrchestrationTracker {
  constructor(sessionId, originalRequest) {
    this.sessionId = sessionId;
    this.originalRequest = originalRequest;
    this.traceId = `orchestration_${sessionId}_${Date.now()}`;
    this.startTime = Date.now();
    this.steps = [];
    
    if (isLangwatchEnabled()) {
      this.initializeTrace();
    }
  }
  
  async initializeTrace() {
    try {
      if (!langwatchClient) return;
      
      await langwatchClient.trace.start({
        traceId: this.traceId,
        userId: this.sessionId,
        metadata: {
          sessionId: this.sessionId,
          originalRequest: this.originalRequest.substring(0, 500) + '...',
          startTime: new Date().toISOString(),
          type: 'orchestration',
          component: 'orchestrationService'
        },
        tags: ['orchestration', 'mcp-system', 'workflow']
      });
      
    } catch (error) {
      logger.warn('⚠️ Error iniciando trace de orquestación:', error);
    }
  }
  
  async trackStep(stepName, stepType, input, output, duration, metadata = {}) {
    try {
      if (!langwatchClient) return;
      
      const spanId = `${stepName}_${Date.now()}`;
      
      await langwatchClient.span.create({
        traceId: this.traceId,
        spanId,
        name: stepName,
        type: stepType,
        input: typeof input === 'string' ? input : JSON.stringify(input),
        output: typeof output === 'string' ? output : JSON.stringify(output),
        metadata: {
          ...metadata,
          sessionId: this.sessionId,
          stepType,
          duration
        },
        metrics: {
          duration
        },
        tags: [stepType, 'orchestration-step']
      });
      
      this.steps.push({
        stepName,
        stepType,
        duration,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.warn('⚠️ Error trackeando paso de orquestación:', error);
    }
  }
  
  async finalize(finalResult) {
    try {
      if (!langwatchClient) return;
      
      const totalDuration = Date.now() - this.startTime;
      
      await langwatchClient.trace.end({
        traceId: this.traceId,
        output: JSON.stringify(finalResult),
        metadata: {
          sessionId: this.sessionId,
          success: finalResult.success,
          totalSteps: this.steps.length,
          totalDuration,
          endTime: new Date().toISOString()
        },
        metrics: {
          totalDuration,
          totalSteps: this.steps.length,
          success: finalResult.success ? 1 : 0
        },
        tags: [
          finalResult.success ? 'success' : 'failure',
          'orchestration-complete'
        ]
      });
      
    } catch (error) {
      logger.warn('⚠️ Error finalizando trace de orquestación:', error);
    }
  }
}

/**
 * Función helper para crear un tracker de recursive planner
 */
export function createRecursiveTracker(sessionId, taskTag, originalPrompt) {
  return new RecursivePlannerTracker(sessionId, taskTag, originalPrompt);
}

/**
 * Función helper para crear un tracker de orquestación
 */
export function createOrchestrationTracker(sessionId, originalRequest) {
  return new OrchestrationTracker(sessionId, originalRequest);
}

/**
 * Middleware express para trackear requests
 */
export function langwatchRequestMiddleware() {
  return (req, res, next) => {
    if (!isLangwatchEnabled()) {
      return next();
    }
    
    const startTime = Date.now();
    const requestId = req.id || `req_${Date.now()}`;
    
    // Trackear request
    req.langwatchTracker = {
      requestId,
      startTime,
      endpoint: req.path,
      method: req.method
    };
    
    // Interceptar response
    const originalSend = res.send;
    res.send = function(data) {
      const duration = Date.now() - startTime;
      
      // Trackear response (async, no bloquear)
      setImmediate(async () => {
        try {
          if (langwatchClient) {
            await langwatchClient.metric.record({
              name: 'api_request',
              value: duration,
              metadata: {
                requestId,
                endpoint: req.path,
                method: req.method,
                statusCode: res.statusCode,
                duration
              },
              tags: ['api-request', req.method.toLowerCase(), req.path.replace(/\//g, '-')]
            });
          }
        } catch (error) {
          logger.warn('⚠️ Error trackeando request en Langwatch:', error);
        }
      });
      
      return originalSend.call(this, data);
    };
    
    next();
  };
}

/**
 * Instancia singleton del middleware
 */
export const langwatchMiddleware = {
  initializeLangwatch,
  isLangwatchEnabled,
  RecursivePlannerTracker,
  OrchestrationTracker,
  createRecursiveTracker,
  createOrchestrationTracker,
  langwatchRequestMiddleware,
  LANGWATCH_CONFIG,
  
  // Métodos adicionales para compatibilidad
  trackLLMCall: async (data) => {
    if (!isLangwatchEnabled()) return;
    // Implementación básica
    logger.info('Tracking LLM call:', data);
  },
  
  trackLLMResponse: async (data) => {
    if (!isLangwatchEnabled()) return;
    // Implementación básica
    logger.info('Tracking LLM response:', data);
  },
  
  trackLLMError: async (data) => {
    if (!isLangwatchEnabled()) return;
    // Implementación básica
    logger.error('Tracking LLM error:', data);
  }
};

export default {
  initializeLangwatch,
  isLangwatchEnabled,
  RecursivePlannerTracker,
  OrchestrationTracker,
  createRecursiveTracker,
  createOrchestrationTracker,
  langwatchRequestMiddleware,
  langwatchMiddleware,
  LANGWATCH_CONFIG
};

