/**
 * Analytics Controller
 * 
 * Controlador para endpoints de analytics y dashboards del sistema recursivo
 * 
 * @module analyticsController
 */

import { generateSystemReport, recursiveAnalytics } from '../services/langwatchAnalytics.js';
import { getContext } from '../services/memoryService.js';
import logger from '../utils/logger.js';

/**
 * Obtiene el dashboard de overview del sistema recursivo
 */
export async function getRecursiveOverview(req, res) {
  try {
    const { timeRange = '24h', limit = 100 } = req.query;
    
    // Simular obtención de sesiones (en implementación real vendría de la base de datos)
    const sessions = await getMockSessions(limit);
    
    const analytics = new recursiveAnalytics.constructor();
    const dashboard = analytics.createRecursiveOverviewDashboard(sessions);
    
    logger.info('📊 Dashboard de overview generado', {
      sessionsAnalyzed: sessions.length,
      timeRange
    });
    
    res.json({
      success: true,
      dashboard,
      metadata: {
        timeRange,
        sessionsAnalyzed: sessions.length,
        generatedAt: new Date().toISOString()
      }
    });
    
  } catch (error) {
    logger.error('Error generando dashboard de overview:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

/**
 * Obtiene el dashboard de análisis de rendimiento
 */
export async function getPerformanceAnalysis(req, res) {
  try {
    const { timeRange = '24h', limit = 100 } = req.query;
    
    const sessions = await getMockSessions(limit);
    
    const analytics = new recursiveAnalytics.constructor();
    const dashboard = analytics.createPerformanceDashboard(sessions);
    
    logger.info('📊 Dashboard de rendimiento generado', {
      sessionsAnalyzed: sessions.length,
      timeRange
    });
    
    res.json({
      success: true,
      dashboard,
      metadata: {
        timeRange,
        sessionsAnalyzed: sessions.length,
        generatedAt: new Date().toISOString()
      }
    });
    
  } catch (error) {
    logger.error('Error generando dashboard de rendimiento:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

/**
 * Obtiene métricas en tiempo real
 */
export async function getRealTimeMetrics(req, res) {
  try {
    const recentSessions = await getMockSessions(20); // Últimas 20 sesiones
    
    const metrics = {
      timestamp: new Date().toISOString(),
      current: {
        activeSessions: 3, // Simular sesiones activas
        averageScore: recentSessions.reduce((sum, s) => sum + s.finalScore, 0) / recentSessions.length,
        successRate: (recentSessions.filter(s => s.thresholdReached).length / recentSessions.length) * 100,
        averageAttempts: recentSessions.reduce((sum, s) => sum + s.totalAttempts, 0) / recentSessions.length
      },
      trends: {
        scoreProgression: calculateRecentTrend(recentSessions, 'finalScore'),
        attemptTrends: calculateRecentTrend(recentSessions, 'totalAttempts'),
        tokenUsage: calculateRecentTrend(recentSessions, 'totalTokens')
      },
      alerts: generateRealTimeAlerts(recentSessions)
    };
    
    res.json({
      success: true,
      metrics
    });
    
  } catch (error) {
    logger.error('Error obteniendo métricas en tiempo real:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

/**
 * Genera reporte completo del sistema
 */
export async function getSystemReport(req, res) {
  try {
    const { timeRange = '7d', format = 'json' } = req.query;
    
    const sessions = await getMockSessions(500); // Más sesiones para reporte completo
    const report = await generateSystemReport(sessions);
    
    if (format === 'pdf') {
      // TODO: Implementar generación de PDF
      return res.status(501).json({
        success: false,
        error: 'PDF generation not implemented yet'
      });
    }
    
    logger.info('📊 Reporte completo del sistema generado', {
      sessionsAnalyzed: sessions.length,
      timeRange,
      format
    });
    
    res.json({
      success: true,
      report,
      metadata: {
        timeRange,
        format,
        sessionsAnalyzed: sessions.length,
        generatedAt: new Date().toISOString()
      }
    });
    
  } catch (error) {
    logger.error('Error generando reporte del sistema:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

/**
 * Obtiene análisis de patrones específicos
 */
export async function getPatternAnalysis(req, res) {
  try {
    const { pattern, timeRange = '7d' } = req.query;
    
    const sessions = await getMockSessions(200);
    const analytics = new recursiveAnalytics.constructor();
    
    let analysis;
    
    switch (pattern) {
      case 'failures':
        analysis = analytics.analyzeFailurePatterns(sessions);
        break;
      case 'contradictions':
        analysis = analyzeContradictionPatterns(sessions);
        break;
      case 'efficiency':
        analysis = analytics.generateEfficiencyMetrics(sessions);
        break;
      default:
        return res.status(400).json({
          success: false,
          error: 'Invalid pattern type. Use: failures, contradictions, efficiency'
        });
    }
    
    res.json({
      success: true,
      pattern,
      analysis,
      metadata: {
        timeRange,
        sessionsAnalyzed: sessions.length,
        generatedAt: new Date().toISOString()
      }
    });
    
  } catch (error) {
    logger.error('Error analizando patrones:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

/**
 * Obtiene métricas de una sesión específica
 */
export async function getSessionMetrics(req, res) {
  try {
    const { sessionId } = req.params;
    
    // En implementación real, obtener de la base de datos
    const sessionData = await getMockSessionData(sessionId);
    
    if (!sessionData) {
      return res.status(404).json({
        success: false,
        error: 'Session not found'
      });
    }
    
    const analytics = new recursiveAnalytics.constructor();
    const scoreAnalysis = analytics.analyzeScoreProgression(sessionData.attempts);
    const contradictionAnalysis = analytics.analyzeContradictionEffectiveness(sessionData.attempts);
    
    const metrics = {
      sessionId,
      summary: {
        finalScore: sessionData.finalScore,
        totalAttempts: sessionData.totalAttempts,
        totalTokens: sessionData.totalTokens,
        totalDuration: sessionData.totalDuration,
        thresholdReached: sessionData.thresholdReached
      },
      scoreAnalysis,
      contradictionAnalysis,
      timeline: sessionData.attempts.map((attempt, index) => ({
        attempt: index + 1,
        score: attempt.score,
        tokens: attempt.tokens,
        duration: attempt.duration,
        contradictionTriggered: attempt.contradictionTriggered || false
      }))
    };
    
    res.json({
      success: true,
      metrics
    });
    
  } catch (error) {
    logger.error('Error obteniendo métricas de sesión:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

/**
 * Funciones auxiliares para generar datos mock
 */
async function getMockSessions(limit) {
  // En implementación real, esto vendría de la base de datos
  const sessions = [];
  
  for (let i = 0; i < limit; i++) {
    const attempts = Math.floor(Math.random() * 5) + 1;
    const finalScore = Math.random() * 0.4 + 0.6; // Score entre 0.6 y 1.0
    const totalTokens = Math.floor(Math.random() * 3000) + 1000;
    const totalDuration = Math.floor(Math.random() * 30000) + 5000;
    
    sessions.push({
      sessionId: `session_${Date.now()}_${i}`,
      finalScore,
      totalAttempts: attempts,
      totalTokens,
      totalDuration,
      thresholdReached: finalScore >= 0.8,
      complexity: Math.floor(Math.random() * 5) + 1,
      attempts: generateMockAttempts(attempts, finalScore),
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
    });
  }
  
  return sessions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

function generateMockAttempts(count, finalScore) {
  const attempts = [];
  let currentScore = Math.random() * 0.3 + 0.2; // Empezar bajo
  
  for (let i = 0; i < count; i++) {
    const isLast = i === count - 1;
    const score = isLast ? finalScore : currentScore + (Math.random() * 0.2);
    const contradictionTriggered = i >= 2 && score < 0.6;
    
    attempts.push({
      attempt: i + 1,
      score: Math.min(score, 1.0),
      tokens: Math.floor(Math.random() * 800) + 200,
      duration: Math.floor(Math.random() * 5000) + 1000,
      contradictionTriggered,
      feedback: generateMockFeedback(score)
    });
    
    currentScore = score;
  }
  
  return attempts;
}

function generateMockFeedback(score) {
  if (score < 0.4) return 'Response needs significant improvement';
  if (score < 0.6) return 'Response partially addresses requirements';
  if (score < 0.8) return 'Good response with minor issues';
  return 'Excellent response meeting all criteria';
}

async function getMockSessionData(sessionId) {
  // Simular obtención de datos de sesión específica
  const attempts = generateMockAttempts(4, 0.85);
  
  return {
    sessionId,
    finalScore: 0.85,
    totalAttempts: 4,
    totalTokens: 2500,
    totalDuration: 15000,
    thresholdReached: true,
    attempts
  };
}

function calculateRecentTrend(sessions, metric) {
  const values = sessions.slice(-10).map(s => s[metric]); // Últimos 10 valores
  if (values.length < 2) return 'insufficient_data';
  
  const recent = values.slice(-3).reduce((a, b) => a + b, 0) / 3;
  const previous = values.slice(-6, -3).reduce((a, b) => a + b, 0) / 3;
  
  const change = ((recent - previous) / previous) * 100;
  
  if (change > 5) return 'increasing';
  if (change < -5) return 'decreasing';
  return 'stable';
}

function generateRealTimeAlerts(sessions) {
  const alerts = [];
  
  const recentFailures = sessions.filter(s => !s.thresholdReached).length;
  if (recentFailures > sessions.length * 0.4) {
    alerts.push({
      type: 'warning',
      message: 'High failure rate in recent sessions',
      severity: 'medium'
    });
  }
  
  const avgAttempts = sessions.reduce((sum, s) => sum + s.totalAttempts, 0) / sessions.length;
  if (avgAttempts > 4) {
    alerts.push({
      type: 'info',
      message: 'Average attempts above normal',
      severity: 'low'
    });
  }
  
  return alerts;
}

function analyzeContradictionPatterns(sessions) {
  const analytics = new recursiveAnalytics.constructor();
  const contradictionData = sessions.map(session => 
    analytics.analyzeContradictionEffectiveness(session.attempts)
  );
  
  const triggered = contradictionData.filter(d => d.triggered).length;
  const effective = contradictionData.filter(d => d.effectiveness > 0.5).length;
  
  return {
    totalSessions: sessions.length,
    contradictionsTriggered: triggered,
    effectiveContradictions: effective,
    effectivenessRate: triggered > 0 ? (effective / triggered) * 100 : 0,
    averageImprovement: contradictionData
      .filter(d => d.triggered)
      .reduce((sum, d) => sum + d.averageImprovement, 0) / triggered || 0
  };
}

export default {
  getRecursiveOverview,
  getPerformanceAnalysis,
  getRealTimeMetrics,
  getSystemReport,
  getPatternAnalysis,
  getSessionMetrics
};

