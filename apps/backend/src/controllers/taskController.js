/**
 * Task Controller
 * 
 * Controlador para el nuevo endpoint /run-task que maneja
 * el ciclo completo: reasoning → builder → reward → persistencia
 * 
 * @module taskController
 */

import { orchestrateTask } from '../services/orchestrationService.js';
import { getContext, getSessionStats } from '../services/memoryService.js';
import retryManager from '../services/retryManager.js';
import { logger } from '../utils/logger.js';
import AppError from '../utils/AppError.js';

/**
 * Ejecuta una tarea completa con el nuevo sistema de orquestación
 * POST /api/run-task
 */
export async function runTask(req, res, next) {
  try {
    const { request, options = {} } = req.body;

    // Validar input
    if (!request || typeof request !== 'string' || request.trim().length === 0) {
      throw new AppError('El campo "request" es requerido y debe ser una cadena no vacía', 400);
    }

    logger.info('TaskController: Iniciando ejecución de tarea', {
      requestLength: request.length,
      userId: options.userId,
      userAgent: req.get('User-Agent')
    });

    // Preparar opciones con información de la request
    const taskOptions = {
      ...options,
      userAgent: req.get('User-Agent'),
      ipAddress: req.ip,
      timestamp: new Date().toISOString()
    };

    // Ejecutar orquestación
    const result = await orchestrateTask(request, taskOptions);

    if (!result.success) {
      throw new AppError(`Error en orquestación: ${result.error}`, 500);
    }

    // Obtener trazabilidad completa
    const traceResult = await getContext(result.sessionId);
    const trace = traceResult.success ? traceResult.context : null;

    // Obtener historial de reintentos
    const retryHistory = retryManager.getRetryHistory(result.sessionId);

    // Preparar respuesta
    const response = {
      success: true,
      sessionId: result.sessionId,
      result: result.result,
      trace: {
        session: trace?.session,
        steps: trace?.steps || [],
        rewards: trace?.rewards || [],
        executionPlan: trace?.executionPlan,
        summary: trace?.summary
      },
      retryInfo: {
        retryCount: retryHistory.length,
        retryHistory,
        maxRetries: 2
      },
      metadata: {
        totalDuration: result.result?.totalDuration,
        finalScore: result.result?.evaluation?.score,
        qualityLevel: result.result?.evaluation?.qualityLevel,
        completedAt: new Date().toISOString()
      }
    };

    logger.info('TaskController: Tarea completada exitosamente', {
      sessionId: result.sessionId,
      finalScore: response.metadata.finalScore,
      retryCount: response.retryInfo.retryCount,
      totalDuration: response.metadata.totalDuration
    });

    res.status(200).json(response);

  } catch (error) {
    logger.error('TaskController: Error ejecutando tarea', {
      error: error.message,
      stack: error.stack,
      requestBody: req.body
    });

    next(error);
  }
}

/**
 * Obtiene el estado de una sesión específica
 * GET /api/task/:sessionId
 */
export async function getTaskStatus(req, res, next) {
  try {
    const { sessionId } = req.params;

    if (!sessionId) {
      throw new AppError('Session ID es requerido', 400);
    }

    logger.info('TaskController: Obteniendo estado de tarea', { sessionId });

    // Obtener contexto completo
    const contextResult = await getContext(sessionId);
    
    if (!contextResult.success) {
      throw new AppError(`Error obteniendo contexto: ${contextResult.error}`, 404);
    }

    const context = contextResult.context;
    const retryHistory = retryManager.getRetryHistory(sessionId);

    // Determinar estado actual
    const currentStatus = determineCurrentStatus(context);

    const response = {
      success: true,
      sessionId,
      status: currentStatus,
      session: context.session,
      progress: {
        totalSteps: context.summary.totalSteps,
        completedSteps: context.summary.completedSteps,
        failedSteps: context.summary.failedSteps,
        completionPercentage: context.summary.totalSteps > 0 ? 
          (context.summary.completedSteps / context.summary.totalSteps) * 100 : 0
      },
      currentScore: context.summary.averageScore,
      retryInfo: {
        retryCount: retryHistory.length,
        retryHistory,
        canRetry: retryHistory.length < 2 && currentStatus !== 'completed'
      },
      lastActivity: new Date(context.summary.lastActivity).toISOString(),
      steps: context.steps,
      rewards: context.rewards
    };

    res.status(200).json(response);

  } catch (error) {
    logger.error('TaskController: Error obteniendo estado de tarea', {
      sessionId: req.params.sessionId,
      error: error.message
    });

    next(error);
  }
}

/**
 * Obtiene el historial de tareas del usuario
 * GET /api/tasks/history
 */
export async function getTaskHistory(req, res, next) {
  try {
    const { 
      userId, 
      taskType, 
      status, 
      limit = 20, 
      offset = 0,
      dateFrom,
      dateTo 
    } = req.query;

    logger.info('TaskController: Obteniendo historial de tareas', {
      userId,
      taskType,
      status,
      limit,
      offset
    });

    // Preparar filtros
    const filters = {};
    if (userId) filters.userId = userId;
    if (taskType) filters.taskType = taskType;
    if (status) filters.status = status;
    if (dateFrom) filters.dateFrom = dateFrom;
    if (dateTo) filters.dateTo = dateTo;

    // Obtener estadísticas
    const statsResult = await getSessionStats(filters);
    
    if (!statsResult.success) {
      throw new AppError(`Error obteniendo estadísticas: ${statsResult.error}`, 500);
    }

    const response = {
      success: true,
      stats: statsResult.stats,
      retryStats: retryManager.getRetryStats(),
      filters: {
        userId,
        taskType,
        status,
        dateFrom,
        dateTo
      },
      pagination: {
        limit: parseInt(limit),
        offset: parseInt(offset),
        total: statsResult.stats.totalSessions
      }
    };

    res.status(200).json(response);

  } catch (error) {
    logger.error('TaskController: Error obteniendo historial', {
      error: error.message,
      query: req.query
    });

    next(error);
  }
}

/**
 * Cancela una tarea en ejecución
 * POST /api/task/:sessionId/cancel
 */
export async function cancelTask(req, res, next) {
  try {
    const { sessionId } = req.params;
    const { reason = 'user_cancelled' } = req.body;

    if (!sessionId) {
      throw new AppError('Session ID es requerido', 400);
    }

    logger.info('TaskController: Cancelando tarea', { sessionId, reason });

    // Obtener contexto actual
    const contextResult = await getContext(sessionId);
    
    if (!contextResult.success) {
      throw new AppError(`Sesión no encontrada: ${contextResult.error}`, 404);
    }

    const context = contextResult.context;

    // Verificar si la tarea puede ser cancelada
    if (context.session.status === 'completed' || context.session.status === 'failed') {
      throw new AppError('La tarea ya está finalizada y no puede ser cancelada', 400);
    }

    // Actualizar estado de la sesión
    const { updateSessionStatus } = await import('../services/memoryService.js');
    const updateResult = await updateSessionStatus(sessionId, 'cancelled', {
      cancelledAt: new Date().toISOString(),
      cancelReason: reason,
      cancelledBy: req.body.userId || 'unknown'
    });

    if (!updateResult.success) {
      throw new AppError(`Error cancelando tarea: ${updateResult.error}`, 500);
    }

    // Limpiar historial de reintentos
    retryManager.clearRetryHistory(sessionId);

    const response = {
      success: true,
      sessionId,
      message: 'Tarea cancelada exitosamente',
      cancelledAt: new Date().toISOString(),
      reason
    };

    logger.info('TaskController: Tarea cancelada exitosamente', { sessionId });

    res.status(200).json(response);

  } catch (error) {
    logger.error('TaskController: Error cancelando tarea', {
      sessionId: req.params.sessionId,
      error: error.message
    });

    next(error);
  }
}

/**
 * Reintenta una tarea manualmente
 * POST /api/task/:sessionId/retry
 */
export async function retryTask(req, res, next) {
  try {
    const { sessionId } = req.params;
    const { strategy = 'enhanced' } = req.body;

    if (!sessionId) {
      throw new AppError('Session ID es requerido', 400);
    }

    logger.info('TaskController: Reintentando tarea manualmente', { 
      sessionId, 
      strategy 
    });

    // Verificar si se puede reintentar
    const retryHistory = retryManager.getRetryHistory(sessionId);
    if (retryHistory.length >= 2) {
      throw new AppError('Se ha alcanzado el límite máximo de reintentos', 400);
    }

    // Obtener contexto actual
    const contextResult = await getContext(sessionId);
    
    if (!contextResult.success) {
      throw new AppError(`Sesión no encontrada: ${contextResult.error}`, 404);
    }

    const context = contextResult.context;

    // Verificar estado de la sesión
    if (context.session.status === 'active') {
      throw new AppError('La tarea está actualmente en ejecución', 400);
    }

    // Preparar opciones para el retry
    const retryOptions = {
      userId: context.session.user_id,
      isManualRetry: true,
      retryStrategy: strategy,
      originalSessionId: sessionId
    };

    // Ejecutar nueva orquestación
    const result = await orchestrateTask(context.session.original_input, retryOptions);

    if (!result.success) {
      throw new AppError(`Error en retry: ${result.error}`, 500);
    }

    const response = {
      success: true,
      originalSessionId: sessionId,
      newSessionId: result.sessionId,
      retryCount: retryHistory.length + 1,
      strategy,
      message: 'Retry iniciado exitosamente'
    };

    logger.info('TaskController: Retry manual iniciado exitosamente', {
      originalSessionId: sessionId,
      newSessionId: result.sessionId
    });

    res.status(200).json(response);

  } catch (error) {
    logger.error('TaskController: Error en retry manual', {
      sessionId: req.params.sessionId,
      error: error.message
    });

    next(error);
  }
}

/**
 * Determina el estado actual de una sesión basado en su contexto
 * @param {Object} context - Contexto de la sesión
 * @returns {string} Estado actual
 */
function determineCurrentStatus(context) {
  const session = context.session;
  const steps = context.steps || [];
  
  // Estados explícitos de la sesión
  if (session.status === 'completed') return 'completed';
  if (session.status === 'failed') return 'failed';
  if (session.status === 'cancelled') return 'cancelled';
  
  // Determinar estado basado en los pasos
  const runningSteps = steps.filter(step => step.status === 'running');
  if (runningSteps.length > 0) return 'running';
  
  const pendingSteps = steps.filter(step => step.status === 'pending');
  if (pendingSteps.length > 0) return 'pending';
  
  const errorSteps = steps.filter(step => step.status === 'error');
  if (errorSteps.length > 0 && context.summary.completedSteps === 0) {
    return 'failed';
  }
  
  // Si hay pasos completados pero no está marcado como completado
  if (context.summary.completedSteps > 0) {
    return 'in_progress';
  }
  
  return 'unknown';
}

