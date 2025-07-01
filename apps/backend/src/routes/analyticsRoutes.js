/**
 * Analytics Routes
 * 
 * Rutas para dashboards y métricas del sistema recursivo con Langwatch
 * 
 * @module analyticsRoutes
 */

const express = require('express');
const router = express.Router();

// Importar controladores
const {
  getRecursiveOverview,
  getPerformanceAnalysis,
  getRealTimeMetrics,
  getSystemReport,
  getPatternAnalysis,
  getSessionMetrics
} = require('../controllers/analyticsController.js');

/**
 * @route GET /api/analytics/overview
 * @desc Obtiene dashboard de overview del sistema recursivo
 * @query {string} timeRange - Rango de tiempo (1h, 24h, 7d, 30d)
 * @query {number} limit - Límite de sesiones a analizar
 */
router.get('/overview', getRecursiveOverview);

/**
 * @route GET /api/analytics/performance
 * @desc Obtiene dashboard de análisis de rendimiento
 * @query {string} timeRange - Rango de tiempo
 * @query {number} limit - Límite de sesiones a analizar
 */
router.get('/performance', getPerformanceAnalysis);

/**
 * @route GET /api/analytics/realtime
 * @desc Obtiene métricas en tiempo real
 */
router.get('/realtime', getRealTimeMetrics);

/**
 * @route GET /api/analytics/report
 * @desc Genera reporte completo del sistema
 * @query {string} timeRange - Rango de tiempo
 * @query {string} format - Formato del reporte (json, pdf)
 */
router.get('/report', getSystemReport);

/**
 * @route GET /api/analytics/patterns
 * @desc Obtiene análisis de patrones específicos
 * @query {string} pattern - Tipo de patrón (failures, contradictions, efficiency)
 * @query {string} timeRange - Rango de tiempo
 */
router.get('/patterns', getPatternAnalysis);

/**
 * @route GET /api/analytics/session/:sessionId
 * @desc Obtiene métricas detalladas de una sesión específica
 * @param {string} sessionId - ID de la sesión
 */
router.get('/session/:sessionId', getSessionMetrics);

/**
 * @route GET /api/analytics/health
 * @desc Health check para el sistema de analytics
 */
router.get('/health', (req, res) => {
  res.json({
    success: true,
    service: 'analytics',
    status: 'healthy',
    timestamp: new Date().toISOString(),
    langwatchEnabled: !!process.env.LANGWATCH_API_KEY,
    features: {
      realTimeMetrics: true,
      dashboards: true,
      patternAnalysis: true,
      reportGeneration: true
    }
  });
});

module.exports = router;

