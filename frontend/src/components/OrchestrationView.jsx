/**
 * Orchestration View Component
 * 
 * Componente principal para mostrar el flujo completo de orquestación:
 * input → tasks → outputs → feedback → score
 * 
 * @component OrchestrationView
 */

import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  RotateCcw,
  Eye,
  TrendingUp,
  Activity,
  Zap
} from 'lucide-react';

const OrchestrationView = () => {
  const [task, setTask] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [currentSession, setCurrentSession] = useState(null);
  const [sessionHistory, setSessionHistory] = useState([]);
  const [error, setError] = useState(null);

  /**
   * Ejecuta una nueva tarea
   */
  const runTask = async () => {
    if (!task.trim()) {
      setError('Por favor ingresa una tarea para ejecutar');
      return;
    }

    setIsRunning(true);
    setError(null);

    try {
      const response = await fetch('/api/run-task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request: task,
          options: {
            userId: 'demo-user',
            maxRetries: 2
          }
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || 'Error ejecutando tarea');
      }

      setCurrentSession(result);
      setSessionHistory(prev => [result, ...prev.slice(0, 9)]); // Mantener últimas 10
      setTask(''); // Limpiar input

    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  /**
   * Reintenta una tarea
   */
  const retryTask = async (sessionId, strategy = 'enhanced') => {
    try {
      const response = await fetch(`/api/task/${sessionId}/retry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          strategy,
          userId: 'demo-user'
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || 'Error reintentando tarea');
      }

      // Actualizar con la nueva sesión
      setCurrentSession(result);
      
    } catch (err) {
      setError(err.message);
    }
  };

  /**
   * Obtiene el estado de una sesión
   */
  const getSessionStatus = async (sessionId) => {
    try {
      const response = await fetch(`/api/task/${sessionId}`);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || 'Error obteniendo estado');
      }

      return result;
    } catch (err) {
      console.error('Error obteniendo estado:', err);
      return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Vista de Orquestación MCP
        </h1>
        <p className="text-gray-600">
          Sistema de reasoning y reward shells con trazabilidad completa
        </p>
      </div>

      {/* Task Input */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Ejecutar Nueva Tarea
        </h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="task-input" className="block text-sm font-medium text-gray-700 mb-2">
              Descripción de la tarea
            </label>
            <textarea
              id="task-input"
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="Describe la tarea que quieres ejecutar..."
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              disabled={isRunning}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {task.length}/10000 caracteres
            </div>
            <button
              onClick={runTask}
              disabled={isRunning || !task.trim()}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isRunning ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Ejecutando...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Ejecutar Tarea
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center">
              <XCircle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Current Session */}
      {currentSession && (
        <SessionView 
          session={currentSession} 
          onRetry={retryTask}
          onRefresh={getSessionStatus}
        />
      )}

      {/* Session History */}
      {sessionHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Historial de Sesiones
          </h2>
          
          <div className="space-y-3">
            {sessionHistory.map((session, index) => (
              <SessionCard 
                key={session.sessionId} 
                session={session}
                isRecent={index === 0}
                onClick={() => setCurrentSession(session)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Componente para mostrar una sesión completa
 */
const SessionView = ({ session, onRetry, onRefresh }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await onRefresh(session.sessionId);
    setRefreshing(false);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'failed': return 'text-red-600 bg-red-50 border-red-200';
      case 'running': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'cancelled': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Session Header */}
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Sesión: {session.sessionId.slice(0, 8)}...
            </h2>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(session.trace?.session?.status || 'unknown')}`}>
              {session.trace?.session?.status || 'Desconocido'}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <RotateCcw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <Eye className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Metrics */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard
            icon={<TrendingUp className="w-5 h-5" />}
            label="Puntuación Final"
            value={session.metadata?.finalScore ? 
              `${(session.metadata.finalScore * 100).toFixed(1)}%` : 'N/A'}
            color={session.metadata?.finalScore ? 
              getScoreColor(session.metadata.finalScore) : 'text-gray-500'}
          />
          <MetricCard
            icon={<Activity className="w-5 h-5" />}
            label="Pasos Completados"
            value={`${session.trace?.summary?.completedSteps || 0}/${session.trace?.summary?.totalSteps || 0}`}
            color="text-blue-600"
          />
          <MetricCard
            icon={<RotateCcw className="w-5 h-5" />}
            label="Reintentos"
            value={`${session.retryInfo?.retryCount || 0}/${session.retryInfo?.maxRetries || 2}`}
            color={session.retryInfo?.retryCount > 0 ? 'text-orange-600' : 'text-green-600'}
          />
          <MetricCard
            icon={<Clock className="w-5 h-5" />}
            label="Duración"
            value={session.metadata?.totalDuration ? 
              `${Math.round(session.metadata.totalDuration / 1000)}s` : 'N/A'}
            color="text-purple-600"
          />
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-6 space-y-6">
          {/* Original Request */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Solicitud Original</h3>
            <div className="bg-gray-50 rounded-md p-4">
              <p className="text-gray-700">{session.trace?.session?.original_input}</p>
            </div>
          </div>

          {/* Execution Plan */}
          {session.trace?.executionPlan && (
            <ExecutionPlanView plan={session.trace.executionPlan} />
          )}

          {/* Steps Timeline */}
          {session.trace?.steps && session.trace.steps.length > 0 && (
            <StepsTimeline steps={session.trace.steps} />
          )}

          {/* Final Evaluation */}
          {session.result?.evaluation && (
            <EvaluationView evaluation={session.result.evaluation} />
          )}

          {/* Retry Actions */}
          {session.retryInfo?.retryCount < session.retryInfo?.maxRetries && (
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-md">
              <div>
                <h4 className="font-medium text-blue-900">¿Quieres reintentar esta tarea?</h4>
                <p className="text-sm text-blue-700">
                  Puedes usar diferentes estrategias para mejorar el resultado.
                </p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => onRetry(session.sessionId, 'enhanced')}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
                >
                  Retry Mejorado
                </button>
                <button
                  onClick={() => onRetry(session.sessionId, 'alternative')}
                  className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors"
                >
                  Agente Alternativo
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Componente para mostrar una tarjeta de métrica
 */
const MetricCard = ({ icon, label, value, color }) => (
  <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-md">
    <div className={`${color}`}>
      {icon}
    </div>
    <div>
      <p className="text-sm text-gray-600">{label}</p>
      <p className={`font-semibold ${color}`}>{value}</p>
    </div>
  </div>
);

/**
 * Componente para mostrar el plan de ejecución
 */
const ExecutionPlanView = ({ plan }) => (
  <div>
    <h3 className="text-lg font-medium text-gray-900 mb-2">Plan de Ejecución</h3>
    <div className="bg-gray-50 rounded-md p-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          <span className="text-sm text-gray-600">Tipo de Tarea:</span>
          <p className="font-medium">{plan.plan_data?.taskType || 'N/A'}</p>
        </div>
        <div>
          <span className="text-sm text-gray-600">Complejidad:</span>
          <p className="font-medium">{plan.plan_data?.complexity?.level || 'N/A'}</p>
        </div>
        <div>
          <span className="text-sm text-gray-600">Tiempo Estimado:</span>
          <p className="font-medium">{plan.estimated_duration || 'N/A'}</p>
        </div>
      </div>
      
      {plan.plan_data?.subtasks && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">Subtareas:</h4>
          <div className="space-y-2">
            {plan.plan_data.subtasks.map((subtask, index) => (
              <div key={subtask.id} className="flex items-center space-x-3 p-2 bg-white rounded border">
                <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                <div className="flex-1">
                  <p className="text-sm font-medium">{subtask.description}</p>
                  <p className="text-xs text-gray-500">Agente: {subtask.agent}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  </div>
);

/**
 * Componente para mostrar la línea de tiempo de pasos
 */
const StepsTimeline = ({ steps }) => (
  <div>
    <h3 className="text-lg font-medium text-gray-900 mb-2">Línea de Tiempo de Pasos</h3>
    <div className="space-y-3">
      {steps.map((step, index) => (
        <StepCard key={step.id} step={step} index={index} />
      ))}
    </div>
  </div>
);

/**
 * Componente para mostrar un paso individual
 */
const StepCard = ({ step, index }) => {
  const getStepIcon = (status) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running': return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      default: return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const formatDuration = (durationMs) => {
    if (!durationMs) return 'N/A';
    return `${Math.round(durationMs / 1000)}s`;
  };

  return (
    <div className="flex items-start space-x-4 p-4 bg-gray-50 rounded-md">
      <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 bg-white rounded-full border">
        {getStepIcon(step.status)}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-gray-900">
            {step.step_name} ({step.step_type})
          </h4>
          <span className="text-xs text-gray-500">
            {formatDuration(step.duration_ms)}
          </span>
        </div>
        
        {step.agent_used && (
          <p className="text-xs text-gray-600 mt-1">
            Agente: {step.agent_used}
          </p>
        )}
        
        {step.error_message && (
          <p className="text-xs text-red-600 mt-1">
            Error: {step.error_message}
          </p>
        )}
        
        <p className="text-xs text-gray-500 mt-1">
          {new Date(step.started_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
};

/**
 * Componente para mostrar la evaluación final
 */
const EvaluationView = ({ evaluation }) => (
  <div>
    <h3 className="text-lg font-medium text-gray-900 mb-2">Evaluación Final</h3>
    <div className="bg-gray-50 rounded-md p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <span className="text-sm text-gray-600">Puntuación:</span>
          <p className="text-2xl font-bold text-blue-600">
            {(evaluation.score * 100).toFixed(1)}%
          </p>
        </div>
        <div>
          <span className="text-sm text-gray-600">Nivel de Calidad:</span>
          <p className="font-medium capitalize">{evaluation.qualityLevel}</p>
        </div>
      </div>
      
      {evaluation.feedback && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">Feedback:</h4>
          <p className="text-sm text-gray-700 mb-3">{evaluation.feedback.summary}</p>
          
          {evaluation.feedback.strengths?.length > 0 && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-green-700 mb-1">Fortalezas:</h5>
              <ul className="text-sm text-green-600 list-disc list-inside">
                {evaluation.feedback.strengths.map((strength, index) => (
                  <li key={index}>{strength}</li>
                ))}
              </ul>
            </div>
          )}
          
          {evaluation.feedback.improvements?.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-orange-700 mb-1">Mejoras:</h5>
              <ul className="text-sm text-orange-600 list-disc list-inside">
                {evaluation.feedback.improvements.map((improvement, index) => (
                  <li key={index}>{improvement}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  </div>
);

/**
 * Componente para mostrar una tarjeta de sesión en el historial
 */
const SessionCard = ({ session, isRecent, onClick }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div 
      onClick={() => onClick()}
      className={`p-4 border rounded-md cursor-pointer hover:bg-gray-50 transition-colors ${
        isRecent ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="font-mono text-sm text-gray-600">
            {session.sessionId.slice(0, 8)}...
          </span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(session.trace?.session?.status)}`}>
            {session.trace?.session?.status || 'unknown'}
          </span>
          {isRecent && (
            <span className="px-2 py-1 bg-blue-600 text-white rounded-full text-xs font-medium">
              Reciente
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          {session.metadata?.finalScore && (
            <span>Score: {(session.metadata.finalScore * 100).toFixed(1)}%</span>
          )}
          {session.retryInfo?.retryCount > 0 && (
            <span>Retries: {session.retryInfo.retryCount}</span>
          )}
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mt-2 truncate">
        {session.trace?.session?.original_input}
      </p>
    </div>
  );
};

export default OrchestrationView;

