/**
 * Simple Test Component for MCP Orchestration
 * 
 * Componente simplificado para probar la funcionalidad básica
 * sin dependencias complejas
 */

import React, { useState } from 'react';

const SimpleOrchestrationTest = () => {
  const [task, setTask] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runTask = async () => {
    if (!task.trim()) {
      setError('Por favor ingresa una tarea para ejecutar');
      return;
    }

    setIsRunning(true);
    setError(null);
    setResult(null);

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

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Error ejecutando tarea');
      }

      setResult(data);
      setTask('');

    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: '0 auto', 
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        padding: '24px',
        marginBottom: '24px'
      }}>
        <h1 style={{ 
          fontSize: '24px', 
          fontWeight: 'bold', 
          color: '#1f2937',
          marginBottom: '8px'
        }}>
          Sistema MCP - Vista de Orquestación
        </h1>
        <p style={{ color: '#6b7280' }}>
          Sistema refactorizado con reasoning y reward shells
        </p>
      </div>

      {/* Task Input */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        padding: '24px',
        marginBottom: '24px'
      }}>
        <h2 style={{ 
          fontSize: '18px', 
          fontWeight: '600', 
          color: '#1f2937',
          marginBottom: '16px'
        }}>
          Ejecutar Nueva Tarea
        </h2>
        
        <div style={{ marginBottom: '16px' }}>
          <label style={{ 
            display: 'block', 
            fontSize: '14px', 
            fontWeight: '500',
            color: '#374151',
            marginBottom: '8px'
          }}>
            Descripción de la tarea
          </label>
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Describe la tarea que quieres ejecutar..."
            style={{
              width: '100%',
              height: '120px',
              padding: '12px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
              resize: 'none',
              outline: 'none',
              boxSizing: 'border-box'
            }}
            disabled={isRunning}
          />
        </div>
        
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            {task.length}/10000 caracteres
          </div>
          <button
            onClick={runTask}
            disabled={isRunning || !task.trim()}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '8px 16px',
              backgroundColor: isRunning || !task.trim() ? '#9ca3af' : '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              cursor: isRunning || !task.trim() ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s'
            }}
          >
            {isRunning ? '⏳ Ejecutando...' : '▶️ Ejecutar Tarea'}
          </button>
        </div>

        {error && (
          <div style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '6px',
            color: '#dc2626'
          }}>
            ❌ {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          padding: '24px'
        }}>
          <h2 style={{ 
            fontSize: '18px', 
            fontWeight: '600', 
            color: '#1f2937',
            marginBottom: '16px'
          }}>
            Resultado de la Ejecución
          </h2>

          {/* Session Info */}
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
              Información de la Sesión
            </h3>
            <div style={{ 
              backgroundColor: '#f9fafb', 
              padding: '12px', 
              borderRadius: '6px',
              fontSize: '14px'
            }}>
              <p><strong>ID de Sesión:</strong> {result.sessionId}</p>
              <p><strong>Estado:</strong> {result.trace?.session?.status || 'Completado'}</p>
              <p><strong>Puntuación Final:</strong> {
                result.metadata?.finalScore ? 
                `${(result.metadata.finalScore * 100).toFixed(1)}%` : 'N/A'
              }</p>
              <p><strong>Duración:</strong> {
                result.metadata?.totalDuration ? 
                `${Math.round(result.metadata.totalDuration / 1000)}s` : 'N/A'
              }</p>
            </div>
          </div>

          {/* Steps */}
          {result.trace?.steps && result.trace.steps.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
                Pasos Ejecutados
              </h3>
              <div style={{ space: '8px' }}>
                {result.trace.steps.map((step, index) => (
                  <div key={step.id} style={{
                    backgroundColor: '#f9fafb',
                    padding: '12px',
                    borderRadius: '6px',
                    marginBottom: '8px',
                    fontSize: '14px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: '500' }}>
                        {step.step_name} ({step.step_type})
                      </span>
                      <span style={{ 
                        color: step.status === 'success' ? '#059669' : 
                               step.status === 'error' ? '#dc2626' : '#d97706'
                      }}>
                        {step.status === 'success' ? '✅' : 
                         step.status === 'error' ? '❌' : '⏳'} {step.status}
                      </span>
                    </div>
                    {step.agent_used && (
                      <p style={{ margin: '4px 0', color: '#6b7280' }}>
                        Agente: {step.agent_used}
                      </p>
                    )}
                    {step.duration_ms && (
                      <p style={{ margin: '4px 0', color: '#6b7280' }}>
                        Duración: {Math.round(step.duration_ms / 1000)}s
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evaluation */}
          {result.result?.evaluation && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
                Evaluación Final
              </h3>
              <div style={{ 
                backgroundColor: '#f9fafb', 
                padding: '12px', 
                borderRadius: '6px',
                fontSize: '14px'
              }}>
                <p><strong>Puntuación:</strong> {(result.result.evaluation.score * 100).toFixed(1)}%</p>
                <p><strong>Nivel de Calidad:</strong> {result.result.evaluation.qualityLevel}</p>
                {result.result.evaluation.feedback?.summary && (
                  <p><strong>Resumen:</strong> {result.result.evaluation.feedback.summary}</p>
                )}
              </div>
            </div>
          )}

          {/* Retry Info */}
          {result.retryInfo && (
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
                Información de Reintentos
              </h3>
              <div style={{ 
                backgroundColor: '#f9fafb', 
                padding: '12px', 
                borderRadius: '6px',
                fontSize: '14px'
              }}>
                <p><strong>Reintentos Realizados:</strong> {result.retryInfo.retryCount}</p>
                <p><strong>Máximo Permitido:</strong> {result.retryInfo.maxRetries}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SimpleOrchestrationTest;

