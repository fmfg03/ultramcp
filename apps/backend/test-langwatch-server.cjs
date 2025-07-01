/**
 * Simple Test Server with Langwatch Integration
 * 
 * Servidor simplificado para probar la integración de Langwatch
 */

const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware básico
app.use(cors());
app.use(express.json());

// Simular inicialización de Langwatch
const LANGWATCH_ENABLED = !!process.env.LANGWATCH_API_KEY;

console.log('🔍 Langwatch Status:', LANGWATCH_ENABLED ? 'ENABLED' : 'DISABLED');
if (LANGWATCH_ENABLED) {
  console.log('🔍 Langwatch API Key:', process.env.LANGWATCH_API_KEY.substring(0, 10) + '...');
}

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    langwatchEnabled: LANGWATCH_ENABLED,
    version: '1.0.0'
  });
});

// Analytics health check
app.get('/api/analytics/health', (req, res) => {
  res.json({
    success: true,
    service: 'analytics',
    status: 'healthy',
    timestamp: new Date().toISOString(),
    langwatchEnabled: LANGWATCH_ENABLED,
    features: {
      realTimeMetrics: true,
      dashboards: true,
      patternAnalysis: true,
      reportGeneration: true
    }
  });
});

// Test endpoint para recursive planner
app.post('/api/test-recursive', async (req, res) => {
  try {
    const { prompt, sessionId } = req.body;
    
    console.log('🔄 Testing recursive planner simulation');
    console.log('📝 Prompt:', prompt?.substring(0, 100) + '...');
    console.log('🆔 Session ID:', sessionId);
    
    // Simular proceso recursivo
    const mockResult = {
      success: true,
      result: {
        reply: 'Mock response from recursive planner',
        score: 0.85,
        attempts: [
          { attempt: 1, score: 0.4, contradictionTriggered: false },
          { attempt: 2, score: 0.6, contradictionTriggered: false },
          { attempt: 3, score: 0.85, contradictionTriggered: true }
        ],
        totalAttempts: 3,
        totalTokens: 1500,
        totalDuration: 8000,
        thresholdReached: true
      },
      langwatchTracked: LANGWATCH_ENABLED
    };
    
    if (LANGWATCH_ENABLED) {
      console.log('🔍 Langwatch tracking simulated');
    }
    
    res.json(mockResult);
    
  } catch (error) {
    console.error('❌ Error in recursive test:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Test endpoint para analytics
app.get('/api/analytics/overview', (req, res) => {
  const mockDashboard = {
    success: true,
    dashboard: {
      title: 'Recursive Planner Overview',
      timestamp: new Date().toISOString(),
      summary: {
        totalSessions: 150,
        successRate: 78.5,
        averageScore: 0.82,
        averageAttempts: 2.8,
        averageTokens: 1850
      },
      trends: {
        scoreProgression: 'improving',
        attemptTrends: 'stable',
        tokenTrends: 'decreasing'
      },
      patterns: {
        commonFailures: [
          { pattern: 'incomplete_response', count: 12, percentage: 15.2 },
          { pattern: 'low_score', count: 8, percentage: 10.1 }
        ],
        successFactors: [
          { factor: 'optimal_attempts', value: 3, description: 'Average attempts in successful sessions' }
        ]
      },
      alerts: [
        {
          type: 'info',
          message: 'System performing within normal parameters',
          severity: 'low'
        }
      ]
    },
    metadata: {
      timeRange: '24h',
      sessionsAnalyzed: 150,
      generatedAt: new Date().toISOString(),
      langwatchEnabled: LANGWATCH_ENABLED
    }
  };
  
  res.json(mockDashboard);
});

// Test endpoint para métricas en tiempo real
app.get('/api/analytics/realtime', (req, res) => {
  const mockMetrics = {
    success: true,
    metrics: {
      timestamp: new Date().toISOString(),
      current: {
        activeSessions: 3,
        averageScore: 0.84,
        successRate: 82.1,
        averageAttempts: 2.6
      },
      trends: {
        scoreProgression: 'improving',
        attemptTrends: 'stable',
        tokenUsage: 'optimizing'
      },
      alerts: []
    },
    langwatchEnabled: LANGWATCH_ENABLED
  };
  
  res.json(mockMetrics);
});

// Test endpoint para análisis de sesión específica
app.get('/api/analytics/session/:sessionId', (req, res) => {
  const { sessionId } = req.params;
  
  const mockSessionMetrics = {
    success: true,
    metrics: {
      sessionId,
      summary: {
        finalScore: 0.87,
        totalAttempts: 3,
        totalTokens: 1650,
        totalDuration: 12000,
        thresholdReached: true
      },
      scoreAnalysis: {
        trend: 'improving',
        improvement: 0.47,
        volatility: 0.15,
        finalScore: 0.87,
        patterns: ['gradual_improvement', 'contradiction_breakthrough']
      },
      contradictionAnalysis: {
        triggered: true,
        count: 1,
        effectiveness: 0.8,
        averageImprovement: 0.25
      },
      timeline: [
        { attempt: 1, score: 0.4, tokens: 500, duration: 3000, contradictionTriggered: false },
        { attempt: 2, score: 0.62, tokens: 550, duration: 4000, contradictionTriggered: false },
        { attempt: 3, score: 0.87, tokens: 600, duration: 5000, contradictionTriggered: true }
      ]
    },
    langwatchEnabled: LANGWATCH_ENABLED
  };
  
  res.json(mockSessionMetrics);
});

// Endpoint de prueba general para Langwatch
app.post('/api/test-langwatch', async (req, res) => {
  try {
    const { message } = req.body;
    
    console.log('🔍 Langwatch test endpoint called');
    console.log('📝 Message:', message);
    
    if (LANGWATCH_ENABLED) {
      console.log('✅ Langwatch is enabled and ready');
    } else {
      console.log('⚠️ Langwatch is disabled - no API key configured');
    }
    
    res.json({
      success: true,
      message: 'Langwatch test completed',
      timestamp: new Date().toISOString(),
      receivedMessage: message,
      langwatchStatus: LANGWATCH_ENABLED ? 'enabled' : 'disabled',
      apiKeyConfigured: !!process.env.LANGWATCH_API_KEY
    });
    
  } catch (error) {
    console.error('❌ Error in Langwatch test:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Middleware de manejo de errores
app.use((error, req, res, next) => {
  console.error('❌ Unhandled error:', error);
  res.status(500).json({
    success: false,
    error: error.message,
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found',
    path: req.originalUrl,
    timestamp: new Date().toISOString()
  });
});

// Iniciar servidor
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 MCP Test Server iniciado en puerto ${PORT}`);
  console.log(`🔍 Langwatch: ${LANGWATCH_ENABLED ? 'ENABLED' : 'DISABLED'}`);
  console.log(`🌐 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`⏰ Started at: ${new Date().toISOString()}`);
});

module.exports = app;

