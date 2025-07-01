"""
Nodos LangGraph con integración completa de LLMs locales y Langwatch

Integra los wrappers de Langwatch y LLMs locales en nodos LangGraph
reutilizables que mantienen toda la funcionalidad avanzada.
"""

import sys
import os
from typing import Dict, Any, List, Optional
import time
import asyncio

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from langgraph_system.schemas.mcp_schemas import (
    ModelType, LangwatchMetadata, ContradictionInfo
)

# Importar servicios existentes
try:
    from backend.src.utils.logger import logger
    from backend.src.services.localLLMWrappers import (
        MistralLangwatchWrapper, LlamaLangwatchWrapper, DeepSeekLangwatchWrapper
    )
    from backend.src.middleware.enhancedLangwatchMiddleware import (
        trackLocalLLMExecution, trackContradictionEvent, trackRetryAttempt
    )
    from backend.src.services.contradictionService import (
        detectContradiction, generateContradictionPrompt, 
        evaluateContradictionEffectiveness
    )
    from adapters.enhancedLocalLLMAdapter import (
        detectBestModel, callLocalModelWithLangwatch, healthCheckModels
    )
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    
    # Mock classes y funciones para desarrollo
    class MockLangwatchWrapper:
        def __init__(self, model_name):
            self.model_name = model_name
        
        async def execute_with_tracking(self, prompt, options=None):
            return {
                'success': True,
                'response': f"Mock response from {self.model_name}: {prompt[:50]}...",
                'metadata': {
                    'langwatchTracking': {
                        'trackingId': f'mock_{hash(prompt) % 10000}',
                        'score': 0.8,
                        'contradiction': {'triggered': False},
                        'tracked': True,
                        'duration_ms': 1500,
                        'token_usage': {'totalTokens': 150}
                    }
                }
            }
    
    MistralLangwatchWrapper = lambda: MockLangwatchWrapper("mistral-local")
    LlamaLangwatchWrapper = lambda: MockLangwatchWrapper("llama-local")
    DeepSeekLangwatchWrapper = lambda: MockLangwatchWrapper("deepseek-local")
    
    async def trackLocalLLMExecution(model_type, prompt, response, metadata):
        return {'success': True, 'tracking_id': f'track_{hash(prompt) % 10000}'}
    
    async def trackContradictionEvent(session_id, contradiction_info):
        return {'success': True, 'event_id': f'contra_{hash(session_id) % 10000}'}
    
    async def trackRetryAttempt(session_id, attempt_info):
        return {'success': True, 'retry_id': f'retry_{hash(session_id) % 10000}'}
    
    def detectBestModel(prompt, context=None):
        return ModelType.MISTRAL_LOCAL
    
    async def callLocalModelWithLangwatch(model_type, prompt, options=None):
        return {
            'success': True,
            'response': f"Mock response for {model_type}",
            'metadata': {'langwatchTracking': {'score': 0.8}}
        }
    
    async def healthCheckModels():
        return {'mistral-local': True, 'llama-local': True, 'deepseek-local': True}

# ============================================================================
# Inicialización de Wrappers
# ============================================================================

# Instancias globales de wrappers
_model_wrappers = {
    ModelType.MISTRAL_LOCAL: None,
    ModelType.LLAMA_LOCAL: None,
    ModelType.DEEPSEEK_LOCAL: None
}

def get_model_wrapper(model_type: ModelType):
    """Obtiene o crea wrapper para el modelo especificado"""
    global _model_wrappers
    
    if _model_wrappers[model_type] is None:
        if model_type == ModelType.MISTRAL_LOCAL:
            _model_wrappers[model_type] = MistralLangwatchWrapper()
        elif model_type == ModelType.LLAMA_LOCAL:
            _model_wrappers[model_type] = LlamaLangwatchWrapper()
        elif model_type == ModelType.DEEPSEEK_LOCAL:
            _model_wrappers[model_type] = DeepSeekLangwatchWrapper()
        else:
            raise ValueError(f"Modelo no soportado: {model_type}")
    
    return _model_wrappers[model_type]

# ============================================================================
# Nodos de Ejecución con LLMs Locales
# ============================================================================

async def local_llm_execution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo que ejecuta prompts usando LLMs locales con tracking completo de Langwatch
    """
    try:
        prompt = state.get('prompt', state.get('request', ''))
        model_type = state.get('model_type', ModelType.AUTO)
        session_id = state.get('session_id', f"llm_{hash(prompt) % 10000}")
        options = state.get('options', {})
        retry_context = state.get('retry_context', {})
        
        logger.info(f"🤖 Ejecutando LLM local: {model_type} para sesión {session_id}")
        
        # Auto-detectar modelo si es necesario
        if model_type == ModelType.AUTO:
            model_type = detectBestModel(prompt, state.get('context', {}))
            logger.info(f"🎯 Modelo auto-detectado: {model_type}")
        
        # Obtener wrapper del modelo
        wrapper = get_model_wrapper(model_type)
        
        # Preparar opciones de ejecución
        execution_options = {
            'sessionId': session_id,
            'maxTokens': options.get('maxTokens', 512),
            'temperature': options.get('temperature', 0.7),
            'tags': options.get('tags', ['local_llm', 'langgraph']),
            **options
        }
        
        # Aplicar contradicción si es necesario
        final_prompt = prompt
        contradiction_applied = False
        
        if retry_context.get('apply_contradiction', False):
            previous_attempts = retry_context.get('previous_attempts', [])
            intensity = retry_context.get('contradiction_intensity', 'moderate')
            
            final_prompt = generateContradictionPrompt(prompt, previous_attempts, intensity)
            contradiction_applied = True
            
            # Trackear evento de contradicción
            contradiction_info = {
                'triggered': True,
                'intensity': intensity,
                'attempt_number': len(previous_attempts) + 1,
                'original_prompt': prompt,
                'modified_prompt': final_prompt
            }
            
            await trackContradictionEvent(session_id, contradiction_info)
            logger.info(f"🔥 Contradicción aplicada: {intensity}")
        
        # Ejecutar con wrapper de Langwatch
        start_time = time.time()
        
        result = await wrapper.execute_with_tracking(final_prompt, execution_options)
        
        execution_duration = (time.time() - start_time) * 1000
        
        # Procesar resultado
        if result['success']:
            response = result['response']
            langwatch_metadata = result.get('metadata', {}).get('langwatchTracking', {})
            
            # Trackear ejecución en Langwatch
            await trackLocalLLMExecution(
                model_type,
                final_prompt,
                response,
                {
                    'session_id': session_id,
                    'duration_ms': execution_duration,
                    'contradiction_applied': contradiction_applied,
                    'options': execution_options
                }
            )
            
            logger.info(f"✅ Ejecución exitosa: {len(response)} chars, score: {langwatch_metadata.get('score', 'N/A')}")
            
            return {
                'success': True,
                'response': response,
                'model_used': model_type,
                'execution_duration_ms': execution_duration,
                'langwatch_metadata': langwatch_metadata,
                'contradiction_applied': contradiction_applied,
                'metadata': {
                    'execution_timestamp': time.time(),
                    'final_prompt_length': len(final_prompt),
                    'response_length': len(response),
                    'wrapper_metadata': result.get('metadata', {})
                }
            }
        
        else:
            error_msg = result.get('error', 'Error desconocido en LLM local')
            logger.error(f"❌ Error en ejecución: {error_msg}")
            
            return {
                'success': False,
                'response': f"Error en LLM local: {error_msg}",
                'model_used': model_type,
                'execution_duration_ms': execution_duration,
                'langwatch_metadata': None,
                'contradiction_applied': contradiction_applied,
                'metadata': {'error': error_msg}
            }
    
    except Exception as e:
        logger.error(f"❌ Error en local_llm_execution_node: {str(e)}")
        return {
            'success': False,
            'response': f"Error interno: {str(e)}",
            'model_used': state.get('model_type', ModelType.AUTO),
            'execution_duration_ms': 0,
            'langwatch_metadata': None,
            'contradiction_applied': False,
            'metadata': {'error': str(e)}
        }

async def adaptive_model_selection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo que selecciona adaptativamente el mejor modelo basado en contexto e historial
    """
    try:
        prompt = state.get('prompt', state.get('request', ''))
        session_id = state.get('session_id', f"adaptive_{hash(prompt) % 10000}")
        context = state.get('context', {})
        previous_attempts = state.get('previous_attempts', [])
        
        logger.info(f"🎯 Selección adaptativa de modelo para sesión {session_id}")
        
        # Análisis de contenido del prompt
        content_analysis = analyze_prompt_content(prompt)
        
        # Análisis de rendimiento histórico
        historical_performance = analyze_historical_performance(previous_attempts)
        
        # Verificar salud de modelos
        model_health = await healthCheckModels()
        
        # Selección inteligente
        selected_model = select_optimal_model(
            content_analysis,
            historical_performance,
            model_health,
            context
        )
        
        # Configuración adaptativa
        adaptive_config = generate_adaptive_config(
            selected_model,
            content_analysis,
            previous_attempts
        )
        
        logger.info(f"✅ Modelo seleccionado: {selected_model} con config adaptativa")
        
        return {
            'model_type': selected_model,
            'adaptive_config': adaptive_config,
            'selection_reasoning': {
                'content_analysis': content_analysis,
                'historical_performance': historical_performance,
                'model_health': model_health,
                'selection_timestamp': time.time()
            },
            'metadata': {
                'selection_method': 'adaptive',
                'confidence': adaptive_config.get('confidence', 0.8)
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Error en adaptive_model_selection_node: {str(e)}")
        return {
            'model_type': ModelType.MISTRAL_LOCAL,  # Fallback seguro
            'adaptive_config': {'temperature': 0.7, 'maxTokens': 512},
            'selection_reasoning': {'error': str(e)},
            'metadata': {'error': str(e)}
        }

def analyze_prompt_content(prompt: str) -> Dict[str, Any]:
    """Analiza el contenido del prompt para determinar el mejor modelo"""
    prompt_lower = prompt.lower()
    
    # Categorías de contenido
    categories = {
        'mathematical': {
            'keywords': ['matemática', 'cálculo', 'ecuación', 'demostrar', 'paradoja', 'teorema', 'fórmula'],
            'weight': 1.0,
            'preferred_model': ModelType.DEEPSEEK_LOCAL
        },
        'technical': {
            'keywords': ['sistema', 'arquitectura', 'diseño', 'implementar', 'código', 'algoritmo'],
            'weight': 0.8,
            'preferred_model': ModelType.LLAMA_LOCAL
        },
        'general': {
            'keywords': ['explica', 'qué es', 'cómo', 'define', 'resume', 'describe'],
            'weight': 0.6,
            'preferred_model': ModelType.MISTRAL_LOCAL
        },
        'creative': {
            'keywords': ['crear', 'generar', 'escribir', 'inventar', 'imaginar'],
            'weight': 0.7,
            'preferred_model': ModelType.MISTRAL_LOCAL
        }
    }
    
    # Calcular scores por categoría
    category_scores = {}
    for category, data in categories.items():
        score = 0
        matched_keywords = []
        for keyword in data['keywords']:
            if keyword in prompt_lower:
                score += data['weight']
                matched_keywords.append(keyword)
        
        category_scores[category] = {
            'score': score,
            'matched_keywords': matched_keywords,
            'preferred_model': data['preferred_model']
        }
    
    # Determinar categoría dominante
    dominant_category = max(category_scores, key=lambda x: category_scores[x]['score'])
    
    # Análisis de complejidad
    complexity_indicators = {
        'word_count': len(prompt.split()),
        'sentence_count': len(prompt.split('.')),
        'technical_terms': sum(1 for word in prompt_lower.split() if len(word) > 8),
        'question_marks': prompt.count('?'),
        'complexity_keywords': sum(1 for kw in ['complejo', 'avanzado', 'detallado', 'completo'] if kw in prompt_lower)
    }
    
    complexity_score = (
        min(complexity_indicators['word_count'] / 50, 2.0) +
        min(complexity_indicators['technical_terms'] / 5, 1.5) +
        complexity_indicators['complexity_keywords'] * 0.5
    )
    
    return {
        'dominant_category': dominant_category,
        'category_scores': category_scores,
        'complexity_score': complexity_score,
        'complexity_indicators': complexity_indicators,
        'recommended_model': category_scores[dominant_category]['preferred_model'],
        'confidence': min(category_scores[dominant_category]['score'] / 2.0, 1.0)
    }

def analyze_historical_performance(previous_attempts: List[Dict]) -> Dict[str, Any]:
    """Analiza el rendimiento histórico de modelos"""
    if not previous_attempts:
        return {'no_history': True}
    
    model_performance = {}
    
    for attempt in previous_attempts:
        model = attempt.get('model_used', 'unknown')
        score = attempt.get('score', attempt.get('langwatch_metadata', {}).get('score', 0))
        duration = attempt.get('execution_duration_ms', 0)
        
        if model not in model_performance:
            model_performance[model] = {
                'scores': [],
                'durations': [],
                'attempts': 0,
                'successes': 0
            }
        
        model_performance[model]['scores'].append(score)
        model_performance[model]['durations'].append(duration)
        model_performance[model]['attempts'] += 1
        
        if score > 0.6:  # Umbral de éxito
            model_performance[model]['successes'] += 1
    
    # Calcular métricas agregadas
    model_metrics = {}
    for model, data in model_performance.items():
        if data['attempts'] > 0:
            model_metrics[model] = {
                'avg_score': sum(data['scores']) / len(data['scores']),
                'avg_duration': sum(data['durations']) / len(data['durations']),
                'success_rate': data['successes'] / data['attempts'],
                'attempts': data['attempts'],
                'trend': 'improving' if len(data['scores']) > 1 and data['scores'][-1] > data['scores'][0] else 'stable'
            }
    
    # Determinar mejor modelo histórico
    best_model = None
    if model_metrics:
        # Combinar score promedio y tasa de éxito
        best_model = max(model_metrics, key=lambda m: 
            model_metrics[m]['avg_score'] * 0.7 + model_metrics[m]['success_rate'] * 0.3
        )
    
    return {
        'model_metrics': model_metrics,
        'best_historical_model': best_model,
        'total_attempts': len(previous_attempts),
        'analysis_timestamp': time.time()
    }

def select_optimal_model(content_analysis: Dict, historical_performance: Dict, 
                        model_health: Dict, context: Dict) -> ModelType:
    """Selecciona el modelo óptimo basado en todos los factores"""
    
    # Modelo recomendado por contenido
    content_recommendation = content_analysis['recommended_model']
    content_confidence = content_analysis['confidence']
    
    # Modelo recomendado por historial
    historical_recommendation = None
    historical_confidence = 0.0
    
    if not historical_performance.get('no_history', False):
        best_historical = historical_performance.get('best_historical_model')
        if best_historical:
            try:
                historical_recommendation = ModelType(best_historical)
                metrics = historical_performance['model_metrics'][best_historical]
                historical_confidence = metrics['avg_score'] * metrics['success_rate']
            except (ValueError, KeyError):
                pass
    
    # Verificar salud de modelos
    available_models = [model for model, healthy in model_health.items() if healthy]
    
    # Lógica de selección
    if historical_confidence > 0.8 and historical_recommendation in [ModelType(m) for m in available_models]:
        # Confiar en historial si es muy bueno
        selected = historical_recommendation
        logger.info(f"🎯 Selección por historial: {selected} (confianza: {historical_confidence:.2f})")
    
    elif content_confidence > 0.7 and content_recommendation.value in available_models:
        # Usar recomendación por contenido si es confiable
        selected = content_recommendation
        logger.info(f"🎯 Selección por contenido: {selected} (confianza: {content_confidence:.2f})")
    
    else:
        # Fallback inteligente
        if ModelType.MISTRAL_LOCAL.value in available_models:
            selected = ModelType.MISTRAL_LOCAL
        elif available_models:
            selected = ModelType(available_models[0])
        else:
            selected = ModelType.MISTRAL_LOCAL  # Último recurso
        
        logger.info(f"🎯 Selección por fallback: {selected}")
    
    return selected

def generate_adaptive_config(model_type: ModelType, content_analysis: Dict, 
                           previous_attempts: List) -> Dict[str, Any]:
    """Genera configuración adaptativa para el modelo seleccionado"""
    
    # Configuración base por modelo
    base_configs = {
        ModelType.MISTRAL_LOCAL: {
            'temperature': 0.7,
            'maxTokens': 512,
            'topP': 0.9
        },
        ModelType.LLAMA_LOCAL: {
            'temperature': 0.6,
            'maxTokens': 768,
            'topP': 0.85
        },
        ModelType.DEEPSEEK_LOCAL: {
            'temperature': 0.3,
            'maxTokens': 512,
            'topP': 0.8
        }
    }
    
    config = base_configs.get(model_type, base_configs[ModelType.MISTRAL_LOCAL]).copy()
    
    # Ajustes por complejidad
    complexity = content_analysis['complexity_score']
    if complexity > 2.0:
        config['maxTokens'] = min(config['maxTokens'] * 1.5, 1024)
        config['temperature'] = max(config['temperature'] - 0.1, 0.1)
    elif complexity < 1.0:
        config['maxTokens'] = max(config['maxTokens'] * 0.8, 256)
    
    # Ajustes por historial de fallos
    if previous_attempts:
        recent_failures = [a for a in previous_attempts[-3:] if a.get('score', 0) < 0.6]
        if len(recent_failures) >= 2:
            # Incrementar creatividad si hay fallos recientes
            config['temperature'] = min(config['temperature'] + 0.2, 0.9)
            config['maxTokens'] = min(config['maxTokens'] * 1.3, 1024)
    
    # Configuración de tracking
    config.update({
        'tags': ['adaptive', f'model_{model_type.value}', f'complexity_{complexity:.1f}'],
        'confidence': content_analysis['confidence'],
        'adaptation_reason': f"Content: {content_analysis['dominant_category']}, Complexity: {complexity:.1f}"
    })
    
    return config

# ============================================================================
# Nodos de Retry con Langwatch
# ============================================================================

async def intelligent_retry_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo que maneja retry inteligente con tracking de Langwatch
    """
    try:
        session_id = state.get('session_id')
        current_score = state.get('score', 0)
        previous_attempts = state.get('previous_attempts', [])
        max_retries = state.get('max_retries', 3)
        
        logger.info(f"🔄 Analizando retry para sesión {session_id}")
        
        # Análisis de retry
        retry_decision = analyze_retry_decision(
            current_score,
            previous_attempts,
            max_retries
        )
        
        # Trackear intento de retry
        retry_info = {
            'session_id': session_id,
            'attempt_number': len(previous_attempts) + 1,
            'current_score': current_score,
            'retry_recommended': retry_decision['should_retry'],
            'strategy': retry_decision.get('strategy', 'standard'),
            'reasoning': retry_decision.get('reasoning', '')
        }
        
        await trackRetryAttempt(session_id, retry_info)
        
        if retry_decision['should_retry']:
            # Preparar contexto de retry
            retry_context = {
                'previous_attempts': previous_attempts,
                'apply_contradiction': retry_decision.get('apply_contradiction', False),
                'contradiction_intensity': retry_decision.get('contradiction_intensity', 'moderate'),
                'strategy': retry_decision['strategy'],
                'modified_approach': retry_decision.get('modified_approach', False)
            }
            
            logger.info(f"✅ Retry autorizado: estrategia {retry_decision['strategy']}")
            
            return {
                'should_retry': True,
                'retry_context': retry_context,
                'retry_strategy': retry_decision['strategy'],
                'metadata': {
                    'retry_analysis': retry_decision,
                    'retry_timestamp': time.time()
                }
            }
        
        else:
            logger.info(f"❌ Retry no recomendado: {retry_decision.get('reasoning', 'Score suficiente')}")
            
            return {
                'should_retry': False,
                'retry_context': None,
                'final_result': True,
                'metadata': {
                    'retry_analysis': retry_decision,
                    'final_timestamp': time.time()
                }
            }
    
    except Exception as e:
        logger.error(f"❌ Error en intelligent_retry_node: {str(e)}")
        return {
            'should_retry': False,
            'retry_context': None,
            'final_result': True,
            'metadata': {'error': str(e)}
        }

def analyze_retry_decision(current_score: float, previous_attempts: List, max_retries: int) -> Dict[str, Any]:
    """Analiza si realizar retry y con qué estrategia"""
    
    attempt_count = len(previous_attempts) + 1
    
    # Decisión básica
    if attempt_count >= max_retries:
        return {
            'should_retry': False,
            'reasoning': f'Máximo de intentos alcanzado ({max_retries})'
        }
    
    if current_score >= 0.8:
        return {
            'should_retry': False,
            'reasoning': f'Score suficientemente alto ({current_score:.2f})'
        }
    
    # Análisis de tendencia
    if previous_attempts:
        previous_scores = [a.get('score', 0) for a in previous_attempts]
        
        if len(previous_scores) >= 2:
            recent_trend = previous_scores[-1] - previous_scores[-2]
            overall_trend = previous_scores[-1] - previous_scores[0]
            
            if recent_trend < -0.1:
                return {
                    'should_retry': False,
                    'reasoning': 'Tendencia decreciente detectada'
                }
        
        # Detectar estancamiento
        if len(previous_scores) >= 2 and all(abs(s - previous_scores[0]) < 0.1 for s in previous_scores):
            strategy = 'contradiction_escalation'
            apply_contradiction = True
            intensity = 'strong' if attempt_count > 2 else 'moderate'
        else:
            strategy = 'standard_retry'
            apply_contradiction = current_score < 0.5
            intensity = 'mild'
    
    else:
        strategy = 'first_retry'
        apply_contradiction = current_score < 0.4
        intensity = 'mild'
    
    return {
        'should_retry': True,
        'strategy': strategy,
        'apply_contradiction': apply_contradiction,
        'contradiction_intensity': intensity,
        'reasoning': f'Score bajo ({current_score:.2f}), estrategia: {strategy}'
    }

# ============================================================================
# Nodos de Health Check
# ============================================================================

async def model_health_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo que verifica la salud de todos los modelos locales
    """
    try:
        logger.info("🏥 Verificando salud de modelos locales")
        
        # Health check de modelos
        health_status = await healthCheckModels()
        
        # Verificar wrappers
        wrapper_status = {}
        for model_type in [ModelType.MISTRAL_LOCAL, ModelType.LLAMA_LOCAL, ModelType.DEEPSEEK_LOCAL]:
            try:
                wrapper = get_model_wrapper(model_type)
                wrapper_status[model_type.value] = True
            except Exception as e:
                wrapper_status[model_type.value] = False
                logger.warning(f"⚠️ Wrapper {model_type} no disponible: {str(e)}")
        
        # Determinar modelos disponibles
        available_models = [
            model for model, healthy in health_status.items() 
            if healthy and wrapper_status.get(model, False)
        ]
        
        # Estado general del sistema
        system_healthy = len(available_models) > 0
        
        logger.info(f"✅ Health check completado: {len(available_models)}/{len(health_status)} modelos disponibles")
        
        return {
            'system_healthy': system_healthy,
            'model_health': health_status,
            'wrapper_status': wrapper_status,
            'available_models': available_models,
            'metadata': {
                'health_check_timestamp': time.time(),
                'total_models_checked': len(health_status)
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Error en model_health_check_node: {str(e)}")
        return {
            'system_healthy': False,
            'model_health': {},
            'wrapper_status': {},
            'available_models': [],
            'metadata': {'error': str(e)}
        }

# ============================================================================
# Exportar Nodos
# ============================================================================

__all__ = [
    'local_llm_execution_node',
    'adaptive_model_selection_node',
    'intelligent_retry_node',
    'model_health_check_node',
    'get_model_wrapper',
    'analyze_prompt_content',
    'analyze_historical_performance',
    'select_optimal_model',
    'generate_adaptive_config',
    'analyze_retry_decision'
]

