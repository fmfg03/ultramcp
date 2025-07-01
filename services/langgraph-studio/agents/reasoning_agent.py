"""
Agente de Razonamiento LangGraph MCP

Migra la funcionalidad del reasoningShell.js a un agente LangGraph nativo,
manteniendo toda la lógica de análisis y planificación de tareas.
"""

import sys
import os
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from langgraph_system.schemas.mcp_schemas import (
    ReasoningInput, ReasoningOutput, ReasoningState,
    TaskComplexity, ModelType
)

# Importar servicios existentes
try:
    from backend.src.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# ============================================================================
# Nodos del Agente de Razonamiento
# ============================================================================

def analyze_request_node(state: ReasoningState) -> Dict[str, Any]:
    """
    Nodo que analiza el request inicial y determina complejidad
    """
    try:
        request = state['request']
        session_id = state.get('session_id', f"reasoning_{hash(request) % 10000}")
        
        logger.info(f"🧠 Analizando request en sesión {session_id}: {request[:100]}...")
        
        # Análisis de complejidad basado en palabras clave y longitud
        complexity_indicators = {
            'simple': ['qué es', 'define', 'explica brevemente', 'resume'],
            'moderate': ['cómo', 'pasos', 'proceso', 'implementar', 'crear'],
            'complex': ['diseña', 'arquitectura', 'sistema completo', 'integración'],
            'expert': ['optimiza', 'escalable', 'producción', 'enterprise', 'migración']
        }
        
        request_lower = request.lower()
        complexity_scores = {}
        
        for level, keywords in complexity_indicators.items():
            score = sum(1 for keyword in keywords if keyword in request_lower)
            complexity_scores[level] = score
        
        # Determinar complejidad basada en scores y longitud
        max_score_level = max(complexity_scores, key=complexity_scores.get)
        request_length = len(request.split())
        
        if request_length > 100 or 'sistema' in request_lower:
            estimated_complexity = TaskComplexity.COMPLEX
        elif request_length > 50 or complexity_scores[max_score_level] > 0:
            estimated_complexity = TaskComplexity.MODERATE
        else:
            estimated_complexity = TaskComplexity.SIMPLE
        
        # Recomendar modelo basado en complejidad y contenido
        if 'matemática' in request_lower or 'cálculo' in request_lower or 'ecuación' in request_lower:
            recommended_model = ModelType.DEEPSEEK_LOCAL
        elif estimated_complexity in [TaskComplexity.COMPLEX, TaskComplexity.EXPERT]:
            recommended_model = ModelType.LLAMA_LOCAL
        else:
            recommended_model = ModelType.MISTRAL_LOCAL
        
        logger.info(f"📊 Complejidad estimada: {estimated_complexity}, Modelo recomendado: {recommended_model}")
        
        return {
            'session_id': session_id,
            'estimated_complexity': estimated_complexity,
            'recommended_model': recommended_model,
            'metadata': {
                'analysis_timestamp': __import__('time').time(),
                'complexity_scores': complexity_scores,
                'request_length': request_length
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en analyze_request_node: {str(e)}")
        return {
            'session_id': state.get('session_id', 'error_session'),
            'estimated_complexity': TaskComplexity.SIMPLE,
            'recommended_model': ModelType.AUTO,
            'metadata': {'error': str(e)}
        }

def create_plan_node(state: ReasoningState) -> Dict[str, Any]:
    """
    Nodo que crea el plan de ejecución y subtareas
    """
    try:
        request = state['request']
        complexity = state.get('estimated_complexity', TaskComplexity.SIMPLE)
        session_id = state['session_id']
        
        logger.info(f"📋 Creando plan para complejidad {complexity} en sesión {session_id}")
        
        # Crear plan basado en complejidad
        if complexity == TaskComplexity.SIMPLE:
            plan = {
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
            
        elif complexity == TaskComplexity.MODERATE:
            plan = {
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
                    'description': f"Implementar solución para: {request}",
                    'priority': 'high',
                    'estimated_tokens': 300
                },
                {
                    'id': 'validation',
                    'description': f"Validar resultado para: {request}",
                    'priority': 'medium',
                    'estimated_tokens': 100
                }
            ]
            
        else:  # COMPLEX or EXPERT
            plan = {
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
                    'description': f"Diseñar arquitectura para: {request}",
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
                },
                {
                    'id': 'documentation_phase',
                    'description': f"Documentar solución: {request}",
                    'priority': 'medium',
                    'estimated_tokens': 150
                }
            ]
        
        logger.info(f"✅ Plan creado con {len(subtasks)} subtareas")
        
        return {
            'plan': plan,
            'subtasks': subtasks,
            'metadata': {
                **state.get('metadata', {}),
                'plan_creation_timestamp': __import__('time').time(),
                'total_estimated_tokens': sum(task.get('estimated_tokens', 0) for task in subtasks)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en create_plan_node: {str(e)}")
        return {
            'plan': {'type': 'error', 'steps': ['retry']},
            'subtasks': [],
            'metadata': {**state.get('metadata', {}), 'error': str(e)}
        }

def finalize_reasoning_node(state: ReasoningState) -> Dict[str, Any]:
    """
    Nodo que finaliza el razonamiento y prepara el output
    """
    try:
        session_id = state['session_id']
        plan = state.get('plan', {})
        subtasks = state.get('subtasks', [])
        
        logger.info(f"🎯 Finalizando razonamiento para sesión {session_id}")
        
        # Validar que tenemos un plan válido
        success = bool(plan and subtasks)
        
        if success:
            logger.info(f"✅ Razonamiento completado exitosamente: {len(subtasks)} subtareas planificadas")
        else:
            logger.warning(f"⚠️ Razonamiento incompleto para sesión {session_id}")
        
        return {
            'success': success,
            'metadata': {
                **state.get('metadata', {}),
                'reasoning_completed_timestamp': __import__('time').time(),
                'total_reasoning_duration': __import__('time').time() - state.get('metadata', {}).get('analysis_timestamp', __import__('time').time())
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en finalize_reasoning_node: {str(e)}")
        return {
            'success': False,
            'metadata': {**state.get('metadata', {}), 'error': str(e)}
        }

# ============================================================================
# Construcción del Grafo
# ============================================================================

def create_reasoning_graph():
    """
    Crea el grafo de razonamiento LangGraph
    """
    # Crear el grafo con schemas explícitos
    builder = StateGraph(
        ReasoningState,
        input=ReasoningInput,
        output=ReasoningOutput
    )
    
    # Agregar nodos
    builder.add_node("analyze_request", analyze_request_node)
    builder.add_node("create_plan", create_plan_node)
    builder.add_node("finalize_reasoning", finalize_reasoning_node)
    
    # Definir flujo
    builder.add_edge(START, "analyze_request")
    builder.add_edge("analyze_request", "create_plan")
    builder.add_edge("create_plan", "finalize_reasoning")
    builder.add_edge("finalize_reasoning", END)
    
    # Compilar con memoria
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    return graph

# ============================================================================
# Instancia del Grafo (para langgraph.json)
# ============================================================================

graph = create_reasoning_graph()

# ============================================================================
# Funciones de Utilidad
# ============================================================================

def test_reasoning_agent():
    """
    Función de prueba para el agente de razonamiento
    """
    test_cases = [
        {
            'request': '¿Qué es el protocolo MCP?',
            'expected_complexity': TaskComplexity.SIMPLE
        },
        {
            'request': 'Crea una API REST para gestionar usuarios con autenticación JWT',
            'expected_complexity': TaskComplexity.MODERATE
        },
        {
            'request': 'Diseña un sistema de microservicios escalable para e-commerce con integración de pagos, inventario y notificaciones',
            'expected_complexity': TaskComplexity.COMPLEX
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🧪 Test Case {i+1}: {test_case['request'][:50]}...")
        
        try:
            result = graph.invoke({
                'request': test_case['request'],
                'session_id': f'test_session_{i+1}'
            })
            
            print(f"✅ Resultado: {result['success']}")
            print(f"📊 Complejidad: {result['estimated_complexity']}")
            print(f"🤖 Modelo recomendado: {result['recommended_model']}")
            print(f"📋 Subtareas: {len(result['subtasks'])}")
            
        except Exception as e:
            print(f"❌ Error en test case {i+1}: {str(e)}")

if __name__ == "__main__":
    print("🧠 Agente de Razonamiento LangGraph MCP")
    print("=" * 50)
    test_reasoning_agent()

