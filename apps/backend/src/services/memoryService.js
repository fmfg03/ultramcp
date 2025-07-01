/**
 * Memory Service
 * 
 * Este servicio maneja la persistencia de datos para el sistema MCP:
 * - Guarda pasos del proceso de orquestación
 * - Mantiene contexto de sesiones
 * - Almacena evaluaciones y rewards
 * - Proporciona trazabilidad completa
 * 
 * @module memoryService
 */

import { getSupabaseClient } from '../../adapters/supabaseAdapter.js';
import { logger } from '../utils/logger.js';

/**
 * Esquemas de las tablas de base de datos
 */
const TABLE_SCHEMAS = {
  sessions: {
    id: 'UUID PRIMARY KEY',
    user_id: 'TEXT',
    original_input: 'TEXT NOT NULL',
    task_type: 'TEXT NOT NULL',
    status: 'TEXT DEFAULT \'active\'',
    created_at: 'TIMESTAMP DEFAULT NOW()',
    updated_at: 'TIMESTAMP DEFAULT NOW()',
    metadata: 'JSONB'
  },
  steps: {
    id: 'UUID PRIMARY KEY',
    session_id: 'UUID REFERENCES sessions(id)',
    step_type: 'TEXT NOT NULL',
    step_name: 'TEXT NOT NULL',
    agent_used: 'TEXT',
    input_data: 'JSONB',
    output_data: 'JSONB',
    status: 'TEXT DEFAULT \'pending\'',
    started_at: 'TIMESTAMP DEFAULT NOW()',
    completed_at: 'TIMESTAMP',
    duration_ms: 'INTEGER',
    error_message: 'TEXT',
    metadata: 'JSONB'
  },
  rewards: {
    id: 'UUID PRIMARY KEY',
    session_id: 'UUID REFERENCES sessions(id)',
    step_id: 'UUID REFERENCES steps(id)',
    score: 'DECIMAL(3,2)',
    quality_level: 'TEXT',
    feedback: 'JSONB',
    retry_recommended: 'BOOLEAN DEFAULT FALSE',
    evaluation_criteria: 'JSONB',
    created_at: 'TIMESTAMP DEFAULT NOW()',
    metadata: 'JSONB'
  },
  execution_plans: {
    id: 'UUID PRIMARY KEY',
    session_id: 'UUID REFERENCES sessions(id)',
    plan_data: 'JSONB NOT NULL',
    complexity_score: 'INTEGER',
    estimated_duration: 'TEXT',
    created_at: 'TIMESTAMP DEFAULT NOW()',
    metadata: 'JSONB'
  }
};

/**
 * Estados posibles para sesiones y pasos
 */
const STATUS = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  PENDING: 'pending',
  RUNNING: 'running',
  SUCCESS: 'success',
  ERROR: 'error'
};

/**
 * Tipos de pasos en el proceso de orquestación
 */
const STEP_TYPES = {
  REASONING: 'reasoning',
  EXECUTION: 'execution',
  EVALUATION: 'evaluation',
  RETRY: 'retry',
  FINALIZATION: 'finalization'
};

/**
 * Inicializa las tablas necesarias en Supabase
 * @returns {Promise<Object>} Resultado de la inicialización
 */
export async function initializeTables() {
  try {
    const supabase = getSupabaseClient();
    
    logger.info('MemoryService: Inicializando tablas de base de datos');

    // Crear tablas si no existen
    const tableCreationPromises = Object.entries(TABLE_SCHEMAS).map(async ([tableName, schema]) => {
      try {
        // Verificar si la tabla existe
        const { data: existingTable, error: checkError } = await supabase
          .from(tableName)
          .select('*')
          .limit(1);

        if (checkError && checkError.code === 'PGRST116') {
          // La tabla no existe, crearla
          logger.info(`MemoryService: Creando tabla ${tableName}`);
          
          // Nota: Supabase no permite crear tablas directamente desde el cliente
          // En un entorno real, estas tablas deberían crearse mediante migraciones SQL
          logger.warn(`MemoryService: La tabla ${tableName} debe crearse manualmente en Supabase`);
          
          return { table: tableName, status: 'needs_manual_creation' };
        } else if (!checkError) {
          logger.info(`MemoryService: Tabla ${tableName} ya existe`);
          return { table: tableName, status: 'exists' };
        } else {
          throw checkError;
        }
      } catch (error) {
        logger.error(`MemoryService: Error verificando tabla ${tableName}`, { error: error.message });
        return { table: tableName, status: 'error', error: error.message };
      }
    });

    const results = await Promise.all(tableCreationPromises);
    
    return {
      success: true,
      results,
      message: 'Inicialización de tablas completada'
    };

  } catch (error) {
    logger.error('MemoryService: Error inicializando tablas', { error: error.message });
    return {
      success: false,
      error: error.message,
      message: 'Error durante la inicialización de tablas'
    };
  }
}

/**
 * Crea una nueva sesión
 * @param {Object} sessionData - Datos de la sesión
 * @returns {Promise<Object>} Sesión creada
 */
export async function createSession(sessionData) {
  try {
    const supabase = getSupabaseClient();
    
    const session = {
      id: crypto.randomUUID(),
      user_id: sessionData.userId || null,
      original_input: sessionData.originalInput,
      task_type: sessionData.taskType,
      status: STATUS.ACTIVE,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata: sessionData.metadata || {}
    };

    const { data, error } = await supabase
      .from('sessions')
      .insert([session])
      .select()
      .single();

    if (error) throw error;

    logger.info('MemoryService: Sesión creada exitosamente', { 
      sessionId: session.id,
      taskType: session.task_type 
    });

    return {
      success: true,
      session: data,
      message: 'Sesión creada exitosamente'
    };

  } catch (error) {
    logger.error('MemoryService: Error creando sesión', { error: error.message });
    return {
      success: false,
      error: error.message,
      message: 'Error al crear la sesión'
    };
  }
}

/**
 * Guarda un paso del proceso de orquestación
 * @param {Object} stepData - Datos del paso
 * @returns {Promise<Object>} Paso guardado
 */
export async function saveStep(stepData) {
  try {
    const supabase = getSupabaseClient();
    
    const step = {
      id: crypto.randomUUID(),
      session_id: stepData.sessionId,
      step_type: stepData.stepType,
      step_name: stepData.stepName,
      agent_used: stepData.agentUsed || null,
      input_data: stepData.inputData || {},
      output_data: stepData.outputData || {},
      status: stepData.status || STATUS.PENDING,
      started_at: stepData.startedAt || new Date().toISOString(),
      completed_at: stepData.completedAt || null,
      duration_ms: stepData.durationMs || null,
      error_message: stepData.errorMessage || null,
      metadata: stepData.metadata || {}
    };

    const { data, error } = await supabase
      .from('steps')
      .insert([step])
      .select()
      .single();

    if (error) throw error;

    logger.info('MemoryService: Paso guardado exitosamente', { 
      stepId: step.id,
      sessionId: step.session_id,
      stepType: step.step_type 
    });

    return {
      success: true,
      step: data,
      message: 'Paso guardado exitosamente'
    };

  } catch (error) {
    logger.error('MemoryService: Error guardando paso', { error: error.message });
    return {
      success: false,
      error: error.message,
      message: 'Error al guardar el paso'
    };
  }
}

/**
 * Actualiza un paso existente
 * @param {string} stepId - ID del paso
 * @param {Object} updateData - Datos a actualizar
 * @returns {Promise<Object>} Paso actualizado
 */
export async function updateStep(stepId, updateData) {
  try {
    const supabase = getSupabaseClient();
    
    const updates = {
      ...updateData,
      updated_at: new Date().toISOString()
    };

    const { data, error } = await supabase
      .from('steps')
      .update(updates)
      .eq('id', stepId)
      .select()
      .single();

    if (error) throw error;

    logger.info('MemoryService: Paso actualizado exitosamente', { stepId });

    return {
      success: true,
      step: data,
      message: 'Paso actualizado exitosamente'
    };

  } catch (error) {
    logger.error('MemoryService: Error actualizando paso', { 
      stepId, 
      error: error.message 
    });
    return {
      success: false,
      error: error.message,
      message: 'Error al actualizar el paso'
    };
  }
}

/**
 * Guarda una evaluación/reward
 * @param {Object} rewardData - Datos de la evaluación
 * @returns {Promise<Object>} Reward guardado
 */
export async function saveReward(rewardData) {
  try {
    const supabase = getSupabaseClient();
    
    const reward = {
      id: crypto.randomUUID(),
      session_id: rewardData.sessionId,
      step_id: rewardData.stepId || null,
      score: rewardData.score,
      quality_level: rewardData.qualityLevel,
      feedback: rewardData.feedback || {},
      retry_recommended: rewardData.retryRecommended || false,
      evaluation_criteria: rewardData.evaluationCriteria || {},
      created_at: new Date().toISOString(),
      metadata: rewardData.metadata || {}
    };

    const { data, error } = await supabase
      .from('rewards')
      .insert([reward])
      .select()
      .single();

    if (error) throw error;

    logger.info('MemoryService: Reward guardado exitosamente', { 
      rewardId: reward.id,
      sessionId: reward.session_id,
      score: reward.score 
    });

    return {
      success: true,
      reward: data,
      message: 'Reward guardado exitosamente'
    };

  } catch (error) {
    logger.error('MemoryService: Error guardando reward', { error: error.message });
    return {
      success: false,
      error: error.message,
      message: 'Error al guardar el reward'
    };
  }
}

/**
 * Obtiene el contexto completo de una sesión
 * @param {string} sessionId - ID de la sesión
 * @returns {Promise<Object>} Contexto de la sesión
 */
export async function getContext(sessionId) {
  try {
    const supabase = getSupabaseClient();
    
    // Obtener datos de la sesión
    const { data: session, error: sessionError } = await supabase
      .from('sessions')
      .select('*')
      .eq('id', sessionId)
      .single();

    if (sessionError) throw sessionError;

    // Obtener pasos de la sesión
    const { data: steps, error: stepsError } = await supabase
      .from('steps')
      .select('*')
      .eq('session_id', sessionId)
      .order('started_at', { ascending: true });

    if (stepsError) throw stepsError;

    // Obtener rewards de la sesión
    const { data: rewards, error: rewardsError } = await supabase
      .from('rewards')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: true });

    if (rewardsError) throw rewardsError;

    // Obtener plan de ejecución
    const { data: executionPlan, error: planError } = await supabase
      .from('execution_plans')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    // No lanzar error si no hay plan de ejecución

    const context = {
      session,
      steps: steps || [],
      rewards: rewards || [],
      executionPlan: executionPlan || null,
      summary: {
        totalSteps: steps?.length || 0,
        completedSteps: steps?.filter(step => step.status === STATUS.SUCCESS)?.length || 0,
        failedSteps: steps?.filter(step => step.status === STATUS.ERROR)?.length || 0,
        averageScore: rewards?.length > 0 ? 
          rewards.reduce((sum, reward) => sum + (reward.score || 0), 0) / rewards.length : 0,
        lastActivity: steps?.length > 0 ? 
          Math.max(...steps.map(step => new Date(step.started_at).getTime())) : 
          new Date(session.created_at).getTime()
      }
    };

    logger.info('MemoryService: Contexto obtenido exitosamente', { 
      sessionId,
      totalSteps: context.summary.totalSteps 
    });

    return {
      success: true,
      context,
      message: 'Contexto obtenido exitosamente'
    };

  } catch (error) {
    logger.error('MemoryService: Error obteniendo contexto', { 
      sessionId, 
      error: error.message 
    });
    return {
      success: false,
      error: error.message,
      message: 'Error al obtener el contexto'
    };
  }
}

/**
 * Guarda un plan de ejecución
 * @param {Object} planData - Datos del plan
 * @returns {Promise<Object>} Plan guardado
 */
export async function saveExecutionPlan(planData) {
  try {
    const supabase = getSupabaseClient();
    
    const plan = {
      id: crypto.randomUUID(),
      session_id: planData.sessionId,
      plan_data: planData.planData,
      complexity_score: planData.complexityScore || null,
      estimated_duration: planData.estimatedDuration || null,
      created_at: new Date().toISOString(),
      metadata: planData.metadata || {}
    };

    const { data, error } = await supabase
      .from('execution_plans')
      .insert([plan])
      .select()
      .single();

    if (error) throw error;

    logger.info('MemoryService: Plan de ejecución guardado exitosamente', { 
      planId: plan.id,
      sessionId: plan.session_id 
    });

    return {
      success: true,
      plan: data,
      message: 'Plan de ejecución guardado exitosamente'
    };

  } catch (error) {
    logger.error('MemoryService: Error guardando plan de ejecución', { 
      error: error.message 
    });
    return {
      success: false,
      error: error.message,
      message: 'Error al guardar el plan de ejecución'
    };
  }
}

/**
 * Actualiza el estado de una sesión
 * @param {string} sessionId - ID de la sesión
 * @param {string} status - Nuevo estado
 * @param {Object} metadata - Metadatos adicionales
 * @returns {Promise<Object>} Sesión actualizada
 */
export async function updateSessionStatus(sessionId, status, metadata = {}) {
  try {
    const supabase = getSupabaseClient();
    
    const updates = {
      status,
      updated_at: new Date().toISOString(),
      metadata: {
        ...metadata,
        statusUpdatedAt: new Date().toISOString()
      }
    };

    const { data, error } = await supabase
      .from('sessions')
      .update(updates)
      .eq('id', sessionId)
      .select()
      .single();

    if (error) throw error;

    logger.info('MemoryService: Estado de sesión actualizado', { 
      sessionId, 
      status 
    });

    return {
      success: true,
      session: data,
      message: 'Estado de sesión actualizado exitosamente'
    };

  } catch (error) {
    logger.error('MemoryService: Error actualizando estado de sesión', { 
      sessionId, 
      status, 
      error: error.message 
    });
    return {
      success: false,
      error: error.message,
      message: 'Error al actualizar el estado de la sesión'
    };
  }
}

/**
 * Obtiene estadísticas de sesiones
 * @param {Object} filters - Filtros opcionales
 * @returns {Promise<Object>} Estadísticas
 */
export async function getSessionStats(filters = {}) {
  try {
    const supabase = getSupabaseClient();
    
    let query = supabase.from('sessions').select('*');
    
    // Aplicar filtros
    if (filters.userId) {
      query = query.eq('user_id', filters.userId);
    }
    if (filters.taskType) {
      query = query.eq('task_type', filters.taskType);
    }
    if (filters.status) {
      query = query.eq('status', filters.status);
    }
    if (filters.dateFrom) {
      query = query.gte('created_at', filters.dateFrom);
    }
    if (filters.dateTo) {
      query = query.lte('created_at', filters.dateTo);
    }

    const { data: sessions, error } = await query;
    
    if (error) throw error;

    // Calcular estadísticas
    const stats = {
      totalSessions: sessions.length,
      byStatus: {},
      byTaskType: {},
      averageDuration: 0,
      successRate: 0
    };

    sessions.forEach(session => {
      // Por estado
      stats.byStatus[session.status] = (stats.byStatus[session.status] || 0) + 1;
      
      // Por tipo de tarea
      stats.byTaskType[session.task_type] = (stats.byTaskType[session.task_type] || 0) + 1;
    });

    // Calcular tasa de éxito
    const completedSessions = stats.byStatus[STATUS.COMPLETED] || 0;
    stats.successRate = sessions.length > 0 ? completedSessions / sessions.length : 0;

    return {
      success: true,
      stats,
      message: 'Estadísticas obtenidas exitosamente'
    };

  } catch (error) {
    logger.error('MemoryService: Error obteniendo estadísticas', { 
      error: error.message 
    });
    return {
      success: false,
      error: error.message,
      message: 'Error al obtener estadísticas'
    };
  }
}

export { STATUS, STEP_TYPES, TABLE_SCHEMAS };

