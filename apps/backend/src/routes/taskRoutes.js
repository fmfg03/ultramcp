/**
 * Task Routes
 * 
 * Rutas para el nuevo sistema de orquestación de tareas
 * 
 * @module taskRoutes
 */

import express from 'express';
import { 
  runTask, 
  getTaskStatus, 
  getTaskHistory, 
  cancelTask, 
  retryTask 
} from '../controllers/taskController.js';
import { validateRequest } from '../middleware/validationMiddleware.js';
import { z } from 'zod';

const router = express.Router();

/**
 * Esquemas de validación
 */
const runTaskSchema = z.object({
  request: z.string().min(1, 'El campo request es requerido').max(10000, 'El request es demasiado largo'),
  options: z.object({
    userId: z.string().optional(),
    maxRetries: z.number().min(0).max(5).optional(),
    retryThreshold: z.number().min(0).max(1).optional(),
    preferredModel: z.enum(['openai', 'anthropic', 'google']).optional(),
    priority: z.enum(['low', 'normal', 'high']).optional()
  }).optional()
});

const retryTaskSchema = z.object({
  strategy: z.enum(['simple', 'enhanced', 'alternative', 'decomposed']).optional(),
  userId: z.string().optional()
});

const cancelTaskSchema = z.object({
  reason: z.string().optional(),
  userId: z.string().optional()
});

const historyQuerySchema = z.object({
  userId: z.string().optional(),
  taskType: z.string().optional(),
  status: z.enum(['active', 'completed', 'failed', 'cancelled']).optional(),
  limit: z.string().regex(/^\d+$/).transform(Number).refine(n => n <= 100).optional(),
  offset: z.string().regex(/^\d+$/).transform(Number).optional(),
  dateFrom: z.string().datetime().optional(),
  dateTo: z.string().datetime().optional()
});

/**
 * POST /api/run-task
 * Ejecuta una tarea completa con el nuevo sistema de orquestación
 */
router.post('/run-task', validateRequest(runTaskSchema), runTask);

/**
 * GET /api/task/:sessionId
 * Obtiene el estado de una sesión específica
 */
router.get('/task/:sessionId', getTaskStatus);

/**
 * GET /api/tasks/history
 * Obtiene el historial de tareas del usuario
 */
router.get('/tasks/history', validateRequest(historyQuerySchema, 'query'), getTaskHistory);

/**
 * POST /api/task/:sessionId/cancel
 * Cancela una tarea en ejecución
 */
router.post('/task/:sessionId/cancel', validateRequest(cancelTaskSchema), cancelTask);

/**
 * POST /api/task/:sessionId/retry
 * Reintenta una tarea manualmente
 */
router.post('/task/:sessionId/retry', validateRequest(retryTaskSchema), retryTask);

/**
 * GET /api/tasks/stats
 * Obtiene estadísticas generales del sistema
 */
router.get('/tasks/stats', async (req, res, next) => {
  try {
    const { getSessionStats } = await import('../services/memoryService.js');
    const retryManager = (await import('../services/retryManager.js')).default;
    
    const statsResult = await getSessionStats();
    const retryStats = retryManager.getRetryStats();
    
    if (!statsResult.success) {
      throw new Error(`Error obteniendo estadísticas: ${statsResult.error}`);
    }
    
    const response = {
      success: true,
      systemStats: statsResult.stats,
      retryStats,
      timestamp: new Date().toISOString()
    };
    
    res.status(200).json(response);
    
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/health
 * Endpoint de health check para el sistema de orquestación
 */
router.get('/health', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'unknown',
        llm_providers: {
          openai: !!process.env.OPENAI_API_KEY,
          anthropic: !!process.env.ANTHROPIC_API_KEY,
          google: !!process.env.GOOGLE_API_KEY
        },
        memory_service: true,
        retry_manager: true
      }
    };
    
    // Verificar conexión a base de datos
    try {
      const { getSupabaseClient } = await import('../../adapters/supabaseAdapter.js');
      const supabase = getSupabaseClient();
      const { data, error } = await supabase.from('sessions').select('id').limit(1);
      health.services.database = error ? 'error' : 'healthy';
    } catch (dbError) {
      health.services.database = 'error';
    }
    
    // Determinar estado general
    const hasHealthyLLM = Object.values(health.services.llm_providers).some(Boolean);
    const isDatabaseHealthy = health.services.database === 'healthy';
    
    if (!hasHealthyLLM || !isDatabaseHealthy) {
      health.status = 'degraded';
    }
    
    const statusCode = health.status === 'healthy' ? 200 : 503;
    res.status(statusCode).json(health);
    
  } catch (error) {
    res.status(503).json({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

export default router;

