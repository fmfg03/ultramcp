/**
 * Enhanced Langwatch Middleware for Local LLM Models
 * 
 * Extensión del middleware de Langwatch para soportar tracking específico
 * de modelos locales con métricas avanzadas y scores simulados
 * 
 * @module enhancedLangwatchMiddleware
 */

import { langwatchMiddleware } from './langwatchMiddleware.js';
import logger from '../utils/logger.js';

/**
 * Configuración de métricas para modelos locales
 */
const LOCAL_METRICS_CONFIG = {
  scoreThresholds: {
    excellent: 0.85,
    good: 0.7,
    acceptable: 0.5,
    poor: 0.3
  },
  contradictionTriggers: {
    minAttempts: 2,
    scoreThreshold: 0.6,
    patterns: [
      'failed before',
      'error anterior',
      'intento previo',
      'no funcionó',
      'enfoque diferente'
    ]
  },
  tokenEfficiency: {
    optimal: { min: 0.8, max: 1.2 }, // Ratio tokens_output/tokens_input
    acceptable: { min: 0.5, max: 2.0 },
    poor: { min: 0, max: 0.5 }
  }
};

/**
 * Clase para tracking avanzado de métricas locales
 */
export class LocalLLMMetricsTracker {
  constructor() {
    this.activeSessions = new Map();
    this.metricsHistory = new Map();
    this.contradictionHistory = new Map();
  }
  
  /**
   * Inicia tracking de una sesión de modelo local
   */
  async startTracking(sessionData) {
    const {
      sessionId,
      modelName,
      provider,
      tags,
      prompt,
      metadata
    } = sessionData;
    
    const trackingId = `local_${modelName}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const session = {
      trackingId,
      sessionId,
      modelName,
      provider,
      tags,
      prompt,
      startTime: Date.now(),
      metadata: {
        ...metadata,
        promptTokens: this.estimateTokens(prompt),
        expectedScore: this.predictScore(prompt, modelName),
        contradictionDetected: metadata.contradiction || false
      }
    };
    
    this.activeSessions.set(trackingId, session);
    
    // Enviar a Langwatch
    try {
      await langwatchMiddleware.trackLLMCall({
        sessionId,
        modelName,
        provider,
        tags: [...tags, 'local_llm', 'metrics_tracked'],
        input: prompt,
        metadata: session.metadata
      });
    } catch (error) {
      logger.error('Error enviando inicio de tracking a Langwatch:', error);
    }
    
    logger.info(`📊 Iniciado tracking local: ${trackingId} para modelo ${modelName}`);
    return trackingId;
  }
  
  /**
   * Finaliza tracking y calcula métricas completas
   */
  async finishTracking(trackingData) {
    const {
      trackingId,
      sessionId,
      modelName,
      prompt,
      response,
      tokenUsage,
      duration,
      score,
      contradiction,
      metadata
    } = trackingData;
    
    const session = this.activeSessions.get(trackingId);
    if (!session) {
      logger.warn(`Sesión no encontrada para tracking: ${trackingId}`);
      return;
    }
    
    // Calcular métricas avanzadas
    const metrics = this.calculateAdvancedMetrics({
      prompt,
      response,
      tokenUsage,
      duration,
      score,
      modelName,
      startTime: session.startTime
    });
    
    // Analizar contradicción
    const contradictionAnalysis = this.analyzeContradiction(
      sessionId,
      contradiction,
      score,
      metrics
    );
    
    // Preparar datos completos para Langwatch
    const langwatchData = {
      trackingId,
      sessionId,
      modelName,
      provider: 'local',
      input: prompt,
      output: response,
      tokenUsage,
      duration,
      score,
      metrics,
      contradiction: contradictionAnalysis,
      metadata: {
        ...metadata,
        ...metrics,
        contradictionAnalysis,
        efficiency: this.calculateEfficiency(tokenUsage, duration),
        qualityGrade: this.getQualityGrade(score)
      }
    };
    
    // Guardar en historial
    this.saveToHistory(sessionId, langwatchData);
    
    // Enviar a Langwatch
    try {
      await langwatchMiddleware.trackLLMResponse({
        ...langwatchData,
        tags: ['local_llm', 'completed', `score_${this.getQualityGrade(score)}`]
      });
    } catch (error) {
      logger.error('Error enviando finalización a Langwatch:', error);
    }
    
    // Limpiar sesión activa
    this.activeSessions.delete(trackingId);
    
    logger.info(`✅ Finalizado tracking: ${trackingId} - Score: ${score.toFixed(3)} - Grade: ${this.getQualityGrade(score)}`);
    
    return langwatchData;
  }
  
  /**
   * Calcula métricas avanzadas
   */
  calculateAdvancedMetrics(data) {
    const { prompt, response, tokenUsage, duration, score, modelName } = data;
    
    // Métricas de tokens
    const tokenMetrics = {
      efficiency: tokenUsage.completionTokens / tokenUsage.promptTokens,
      density: response.length / tokenUsage.completionTokens,
      utilization: tokenUsage.totalTokens / 512 // Asumiendo max 512 tokens
    };
    
    // Métricas de tiempo
    const timeMetrics = {
      tokensPerSecond: tokenUsage.completionTokens / (duration / 1000),
      responseTime: duration,
      timePerToken: duration / tokenUsage.completionTokens
    };
    
    // Métricas de calidad
    const qualityMetrics = {
      lengthRatio: response.length / prompt.length,
      complexityScore: this.calculateComplexity(response),
      coherenceScore: this.calculateCoherence(response),
      relevanceScore: this.calculateRelevance(prompt, response)
    };
    
    // Métricas específicas del modelo
    const modelSpecificMetrics = this.getModelSpecificMetrics(modelName, response);
    
    return {
      tokens: tokenMetrics,
      time: timeMetrics,
      quality: qualityMetrics,
      modelSpecific: modelSpecificMetrics,
      overall: {
        score,
        grade: this.getQualityGrade(score),
        efficiency: this.calculateOverallEfficiency(tokenMetrics, timeMetrics, qualityMetrics)
      }
    };
  }
  
  /**
   * Analiza contradicción explícita
   */
  analyzeContradiction(sessionId, contradiction, score, metrics) {
    if (!contradiction.triggered) {
      return {
        triggered: false,
        effectiveness: null,
        improvement: null,
        recommendation: null
      };
    }
    
    // Obtener historial de la sesión
    const history = this.getSessionHistory(sessionId);
    const previousAttempts = history.filter(h => h.contradiction?.triggered === false);
    
    if (previousAttempts.length === 0) {
      return {
        triggered: true,
        effectiveness: 'unknown',
        improvement: null,
        recommendation: 'Primera contradicción aplicada'
      };
    }
    
    // Calcular mejora
    const previousScores = previousAttempts.map(a => a.score);
    const avgPreviousScore = previousScores.reduce((a, b) => a + b, 0) / previousScores.length;
    const improvement = score - avgPreviousScore;
    
    // Analizar efectividad
    let effectiveness = 'neutral';
    if (improvement > 0.2) effectiveness = 'highly_effective';
    else if (improvement > 0.1) effectiveness = 'effective';
    else if (improvement > 0) effectiveness = 'slightly_effective';
    else if (improvement < -0.1) effectiveness = 'counterproductive';
    
    // Generar recomendación
    const recommendation = this.generateContradictionRecommendation(
      effectiveness,
      improvement,
      contradiction.attemptNumber
    );
    
    // Guardar en historial de contradicciones
    this.contradictionHistory.set(`${sessionId}_${contradiction.attemptNumber}`, {
      sessionId,
      attemptNumber: contradiction.attemptNumber,
      patterns: contradiction.patterns,
      score,
      improvement,
      effectiveness,
      timestamp: Date.now()
    });
    
    return {
      triggered: true,
      effectiveness,
      improvement,
      recommendation,
      patterns: contradiction.patterns,
      attemptNumber: contradiction.attemptNumber
    };
  }
  
  /**
   * Calcula eficiencia general
   */
  calculateOverallEfficiency(tokenMetrics, timeMetrics, qualityMetrics) {
    const tokenEfficiency = Math.min(tokenMetrics.efficiency / 1.5, 1); // Normalizado
    const timeEfficiency = Math.min(timeMetrics.tokensPerSecond / 10, 1); // Normalizado
    const qualityEfficiency = (qualityMetrics.relevanceScore + qualityMetrics.coherenceScore) / 2;
    
    return (tokenEfficiency * 0.3 + timeEfficiency * 0.3 + qualityEfficiency * 0.4);
  }
  
  /**
   * Calcula complejidad de la respuesta
   */
  calculateComplexity(response) {
    let complexity = 0;
    
    // Longitud
    complexity += Math.min(response.length / 1000, 0.3);
    
    // Vocabulario único
    const words = response.toLowerCase().split(/\s+/);
    const uniqueWords = new Set(words);
    complexity += Math.min(uniqueWords.size / words.length, 0.3);
    
    // Estructura
    if (response.includes('\n')) complexity += 0.1;
    if (response.match(/\d+\./)) complexity += 0.1; // Listas
    if (response.includes(':')) complexity += 0.1; // Explicaciones
    if (response.match(/[()]/)) complexity += 0.1; // Paréntesis
    
    return Math.min(complexity, 1);
  }
  
  /**
   * Calcula coherencia de la respuesta
   */
  calculateCoherence(response) {
    let coherence = 0.5; // Base
    
    // Conectores lógicos
    const connectors = ['porque', 'por lo tanto', 'además', 'sin embargo', 'entonces'];
    const connectorsFound = connectors.filter(c => response.toLowerCase().includes(c));
    coherence += connectorsFound.length * 0.1;
    
    // Estructura lógica
    if (response.includes('primero') || response.includes('segundo')) coherence += 0.1;
    if (response.includes('finalmente') || response.includes('en conclusión')) coherence += 0.1;
    
    // Penalización por repetición
    const sentences = response.split(/[.!?]+/);
    const uniqueSentences = new Set(sentences.map(s => s.trim().toLowerCase()));
    if (uniqueSentences.size / sentences.length < 0.8) coherence -= 0.2;
    
    return Math.max(0, Math.min(1, coherence));
  }
  
  /**
   * Calcula relevancia entre prompt y respuesta
   */
  calculateRelevance(prompt, response) {
    const promptWords = prompt.toLowerCase().split(/\s+/).filter(w => w.length > 3);
    const responseWords = response.toLowerCase().split(/\s+/);
    
    let relevantWords = 0;
    for (const word of promptWords) {
      if (responseWords.includes(word)) {
        relevantWords++;
      }
    }
    
    return Math.min(relevantWords / Math.max(promptWords.length, 1), 1);
  }
  
  /**
   * Obtiene métricas específicas del modelo
   */
  getModelSpecificMetrics(modelName, response) {
    switch (modelName) {
      case 'mistral-local':
        return {
          instructionFollowing: response.includes('[INST]') || response.includes('instrucción'),
          reasoningSteps: (response.match(/paso|step/gi) || []).length,
          explanationQuality: response.includes('porque') || response.includes('because')
        };
        
      case 'llama-local':
        return {
          conversationalTone: response.includes('### Human') || response.includes('### Assistant'),
          examplesProvided: (response.match(/ejemplo|example/gi) || []).length,
          contextualAwareness: response.includes('contexto') || response.includes('context')
        };
        
      case 'deepseek-local':
        return {
          mathematicalContent: !!(response.match(/\d+[\+\-\*\/]\d+/)),
          logicalStructure: response.includes('step by step') || response.includes('paso a paso'),
          problemSolving: response.includes('Problem:') && response.includes('Solution:'),
          precision: (response.match(/\d+\.\d+/g) || []).length
        };
        
      default:
        return {};
    }
  }
  
  /**
   * Genera recomendación para contradicción
   */
  generateContradictionRecommendation(effectiveness, improvement, attemptNumber) {
    if (effectiveness === 'highly_effective') {
      return 'Contradicción muy efectiva. Continuar con este enfoque.';
    } else if (effectiveness === 'effective') {
      return 'Contradicción efectiva. Considerar refinar la estrategia.';
    } else if (effectiveness === 'counterproductive') {
      return 'Contradicción contraproducente. Cambiar estrategia o reducir intensidad.';
    } else if (attemptNumber > 3) {
      return 'Múltiples intentos sin mejora significativa. Considerar cambio de modelo o enfoque.';
    } else {
      return 'Contradicción neutral. Monitorear próximos intentos.';
    }
  }
  
  /**
   * Calcula eficiencia de tokens y tiempo
   */
  calculateEfficiency(tokenUsage, duration) {
    const tokensPerMs = tokenUsage.completionTokens / duration;
    const tokenRatio = tokenUsage.completionTokens / tokenUsage.promptTokens;
    
    return {
      tokensPerSecond: tokensPerMs * 1000,
      tokenRatio,
      efficiency: Math.min(tokensPerMs * 1000 / 5, 1) // Normalizado a 5 tokens/sec
    };
  }
  
  /**
   * Obtiene grado de calidad basado en score
   */
  getQualityGrade(score) {
    const thresholds = LOCAL_METRICS_CONFIG.scoreThresholds;
    
    if (score >= thresholds.excellent) return 'excellent';
    if (score >= thresholds.good) return 'good';
    if (score >= thresholds.acceptable) return 'acceptable';
    if (score >= thresholds.poor) return 'poor';
    return 'very_poor';
  }
  
  /**
   * Predice score esperado basado en prompt y modelo
   */
  predictScore(prompt, modelName) {
    let baseScore = 0.6; // Score base
    
    // Ajuste por longitud del prompt
    if (prompt.length > 200) baseScore += 0.1;
    if (prompt.length < 50) baseScore -= 0.1;
    
    // Ajuste por modelo
    switch (modelName) {
      case 'deepseek-local':
        if (prompt.toLowerCase().includes('matemática') || prompt.includes('cálculo')) {
          baseScore += 0.2;
        }
        break;
      case 'mistral-local':
        if (prompt.toLowerCase().includes('explica') || prompt.includes('razona')) {
          baseScore += 0.15;
        }
        break;
      case 'llama-local':
        if (prompt.toLowerCase().includes('describe') || prompt.includes('cuenta')) {
          baseScore += 0.1;
        }
        break;
    }
    
    return Math.max(0.3, Math.min(0.9, baseScore));
  }
  
  /**
   * Estima tokens en un texto
   */
  estimateTokens(text) {
    return Math.ceil(text.length / 4); // Estimación simple
  }
  
  /**
   * Guarda datos en historial
   */
  saveToHistory(sessionId, data) {
    if (!this.metricsHistory.has(sessionId)) {
      this.metricsHistory.set(sessionId, []);
    }
    this.metricsHistory.get(sessionId).push(data);
  }
  
  /**
   * Obtiene historial de sesión
   */
  getSessionHistory(sessionId) {
    return this.metricsHistory.get(sessionId) || [];
  }
  
  /**
   * Obtiene estadísticas generales
   */
  getOverallStats() {
    const allSessions = Array.from(this.metricsHistory.values()).flat();
    
    if (allSessions.length === 0) {
      return {
        totalSessions: 0,
        averageScore: 0,
        averageDuration: 0,
        contradictionEffectiveness: 0
      };
    }
    
    const totalScore = allSessions.reduce((sum, s) => sum + s.score, 0);
    const totalDuration = allSessions.reduce((sum, s) => sum + s.duration, 0);
    const contradictions = allSessions.filter(s => s.contradiction?.triggered);
    const effectiveContradictions = contradictions.filter(s => 
      s.contradiction?.effectiveness === 'effective' || 
      s.contradiction?.effectiveness === 'highly_effective'
    );
    
    return {
      totalSessions: allSessions.length,
      averageScore: totalScore / allSessions.length,
      averageDuration: totalDuration / allSessions.length,
      contradictionRate: contradictions.length / allSessions.length,
      contradictionEffectiveness: contradictions.length > 0 ? 
        effectiveContradictions.length / contradictions.length : 0,
      qualityDistribution: this.getQualityDistribution(allSessions)
    };
  }
  
  /**
   * Obtiene distribución de calidad
   */
  getQualityDistribution(sessions) {
    const distribution = {
      excellent: 0,
      good: 0,
      acceptable: 0,
      poor: 0,
      very_poor: 0
    };
    
    sessions.forEach(session => {
      const grade = this.getQualityGrade(session.score);
      distribution[grade]++;
    });
    
    return distribution;
  }
  
  /**
   * Tracking de errores
   */
  async trackError(errorData) {
    const { sessionId, modelName, prompt, error, duration } = errorData;
    
    try {
      await langwatchMiddleware.trackLLMError({
        sessionId,
        modelName,
        provider: 'local',
        input: prompt,
        error,
        duration,
        tags: ['local_llm', 'error'],
        metadata: {
          errorType: error.includes('timeout') ? 'timeout' : 'execution_error',
          promptLength: prompt.length,
          estimatedTokens: this.estimateTokens(prompt)
        }
      });
    } catch (langwatchError) {
      logger.error('Error enviando error a Langwatch:', langwatchError);
    }
    
    logger.error(`❌ Error trackeado para ${modelName}: ${error}`);
  }
}

/**
 * Instancia singleton del tracker
 */
export const localMetricsTracker = new LocalLLMMetricsTracker();

/**
 * Extensión del middleware de Langwatch para modelos locales
 */
export const enhancedLangwatchMiddleware = {
  ...langwatchMiddleware,
  
  /**
   * Inicia tracking de modelo local
   */
  async startLocalModelTracking(sessionData) {
    return await localMetricsTracker.startTracking(sessionData);
  },
  
  /**
   * Finaliza tracking de modelo local
   */
  async finishLocalModelTracking(trackingData) {
    return await localMetricsTracker.finishTracking(trackingData);
  },
  
  /**
   * Trackea error de modelo local
   */
  async trackLocalModelError(errorData) {
    return await localMetricsTracker.trackError(errorData);
  },
  
  /**
   * Obtiene estadísticas de modelos locales
   */
  getLocalModelStats() {
    return localMetricsTracker.getOverallStats();
  },
  
  /**
   * Obtiene historial de sesión específica
   */
  getSessionHistory(sessionId) {
    return localMetricsTracker.getSessionHistory(sessionId);
  }
};

export default enhancedLangwatchMiddleware;

