/**
 * Simple test server for the refactored MCP system
 * This is a simplified version to test the new orchestration system
 */

const express = require("express");
const cors = require("cors");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: true,
  credentials: true
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Simple logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    environment: 'development',
    services: {
      database: 'not_configured',
      llm_providers: {
        openai: !!process.env.OPENAI_API_KEY,
        anthropic: !!process.env.ANTHROPIC_API_KEY,
        google: !!process.env.GOOGLE_API_KEY
      }
    }
  });
});

// Mock endpoint for run-task (for testing frontend)
app.post('/api/run-task', async (req, res) => {
  try {
    const { request, options = {} } = req.body;
    
    if (!request) {
      return res.status(400).json({
        success: false,
        error: 'Request field is required'
      });
    }

    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Mock response
    const sessionId = `session_${Date.now()}`;
    const mockResponse = {
      success: true,
      sessionId,
      result: {
        builderOutput: {
          sessionId,
          results: [
            {
              subtaskId: 'analyze_request',
              agent: 'researcher',
              response: `Análisis completado para: "${request.substring(0, 100)}..."`,
              timestamp: new Date().toISOString()
            },
            {
              subtaskId: 'execute_task',
              agent: 'builder',
              response: 'Tarea ejecutada exitosamente con implementación completa.',
              timestamp: new Date().toISOString()
            }
          ],
          completedSteps: [
            { id: 'analyze_request', status: 'completed' },
            { id: 'execute_task', status: 'completed' }
          ],
          errors: [],
          warnings: []
        },
        evaluation: {
          score: 0.85,
          qualityLevel: 'good',
          feedback: {
            summary: 'Buen trabajo. El resultado cumple con la mayoría de los requerimientos.',
            strengths: [
              'Implementación completa',
              'Buena estructura del código',
              'Documentación clara'
            ],
            improvements: [
              'Podría mejorar el manejo de errores',
              'Agregar más pruebas unitarias'
            ],
            recommendations: []
          },
          retry: false
        },
        totalDuration: 2000,
        status: 'completed'
      },
      trace: {
        session: {
          id: sessionId,
          original_input: request,
          task_type: 'web_development',
          status: 'completed',
          created_at: new Date().toISOString()
        },
        steps: [
          {
            id: 'step_1',
            step_name: 'reasoning_analysis',
            step_type: 'reasoning',
            agent_used: 'reasoningShell',
            status: 'success',
            started_at: new Date(Date.now() - 2000).toISOString(),
            completed_at: new Date(Date.now() - 1500).toISOString(),
            duration_ms: 500
          },
          {
            id: 'step_2',
            step_name: 'execute_task',
            step_type: 'execution',
            agent_used: 'builder',
            status: 'success',
            started_at: new Date(Date.now() - 1500).toISOString(),
            completed_at: new Date(Date.now() - 500).toISOString(),
            duration_ms: 1000
          },
          {
            id: 'step_3',
            step_name: 'reward_evaluation',
            step_type: 'evaluation',
            agent_used: 'rewardShell',
            status: 'success',
            started_at: new Date(Date.now() - 500).toISOString(),
            completed_at: new Date().toISOString(),
            duration_ms: 500
          }
        ],
        rewards: [
          {
            id: 'reward_1',
            score: 0.85,
            quality_level: 'good',
            retry_recommended: false,
            created_at: new Date().toISOString()
          }
        ],
        executionPlan: {
          plan_data: {
            taskType: 'web_development',
            complexity: {
              level: 'medium',
              score: 4
            },
            subtasks: [
              {
                id: 'analyze_request',
                description: 'Analizar y entender la solicitud del usuario',
                agent: 'researcher',
                priority: 1
              },
              {
                id: 'execute_task',
                description: 'Ejecutar la tarea principal',
                agent: 'builder',
                priority: 2
              }
            ]
          },
          estimated_duration: '15-30 min'
        },
        summary: {
          totalSteps: 3,
          completedSteps: 3,
          failedSteps: 0,
          averageScore: 0.85
        }
      },
      retryInfo: {
        retryCount: 0,
        retryHistory: [],
        maxRetries: 2
      },
      metadata: {
        totalDuration: 2000,
        finalScore: 0.85,
        qualityLevel: 'good',
        completedAt: new Date().toISOString()
      }
    };

    res.status(200).json(mockResponse);

  } catch (error) {
    console.error('Error in run-task:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Mock endpoint for task status
app.get('/api/task/:sessionId', (req, res) => {
  const { sessionId } = req.params;
  
  res.status(200).json({
    success: true,
    sessionId,
    status: 'completed',
    progress: {
      totalSteps: 3,
      completedSteps: 3,
      failedSteps: 0,
      completionPercentage: 100
    },
    currentScore: 0.85,
    retryInfo: {
      retryCount: 0,
      retryHistory: [],
      canRetry: false
    },
    lastActivity: new Date().toISOString()
  });
});

// Mock endpoint for task retry
app.post('/api/task/:sessionId/retry', (req, res) => {
  const { sessionId } = req.params;
  const { strategy = 'enhanced' } = req.body;
  
  res.status(200).json({
    success: true,
    originalSessionId: sessionId,
    newSessionId: `session_${Date.now()}`,
    retryCount: 1,
    strategy,
    message: 'Retry iniciado exitosamente'
  });
});

// Mock endpoint for task history
app.get('/api/tasks/history', (req, res) => {
  res.status(200).json({
    success: true,
    stats: {
      totalSessions: 5,
      byStatus: {
        completed: 3,
        failed: 1,
        active: 1
      },
      byTaskType: {
        web_development: 3,
        data_analysis: 2
      },
      successRate: 0.6
    },
    retryStats: {
      activeSessions: 1,
      totalSessions: 5,
      averageRetries: 0.4
    }
  });
});

// Mock endpoint for system stats
app.get('/api/tasks/stats', (req, res) => {
  res.status(200).json({
    success: true,
    systemStats: {
      totalSessions: 10,
      byStatus: {
        completed: 7,
        failed: 2,
        active: 1
      },
      successRate: 0.7
    },
    retryStats: {
      activeSessions: 1,
      totalSessions: 10,
      averageRetries: 0.3
    },
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Route not found',
    path: req.originalUrl
  });
});

// Error handler
app.use((error, req, res, next) => {
  console.error('Server error:', error);
  res.status(500).json({
    error: 'Internal server error',
    message: error.message
  });
});

// Start server
const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌐 MCP Test Server running on http://0.0.0.0:${PORT}`);
  console.log(`📋 Available endpoints:`);
  console.log(`   - GET  /health - Health check`);
  console.log(`   - POST /api/run-task - Execute task (MOCK)`);
  console.log(`   - GET  /api/task/:id - Get task status (MOCK)`);
  console.log(`   - GET  /api/tasks/history - Get task history (MOCK)`);
  console.log(`   - POST /api/task/:id/retry - Retry task (MOCK)`);
  console.log(`   - GET  /api/tasks/stats - System statistics (MOCK)`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🛑 SIGTERM received, shutting down gracefully...');
  server.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('🛑 SIGINT received, shutting down gracefully...');
  server.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});

module.exports = { app, server };

