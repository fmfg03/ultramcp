/**
 * Reward Shell Service
 * 
 * Este servicio recibe el output del Builder y el contexto original para:
 * - Evaluar si el resultado cumple con el objetivo establecido
 * - Usar el Judge o heurísticas simples para la evaluación
 * - Retornar un objeto con score, feedback y decisión de retry
 * 
 * @module rewardShell
 */

import { logger } from '../utils/logger.js';

/**
 * Criterios de evaluación para diferentes tipos de tareas
 */
const EVALUATION_CRITERIA = {
  web_development: {
    functionality: { weight: 0.3, description: 'Funcionalidad correcta' },
    usability: { weight: 0.2, description: 'Facilidad de uso' },
    performance: { weight: 0.2, description: 'Rendimiento' },
    code_quality: { weight: 0.15, description: 'Calidad del código' },
    completeness: { weight: 0.15, description: 'Completitud de la implementación' }
  },
  data_analysis: {
    accuracy: { weight: 0.3, description: 'Precisión de los resultados' },
    completeness: { weight: 0.25, description: 'Completitud del análisis' },
    clarity: { weight: 0.2, description: 'Claridad de la presentación' },
    insights: { weight: 0.15, description: 'Calidad de los insights' },
    methodology: { weight: 0.1, description: 'Metodología utilizada' }
  },
  content_creation: {
    relevance: { weight: 0.25, description: 'Relevancia del contenido' },
    quality: { weight: 0.25, description: 'Calidad de la escritura' },
    completeness: { weight: 0.2, description: 'Completitud del contenido' },
    originality: { weight: 0.15, description: 'Originalidad' },
    structure: { weight: 0.15, description: 'Estructura y organización' }
  },
  api_integration: {
    functionality: { weight: 0.3, description: 'Funcionalidad de la integración' },
    reliability: { weight: 0.25, description: 'Confiabilidad' },
    security: { weight: 0.2, description: 'Seguridad' },
    documentation: { weight: 0.15, description: 'Documentación' },
    error_handling: { weight: 0.1, description: 'Manejo de errores' }
  },
  research: {
    accuracy: { weight: 0.3, description: 'Precisión de la información' },
    completeness: { weight: 0.25, description: 'Completitud de la investigación' },
    sources: { weight: 0.2, description: 'Calidad de las fuentes' },
    organization: { weight: 0.15, description: 'Organización de la información' },
    relevance: { weight: 0.1, description: 'Relevancia al tema' }
  }
};

/**
 * Umbrales de puntuación para determinar si se requiere retry
 */
const SCORE_THRESHOLDS = {
  EXCELLENT: 0.9,
  GOOD: 0.75,
  ACCEPTABLE: 0.6,
  POOR: 0.4,
  UNACCEPTABLE: 0.2
};

/**
 * Evalúa la completitud de un resultado basado en los requerimientos originales
 * @param {Object} output - Output del Builder
 * @param {Object} originalContext - Contexto original de la tarea
 * @returns {Object} Evaluación de completitud
 */
function evaluateCompleteness(output, originalContext) {
  const { plan } = originalContext;
  const completedSteps = output.completedSteps || [];
  const totalSteps = plan?.subtasks?.length || 1;
  
  const completionRate = completedSteps.length / totalSteps;
  
  // Verificar si todos los pasos críticos fueron completados
  const criticalSteps = plan?.subtasks?.filter(task => task.priority <= 2) || [];
  const completedCriticalSteps = criticalSteps.filter(step => 
    completedSteps.some(completed => completed.id === step.id)
  );
  
  const criticalCompletionRate = criticalSteps.length > 0 ? 
    completedCriticalSteps.length / criticalSteps.length : 1;
  
  return {
    overallCompletion: completionRate,
    criticalCompletion: criticalCompletionRate,
    score: (completionRate * 0.6) + (criticalCompletionRate * 0.4),
    feedback: `Completitud: ${Math.round(completionRate * 100)}% general, ${Math.round(criticalCompletionRate * 100)}% crítico`
  };
}

/**
 * Evalúa la calidad técnica del output
 * @param {Object} output - Output del Builder
 * @param {string} taskType - Tipo de tarea
 * @returns {Object} Evaluación de calidad técnica
 */
function evaluateTechnicalQuality(output, taskType) {
  let score = 0.5; // Puntuación base
  const feedback = [];
  
  // Verificar presencia de elementos clave según el tipo de tarea
  switch (taskType) {
    case 'web_development':
      if (output.files && output.files.length > 0) {
        score += 0.2;
        feedback.push('Archivos de código generados');
      }
      if (output.structure) {
        score += 0.15;
        feedback.push('Estructura del proyecto definida');
      }
      if (output.dependencies) {
        score += 0.1;
        feedback.push('Dependencias especificadas');
      }
      break;
      
    case 'data_analysis':
      if (output.visualizations) {
        score += 0.2;
        feedback.push('Visualizaciones incluidas');
      }
      if (output.statistics) {
        score += 0.15;
        feedback.push('Análisis estadístico realizado');
      }
      if (output.insights) {
        score += 0.1;
        feedback.push('Insights identificados');
      }
      break;
      
    case 'content_creation':
      if (output.content && output.content.length > 100) {
        score += 0.2;
        feedback.push('Contenido sustancial generado');
      }
      if (output.structure) {
        score += 0.15;
        feedback.push('Estructura clara');
      }
      if (output.references) {
        score += 0.1;
        feedback.push('Referencias incluidas');
      }
      break;
  }
  
  // Verificar errores reportados
  if (output.errors && output.errors.length > 0) {
    score -= 0.2;
    feedback.push(`${output.errors.length} errores detectados`);
  }
  
  // Verificar warnings
  if (output.warnings && output.warnings.length > 0) {
    score -= 0.1;
    feedback.push(`${output.warnings.length} advertencias`);
  }
  
  return {
    score: Math.max(0, Math.min(1, score)),
    feedback: feedback.join(', ')
  };
}

/**
 * Evalúa si el output cumple con los objetivos específicos del usuario
 * @param {Object} output - Output del Builder
 * @param {Object} originalContext - Contexto original
 * @returns {Object} Evaluación de cumplimiento de objetivos
 */
function evaluateObjectiveFulfillment(output, originalContext) {
  const userInput = originalContext.originalInput || '';
  const taskType = originalContext.taskType || 'general';
  
  let score = 0.5; // Puntuación base
  const feedback = [];
  
  // Análisis de palabras clave del input original
  const inputKeywords = extractKeywords(userInput);
  const outputText = JSON.stringify(output).toLowerCase();
  
  // Verificar presencia de conceptos clave en el output
  const matchedKeywords = inputKeywords.filter(keyword => 
    outputText.includes(keyword.toLowerCase())
  );
  
  const keywordMatchRate = inputKeywords.length > 0 ? 
    matchedKeywords.length / inputKeywords.length : 0.5;
  
  score += keywordMatchRate * 0.3;
  
  if (keywordMatchRate > 0.7) {
    feedback.push('Excelente cobertura de conceptos clave');
  } else if (keywordMatchRate > 0.4) {
    feedback.push('Buena cobertura de conceptos clave');
  } else {
    feedback.push('Cobertura limitada de conceptos clave');
  }
  
  // Verificar si se abordaron los requerimientos específicos
  const requirements = extractRequirements(userInput);
  const addressedRequirements = requirements.filter(req => 
    outputText.includes(req.toLowerCase())
  );
  
  const requirementFulfillment = requirements.length > 0 ? 
    addressedRequirements.length / requirements.length : 0.5;
  
  score += requirementFulfillment * 0.2;
  
  return {
    score: Math.max(0, Math.min(1, score)),
    feedback: feedback.join(', '),
    details: {
      keywordMatchRate,
      requirementFulfillment,
      matchedKeywords: matchedKeywords.length,
      totalKeywords: inputKeywords.length
    }
  };
}

/**
 * Extrae palabras clave importantes del input del usuario
 * @param {string} input - Input del usuario
 * @returns {Array} Lista de palabras clave
 */
function extractKeywords(input) {
  // Palabras comunes a filtrar
  const stopWords = new Set([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
  ]);
  
  return input
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/\s+/)
    .filter(word => word.length > 2 && !stopWords.has(word))
    .filter((word, index, arr) => arr.indexOf(word) === index) // Eliminar duplicados
    .slice(0, 20); // Limitar a 20 palabras clave más relevantes
}

/**
 * Extrae requerimientos específicos del input del usuario
 * @param {string} input - Input del usuario
 * @returns {Array} Lista de requerimientos
 */
function extractRequirements(input) {
  const requirements = [];
  const patterns = [
    /need to (.+?)(?:\.|$)/gi,
    /should (.+?)(?:\.|$)/gi,
    /must (.+?)(?:\.|$)/gi,
    /require (.+?)(?:\.|$)/gi,
    /want to (.+?)(?:\.|$)/gi,
    /looking for (.+?)(?:\.|$)/gi
  ];
  
  patterns.forEach(pattern => {
    const matches = input.match(pattern);
    if (matches) {
      matches.forEach(match => {
        const requirement = match.replace(pattern, '$1').trim();
        if (requirement.length > 3) {
          requirements.push(requirement);
        }
      });
    }
  });
  
  return requirements;
}

/**
 * Calcula la puntuación final basada en múltiples criterios
 * @param {Object} evaluations - Evaluaciones individuales
 * @param {string} taskType - Tipo de tarea
 * @returns {Object} Puntuación final y detalles
 */
function calculateFinalScore(evaluations, taskType) {
  const criteria = EVALUATION_CRITERIA[taskType] || EVALUATION_CRITERIA.web_development;
  
  // Mapear evaluaciones a criterios
  const scores = {
    completeness: evaluations.completeness.score,
    technical_quality: evaluations.technicalQuality.score,
    objective_fulfillment: evaluations.objectiveFulfillment.score
  };
  
  // Calcular puntuación ponderada
  let finalScore = 0;
  finalScore += scores.completeness * 0.4;
  finalScore += scores.technical_quality * 0.3;
  finalScore += scores.objective_fulfillment * 0.3;
  
  // Determinar nivel de calidad
  let qualityLevel;
  if (finalScore >= SCORE_THRESHOLDS.EXCELLENT) qualityLevel = 'excellent';
  else if (finalScore >= SCORE_THRESHOLDS.GOOD) qualityLevel = 'good';
  else if (finalScore >= SCORE_THRESHOLDS.ACCEPTABLE) qualityLevel = 'acceptable';
  else if (finalScore >= SCORE_THRESHOLDS.POOR) qualityLevel = 'poor';
  else qualityLevel = 'unacceptable';
  
  return {
    finalScore,
    qualityLevel,
    breakdown: scores,
    thresholds: SCORE_THRESHOLDS
  };
}

/**
 * Genera feedback detallado basado en las evaluaciones
 * @param {Object} evaluations - Evaluaciones realizadas
 * @param {Object} scoreDetails - Detalles de la puntuación
 * @returns {Object} Feedback estructurado
 */
function generateFeedback(evaluations, scoreDetails) {
  const feedback = {
    summary: '',
    strengths: [],
    improvements: [],
    recommendations: []
  };
  
  // Generar resumen basado en la calidad
  switch (scoreDetails.qualityLevel) {
    case 'excellent':
      feedback.summary = 'Excelente trabajo. El resultado cumple y supera las expectativas.';
      break;
    case 'good':
      feedback.summary = 'Buen trabajo. El resultado cumple con la mayoría de los requerimientos.';
      break;
    case 'acceptable':
      feedback.summary = 'Trabajo aceptable. El resultado cumple los requerimientos básicos.';
      break;
    case 'poor':
      feedback.summary = 'El trabajo necesita mejoras significativas.';
      break;
    case 'unacceptable':
      feedback.summary = 'El resultado no cumple con los estándares mínimos requeridos.';
      break;
  }
  
  // Identificar fortalezas
  if (evaluations.completeness.score > 0.7) {
    feedback.strengths.push('Alta completitud de la implementación');
  }
  if (evaluations.technicalQuality.score > 0.7) {
    feedback.strengths.push('Buena calidad técnica');
  }
  if (evaluations.objectiveFulfillment.score > 0.7) {
    feedback.strengths.push('Cumple bien con los objetivos establecidos');
  }
  
  // Identificar áreas de mejora
  if (evaluations.completeness.score < 0.6) {
    feedback.improvements.push('Mejorar la completitud de la implementación');
  }
  if (evaluations.technicalQuality.score < 0.6) {
    feedback.improvements.push('Mejorar la calidad técnica del código/contenido');
  }
  if (evaluations.objectiveFulfillment.score < 0.6) {
    feedback.improvements.push('Alinearse mejor con los objetivos originales');
  }
  
  // Generar recomendaciones
  if (scoreDetails.finalScore < SCORE_THRESHOLDS.ACCEPTABLE) {
    feedback.recommendations.push('Se recomienda revisar y mejorar el resultado antes de continuar');
    feedback.recommendations.push('Considerar dividir la tarea en pasos más pequeños');
  }
  
  return feedback;
}

/**
 * Función principal del Reward Shell
 * Evalúa el output del Builder y determina si cumple con los objetivos
 * 
 * @param {Object} builderOutput - Output generado por el Builder
 * @param {Object} originalContext - Contexto original de la tarea
 * @param {Object} options - Opciones adicionales para la evaluación
 * @returns {Object} Resultado de la evaluación con score, feedback y decisión de retry
 */
export async function evaluateOutput(builderOutput, originalContext, options = {}) {
  try {
    logger.info('RewardShell: Iniciando evaluación del output', {
      sessionId: originalContext.sessionId,
      taskType: originalContext.taskType
    });

    // 1. Realizar evaluaciones individuales
    const evaluations = {
      completeness: evaluateCompleteness(builderOutput, originalContext),
      technicalQuality: evaluateTechnicalQuality(builderOutput, originalContext.taskType),
      objectiveFulfillment: evaluateObjectiveFulfillment(builderOutput, originalContext)
    };

    // 2. Calcular puntuación final
    const scoreDetails = calculateFinalScore(evaluations, originalContext.taskType);

    // 3. Generar feedback
    const feedback = generateFeedback(evaluations, scoreDetails);

    // 4. Determinar si se requiere retry
    const shouldRetry = scoreDetails.finalScore < (options.retryThreshold || SCORE_THRESHOLDS.ACCEPTABLE);
    
    // 5. Preparar resultado final
    const result = {
      id: `evaluation_${Date.now()}`,
      timestamp: new Date().toISOString(),
      score: scoreDetails.finalScore,
      qualityLevel: scoreDetails.qualityLevel,
      feedback,
      retry: shouldRetry,
      evaluations,
      scoreDetails,
      metadata: {
        evaluatedBy: 'rewardShell',
        version: '1.0.0',
        taskType: originalContext.taskType,
        sessionId: originalContext.sessionId
      }
    };

    logger.info('RewardShell: Evaluación completada', {
      score: result.score,
      qualityLevel: result.qualityLevel,
      retry: result.retry,
      sessionId: originalContext.sessionId
    });

    return {
      success: true,
      evaluation: result,
      message: 'Evaluación completada exitosamente'
    };

  } catch (error) {
    logger.error('RewardShell: Error durante la evaluación', {
      error: error.message,
      stack: error.stack,
      sessionId: originalContext.sessionId
    });

    return {
      success: false,
      error: error.message,
      message: 'Error durante la evaluación del output'
    };
  }
}

/**
 * Evalúa múltiples outputs y los compara
 * @param {Array} outputs - Lista de outputs a evaluar
 * @param {Object} originalContext - Contexto original
 * @returns {Object} Comparación de evaluaciones
 */
export async function compareOutputs(outputs, originalContext) {
  try {
    const evaluations = [];
    
    for (const output of outputs) {
      const evaluation = await evaluateOutput(output, originalContext);
      if (evaluation.success) {
        evaluations.push(evaluation.evaluation);
      }
    }
    
    // Ordenar por puntuación
    evaluations.sort((a, b) => b.score - a.score);
    
    return {
      success: true,
      evaluations,
      best: evaluations[0],
      worst: evaluations[evaluations.length - 1],
      average: evaluations.reduce((sum, eval) => sum + eval.score, 0) / evaluations.length
    };
    
  } catch (error) {
    logger.error('RewardShell: Error comparando outputs', { error: error.message });
    return {
      success: false,
      error: error.message
    };
  }
}

export { EVALUATION_CRITERIA, SCORE_THRESHOLDS };

