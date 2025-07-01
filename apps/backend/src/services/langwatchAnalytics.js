/**
 * Langwatch Analytics Service
 * 
 * Servicio para crear dashboards y métricas específicas del sistema recursivo
 * con análisis avanzado de patrones y tendencias
 * 
 * @module langwatchAnalytics
 */

import { isLangwatchEnabled } from '../middleware/langwatchMiddleware.js';
import logger from '../utils/logger.js';

/**
 * Configuración de métricas y dashboards
 */
const ANALYTICS_CONFIG = {
  // Métricas de rendimiento
  performanceMetrics: {
    scoreProgression: 'recursive_score_progression',
    attemptEfficiency: 'recursive_attempt_efficiency',
    contradictionTriggers: 'recursive_contradiction_triggers',
    timeToSuccess: 'recursive_time_to_success',
    tokenUsage: 'recursive_token_usage'
  },
  
  // Métricas de calidad
  qualityMetrics: {
    averageScore: 'recursive_average_score',
    successRate: 'recursive_success_rate',
    improvementRate: 'recursive_improvement_rate',
    stagnationRate: 'recursive_stagnation_rate'
  },
  
  // Métricas de patrones
  patternMetrics: {
    commonFailures: 'recursive_common_failures',
    successPatterns: 'recursive_success_patterns',
    taskComplexity: 'recursive_task_complexity',
    agentPerformance: 'recursive_agent_performance'
  },
  
  // Configuración de dashboards
  dashboards: {
    recursiveOverview: 'recursive_planner_overview',
    performanceAnalysis: 'recursive_performance_analysis',
    patternAnalysis: 'recursive_pattern_analysis',
    realTimeMonitoring: 'recursive_realtime_monitoring'
  }
};

/**
 * Clase para análisis de métricas del sistema recursivo
 */
export class RecursiveAnalytics {
  constructor() {
    this.metrics = new Map();
    this.patterns = new Map();
    this.alerts = [];
  }
  
  /**
   * Analiza la progresión de scores en una sesión
   */
  analyzeScoreProgression(attempts) {
    const scores = attempts.map(a => a.score);
    
    if (scores.length < 2) {
      return {
        trend: 'insufficient_data',
        improvement: 0,
        volatility: 0,
        finalScore: scores[0] || 0
      };
    }
    
    // Calcular tendencia
    const firstScore = scores[0];
    const lastScore = scores[scores.length - 1];
    const improvement = lastScore - firstScore;
    
    // Calcular volatilidad
    const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
    const variance = scores.reduce((sum, score) => sum + Math.pow(score - mean, 2), 0) / scores.length;
    const volatility = Math.sqrt(variance);
    
    // Determinar tendencia
    let trend = 'stable';
    if (improvement > 0.1) trend = 'improving';
    else if (improvement < -0.1) trend = 'declining';
    
    // Detectar patrones específicos
    const patterns = this.detectScorePatterns(scores);
    
    return {
      trend,
      improvement,
      volatility,
      finalScore: lastScore,
      patterns,
      analysis: {
        consistentImprovement: this.isConsistentImprovement(scores),
        hasBreakthrough: this.hasBreakthrough(scores),
        stagnationPeriods: this.findStagnationPeriods(scores)
      }
    };
  }
  
  /**
   * Detecta patrones en la progresión de scores
   */
  detectScorePatterns(scores) {
    const patterns = [];
    
    // Patrón de mejora gradual
    if (this.isGradualImprovement(scores)) {
      patterns.push('gradual_improvement');
    }
    
    // Patrón de breakthrough súbito
    if (this.hasSuddenBreakthrough(scores)) {
      patterns.push('sudden_breakthrough');
    }
    
    // Patrón de oscilación
    if (this.hasOscillation(scores)) {
      patterns.push('oscillation');
    }
    
    // Patrón de plateau
    if (this.hasPlateau(scores)) {
      patterns.push('plateau');
    }
    
    return patterns;
  }
  
  /**
   * Analiza la efectividad de la contradicción explícita
   */
  analyzeContradictionEffectiveness(attempts) {
    const contradictionAttempts = attempts.filter(a => a.contradictionTriggered);
    
    if (contradictionAttempts.length === 0) {
      return {
        triggered: false,
        effectiveness: 0,
        averageImprovement: 0
      };
    }
    
    let totalImprovement = 0;
    let successfulContradictions = 0;
    
    contradictionAttempts.forEach((attempt, index) => {
      const previousAttempt = attempts[attempts.indexOf(attempt) - 1];
      if (previousAttempt) {
        const improvement = attempt.score - previousAttempt.score;
        totalImprovement += improvement;
        if (improvement > 0.1) successfulContradictions++;
      }
    });
    
    return {
      triggered: true,
      count: contradictionAttempts.length,
      effectiveness: successfulContradictions / contradictionAttempts.length,
      averageImprovement: totalImprovement / contradictionAttempts.length,
      successfulContradictions
    };
  }
  
  /**
   * Analiza patrones de fallo comunes
   */
  analyzeFailurePatterns(sessions) {
    const failurePatterns = new Map();
    const lowScoreSessions = sessions.filter(s => s.finalScore < 0.6);
    
    lowScoreSessions.forEach(session => {
      // Analizar tipos de error
      const errorTypes = this.categorizeErrors(session.attempts);
      errorTypes.forEach(errorType => {
        const count = failurePatterns.get(errorType) || 0;
        failurePatterns.set(errorType, count + 1);
      });
    });
    
    // Convertir a array ordenado
    const sortedPatterns = Array.from(failurePatterns.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([pattern, count]) => ({
        pattern,
        count,
        percentage: (count / lowScoreSessions.length) * 100
      }));
    
    return {
      totalFailures: lowScoreSessions.length,
      patterns: sortedPatterns,
      recommendations: this.generateFailureRecommendations(sortedPatterns)
    };
  }
  
  /**
   * Genera métricas de eficiencia del sistema
   */
  generateEfficiencyMetrics(sessions) {
    const totalSessions = sessions.length;
    const successfulSessions = sessions.filter(s => s.thresholdReached).length;
    const averageAttempts = sessions.reduce((sum, s) => sum + s.totalAttempts, 0) / totalSessions;
    const averageTokens = sessions.reduce((sum, s) => sum + s.totalTokens, 0) / totalSessions;
    const averageDuration = sessions.reduce((sum, s) => sum + s.totalDuration, 0) / totalSessions;
    
    // Calcular eficiencia por intento
    const efficiencyPerAttempt = sessions.map(s => s.finalScore / s.totalAttempts);
    const averageEfficiency = efficiencyPerAttempt.reduce((a, b) => a + b, 0) / totalSessions;
    
    // Calcular ROI de tokens
    const tokenROI = sessions.map(s => s.finalScore / (s.totalTokens / 1000)); // Score per 1K tokens
    const averageTokenROI = tokenROI.reduce((a, b) => a + b, 0) / totalSessions;
    
    return {
      successRate: (successfulSessions / totalSessions) * 100,
      averageAttempts,
      averageTokens,
      averageDuration,
      averageEfficiency,
      averageTokenROI,
      metrics: {
        timeToSuccess: this.calculateTimeToSuccess(sessions),
        attemptDistribution: this.calculateAttemptDistribution(sessions),
        complexityImpact: this.analyzeComplexityImpact(sessions)
      }
    };
  }
  
  /**
   * Crea dashboard de overview del sistema recursivo
   */
  createRecursiveOverviewDashboard(sessions) {
    const efficiency = this.generateEfficiencyMetrics(sessions);
    const patterns = this.analyzeFailurePatterns(sessions);
    const recentSessions = sessions.slice(-50); // Últimas 50 sesiones
    
    return {
      title: 'Recursive Planner Overview',
      timestamp: new Date().toISOString(),
      summary: {
        totalSessions: sessions.length,
        successRate: efficiency.successRate,
        averageScore: sessions.reduce((sum, s) => sum + s.finalScore, 0) / sessions.length,
        averageAttempts: efficiency.averageAttempts,
        averageTokens: efficiency.averageTokens
      },
      trends: {
        scoreProgression: this.analyzeTrends(recentSessions, 'finalScore'),
        attemptTrends: this.analyzeTrends(recentSessions, 'totalAttempts'),
        tokenTrends: this.analyzeTrends(recentSessions, 'totalTokens')
      },
      patterns: {
        commonFailures: patterns.patterns.slice(0, 5),
        successFactors: this.analyzeSuccessFactors(sessions)
      },
      alerts: this.generateAlerts(recentSessions),
      recommendations: this.generateSystemRecommendations(efficiency, patterns)
    };
  }
  
  /**
   * Crea dashboard de análisis de rendimiento
   */
  createPerformanceDashboard(sessions) {
    const performanceData = sessions.map(session => ({
      sessionId: session.sessionId,
      finalScore: session.finalScore,
      attempts: session.totalAttempts,
      tokens: session.totalTokens,
      duration: session.totalDuration,
      efficiency: session.finalScore / session.totalAttempts,
      tokenEfficiency: session.finalScore / (session.totalTokens / 1000),
      timeEfficiency: session.finalScore / (session.totalDuration / 1000),
      contradictionUsed: session.attempts.some(a => a.contradictionTriggered)
    }));
    
    return {
      title: 'Performance Analysis Dashboard',
      timestamp: new Date().toISOString(),
      metrics: {
        efficiency: this.calculatePerformanceMetrics(performanceData, 'efficiency'),
        tokenEfficiency: this.calculatePerformanceMetrics(performanceData, 'tokenEfficiency'),
        timeEfficiency: this.calculatePerformanceMetrics(performanceData, 'timeEfficiency')
      },
      correlations: {
        attemptsVsScore: this.calculateCorrelation(performanceData, 'attempts', 'finalScore'),
        tokensVsScore: this.calculateCorrelation(performanceData, 'tokens', 'finalScore'),
        durationVsScore: this.calculateCorrelation(performanceData, 'duration', 'finalScore')
      },
      distributions: {
        scoreDistribution: this.calculateDistribution(performanceData, 'finalScore'),
        attemptDistribution: this.calculateDistribution(performanceData, 'attempts'),
        tokenDistribution: this.calculateDistribution(performanceData, 'tokens')
      },
      outliers: this.detectOutliers(performanceData)
    };
  }
  
  /**
   * Métodos auxiliares para análisis de patrones
   */
  isConsistentImprovement(scores) {
    let improvements = 0;
    for (let i = 1; i < scores.length; i++) {
      if (scores[i] > scores[i - 1]) improvements++;
    }
    return improvements / (scores.length - 1) > 0.7;
  }
  
  hasBreakthrough(scores) {
    for (let i = 1; i < scores.length; i++) {
      if (scores[i] - scores[i - 1] > 0.3) return true;
    }
    return false;
  }
  
  findStagnationPeriods(scores) {
    const periods = [];
    let currentPeriod = 0;
    
    for (let i = 1; i < scores.length; i++) {
      if (Math.abs(scores[i] - scores[i - 1]) < 0.05) {
        currentPeriod++;
      } else {
        if (currentPeriod >= 2) {
          periods.push(currentPeriod);
        }
        currentPeriod = 0;
      }
    }
    
    return periods;
  }
  
  isGradualImprovement(scores) {
    const improvements = scores.filter((score, i) => 
      i > 0 && score > scores[i - 1]
    ).length;
    return improvements >= scores.length * 0.6;
  }
  
  hasSuddenBreakthrough(scores) {
    return scores.some((score, i) => 
      i > 0 && score - scores[i - 1] > 0.25
    );
  }
  
  hasOscillation(scores) {
    let changes = 0;
    for (let i = 2; i < scores.length; i++) {
      const trend1 = scores[i - 1] - scores[i - 2];
      const trend2 = scores[i] - scores[i - 1];
      if (trend1 * trend2 < 0) changes++; // Cambio de dirección
    }
    return changes >= scores.length * 0.4;
  }
  
  hasPlateau(scores) {
    const stagnationPeriods = this.findStagnationPeriods(scores);
    return stagnationPeriods.some(period => period >= 3);
  }
  
  categorizeErrors(attempts) {
    const errors = [];
    attempts.forEach(attempt => {
      if (attempt.score < 0.3) errors.push('very_low_score');
      else if (attempt.score < 0.6) errors.push('low_score');
      
      if (attempt.feedback?.includes('incomplete')) errors.push('incomplete_response');
      if (attempt.feedback?.includes('unclear')) errors.push('unclear_response');
      if (attempt.feedback?.includes('incorrect')) errors.push('incorrect_response');
    });
    return errors;
  }
  
  generateFailureRecommendations(patterns) {
    const recommendations = [];
    
    patterns.forEach(({ pattern, percentage }) => {
      if (pattern === 'very_low_score' && percentage > 20) {
        recommendations.push('Consider adjusting score threshold or improving initial prompts');
      }
      if (pattern === 'incomplete_response' && percentage > 15) {
        recommendations.push('Add more specific completion criteria to prompts');
      }
      if (pattern === 'unclear_response' && percentage > 10) {
        recommendations.push('Implement clarity checks in evaluation criteria');
      }
    });
    
    return recommendations;
  }
  
  calculateTimeToSuccess(sessions) {
    const successfulSessions = sessions.filter(s => s.thresholdReached);
    if (successfulSessions.length === 0) return null;
    
    const times = successfulSessions.map(s => s.totalDuration);
    return {
      average: times.reduce((a, b) => a + b, 0) / times.length,
      median: this.calculateMedian(times),
      min: Math.min(...times),
      max: Math.max(...times)
    };
  }
  
  calculateAttemptDistribution(sessions) {
    const attemptCounts = sessions.map(s => s.totalAttempts);
    const distribution = {};
    
    attemptCounts.forEach(count => {
      distribution[count] = (distribution[count] || 0) + 1;
    });
    
    return distribution;
  }
  
  analyzeComplexityImpact(sessions) {
    const complexityGroups = {
      low: sessions.filter(s => s.complexity < 3),
      medium: sessions.filter(s => s.complexity >= 3 && s.complexity < 4),
      high: sessions.filter(s => s.complexity >= 4)
    };
    
    return Object.entries(complexityGroups).map(([level, group]) => ({
      level,
      count: group.length,
      averageScore: group.reduce((sum, s) => sum + s.finalScore, 0) / group.length,
      averageAttempts: group.reduce((sum, s) => sum + s.totalAttempts, 0) / group.length,
      successRate: (group.filter(s => s.thresholdReached).length / group.length) * 100
    }));
  }
  
  analyzeTrends(sessions, metric) {
    const values = sessions.map(s => s[metric]);
    const trend = this.calculateLinearTrend(values);
    
    return {
      current: values[values.length - 1],
      trend: trend.slope > 0 ? 'increasing' : trend.slope < 0 ? 'decreasing' : 'stable',
      slope: trend.slope,
      correlation: trend.correlation
    };
  }
  
  analyzeSuccessFactors(sessions) {
    const successfulSessions = sessions.filter(s => s.thresholdReached);
    const factors = [];
    
    // Analizar factores comunes en sesiones exitosas
    const avgSuccessAttempts = successfulSessions.reduce((sum, s) => sum + s.totalAttempts, 0) / successfulSessions.length;
    const avgSuccessTokens = successfulSessions.reduce((sum, s) => sum + s.totalTokens, 0) / successfulSessions.length;
    
    factors.push({
      factor: 'optimal_attempts',
      value: Math.round(avgSuccessAttempts),
      description: 'Average attempts in successful sessions'
    });
    
    factors.push({
      factor: 'optimal_tokens',
      value: Math.round(avgSuccessTokens),
      description: 'Average tokens in successful sessions'
    });
    
    return factors;
  }
  
  generateAlerts(recentSessions) {
    const alerts = [];
    
    // Alerta por baja tasa de éxito reciente
    const recentSuccessRate = (recentSessions.filter(s => s.thresholdReached).length / recentSessions.length) * 100;
    if (recentSuccessRate < 50) {
      alerts.push({
        type: 'warning',
        message: `Low recent success rate: ${recentSuccessRate.toFixed(1)}%`,
        severity: 'medium'
      });
    }
    
    // Alerta por aumento en intentos promedio
    const recentAvgAttempts = recentSessions.reduce((sum, s) => sum + s.totalAttempts, 0) / recentSessions.length;
    if (recentAvgAttempts > 4) {
      alerts.push({
        type: 'warning',
        message: `High average attempts: ${recentAvgAttempts.toFixed(1)}`,
        severity: 'medium'
      });
    }
    
    return alerts;
  }
  
  generateSystemRecommendations(efficiency, patterns) {
    const recommendations = [];
    
    if (efficiency.successRate < 70) {
      recommendations.push('Consider lowering score threshold or improving prompt engineering');
    }
    
    if (efficiency.averageAttempts > 4) {
      recommendations.push('Optimize initial prompts to reduce required attempts');
    }
    
    if (patterns.patterns.length > 0) {
      recommendations.push(`Address common failure pattern: ${patterns.patterns[0].pattern}`);
    }
    
    return recommendations;
  }
  
  // Métodos matemáticos auxiliares
  calculateMedian(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0 
      ? (sorted[mid - 1] + sorted[mid]) / 2 
      : sorted[mid];
  }
  
  calculateLinearTrend(values) {
    const n = values.length;
    const x = Array.from({ length: n }, (_, i) => i);
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * values[i], 0);
    const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    // Calcular correlación
    const meanX = sumX / n;
    const meanY = sumY / n;
    const numerator = x.reduce((sum, xi, i) => sum + (xi - meanX) * (values[i] - meanY), 0);
    const denomX = Math.sqrt(x.reduce((sum, xi) => sum + Math.pow(xi - meanX, 2), 0));
    const denomY = Math.sqrt(values.reduce((sum, yi) => sum + Math.pow(yi - meanY, 2), 0));
    const correlation = numerator / (denomX * denomY);
    
    return { slope, intercept, correlation };
  }
  
  calculatePerformanceMetrics(data, metric) {
    const values = data.map(d => d[metric]);
    return {
      mean: values.reduce((a, b) => a + b, 0) / values.length,
      median: this.calculateMedian(values),
      min: Math.min(...values),
      max: Math.max(...values),
      std: Math.sqrt(values.reduce((sum, val) => sum + Math.pow(val - (values.reduce((a, b) => a + b, 0) / values.length), 2), 0) / values.length)
    };
  }
  
  calculateCorrelation(data, metric1, metric2) {
    const values1 = data.map(d => d[metric1]);
    const values2 = data.map(d => d[metric2]);
    
    const mean1 = values1.reduce((a, b) => a + b, 0) / values1.length;
    const mean2 = values2.reduce((a, b) => a + b, 0) / values2.length;
    
    const numerator = values1.reduce((sum, val1, i) => sum + (val1 - mean1) * (values2[i] - mean2), 0);
    const denom1 = Math.sqrt(values1.reduce((sum, val) => sum + Math.pow(val - mean1, 2), 0));
    const denom2 = Math.sqrt(values2.reduce((sum, val) => sum + Math.pow(val - mean2, 2), 0));
    
    return numerator / (denom1 * denom2);
  }
  
  calculateDistribution(data, metric) {
    const values = data.map(d => d[metric]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min;
    const buckets = 10;
    const bucketSize = range / buckets;
    
    const distribution = Array(buckets).fill(0);
    
    values.forEach(value => {
      const bucketIndex = Math.min(Math.floor((value - min) / bucketSize), buckets - 1);
      distribution[bucketIndex]++;
    });
    
    return distribution.map((count, i) => ({
      range: `${(min + i * bucketSize).toFixed(2)}-${(min + (i + 1) * bucketSize).toFixed(2)}`,
      count,
      percentage: (count / values.length) * 100
    }));
  }
  
  detectOutliers(data) {
    const outliers = [];
    
    ['finalScore', 'attempts', 'tokens', 'duration'].forEach(metric => {
      const values = data.map(d => d[metric]);
      const q1 = this.calculatePercentile(values, 25);
      const q3 = this.calculatePercentile(values, 75);
      const iqr = q3 - q1;
      const lowerBound = q1 - 1.5 * iqr;
      const upperBound = q3 + 1.5 * iqr;
      
      data.forEach(session => {
        const value = session[metric];
        if (value < lowerBound || value > upperBound) {
          outliers.push({
            sessionId: session.sessionId,
            metric,
            value,
            type: value < lowerBound ? 'low' : 'high'
          });
        }
      });
    });
    
    return outliers;
  }
  
  calculatePercentile(values, percentile) {
    const sorted = [...values].sort((a, b) => a - b);
    const index = (percentile / 100) * (sorted.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const weight = index - lower;
    
    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
  }
}

/**
 * Instancia global del analizador
 */
export const recursiveAnalytics = new RecursiveAnalytics();

/**
 * Función para generar reporte completo del sistema
 */
export async function generateSystemReport(sessions) {
  try {
    if (!isLangwatchEnabled()) {
      logger.warn('Langwatch no habilitado, generando reporte básico');
      return generateBasicReport(sessions);
    }
    
    const analytics = new RecursiveAnalytics();
    
    const report = {
      timestamp: new Date().toISOString(),
      overview: analytics.createRecursiveOverviewDashboard(sessions),
      performance: analytics.createPerformanceDashboard(sessions),
      efficiency: analytics.generateEfficiencyMetrics(sessions),
      patterns: analytics.analyzeFailurePatterns(sessions),
      recommendations: analytics.generateSystemRecommendations(
        analytics.generateEfficiencyMetrics(sessions),
        analytics.analyzeFailurePatterns(sessions)
      )
    };
    
    logger.info('📊 Reporte del sistema generado exitosamente', {
      sessionsAnalyzed: sessions.length,
      reportSections: Object.keys(report).length
    });
    
    return report;
    
  } catch (error) {
    logger.error('Error generando reporte del sistema:', error);
    throw error;
  }
}

/**
 * Función para generar reporte básico sin Langwatch
 */
function generateBasicReport(sessions) {
  const totalSessions = sessions.length;
  const successfulSessions = sessions.filter(s => s.thresholdReached).length;
  const averageScore = sessions.reduce((sum, s) => sum + s.finalScore, 0) / totalSessions;
  const averageAttempts = sessions.reduce((sum, s) => sum + s.totalAttempts, 0) / totalSessions;
  
  return {
    timestamp: new Date().toISOString(),
    basic: true,
    summary: {
      totalSessions,
      successRate: (successfulSessions / totalSessions) * 100,
      averageScore,
      averageAttempts
    },
    note: 'Reporte básico - Langwatch no habilitado'
  };
}

export default {
  RecursiveAnalytics,
  recursiveAnalytics,
  generateSystemReport,
  ANALYTICS_CONFIG
};

