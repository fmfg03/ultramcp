"""
Nodos LangGraph para Reasoning y Reward Shells

Migra la funcionalidad de reasoningShell.js y rewardShell.js 
a nodos LangGraph reutilizables que pueden ser usados en múltiples agentes.
"""

import sys
import os
from typing import Dict, Any, List, Optional
import time
import json

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from langgraph_system.schemas.mcp_schemas import (
    ReasoningInput, ReasoningOutput, RewardInput, RewardOutput,
    TaskComplexity, ModelType, ContradictionInfo
)

# Importar servicios existentes
try:
    from backend.src.utils.logger import logger
    from backend.src.services.memoryService import saveStep, getContext, saveReward
    from backend.src.services.contradictionService import (
        detectContradiction, generateContradictionPrompt, 
        evaluateContradictionEffectiveness
    )
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    
    # Mock functions para desarrollo
    async def saveStep(session_id, step_data):
        return {'success': True, 'step_id': f'step_{hash(str(step_data)) % 10000}'}
    
    async def getContext(session_id):
        return {'success': True, 'context': {'previous_attempts': []}}
    
    async def saveReward(session_id, reward_data):
        return {'success': True, 'reward_id': f'reward_{hash(str(reward_data)) % 10000}'}
    
    def detectContradiction(attempts, current_score):
        return len(attempts) > 2 and current_score < 0.6
    
    def generateContradictionPrompt(original_prompt, attempts, intensity='moderate'):
        return f"CONTRADICCIÓN EXPLÍCITA ({intensity}): {original_prompt}"
    
    def evaluateContradictionEffectiveness(before_score, after_score, attempts):
        return {
            'effective': after_score > before_score,
            'improvement': after_score - before_score,
            'recommendation': 'continue' if after_score > before_score else 'escalate'
        }

# ============================================================================
# Nodos de Reasoning Shell
# ============================================================================

async def enhanced_reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo de razonamiento mejorado que integra memoria y contexto histórico
    """
    try:
        request = state['request']
        session_id = state.get('session_id', f"reasoning_{hash(request) % 10000}")
        context = state.get('context', {})
        
        logger.info(f"🧠 Iniciando razonamiento mejorado para sesión {session_id}")
        
        # Obtener contexto histórico
        context_result = await getContext(session_id)
        historical_context = context_result.get('context', {}) if context_result.get('success') else {}
        previous_attempts = historical_context.get('previous_attempts', [])
        
        # Análisis de complejidad mejorado con contexto histórico
        complexity_analysis = analyze_task_complexity(request, previous_attempts)
        
        # Crear plan adaptativo basado en historial
        adaptive_plan = create_adaptive_plan(
            request, 
            complexity_analysis,
            previous_attempts,
            context
        )
        
        # Recomendar modelo basado en análisis y historial
        model_recommendation = recommend_model_with_history(
            request,
            complexity_analysis,
            previous_attempts
        )
        
        # Guardar paso de razonamiento
        reasoning_step = {
            'type': 'reasoning',
            'timestamp': time.time(),
            'request': request,
            'complexity': complexity_analysis,
            'plan': adaptive_plan,
            'model_recommendation': model_recommendation,
            'context_used': bool(previous_attempts)
        }
        
        await saveStep(session_id, reasoning_step)
        
        result = {
            'success': True,
            'plan': adaptive_plan,
            'subtasks': adaptive_plan.get('subtasks', []),
            'estimated_complexity': complexity_analysis['level'],
            'recommended_model': model_recommendation,
            'session_id': session_id,
            'metadata': {
                'reasoning_timestamp': time.time(),
                'complexity_analysis': complexity_analysis,
                'historical_context_used': bool(previous_attempts),
                'previous_attempts_count': len(previous_attempts)
            }
        }
        
        logger.info(f"✅ Razonamiento completado: {complexity_analysis['level']} | {model_recommendation}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en enhanced_reasoning_node: {str(e)}")
        return {
            'success': False,
            'plan': {'type': 'error', 'error': str(e)},
            'subtasks': [],
            'estimated_complexity': TaskComplexity.SIMPLE,
            'recommended_model': ModelType.AUTO,
            'session_id': state.get('session_id', 'error_session'),
            'metadata': {'error': str(e)}
        }

def analyze_task_complexity(request: str, previous_attempts: List[Dict]) -> Dict[str, Any]:
    """
    Analiza la complejidad de la tarea considerando intentos previos
    """
    request_lower = request.lower()
    
    # Indicadores base de complejidad
    complexity_indicators = {
        'simple': {
            'keywords': ['qué es', 'define', 'explica', 'resume', 'lista'],
            'weight': 1.0
        },
        'moderate': {
            'keywords': ['cómo', 'pasos', 'proceso', 'implementar', 'crear', 'diseñar'],
            'weight': 2.0
        },
        'complex': {
            'keywords': ['sistema', 'arquitectura', 'integración', 'escalable', 'completo'],
            'weight': 3.0
        },
        'expert': {
            'keywords': ['optimizar', 'producción', 'enterprise', 'migración', 'performance'],
            'weight': 4.0
        }
    }
    
    # Calcular score base
    base_score = 0
    matched_keywords = []
    
    for level, data in complexity_indicators.items():
        for keyword in data['keywords']:
            if keyword in request_lower:
                base_score += data['weight']
                matched_keywords.append((keyword, level))
    
    # Ajustar por longitud del request
    word_count = len(request.split())
    length_multiplier = min(word_count / 50, 2.0)  # Max 2x multiplier
    
    # Ajustar por historial de fallos
    failure_multiplier = 1.0
    if previous_attempts:
        failed_attempts = [a for a in previous_attempts if a.get('score', 0) < 0.6]
        if failed_attempts:
            failure_multiplier = 1.0 + (len(failed_attempts) * 0.3)  # Incrementar complejidad por fallos
    
    # Score final
    final_score = base_score * length_multiplier * failure_multiplier
    
    # Determinar nivel
    if final_score >= 8:
        level = TaskComplexity.EXPERT
    elif final_score >= 5:
        level = TaskComplexity.COMPLEX
    elif final_score >= 2:
        level = TaskComplexity.MODERATE
    else:
        level = TaskComplexity.SIMPLE
    
    return {
        'level': level,
        'score': final_score,
        'base_score': base_score,
        'length_multiplier': length_multiplier,
        'failure_multiplier': failure_multiplier,
        'matched_keywords': matched_keywords,
        'word_count': word_count,
        'previous_failures': len([a for a in previous_attempts if a.get('score', 0) < 0.6])
    }

def create_adaptive_plan(request: str, complexity: Dict, previous_attempts: List, context: Dict) -> Dict[str, Any]:
    """
    Crea un plan adaptativo basado en complejidad e historial
    """
    level = complexity['level']
    has_failures = complexity['previous_failures'] > 0
    
    # Plan base según complejidad
    if level == TaskComplexity.SIMPLE:
        base_plan = {
            'type': 'direct_execution',
            'steps': ['analyze', 'execute', 'validate'],
            'estimated_duration': 30,
            'requires_iteration': False
        }
        subtasks = [
            {
                'id': 'main_task',
                'description': request,
                'priority': 'high',
                'estimated_tokens': 200
            }
        ]
    
    elif level == TaskComplexity.MODERATE:
        base_plan = {
            'type': 'structured_execution',
            'steps': ['analyze', 'plan', 'execute', 'review', 'finalize'],
            'estimated_duration': 120,
            'requires_iteration': True
        }
        subtasks = [
            {
                'id': 'analysis',
                'description': f"Analizar requerimientos: {request}",
                'priority': 'high',
                'estimated_tokens': 150
            },
            {
                'id': 'implementation',
                'description': f"Implementar solución: {request}",
                'priority': 'high',
                'estimated_tokens': 300
            },
            {
                'id': 'validation',
                'description': f"Validar resultado: {request}",
                'priority': 'medium',
                'estimated_tokens': 100
            }
        ]
    
    else:  # COMPLEX or EXPERT
        base_plan = {
            'type': 'iterative_execution',
            'steps': ['research', 'design', 'implement', 'test', 'optimize', 'document'],
            'estimated_duration': 300,
            'requires_iteration': True,
            'requires_recursive_planning': True
        }
        subtasks = [
            {
                'id': 'research_phase',
                'description': f"Investigar y analizar: {request}",
                'priority': 'critical',
                'estimated_tokens': 200
            },
            {
                'id': 'design_phase',
                'description': f"Diseñar arquitectura: {request}",
                'priority': 'critical',
                'estimated_tokens': 400
            },
            {
                'id': 'implementation_phase',
                'description': f"Implementar solución completa: {request}",
                'priority': 'high',
                'estimated_tokens': 500
            },
            {
                'id': 'testing_phase',
                'description': f"Probar y validar: {request}",
                'priority': 'high',
                'estimated_tokens': 200
            }
        ]
    
    # Adaptaciones por historial de fallos
    if has_failures:
        base_plan['type'] = f"adaptive_{base_plan['type']}"
        base_plan['failure_aware'] = True
        base_plan['estimated_duration'] = int(base_plan['estimated_duration'] * 1.5)
        
        # Agregar subtarea de análisis de fallos previos
        failure_analysis_task = {
            'id': 'failure_analysis',
            'description': f"Analizar fallos previos y ajustar enfoque para: {request}",
            'priority': 'critical',
            'estimated_tokens': 150
        }
        subtasks.insert(0, failure_analysis_task)
    
    base_plan['subtasks'] = subtasks
    base_plan['total_estimated_tokens'] = sum(task.get('estimated_tokens', 0) for task in subtasks)
    base_plan['complexity_analysis'] = complexity
    
    return base_plan

def recommend_model_with_history(request: str, complexity: Dict, previous_attempts: List) -> ModelType:
    """
    Recomienda modelo considerando historial de rendimiento
    """
    request_lower = request.lower()
    
    # Análisis de contenido
    if any(keyword in request_lower for keyword in ['matemática', 'cálculo', 'ecuación', 'demostrar', 'paradoja']):
        content_recommendation = ModelType.DEEPSEEK_LOCAL
    elif any(keyword in request_lower for keyword in ['sistema', 'arquitectura', 'complejo', 'diseño']):
        content_recommendation = ModelType.LLAMA_LOCAL
    else:
        content_recommendation = ModelType.MISTRAL_LOCAL
    
    # Análisis de historial
    if previous_attempts:
        model_performance = {}
        for attempt in previous_attempts:
            model = attempt.get('model_used', 'unknown')
            score = attempt.get('score', 0)
            if model not in model_performance:
                model_performance[model] = []
            model_performance[model].append(score)
        
        # Calcular promedio de rendimiento por modelo
        model_averages = {}
        for model, scores in model_performance.items():
            model_averages[model] = sum(scores) / len(scores)
        
        # Si hay historial, considerar el mejor modelo histórico
        if model_averages:
            best_historical_model = max(model_averages, key=model_averages.get)
            best_score = model_averages[best_historical_model]
            
            # Si el mejor modelo histórico tiene buen rendimiento, usarlo
            if best_score > 0.7:
                try:
                    return ModelType(best_historical_model)
                except ValueError:
                    pass  # Modelo no válido, usar recomendación por contenido
    
    # Ajustar por complejidad
    if complexity['level'] == TaskComplexity.EXPERT:
        if content_recommendation == ModelType.MISTRAL_LOCAL:
            return ModelType.LLAMA_LOCAL  # Upgrade para tareas expertas
    
    return content_recommendation

# ============================================================================
# Nodos de Reward Shell
# ============================================================================

async def enhanced_reward_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo de evaluación mejorado que integra múltiples métricas y contexto histórico
    """
    try:
        original_request = state.get('original_request', state.get('request', ''))
        builder_output = state.get('result', state.get('builder_output', ''))
        context = state.get('context', {})
        session_id = state.get('session_id', f"reward_{hash(original_request) % 10000}")
        
        logger.info(f"🏆 Iniciando evaluación mejorada para sesión {session_id}")
        
        # Obtener contexto histórico
        context_result = await getContext(session_id)
        historical_context = context_result.get('context', {}) if context_result.get('success') else {}
        previous_attempts = historical_context.get('previous_attempts', [])
        
        # Evaluación multi-dimensional
        evaluation_result = evaluate_multidimensional(
            original_request,
            builder_output,
            context,
            previous_attempts
        )
        
        # Determinar si recomendar retry
        retry_analysis = analyze_retry_recommendation(
            evaluation_result,
            previous_attempts,
            context
        )
        
        # Generar feedback específico
        detailed_feedback = generate_detailed_feedback(
            original_request,
            builder_output,
            evaluation_result,
            retry_analysis
        )
        
        # Guardar evaluación
        reward_step = {
            'type': 'reward_evaluation',
            'timestamp': time.time(),
            'original_request': original_request,
            'builder_output': builder_output,
            'evaluation': evaluation_result,
            'retry_analysis': retry_analysis,
            'feedback': detailed_feedback
        }
        
        await saveReward(session_id, reward_step)
        
        result = {
            'score': evaluation_result['overall_score'],
            'feedback': detailed_feedback['summary'],
            'retry_recommended': retry_analysis['should_retry'],
            'improvement_suggestions': detailed_feedback['suggestions'],
            'quality_metrics': evaluation_result['metrics'],
            'session_id': session_id,
            'metadata': {
                'evaluation_timestamp': time.time(),
                'detailed_evaluation': evaluation_result,
                'retry_analysis': retry_analysis,
                'previous_attempts_count': len(previous_attempts)
            }
        }
        
        logger.info(f"✅ Evaluación completada: Score {evaluation_result['overall_score']:.2f} | Retry: {retry_analysis['should_retry']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en enhanced_reward_node: {str(e)}")
        return {
            'score': 0.0,
            'feedback': f"Error en evaluación: {str(e)}",
            'retry_recommended': True,
            'improvement_suggestions': ["Revisar el sistema de evaluación"],
            'quality_metrics': {},
            'session_id': state.get('session_id', 'error_session'),
            'metadata': {'error': str(e)}
        }

def evaluate_multidimensional(request: str, output: str, context: Dict, previous_attempts: List) -> Dict[str, Any]:
    """
    Evaluación multi-dimensional de la calidad del output
    """
    metrics = {}
    
    # 1. Relevancia (0-1)
    relevance_score = calculate_relevance(request, output)
    metrics['relevance'] = relevance_score
    
    # 2. Completitud (0-1)
    completeness_score = calculate_completeness(request, output)
    metrics['completeness'] = completeness_score
    
    # 3. Claridad (0-1)
    clarity_score = calculate_clarity(output)
    metrics['clarity'] = clarity_score
    
    # 4. Coherencia (0-1)
    coherence_score = calculate_coherence(output)
    metrics['coherence'] = coherence_score
    
    # 5. Utilidad práctica (0-1)
    utility_score = calculate_utility(request, output)
    metrics['utility'] = utility_score
    
    # 6. Mejora respecto a intentos previos (0-1)
    improvement_score = calculate_improvement(output, previous_attempts)
    metrics['improvement'] = improvement_score
    
    # Pesos adaptativos basados en el tipo de request
    weights = calculate_adaptive_weights(request, context)
    
    # Score general ponderado
    overall_score = sum(metrics[metric] * weights[metric] for metric in metrics)
    
    return {
        'overall_score': overall_score,
        'metrics': metrics,
        'weights': weights,
        'breakdown': {
            metric: {
                'score': score,
                'weight': weights[metric],
                'contribution': score * weights[metric]
            }
            for metric, score in metrics.items()
        }
    }

def calculate_relevance(request: str, output: str) -> float:
    """Calcula qué tan relevante es el output al request"""
    request_words = set(request.lower().split())
    output_words = set(output.lower().split())
    
    # Intersección de palabras clave
    common_words = request_words.intersection(output_words)
    
    # Filtrar palabras comunes irrelevantes
    stop_words = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como', 'pero', 'sus', 'han', 'fue', 'ser', 'está', 'todo', 'más', 'muy', 'puede', 'si', 'ya', 'sobre', 'este', 'esta', 'hasta', 'cuando', 'donde', 'quien', 'cual', 'como'}
    relevant_common = common_words - stop_words
    
    if not request_words - stop_words:
        return 0.5  # Request muy genérico
    
    relevance = len(relevant_common) / len(request_words - stop_words)
    return min(relevance, 1.0)

def calculate_completeness(request: str, output: str) -> float:
    """Calcula qué tan completo es el output"""
    # Heurísticas básicas de completitud
    output_length = len(output)
    
    # Longitud mínima esperada basada en el request
    request_complexity = len(request.split())
    expected_min_length = request_complexity * 10  # ~10 chars por palabra del request
    
    if output_length < expected_min_length * 0.5:
        return 0.3  # Muy corto
    elif output_length < expected_min_length:
        return 0.6  # Algo corto
    elif output_length > expected_min_length * 3:
        return 0.8  # Posiblemente verboso pero completo
    else:
        return 0.9  # Longitud apropiada

def calculate_clarity(output: str) -> float:
    """Calcula la claridad del output"""
    # Heurísticas de claridad
    sentences = output.split('.')
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    
    # Penalizar oraciones muy largas o muy cortas
    if avg_sentence_length < 5:
        clarity = 0.6  # Muy telegráfico
    elif avg_sentence_length > 30:
        clarity = 0.7  # Posiblemente confuso
    else:
        clarity = 0.9  # Longitud apropiada
    
    # Bonus por estructura (listas, párrafos, etc.)
    if '\n' in output or '1.' in output or '-' in output:
        clarity += 0.1
    
    return min(clarity, 1.0)

def calculate_coherence(output: str) -> float:
    """Calcula la coherencia del output"""
    # Heurística simple: repetición de conceptos clave
    words = output.lower().split()
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Solo palabras significativas
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Coherencia basada en repetición balanceada de conceptos
    if not word_freq:
        return 0.5
    
    max_freq = max(word_freq.values())
    avg_freq = sum(word_freq.values()) / len(word_freq)
    
    # Coherencia alta si hay repetición balanceada
    coherence = min(avg_freq / max_freq * 2, 1.0)
    return coherence

def calculate_utility(request: str, output: str) -> float:
    """Calcula la utilidad práctica del output"""
    request_lower = request.lower()
    output_lower = output.lower()
    
    # Indicadores de utilidad
    utility_indicators = {
        'código': ['def ', 'function', 'class ', 'import', '```'],
        'pasos': ['1.', '2.', 'paso', 'primero', 'segundo'],
        'explicación': ['porque', 'debido', 'razón', 'causa'],
        'ejemplo': ['ejemplo', 'por ejemplo', 'como:', 'tal como'],
        'solución': ['solución', 'resolver', 'resultado', 'respuesta']
    }
    
    utility_score = 0.5  # Base
    
    for intent, indicators in utility_indicators.items():
        if intent in request_lower:
            for indicator in indicators:
                if indicator in output_lower:
                    utility_score += 0.1
                    break
    
    return min(utility_score, 1.0)

def calculate_improvement(output: str, previous_attempts: List) -> float:
    """Calcula mejora respecto a intentos previos"""
    if not previous_attempts:
        return 0.8  # Primer intento, score neutral alto
    
    # Comparar longitud y complejidad con intentos previos
    current_length = len(output)
    previous_lengths = [len(attempt.get('output', '')) for attempt in previous_attempts]
    
    if not previous_lengths:
        return 0.8
    
    avg_previous_length = sum(previous_lengths) / len(previous_lengths)
    
    # Mejora si es significativamente más largo (más detallado)
    if current_length > avg_previous_length * 1.2:
        return 0.9
    elif current_length > avg_previous_length:
        return 0.8
    elif current_length > avg_previous_length * 0.8:
        return 0.6
    else:
        return 0.4  # Posible regresión

def calculate_adaptive_weights(request: str, context: Dict) -> Dict[str, float]:
    """Calcula pesos adaptativos basados en el tipo de request"""
    request_lower = request.lower()
    
    # Pesos por defecto
    weights = {
        'relevance': 0.25,
        'completeness': 0.20,
        'clarity': 0.15,
        'coherence': 0.15,
        'utility': 0.15,
        'improvement': 0.10
    }
    
    # Ajustes por tipo de request
    if any(word in request_lower for word in ['explica', 'qué es', 'define']):
        # Requests explicativos: priorizar claridad y completitud
        weights['clarity'] = 0.25
        weights['completeness'] = 0.25
        weights['relevance'] = 0.20
    
    elif any(word in request_lower for word in ['cómo', 'pasos', 'implementar']):
        # Requests procedimentales: priorizar utilidad y completitud
        weights['utility'] = 0.30
        weights['completeness'] = 0.25
        weights['clarity'] = 0.20
    
    elif any(word in request_lower for word in ['código', 'función', 'programa']):
        # Requests de código: priorizar utilidad y coherencia
        weights['utility'] = 0.35
        weights['coherence'] = 0.25
        weights['relevance'] = 0.20
    
    # Ajustar por contexto de fallos previos
    failure_count = context.get('previous_failures', 0)
    if failure_count > 0:
        # Incrementar peso de mejora si hay fallos previos
        weights['improvement'] = min(0.20 + (failure_count * 0.05), 0.30)
        # Redistribuir otros pesos proporcionalmente
        total_other = sum(v for k, v in weights.items() if k != 'improvement')
        scale_factor = (1.0 - weights['improvement']) / total_other
        for key in weights:
            if key != 'improvement':
                weights[key] *= scale_factor
    
    return weights

def analyze_retry_recommendation(evaluation: Dict, previous_attempts: List, context: Dict) -> Dict[str, Any]:
    """Analiza si recomendar retry basado en evaluación e historial"""
    overall_score = evaluation['overall_score']
    attempt_count = len(previous_attempts) + 1
    
    # Umbrales adaptativos
    retry_threshold = 0.7  # Score mínimo aceptable
    max_attempts = 3
    
    # Ajustar umbral por número de intentos
    adjusted_threshold = retry_threshold - (attempt_count * 0.1)
    
    # Decisión básica
    should_retry = overall_score < adjusted_threshold and attempt_count < max_attempts
    
    # Análisis de tendencia
    if previous_attempts:
        previous_scores = [a.get('score', 0) for a in previous_attempts]
        if previous_scores:
            trend = 'improving' if overall_score > max(previous_scores) else 'declining'
            
            # Si está mejorando pero aún bajo, dar una oportunidad más
            if trend == 'improving' and should_retry:
                confidence = 0.8
            elif trend == 'declining':
                confidence = 0.3
                # Si está empeorando, ser más estricto
                should_retry = should_retry and overall_score > 0.4
            else:
                confidence = 0.6
        else:
            trend = 'unknown'
            confidence = 0.5
    else:
        trend = 'first_attempt'
        confidence = 0.7
    
    return {
        'should_retry': should_retry,
        'confidence': confidence,
        'trend': trend,
        'attempt_count': attempt_count,
        'adjusted_threshold': adjusted_threshold,
        'score_gap': adjusted_threshold - overall_score,
        'max_attempts_reached': attempt_count >= max_attempts
    }

def generate_detailed_feedback(request: str, output: str, evaluation: Dict, retry_analysis: Dict) -> Dict[str, Any]:
    """Genera feedback detallado y sugerencias de mejora"""
    metrics = evaluation['metrics']
    breakdown = evaluation['breakdown']
    
    # Identificar áreas más débiles
    weak_areas = [metric for metric, data in breakdown.items() if data['score'] < 0.6]
    strong_areas = [metric for metric, data in breakdown.items() if data['score'] > 0.8]
    
    # Generar feedback específico
    feedback_parts = []
    suggestions = []
    
    # Feedback general
    if evaluation['overall_score'] > 0.8:
        feedback_parts.append("Excelente respuesta que cumple con los requerimientos.")
    elif evaluation['overall_score'] > 0.6:
        feedback_parts.append("Buena respuesta con algunas áreas de mejora.")
    else:
        feedback_parts.append("La respuesta necesita mejoras significativas.")
    
    # Feedback específico por métrica débil
    if 'relevance' in weak_areas:
        feedback_parts.append("La respuesta no aborda completamente el tema solicitado.")
        suggestions.append("Enfocarse más directamente en los aspectos específicos del request")
    
    if 'completeness' in weak_areas:
        feedback_parts.append("La respuesta parece incompleta o superficial.")
        suggestions.append("Proporcionar más detalles y cubrir todos los aspectos relevantes")
    
    if 'clarity' in weak_areas:
        feedback_parts.append("La respuesta podría ser más clara y fácil de entender.")
        suggestions.append("Usar estructura más clara, párrafos bien definidos y ejemplos")
    
    if 'utility' in weak_areas:
        feedback_parts.append("La respuesta carece de aplicabilidad práctica.")
        suggestions.append("Incluir ejemplos concretos, código funcional o pasos específicos")
    
    # Reconocer fortalezas
    if strong_areas:
        strengths = ", ".join(strong_areas)
        feedback_parts.append(f"Puntos fuertes: {strengths}.")
    
    # Sugerencias basadas en retry analysis
    if retry_analysis['should_retry']:
        if retry_analysis['trend'] == 'declining':
            suggestions.append("Considerar un enfoque completamente diferente")
        else:
            suggestions.append("Refinar la respuesta actual manteniendo los elementos exitosos")
    
    return {
        'summary': " ".join(feedback_parts),
        'suggestions': suggestions,
        'weak_areas': weak_areas,
        'strong_areas': strong_areas,
        'detailed_scores': {
            metric: f"{data['score']:.2f} (peso: {data['weight']:.2f})"
            for metric, data in breakdown.items()
        }
    }

# ============================================================================
# Nodos de Contradicción
# ============================================================================

async def contradiction_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo que analiza si aplicar contradicción explícita
    """
    try:
        session_id = state.get('session_id')
        current_score = state.get('score', state.get('reward_score', 0))
        
        # Obtener historial
        context_result = await getContext(session_id)
        historical_context = context_result.get('context', {}) if context_result.get('success') else {}
        previous_attempts = historical_context.get('previous_attempts', [])
        
        # Detectar si aplicar contradicción
        should_apply = detectContradiction(previous_attempts, current_score)
        
        contradiction_info = {
            'triggered': should_apply,
            'attempt_number': len(previous_attempts) + 1,
            'previous_scores': [a.get('score', 0) for a in previous_attempts],
            'current_score': current_score,
            'improvement_detected': False
        }
        
        if should_apply:
            # Determinar intensidad
            if len(previous_attempts) <= 2:
                intensity = 'mild'
            elif len(previous_attempts) <= 4:
                intensity = 'moderate'
            else:
                intensity = 'strong'
            
            contradiction_info['intensity'] = intensity
            
            # Evaluar efectividad de contradicciones previas
            if len(previous_attempts) > 1:
                effectiveness = evaluateContradictionEffectiveness(
                    previous_attempts[-2].get('score', 0),
                    previous_attempts[-1].get('score', 0),
                    previous_attempts
                )
                contradiction_info['previous_effectiveness'] = effectiveness
            
            logger.info(f"🔥 Contradicción detectada: intensidad {intensity}, intento {contradiction_info['attempt_number']}")
        
        return {
            'contradiction': contradiction_info,
            'metadata': {
                'contradiction_analysis_timestamp': time.time(),
                'previous_attempts_analyzed': len(previous_attempts)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en contradiction_analysis_node: {str(e)}")
        return {
            'contradiction': {
                'triggered': False,
                'attempt_number': 1,
                'previous_scores': [],
                'improvement_detected': False
            },
            'metadata': {'error': str(e)}
        }

# ============================================================================
# Exportar Nodos
# ============================================================================

__all__ = [
    'enhanced_reasoning_node',
    'enhanced_reward_node', 
    'contradiction_analysis_node',
    'analyze_task_complexity',
    'create_adaptive_plan',
    'recommend_model_with_history',
    'evaluate_multidimensional',
    'analyze_retry_recommendation',
    'generate_detailed_feedback'
]

