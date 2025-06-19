"""
Agente Constructor LangGraph MCP

Migra la funcionalidad del builder y ejecuta tareas usando LLMs locales
con integración completa de Langwatch y contradicción explícita.
"""

import sys
import os
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from langgraph_system.schemas.mcp_schemas import (
    BuilderInput, BuilderOutput, BuilderState,
    ModelType, LangwatchMetadata
)

# Importar servicios existentes
try:
    from backend.src.utils.logger import logger
    from adapters.enhancedLocalLLMAdapter import callLocalModelWithLangwatch
    from backend.src.services.contradictionService import detectContradiction, generateContradictionPrompt
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    
    # Mock functions para desarrollo
    async def callLocalModelWithLangwatch(model_type, prompt, options=None):
        return {
            'success': True,
            'response': f"Mock response for {model_type}: {prompt[:50]}...",
            'metadata': {
                'langwatchTracking': {
                    'trackingId': f'mock_{hash(prompt) % 10000}',
                    'score': 0.8,
                    'contradiction': {'triggered': False},
                    'tracked': True
                },
                'duration': 1500
            },
            'tokenUsage': {'totalTokens': 150}
        }
    
    def detectContradiction(attempts, current_score):
        return len(attempts) > 2 and current_score < 0.6
    
    def generateContradictionPrompt(original_prompt, attempts, intensity='moderate'):
        return f"CONTRADICCIÓN EXPLÍCITA: {original_prompt}\n\nIntentos previos fallaron. Explica por qué y reintenta."

# ============================================================================
# Nodos del Agente Constructor
# ============================================================================

def prepare_execution_node(state: BuilderState) -> Dict[str, Any]:
    """
    Nodo que prepara la ejecución analizando el plan y subtareas
    """
    try:
        request = state['request']
        plan = state.get('plan', {})
        subtasks = state.get('subtasks', [])
        session_id = state.get('session_id', f"builder_{hash(request) % 10000}")
        model_type = state.get('model_type', ModelType.AUTO)
        
        logger.info(f"🔧 Preparando ejecución en sesión {session_id}")
        logger.info(f"📋 Plan: {plan.get('type', 'unknown')}, Subtareas: {len(subtasks)}")
        
        # Determinar modelo si es AUTO
        if model_type == ModelType.AUTO:
            request_lower = request.lower()
            if any(keyword in request_lower for keyword in ['matemática', 'cálculo', 'ecuación', 'demostrar']):
                model_type = ModelType.DEEPSEEK_LOCAL
            elif any(keyword in request_lower for keyword in ['sistema', 'arquitectura', 'complejo']):
                model_type = ModelType.LLAMA_LOCAL
            else:
                model_type = ModelType.MISTRAL_LOCAL
        
        # Preparar contexto de ejecución
        execution_context = {
            'model_type': model_type,
            'plan_type': plan.get('type', 'direct_execution'),
            'total_subtasks': len(subtasks),
            'estimated_duration': plan.get('estimated_duration', 60),
            'requires_iteration': plan.get('requires_iteration', False)
        }
        
        # Inicializar logs de ejecución
        execution_log = [
            {
                'timestamp': __import__('time').time(),
                'event': 'execution_prepared',
                'details': execution_context
            }
        ]
        
        logger.info(f"✅ Ejecución preparada con modelo {model_type}")
        
        return {
            'session_id': session_id,
            'model_type': model_type,
            'execution_log': execution_log,
            'metadata': {
                'execution_context': execution_context,
                'preparation_timestamp': __import__('time').time()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en prepare_execution_node: {str(e)}")
        return {
            'session_id': state.get('session_id', 'error_session'),
            'model_type': ModelType.MISTRAL_LOCAL,
            'execution_log': [{'event': 'preparation_error', 'error': str(e)}],
            'metadata': {'error': str(e)}
        }

async def execute_with_llm_node(state: BuilderState) -> Dict[str, Any]:
    """
    Nodo que ejecuta la tarea usando LLMs locales con Langwatch
    """
    try:
        request = state['request']
        model_type = state['model_type']
        session_id = state['session_id']
        subtasks = state.get('subtasks', [])
        retry_context = state.get('retry_context', {})
        execution_log = state.get('execution_log', [])
        
        logger.info(f"🤖 Ejecutando con modelo {model_type} en sesión {session_id}")
        
        # Determinar si aplicar contradicción
        previous_attempts = retry_context.get('previous_attempts', [])
        current_attempt = len(previous_attempts) + 1
        
        # Construir prompt basado en subtareas o request directo
        if subtasks:
            prompt_parts = [f"Tarea principal: {request}\n"]
            prompt_parts.append("Subtareas a completar:")
            for i, subtask in enumerate(subtasks, 1):
                prompt_parts.append(f"{i}. {subtask.get('description', subtask.get('id', 'Subtarea'))}")
            prompt_parts.append("\nProporciona una solución completa y detallada.")
            execution_prompt = "\n".join(prompt_parts)
        else:
            execution_prompt = request
        
        # Aplicar contradicción si es necesario
        if previous_attempts:
            last_score = previous_attempts[-1].get('score', 0.5)
            if detectContradiction(previous_attempts, last_score):
                logger.info(f"🔥 Aplicando contradicción explícita (intento {current_attempt})")
                execution_prompt = generateContradictionPrompt(
                    execution_prompt, 
                    previous_attempts,
                    intensity='moderate' if current_attempt <= 3 else 'strong'
                )
                
                execution_log.append({
                    'timestamp': __import__('time').time(),
                    'event': 'contradiction_applied',
                    'attempt': current_attempt,
                    'previous_score': last_score
                })
        
        # Ejecutar con LLM local y Langwatch
        start_time = __import__('time').time()
        
        llm_result = await callLocalModelWithLangwatch(
            model_type,
            execution_prompt,
            {
                'sessionId': session_id,
                'maxTokens': 512,
                'tags': ['builder', 'execution', f'attempt_{current_attempt}']
            }
        )
        
        execution_duration = (__import__('time').time() - start_time) * 1000
        
        # Procesar resultado
        if llm_result['success']:
            result = llm_result['response']
            langwatch_metadata = llm_result.get('metadata', {}).get('langwatchTracking')
            
            # Crear artifacts basados en el resultado
            artifacts = [
                {
                    'type': 'text_response',
                    'content': result,
                    'metadata': {
                        'model_used': model_type,
                        'tokens_used': llm_result.get('tokenUsage', {}).get('totalTokens', 0),
                        'execution_time_ms': execution_duration
                    }
                }
            ]
            
            # Si hay subtareas, intentar extraer resultados por subtarea
            if subtasks and len(result.split('\n\n')) >= len(subtasks):
                result_sections = result.split('\n\n')
                for i, subtask in enumerate(subtasks):
                    if i < len(result_sections):
                        artifacts.append({
                            'type': 'subtask_result',
                            'subtask_id': subtask.get('id', f'subtask_{i}'),
                            'content': result_sections[i],
                            'metadata': {'subtask_description': subtask.get('description', '')}
                        })
            
            execution_log.append({
                'timestamp': __import__('time').time(),
                'event': 'llm_execution_success',
                'model': model_type,
                'duration_ms': execution_duration,
                'tokens': llm_result.get('tokenUsage', {}).get('totalTokens', 0),
                'score': langwatch_metadata.get('score') if langwatch_metadata else None
            })
            
            logger.info(f"✅ Ejecución exitosa con {model_type}: {len(result)} caracteres generados")
            
            return {
                'success': True,
                'result': result,
                'artifacts': artifacts,
                'execution_log': execution_log,
                'langwatch_metadata': langwatch_metadata
            }
            
        else:
            error_msg = llm_result.get('error', 'Error desconocido en LLM')
            execution_log.append({
                'timestamp': __import__('time').time(),
                'event': 'llm_execution_error',
                'error': error_msg,
                'model': model_type
            })
            
            logger.error(f"❌ Error en ejecución con {model_type}: {error_msg}")
            
            return {
                'success': False,
                'result': f"Error en ejecución: {error_msg}",
                'artifacts': [],
                'execution_log': execution_log,
                'langwatch_metadata': None
            }
        
    except Exception as e:
        logger.error(f"❌ Error en execute_with_llm_node: {str(e)}")
        return {
            'success': False,
            'result': f"Error interno: {str(e)}",
            'artifacts': [],
            'execution_log': state.get('execution_log', []) + [
                {'event': 'execution_error', 'error': str(e)}
            ],
            'langwatch_metadata': None
        }

def finalize_builder_node(state: BuilderState) -> Dict[str, Any]:
    """
    Nodo que finaliza la construcción y prepara el output
    """
    try:
        session_id = state['session_id']
        success = state.get('success', False)
        result = state.get('result', '')
        artifacts = state.get('artifacts', [])
        execution_log = state.get('execution_log', [])
        langwatch_metadata = state.get('langwatch_metadata')
        
        logger.info(f"🎯 Finalizando construcción para sesión {session_id}")
        
        # Agregar log final
        final_log_entry = {
            'timestamp': __import__('time').time(),
            'event': 'builder_finalized',
            'success': success,
            'artifacts_count': len(artifacts),
            'result_length': len(result) if result else 0
        }
        
        execution_log.append(final_log_entry)
        
        if success:
            logger.info(f"✅ Construcción completada exitosamente: {len(artifacts)} artifacts generados")
        else:
            logger.warning(f"⚠️ Construcción completada con errores para sesión {session_id}")
        
        return {
            'execution_log': execution_log,
            'metadata': {
                **state.get('metadata', {}),
                'builder_completed_timestamp': __import__('time').time(),
                'final_success': success
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en finalize_builder_node: {str(e)}")
        return {
            'execution_log': state.get('execution_log', []) + [
                {'event': 'finalization_error', 'error': str(e)}
            ],
            'metadata': {**state.get('metadata', {}), 'error': str(e)}
        }

# ============================================================================
# Construcción del Grafo
# ============================================================================

def create_builder_graph():
    """
    Crea el grafo de construcción LangGraph
    """
    # Crear el grafo con schemas explícitos
    builder = StateGraph(
        BuilderState,
        input=BuilderInput,
        output=BuilderOutput
    )
    
    # Agregar nodos
    builder.add_node("prepare_execution", prepare_execution_node)
    builder.add_node("execute_with_llm", execute_with_llm_node)
    builder.add_node("finalize_builder", finalize_builder_node)
    
    # Definir flujo
    builder.add_edge(START, "prepare_execution")
    builder.add_edge("prepare_execution", "execute_with_llm")
    builder.add_edge("execute_with_llm", "finalize_builder")
    builder.add_edge("finalize_builder", END)
    
    # Compilar con memoria
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    return graph

# ============================================================================
# Instancia del Grafo (para langgraph.json)
# ============================================================================

graph = create_builder_graph()

# ============================================================================
# Funciones de Utilidad
# ============================================================================

async def test_builder_agent():
    """
    Función de prueba para el agente constructor
    """
    test_cases = [
        {
            'request': 'Explica qué es el protocolo MCP',
            'model_type': ModelType.MISTRAL_LOCAL
        },
        {
            'request': 'Resuelve la ecuación: 2x + 5 = 15',
            'model_type': ModelType.DEEPSEEK_LOCAL
        },
        {
            'request': 'Crea una función Python para validar emails',
            'plan': {'type': 'structured_execution'},
            'subtasks': [
                {'id': 'design', 'description': 'Diseñar la función de validación'},
                {'id': 'implement', 'description': 'Implementar la función'},
                {'id': 'test', 'description': 'Crear casos de prueba'}
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🧪 Test Case {i+1}: {test_case['request'][:50]}...")
        
        try:
            result = await graph.ainvoke({
                'request': test_case['request'],
                'session_id': f'test_builder_{i+1}',
                'model_type': test_case.get('model_type', ModelType.AUTO),
                'plan': test_case.get('plan'),
                'subtasks': test_case.get('subtasks')
            })
            
            print(f"✅ Resultado: {result['success']}")
            print(f"📝 Respuesta: {result['result'][:100]}...")
            print(f"📦 Artifacts: {len(result['artifacts'])}")
            print(f"📊 Logs: {len(result['execution_log'])}")
            
            if result.get('langwatch_metadata'):
                lw = result['langwatch_metadata']
                print(f"🔍 Langwatch Score: {lw.get('score', 'N/A')}")
                print(f"🔥 Contradicción: {lw.get('contradiction', {}).get('triggered', False)}")
            
        except Exception as e:
            print(f"❌ Error en test case {i+1}: {str(e)}")

if __name__ == "__main__":
    import asyncio
    print("🔧 Agente Constructor LangGraph MCP")
    print("=" * 50)
    asyncio.run(test_builder_agent())

