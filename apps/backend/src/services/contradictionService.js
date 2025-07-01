/**
 * Contradiction Detection and Analysis Service
 * 
 * Servicio especializado en detectar, analizar y optimizar la contradicción explícita
 * en modelos LLM locales para mejorar la calidad de respuestas iterativas
 * 
 * @module contradictionService
 */

import logger from '../utils/logger.js';

/**
 * Configuración de contradicción explícita
 */
const CONTRADICTION_CONFIG = {
  // Umbrales para activar contradicción
  triggers: {
    minAttempts: 2,
    scoreThreshold: 0.6,
    improvementThreshold: 0.1,
    stagnationThreshold: 0.05
  },
  
  // Patrones de contradicción por intensidad
  patterns: {
    mild: [
      'Consider a different approach',
      'Try another perspective',
      'Reconsider your method',
      'Piensa en otra forma',
      'Considera un enfoque diferente'
    ],
    moderate: [
      'Your previous attempt was insufficient',
      'The prior response missed key points',
      'Tu respuesta anterior fue incompleta',
      'El intento previo no cumplió los requisitos'
    ],
    strong: [
      'You failed before, explain why, then retry',
      'Your previous attempts were wrong, analyze the errors',
      'Fallaste anteriormente, explica por qué, luego reintenta',
      'Tus intentos previos fueron incorrectos, analiza los errores'
    ],
    extreme: [
      'CRITICAL ANALYSIS REQUIRED: You have consistently failed',
      'ANÁLISIS CRÍTICO REQUERIDO: Has fallado consistentemente',
      'Your approach is fundamentally flawed, start over completely',
      'Tu enfoque es fundamentalmente defectuoso, comienza completamente de nuevo'
    ]
  },
  
  // Estrategias de contradicción por modelo
  modelStrategies: {
    'mistral-local': {
      focus: 'reasoning',
      patterns: ['logical_contradiction', 'instruction_challenge', 'method_questioning'],
      effectiveness: 0.75
    },
    'llama-local': {
      focus: 'comprehension',
      patterns: ['context_challenge', 'understanding_test', 'perspective_shift'],
      effectiveness: 0.70
    },
    'deepseek-local': {
      focus: 'precision',
      patterns: ['mathematical_challenge', 'logical_proof', 'step_verification'],
      effectiveness: 0.85
    }
  }
};

/**
 * Clase principal para detección y análisis de contradicción
 */
export class ContradictionDetectionService {
  constructor() {
    this.sessionHistory = new Map();
    this.contradictionHistory = new Map();
    this.effectivenessStats = new Map();
  }
  
  /**
   * Detecta si se debe aplicar contradicción explícita
   */
  shouldApplyContradiction(sessionId, currentAttempt, previousResults = []) {
    try {
      // Verificar umbrales básicos
      if (currentAttempt < CONTRADICTION_CONFIG.triggers.minAttempts) {
        return {
          shouldApply: false,
          reason: 'Insufficient attempts',
          intensity: null
        };
      }
      
      // Analizar resultados previos
      const analysis = this.analyzePreviousResults(previousResults);
      
      // Determinar si aplicar contradicción
      const shouldApply = this.evaluateContradictionNeed(analysis, currentAttempt);
      
      if (shouldApply.apply) {
        // Determinar intensidad
        const intensity = this.determineIntensity(analysis, currentAttempt);
        
        logger.info(`🎯 Contradicción recomendada para sesión ${sessionId}: ${intensity}`);
        
        return {
          shouldApply: true,
          intensity,
          reason: shouldApply.reason,
          analysis,
          recommendation: this.generateRecommendation(intensity, analysis)
        };
      }
      
      return {
        shouldApply: false,
        reason: shouldApply.reason,
        analysis
      };
      
    } catch (error) {
      logger.error('Error en detección de contradicción:', error);
      return {
        shouldApply: false,
        reason: 'Detection error',
        error: error.message
      };
    }
  }
  
  /**
   * Analiza resultados de intentos previos
   */
  analyzePreviousResults(results) {
    if (results.length === 0) {
      return {
        averageScore: 0,
        trend: 'unknown',
        stagnation: false,
        improvement: 0,
        consistency: 0
      };
    }
    
    const scores = results.map(r => r.score || 0);
    const averageScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    
    // Analizar tendencia
    const trend = this.analyzeTrend(scores);
    
    // Detectar estancamiento
    const stagnation = this.detectStagnation(scores);
    
    // Calcular mejora
    const improvement = scores.length > 1 ? 
      scores[scores.length - 1] - scores[scores.length - 2] : 0;
    
    // Calcular consistencia
    const consistency = this.calculateConsistency(scores);
    
    return {
      averageScore,
      trend,
      stagnation,
      improvement,
      consistency,
      scores,
      totalAttempts: results.length
    };
  }
  
  /**
   * Evalúa si se necesita contradicción
   */
  evaluateContradictionNeed(analysis, currentAttempt) {
    const config = CONTRADICTION_CONFIG.triggers;
    
    // Score bajo persistente
    if (analysis.averageScore < config.scoreThreshold) {
      return {
        apply: true,
        reason: 'Low average score'
      };
    }
    
    // Estancamiento detectado
    if (analysis.stagnation) {
      return {
        apply: true,
        reason: 'Score stagnation detected'
      };
    }
    
    // Mejora insuficiente
    if (analysis.improvement < config.improvementThreshold && currentAttempt > 2) {
      return {
        apply: true,
        reason: 'Insufficient improvement'
      };
    }
    
    // Tendencia negativa
    if (analysis.trend === 'declining' && currentAttempt > 2) {
      return {
        apply: true,
        reason: 'Declining performance trend'
      };
    }
    
    // Múltiples intentos sin éxito
    if (currentAttempt > 4 && analysis.averageScore < 0.7) {
      return {
        apply: true,
        reason: 'Multiple attempts without success'
      };
    }
    
    return {
      apply: false,
      reason: 'Performance within acceptable range'
    };
  }
  
  /**
   * Determina la intensidad de contradicción
   */
  determineIntensity(analysis, currentAttempt) {
    const avgScore = analysis.averageScore;
    const attempts = currentAttempt;
    
    // Intensidad extrema
    if (attempts > 5 && avgScore < 0.3) {
      return 'extreme';
    }
    
    // Intensidad fuerte
    if ((attempts > 4 && avgScore < 0.5) || 
        (attempts > 3 && analysis.trend === 'declining')) {
      return 'strong';
    }
    
    // Intensidad moderada
    if ((attempts > 3 && avgScore < 0.6) || 
        analysis.stagnation) {
      return 'moderate';
    }
    
    // Intensidad suave
    return 'mild';
  }
  
  /**
   * Genera prompt de contradicción específico
   */
  generateContradictionPrompt(originalPrompt, modelType, intensity, previousResults = []) {
    try {
      const patterns = CONTRADICTION_CONFIG.patterns[intensity];
      const modelStrategy = CONTRADICTION_CONFIG.modelStrategies[modelType];
      
      // Seleccionar patrón base
      const basePattern = patterns[Math.floor(Math.random() * patterns.length)];
      
      // Construir análisis de fallos previos
      const failureAnalysis = this.buildFailureAnalysis(previousResults);
      
      // Construir prompt de contradicción
      let contradictionPrompt = '';
      
      if (intensity === 'extreme' || intensity === 'strong') {
        contradictionPrompt = this.buildStrongContradictionPrompt(
          originalPrompt,
          basePattern,
          failureAnalysis,
          modelStrategy
        );
      } else {
        contradictionPrompt = this.buildMildContradictionPrompt(
          originalPrompt,
          basePattern,
          failureAnalysis,
          modelStrategy
        );
      }
      
      logger.info(`🔥 Generado prompt de contradicción ${intensity} para ${modelType}`);
      
      return {
        prompt: contradictionPrompt,
        intensity,
        patterns: [basePattern],
        metadata: {
          originalPrompt,
          failureAnalysis,
          modelStrategy: modelStrategy?.focus,
          timestamp: Date.now()
        }
      };
      
    } catch (error) {
      logger.error('Error generando prompt de contradicción:', error);
      return {
        prompt: originalPrompt,
        intensity: 'none',
        error: error.message
      };
    }
  }
  
  /**
   * Construye prompt de contradicción fuerte
   */
  buildStrongContradictionPrompt(originalPrompt, basePattern, failureAnalysis, modelStrategy) {
    return `ANÁLISIS CRÍTICO REQUERIDO:

${basePattern}

FALLOS IDENTIFICADOS EN INTENTOS PREVIOS:
${failureAnalysis}

CONTRADICCIÓN EXPLÍCITA:
Claramente tu enfoque anterior no funcionó. Debes:
1. EXPLICAR específicamente por qué fallaron tus intentos anteriores
2. IDENTIFICAR los errores conceptuales o de ejecución
3. PROPONER un enfoque completamente diferente
4. IMPLEMENTAR la solución con una metodología nueva

ENFOQUE REQUERIDO: ${modelStrategy?.focus || 'comprehensive analysis'}

TAREA ORIGINAL (que debes abordar de forma completamente nueva):
${originalPrompt}

RESPUESTA REQUERIDA: Comienza con "ANÁLISIS DE FALLOS PREVIOS:" seguido de tu nueva solución.`;
  }
  
  /**
   * Construye prompt de contradicción suave
   */
  buildMildContradictionPrompt(originalPrompt, basePattern, failureAnalysis, modelStrategy) {
    return `REVISIÓN REQUERIDA:

${basePattern}

Observaciones sobre intentos previos:
${failureAnalysis}

Por favor:
1. Revisa tu enfoque anterior
2. Identifica áreas de mejora
3. Propón una solución mejorada

Enfoque sugerido: ${modelStrategy?.focus || 'comprehensive review'}

Tarea original:
${originalPrompt}`;
  }
  
  /**
   * Construye análisis de fallos previos
   */
  buildFailureAnalysis(previousResults) {
    if (previousResults.length === 0) {
      return 'No hay intentos previos para analizar.';
    }
    
    let analysis = '';
    
    previousResults.forEach((result, index) => {
      const attempt = index + 1;
      const score = result.score || 0;
      const issues = this.identifyIssues(result);
      
      analysis += `\nINTENTO ${attempt}:\n`;
      analysis += `- Score obtenido: ${score.toFixed(2)}\n`;
      analysis += `- Problemas identificados: ${issues.join(', ')}\n`;
      
      if (result.response) {
        const responsePreview = result.response.substring(0, 100) + '...';
        analysis += `- Respuesta: "${responsePreview}"\n`;
      }
    });
    
    return analysis;
  }
  
  /**
   * Identifica problemas en un resultado
   */
  identifyIssues(result) {
    const issues = [];
    
    if (result.score < 0.3) issues.push('Score muy bajo');
    if (result.score < 0.5) issues.push('Calidad insuficiente');
    
    if (result.response) {
      if (result.response.length < 50) issues.push('Respuesta muy corta');
      if (result.response.length > 2000) issues.push('Respuesta muy larga');
      if (!result.response.includes('.')) issues.push('Falta de estructura');
    }
    
    if (result.tokenUsage) {
      const ratio = result.tokenUsage.completionTokens / result.tokenUsage.promptTokens;
      if (ratio < 0.5) issues.push('Respuesta insuficientemente desarrollada');
      if (ratio > 3) issues.push('Respuesta excesivamente verbosa');
    }
    
    if (result.duration > 10000) issues.push('Tiempo de respuesta excesivo');
    
    return issues.length > 0 ? issues : ['Problemas no específicos'];
  }
  
  /**
   * Analiza tendencia de scores
   */
  analyzeTrend(scores) {
    if (scores.length < 2) return 'unknown';
    
    let increasing = 0;
    let decreasing = 0;
    
    for (let i = 1; i < scores.length; i++) {
      if (scores[i] > scores[i-1]) increasing++;
      else if (scores[i] < scores[i-1]) decreasing++;
    }
    
    if (increasing > decreasing) return 'improving';
    if (decreasing > increasing) return 'declining';
    return 'stable';
  }
  
  /**
   * Detecta estancamiento en scores
   */
  detectStagnation(scores) {
    if (scores.length < 3) return false;
    
    const recent = scores.slice(-3);
    const variance = this.calculateVariance(recent);
    
    return variance < CONTRADICTION_CONFIG.triggers.stagnationThreshold;
  }
  
  /**
   * Calcula consistencia de scores
   */
  calculateConsistency(scores) {
    if (scores.length < 2) return 1;
    
    const variance = this.calculateVariance(scores);
    return Math.max(0, 1 - variance);
  }
  
  /**
   * Calcula varianza
   */
  calculateVariance(values) {
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(value => Math.pow(value - mean, 2));
    return squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
  }
  
  /**
   * Genera recomendación basada en análisis
   */
  generateRecommendation(intensity, analysis) {
    switch (intensity) {
      case 'extreme':
        return 'Aplicar contradicción extrema. Considerar cambio de modelo o estrategia fundamental.';
      case 'strong':
        return 'Aplicar contradicción fuerte. Forzar análisis crítico completo.';
      case 'moderate':
        return 'Aplicar contradicción moderada. Solicitar revisión y mejora.';
      case 'mild':
        return 'Aplicar contradicción suave. Sugerir refinamiento del enfoque.';
      default:
        return 'Continuar sin contradicción. Rendimiento aceptable.';
    }
  }
  
  /**
   * Evalúa efectividad de contradicción aplicada
   */
  evaluateContradictionEffectiveness(sessionId, contradictionData, newResult) {
    try {
      const { intensity, previousScore } = contradictionData;
      const newScore = newResult.score || 0;
      const improvement = newScore - previousScore;
      
      let effectiveness = 'neutral';
      
      if (improvement > 0.3) effectiveness = 'highly_effective';
      else if (improvement > 0.15) effectiveness = 'effective';
      else if (improvement > 0.05) effectiveness = 'slightly_effective';
      else if (improvement < -0.1) effectiveness = 'counterproductive';
      
      // Guardar estadísticas
      this.updateEffectivenessStats(intensity, effectiveness, improvement);
      
      logger.info(`📊 Efectividad de contradicción ${intensity}: ${effectiveness} (mejora: ${improvement.toFixed(3)})`);
      
      return {
        effectiveness,
        improvement,
        recommendation: this.getEffectivenessRecommendation(effectiveness, intensity)
      };
      
    } catch (error) {
      logger.error('Error evaluando efectividad de contradicción:', error);
      return {
        effectiveness: 'unknown',
        improvement: 0,
        error: error.message
      };
    }
  }
  
  /**
   * Actualiza estadísticas de efectividad
   */
  updateEffectivenessStats(intensity, effectiveness, improvement) {
    const key = `${intensity}_${effectiveness}`;
    
    if (!this.effectivenessStats.has(key)) {
      this.effectivenessStats.set(key, {
        count: 0,
        totalImprovement: 0,
        averageImprovement: 0
      });
    }
    
    const stats = this.effectivenessStats.get(key);
    stats.count++;
    stats.totalImprovement += improvement;
    stats.averageImprovement = stats.totalImprovement / stats.count;
  }
  
  /**
   * Obtiene recomendación basada en efectividad
   */
  getEffectivenessRecommendation(effectiveness, intensity) {
    switch (effectiveness) {
      case 'highly_effective':
        return `Contradicción ${intensity} muy efectiva. Continuar con esta estrategia.`;
      case 'effective':
        return `Contradicción ${intensity} efectiva. Mantener enfoque.`;
      case 'slightly_effective':
        return `Contradicción ${intensity} ligeramente efectiva. Considerar intensificar.`;
      case 'counterproductive':
        return `Contradicción ${intensity} contraproducente. Reducir intensidad o cambiar estrategia.`;
      default:
        return `Contradicción ${intensity} con efectividad neutral. Monitorear próximos intentos.`;
    }
  }
  
  /**
   * Obtiene estadísticas generales de contradicción
   */
  getContradictionStats() {
    const stats = {
      totalContradictions: 0,
      byIntensity: {
        mild: 0,
        moderate: 0,
        strong: 0,
        extreme: 0
      },
      byEffectiveness: {
        highly_effective: 0,
        effective: 0,
        slightly_effective: 0,
        neutral: 0,
        counterproductive: 0
      },
      averageImprovement: 0
    };
    
    let totalImprovement = 0;
    let count = 0;
    
    for (const [key, data] of this.effectivenessStats) {
      const [intensity, effectiveness] = key.split('_');
      
      stats.totalContradictions += data.count;
      stats.byIntensity[intensity] = (stats.byIntensity[intensity] || 0) + data.count;
      stats.byEffectiveness[effectiveness] = (stats.byEffectiveness[effectiveness] || 0) + data.count;
      
      totalImprovement += data.totalImprovement;
      count += data.count;
    }
    
    stats.averageImprovement = count > 0 ? totalImprovement / count : 0;
    
    return stats;
  }
}

/**
 * Instancia singleton del servicio
 */
export const contradictionService = new ContradictionDetectionService();

/**
 * Función utilitaria para detectar contradicción
 */
export function detectContradiction(sessionId, currentAttempt, previousResults) {
  return contradictionService.shouldApplyContradiction(sessionId, currentAttempt, previousResults);
}

/**
 * Función utilitaria para generar prompt de contradicción
 */
export function generateContradictionPrompt(originalPrompt, modelType, intensity, previousResults) {
  return contradictionService.generateContradictionPrompt(originalPrompt, modelType, intensity, previousResults);
}

/**
 * Función utilitaria para evaluar efectividad
 */
export function evaluateContradictionEffectiveness(sessionId, contradictionData, newResult) {
  return contradictionService.evaluateContradictionEffectiveness(sessionId, contradictionData, newResult);
}

export default {
  ContradictionDetectionService,
  contradictionService,
  detectContradiction,
  generateContradictionPrompt,
  evaluateContradictionEffectiveness,
  CONTRADICTION_CONFIG
};

