/**
 * Langwatch Wrappers for Local LLM Models
 * 
 * Wrappers específicos para cada modelo local que integran Langwatch
 * para tracking completo de métricas, scores y contradicción explícita
 * 
 * @module localLLMWrappers
 */

import { langwatchMiddleware } from '../middleware/langwatchMiddleware.js';
import logger from '../utils/logger.js';

/**
 * Configuración específica de Langwatch para modelos locales
 */
const LANGWATCH_LOCAL_CONFIG = {
  'mistral-local': {
    modelName: 'mistral-local',
    provider: 'local',
    tags: ['local', 'mistral', 'general', 'reasoning'],
    expectedTokenRange: { min: 50, max: 512 },
    expectedDurationMs: { min: 1000, max: 10000 },
    scoreWeights: {
      relevance: 0.3,
      accuracy: 0.25,
      completeness: 0.2,
      clarity: 0.15,
      efficiency: 0.1
    }
  },
  'llama-local': {
    modelName: 'llama-local',
    provider: 'local',
    tags: ['local', 'llama', 'comprehension', 'generation'],
    expectedTokenRange: { min: 80, max: 512 },
    expectedDurationMs: { min: 1500, max: 12000 },
    scoreWeights: {
      relevance: 0.25,
      accuracy: 0.2,
      completeness: 0.25,
      clarity: 0.2,
      creativity: 0.1
    }
  },
  'deepseek-local': {
    modelName: 'deepseek-local',
    provider: 'local',
    tags: ['local', 'deepseek', 'mathematics', 'logic'],
    expectedTokenRange: { min: 100, max: 512 },
    expectedDurationMs: { min: 2000, max: 15000 },
    scoreWeights: {
      accuracy: 0.4,
      completeness: 0.25,
      logical_consistency: 0.2,
      clarity: 0.1,
      efficiency: 0.05
    }
  }
};

/**
 * Clase base para wrappers de Langwatch
 */
class BaseLangwatchWrapper {
  constructor(modelType) {
    this.modelType = modelType;
    this.config = LANGWATCH_LOCAL_CONFIG[modelType];
    this.middleware = langwatchMiddleware;
    
    if (!this.config) {
      throw new Error(`Configuración no encontrada para modelo: ${modelType}`);
    }
  }
  
  /**
   * Simula un score basado en la respuesta y métricas
   */
  simulateScore(prompt, response, metadata) {
    try {
      const weights = this.config.scoreWeights;
      let totalScore = 0;
      
      // Score base por longitud de respuesta
      const responseLength = response.length;
      const lengthScore = Math.min(responseLength / 200, 1); // Normalizado a 1
      
      // Score por tiempo de respuesta (más rápido = mejor, hasta cierto punto)
      const duration = metadata.duration || 5000;
      const expectedMax = this.config.expectedDurationMs.max;
      const timeScore = Math.max(0, 1 - (duration / expectedMax));
      
      // Score por relevancia (heurística simple)
      const relevanceScore = this.calculateRelevanceScore(prompt, response);
      
      // Score por claridad (basado en estructura)
      const clarityScore = this.calculateClarityScore(response);
      
      // Score por completitud (basado en longitud y estructura)
      const completenessScore = this.calculateCompletenessScore(prompt, response);
      
      // Calcular score ponderado
      totalScore += (weights.relevance || 0.3) * relevanceScore;
      totalScore += (weights.accuracy || 0.25) * lengthScore;
      totalScore += (weights.completeness || 0.2) * completenessScore;
      totalScore += (weights.clarity || 0.15) * clarityScore;
      totalScore += (weights.efficiency || 0.1) * timeScore;
      
      // Bonus específico por modelo
      const modelBonus = this.calculateModelSpecificBonus(prompt, response);
      totalScore += modelBonus * 0.1;
      
      // Normalizar entre 0 y 1
      return Math.max(0, Math.min(1, totalScore));
      
    } catch (error) {
      logger.error('Error simulando score:', error);
      return 0.5; // Score neutro en caso de error
    }
  }
  
  /**
   * Calcula score de relevancia basado en palabras clave
   */
  calculateRelevanceScore(prompt, response) {
    const promptWords = prompt.toLowerCase().split(/\s+/);
    const responseWords = response.toLowerCase().split(/\s+/);
    
    let matches = 0;
    for (const word of promptWords) {
      if (word.length > 3 && responseWords.includes(word)) {
        matches++;
      }
    }
    
    return Math.min(matches / Math.max(promptWords.length * 0.3, 1), 1);
  }
  
  /**
   * Calcula score de claridad basado en estructura
   */
  calculateClarityScore(response) {
    let score = 0.5; // Base score
    
    // Bonus por estructura
    if (response.includes('\n')) score += 0.1;
    if (response.match(/\d+\./)) score += 0.1; // Listas numeradas
    if (response.match(/[-*]/)) score += 0.1; // Listas con viñetas
    if (response.includes('?')) score += 0.05; // Preguntas retóricas
    if (response.includes(':')) score += 0.05; // Explicaciones
    
    // Penalización por repetición excesiva
    const words = response.split(/\s+/);
    const uniqueWords = new Set(words);
    const repetitionRatio = uniqueWords.size / words.length;
    if (repetitionRatio < 0.5) score -= 0.2;
    
    return Math.max(0, Math.min(1, score));
  }
  
  /**
   * Calcula score de completitud
   */
  calculateCompletenessScore(prompt, response) {
    const promptLength = prompt.length;
    const responseLength = response.length;
    
    // Ratio ideal de respuesta vs prompt
    const idealRatio = 2; // Respuesta debería ser ~2x el prompt
    const actualRatio = responseLength / promptLength;
    
    if (actualRatio < 0.5) return 0.3; // Muy corta
    if (actualRatio > 5) return 0.7; // Muy larga
    
    // Score óptimo alrededor del ratio ideal
    return Math.max(0.5, 1 - Math.abs(actualRatio - idealRatio) / idealRatio);
  }
  
  /**
   * Bonus específico por modelo (implementado en subclases)
   */
  calculateModelSpecificBonus(prompt, response) {
    return 0; // Base implementation
  }
  
  /**
   * Detecta si se aplicó contradicción explícita
   */
  detectContradiction(prompt, previousAttempts = []) {
    const promptLower = prompt.toLowerCase();
    
    // Patrones de contradicción explícita
    const contradictionPatterns = [
      'failed before',
      'fallaste',
      'error anterior',
      'intento previo',
      'no funcionó',
      'enfoque diferente',
      'nueva metodología',
      'análisis crítico'
    ];
    
    const hasContradiction = contradictionPatterns.some(pattern => 
      promptLower.includes(pattern)
    );
    
    return {
      triggered: hasContradiction,
      attemptNumber: previousAttempts.length + 1,
      patterns: contradictionPatterns.filter(pattern => promptLower.includes(pattern))
    };
  }
  
  /**
   * Wrapper principal que integra Langwatch
   */
  async withLangwatch(callFunction, prompt, options = {}) {
    const startTime = Date.now();
    const sessionId = options.sessionId || `local_${Date.now()}`;
    
    try {
      logger.info(`🔍 Iniciando tracking Langwatch para ${this.modelType}`);
      
      // Detectar contradicción
      const contradiction = this.detectContradiction(prompt, options.previousAttempts);
      
      // Iniciar tracking en Langwatch
      const trackingId = await this.middleware.startLocalModelTracking({
        sessionId,
        modelName: this.config.modelName,
        provider: this.config.provider,
        tags: [...this.config.tags, ...(options.tags || [])],
        prompt,
        metadata: {
          contradiction: contradiction.triggered,
          attemptNumber: contradiction.attemptNumber,
          expectedTokens: this.config.expectedTokenRange,
          expectedDuration: this.config.expectedDurationMs
        }
      });
      
      // Ejecutar función del modelo
      const result = await callFunction(prompt, options);
      
      const duration = Date.now() - startTime;
      
      // Simular score
      const score = this.simulateScore(prompt, result.response, {
        duration,
        ...result.metadata
      });
      
      // Preparar datos para Langwatch
      const langwatchData = {
        trackingId,
        sessionId,
        modelName: this.config.modelName,
        prompt,
        response: result.response,
        tokenUsage: result.tokenUsage,
        duration,
        score,
        contradiction,
        metadata: {
          ...result.metadata,
          scoreBreakdown: this.getScoreBreakdown(prompt, result.response, { duration }),
          modelSpecific: this.getModelSpecificMetrics(result)
        }
      };
      
      // Finalizar tracking en Langwatch
      await this.middleware.finishLocalModelTracking(langwatchData);
      
      logger.info(`✅ Tracking completado para ${this.modelType} - Score: ${score.toFixed(3)}`);
      
      // Retornar resultado enriquecido
      return {
        ...result,
        langwatch: {
          trackingId,
          score,
          contradiction,
          tracked: true
        }
      };
      
    } catch (error) {
      const duration = Date.now() - startTime;
      
      logger.error(`❌ Error en wrapper Langwatch para ${this.modelType}:`, error);
      
      // Tracking de error en Langwatch
      await this.middleware.trackLocalModelError({
        sessionId,
        modelName: this.config.modelName,
        prompt,
        error: error.message,
        duration
      });
      
      throw error;
    }
  }
  
  /**
   * Obtiene desglose detallado del score
   */
  getScoreBreakdown(prompt, response, metadata) {
    return {
      relevance: this.calculateRelevanceScore(prompt, response),
      clarity: this.calculateClarityScore(response),
      completeness: this.calculateCompletenessScore(prompt, response),
      efficiency: metadata.duration ? Math.max(0, 1 - (metadata.duration / 10000)) : 0.5,
      modelSpecific: this.calculateModelSpecificBonus(prompt, response)
    };
  }
  
  /**
   * Métricas específicas del modelo (implementado en subclases)
   */
  getModelSpecificMetrics(result) {
    return {};
  }
}

/**
 * Wrapper específico para Mistral
 */
export class MistralLangwatchWrapper extends BaseLangwatchWrapper {
  constructor() {
    super('mistral-local');
  }
  
  calculateModelSpecificBonus(prompt, response) {
    let bonus = 0;
    
    // Bonus por razonamiento estructurado
    if (response.includes('paso') || response.includes('step')) bonus += 0.2;
    if (response.includes('porque') || response.includes('because')) bonus += 0.1;
    if (response.includes('por lo tanto') || response.includes('therefore')) bonus += 0.1;
    
    // Bonus por formato de instrucciones
    if (response.match(/\[INST\]/) || response.includes('instrucción')) bonus += 0.1;
    
    return Math.min(bonus, 0.3);
  }
  
  getModelSpecificMetrics(result) {
    return {
      instructionFormat: result.response.includes('[INST]'),
      reasoningSteps: (result.response.match(/paso|step/gi) || []).length,
      explanationQuality: result.response.includes('porque') || result.response.includes('because')
    };
  }
}

/**
 * Wrapper específico para LLaMA
 */
export class LlamaLangwatchWrapper extends BaseLangwatchWrapper {
  constructor() {
    super('llama-local');
  }
  
  calculateModelSpecificBonus(prompt, response) {
    let bonus = 0;
    
    // Bonus por comprensión contextual
    const contextWords = ['contexto', 'situación', 'escenario', 'context'];
    if (contextWords.some(word => response.toLowerCase().includes(word))) bonus += 0.2;
    
    // Bonus por creatividad
    if (response.includes('imaginemos') || response.includes('supongamos')) bonus += 0.1;
    if (response.includes('ejemplo') || response.includes('example')) bonus += 0.1;
    
    // Bonus por formato conversacional
    if (response.includes('### Human') || response.includes('### Assistant')) bonus += 0.1;
    
    return Math.min(bonus, 0.3);
  }
  
  getModelSpecificMetrics(result) {
    return {
      conversationalFormat: result.response.includes('### Human') || result.response.includes('### Assistant'),
      examplesProvided: (result.response.match(/ejemplo|example/gi) || []).length,
      contextualUnderstanding: result.response.includes('contexto') || result.response.includes('context')
    };
  }
}

/**
 * Wrapper específico para DeepSeek
 */
export class DeepSeekLangwatchWrapper extends BaseLangwatchWrapper {
  constructor() {
    super('deepseek-local');
  }
  
  calculateModelSpecificBonus(prompt, response) {
    let bonus = 0;
    
    // Bonus por contenido matemático
    if (response.match(/\d+[\+\-\*\/]\d+/)) bonus += 0.2;
    if (response.includes('ecuación') || response.includes('equation')) bonus += 0.2;
    if (response.includes('demostración') || response.includes('proof')) bonus += 0.2;
    
    // Bonus por lógica estructurada
    if (response.includes('step by step') || response.includes('paso a paso')) bonus += 0.1;
    if (response.includes('Problem:') || response.includes('Solution:')) bonus += 0.1;
    
    // Bonus por precisión matemática
    if (response.match(/\d+\.\d+/) || response.includes('=')) bonus += 0.1;
    
    return Math.min(bonus, 0.4);
  }
  
  getModelSpecificMetrics(result) {
    return {
      mathematicalContent: !!(result.response.match(/\d+[\+\-\*\/]\d+/)),
      stepByStepSolution: result.response.includes('step by step') || result.response.includes('paso a paso'),
      problemSolutionFormat: result.response.includes('Problem:') && result.response.includes('Solution:'),
      equationsCount: (result.response.match(/\d+\s*=\s*\d+/g) || []).length
    };
  }
}

/**
 * Factory para crear wrappers
 */
export class LocalLLMWrapperFactory {
  static createWrapper(modelType) {
    switch (modelType) {
      case 'mistral-local':
        return new MistralLangwatchWrapper();
      case 'llama-local':
        return new LlamaLangwatchWrapper();
      case 'deepseek-local':
        return new DeepSeekLangwatchWrapper();
      default:
        throw new Error(`Wrapper no disponible para modelo: ${modelType}`);
    }
  }
  
  static getAllWrappers() {
    return {
      'mistral-local': new MistralLangwatchWrapper(),
      'llama-local': new LlamaLangwatchWrapper(),
      'deepseek-local': new DeepSeekLangwatchWrapper()
    };
  }
}

/**
 * Función utilitaria para envolver cualquier llamada local con Langwatch
 */
export async function withLocalLangwatch(modelType, callFunction, prompt, options = {}) {
  const wrapper = LocalLLMWrapperFactory.createWrapper(modelType);
  return await wrapper.withLangwatch(callFunction, prompt, options);
}

export default {
  BaseLangwatchWrapper,
  MistralLangwatchWrapper,
  LlamaLangwatchWrapper,
  DeepSeekLangwatchWrapper,
  LocalLLMWrapperFactory,
  withLocalLangwatch,
  LANGWATCH_LOCAL_CONFIG
};

