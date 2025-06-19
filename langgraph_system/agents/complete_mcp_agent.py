"""
Agente MCP Completo con LangGraph

Integra todos los nodos y servicios en un agente LangGraph completo
que se expone automáticamente como herramienta MCP.
"""

import sys
import os
from typing import Dict, Any, List, Optional, TypedDict
import time

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from langgraph.graph import StateGraph, START, END
from langgraph.graph import Graph

# Importar schemas
from langgraph_system.schemas.mcp_schemas import (
    MCPAgentInput, MCPAgentOutput, MCPAgentState,
    TaskComplexity, ModelType, ContradictionInfo
)

# Importar nodos
from langgraph_system.nodes.reasoning_reward_nodes import (
    enhanced_reasoning_node, enhanced_reward_node, contradiction_analysis_node
)
from langgraph_system.nodes.llm_langwatch_nodes import (
    local_llm_execution_node, adaptive_model_selection_node,
    intelligent_retry_node, model_health_check_node
)

# Importar servicios
try:
    from backend.src.utils.logger import logger
    from backend.src.services.memoryService import saveStep, getContext
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    
    async def saveStep(session_id, step_data):
        return {'success': True}
    
    async def getContext(session_id):
        return {'success': True, 'context': {'previous_attempts': []}}

# ============================================================================
# Nodos de Control de Flujo
# ============================================================================

async def initialization_node(state: MCPAgentState) -> Dict[str, Any]:
    """Nodo de inicialización del agente MCP"""
    try:
        request = state['request']
        session_id = state.get('session_id', f"mcp_{hash(request) % 10000}")
        
        logger.info(f"🚀 Iniciando agente MCP para sesión {session_id}")
        
        # Inicializar contexto
        context_result = await getContext(session_id)
        historical_context = context_result.get('context', {}) if context_result.get('success') else {}
        
        # Guardar paso de inicialización
        init_step = {
            'type': 'initialization',
            'timestamp': time.time(),
            'request': request,
            'session_id': session_id
        }
        
        await saveStep(session_id, init_step)
        
        return {
            'session_id': session_id,
            'context': historical_context,
            'previous_attempts': historical_context.get('previous_attempts', []),
            'initialization_timestamp': time.time(),
            'status': 'initialized'
        }
    
    except Exception as e:
        logger.error(f"❌ Error en initialization_node: {str(e)}")
        return {
            'session_id': f"error_{hash(str(e)) % 10000}",
            'context': {},
            'previous_attempts': [],
            'initialization_timestamp': time.time(),
            'status': 'error',
            'error': str(e)
        }

async def finalization_node(state: MCPAgentState) -> Dict[str, Any]:
    """Nodo de finalización del agente MCP"""
    try:
        session_id = state.get('session_id')
        final_result = state.get('result', state.get('response', ''))
        final_score = state.get('score', 0)
        
        logger.info(f"🏁 Finalizando agente MCP para sesión {session_id}")
        
        # Preparar resultado final
        final_output = {
            'success': True,
            'result': final_result,
            'score': final_score,
            'session_id': session_id,
            'metadata': {
                'finalization_timestamp': time.time(),
                'total_attempts': len(state.get('previous_attempts', [])) + 1,
                'final_model_used': state.get('model_used', 'unknown'),
                'langwatch_tracking': state.get('langwatch_metadata', {}),
                'contradiction_applied': state.get('contradiction_applied', False)
            }
        }
        
        # Guardar paso final
        final_step = {
            'type': 'finalization',
            'timestamp': time.time(),
            'final_result': final_result,
            'final_score': final_score,
            'session_completed': True
        }
        
        await saveStep(session_id, final_step)
        
        logger.info(f"✅ Sesión {session_id} completada con score {final_score:.2f}")
        
        return final_output
    
    except Exception as e:
        logger.error(f"❌ Error en finalization_node: {str(e)}")
        return {
            'success': False,
            'result': f"Error en finalización: {str(e)}",
            'score': 0.0,
            'session_id': state.get('session_id', 'error_session'),
            'metadata': {'error': str(e)}
        }

# ============================================================================
# Funciones de Decisión (Conditional Edges)
# ============================================================================

def should_retry_decision(state: MCPAgentState) -> str:
    """Decide si continuar con retry o finalizar"""
    should_retry = state.get('should_retry', False)
    max_attempts_reached = state.get('metadata', {}).get('retry_analysis', {}).get('max_attempts_reached', False)
    
    if should_retry and not max_attempts_reached:
        return "retry"
    else:
        return "finalize"

def model_selection_decision(state: MCPAgentState) -> str:
    """Decide si usar selección adaptativa o modelo específico"""
    model_type = state.get('model_type', ModelType.AUTO)
    
    if model_type == ModelType.AUTO:
        return "adaptive_selection"
    else:
        return "direct_execution"

def health_check_decision(state: MCPAgentState) -> str:
    """Decide si el sistema está saludable para continuar"""
    system_healthy = state.get('system_healthy', True)
    available_models = state.get('available_models', [])
    
    if system_healthy and available_models:
        return "continue"
    else:
        return "error"

# ============================================================================
# Construcción del Grafo
# ============================================================================

def create_mcp_agent_graph() -> StateGraph:
    """Crea el grafo completo del agente MCP"""
    
    # Crear el grafo con el estado tipado
    workflow = StateGraph(
        MCPAgentState,
        input=MCPAgentInput,
        output=MCPAgentOutput
    )
    
    # Agregar nodos
    workflow.add_node("initialize", initialization_node)
    workflow.add_node("health_check", model_health_check_node)
    workflow.add_node("reasoning", enhanced_reasoning_node)
    workflow.add_node("adaptive_selection", adaptive_model_selection_node)
    workflow.add_node("execute_llm", local_llm_execution_node)
    workflow.add_node("evaluate", enhanced_reward_node)
    workflow.add_node("contradiction_analysis", contradiction_analysis_node)
    workflow.add_node("retry_analysis", intelligent_retry_node)
    workflow.add_node("finalize", finalization_node)
    
    # Flujo principal
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "health_check")
    
    # Decisión de salud del sistema
    workflow.add_conditional_edges(
        "health_check",
        health_check_decision,
        {
            "continue": "reasoning",
            "error": "finalize"
        }
    )
    
    workflow.add_edge("reasoning", "adaptive_selection")
    workflow.add_edge("adaptive_selection", "execute_llm")
    workflow.add_edge("execute_llm", "evaluate")
    workflow.add_edge("evaluate", "contradiction_analysis")
    workflow.add_edge("contradiction_analysis", "retry_analysis")
    
    # Decisión de retry
    workflow.add_conditional_edges(
        "retry_analysis",
        should_retry_decision,
        {
            "retry": "adaptive_selection",  # Volver a selección de modelo
            "finalize": "finalize"
        }
    )
    
    workflow.add_edge("finalize", END)
    
    return workflow

# ============================================================================
# Agente MCP Principal
# ============================================================================

class MCPAgent:
    """Agente MCP completo con LangGraph"""
    
    def __init__(self):
        self.graph = create_mcp_agent_graph()
        self.compiled_graph = None
        self._compile_graph()
    
    def _compile_graph(self):
        """Compila el grafo para ejecución"""
        try:
            self.compiled_graph = self.graph.compile()
            logger.info("✅ Grafo MCP compilado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error compilando grafo MCP: {str(e)}")
            raise
    
    async def execute(self, request: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecuta el agente MCP completo"""
        try:
            # Preparar input
            input_data = {
                'request': request,
                'options': options or {},
                'session_id': options.get('session_id') if options else None
            }
            
            logger.info(f"🎯 Ejecutando agente MCP: {request[:100]}...")
            
            # Ejecutar grafo
            result = await self.compiled_graph.ainvoke(input_data)
            
            logger.info(f"✅ Agente MCP completado: {result.get('success', False)}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error ejecutando agente MCP: {str(e)}")
            return {
                'success': False,
                'result': f"Error interno del agente: {str(e)}",
                'score': 0.0,
                'metadata': {'error': str(e)}
            }
    
    async def stream_execute(self, request: str, options: Optional[Dict[str, Any]] = None):
        """Ejecuta el agente MCP con streaming"""
        try:
            input_data = {
                'request': request,
                'options': options or {},
                'session_id': options.get('session_id') if options else None
            }
            
            logger.info(f"🌊 Streaming agente MCP: {request[:100]}...")
            
            async for chunk in self.compiled_graph.astream(input_data):
                yield chunk
        
        except Exception as e:
            logger.error(f"❌ Error en streaming MCP: {str(e)}")
            yield {
                'error': str(e),
                'success': False
            }
    
    def get_graph_visualization(self) -> str:
        """Obtiene visualización del grafo"""
        try:
            # Esto requeriría graphviz o similar para visualización completa
            nodes = list(self.graph.nodes.keys())
            edges = [(edge.source, edge.target) for edge in self.graph.edges]
            
            viz = "Grafo MCP Agent:\n"
            viz += f"Nodos: {', '.join(nodes)}\n"
            viz += f"Conexiones: {len(edges)} edges\n"
            
            for source, target in edges:
                viz += f"  {source} → {target}\n"
            
            return viz
        
        except Exception as e:
            return f"Error generando visualización: {str(e)}"

# ============================================================================
# Instancia Global del Agente
# ============================================================================

# Crear instancia global del agente MCP
mcp_agent = None

def get_mcp_agent() -> MCPAgent:
    """Obtiene la instancia global del agente MCP"""
    global mcp_agent
    if mcp_agent is None:
        mcp_agent = MCPAgent()
    return mcp_agent

# ============================================================================
# Funciones de Conveniencia
# ============================================================================

async def execute_mcp_task(request: str, **options) -> Dict[str, Any]:
    """Función de conveniencia para ejecutar tareas MCP"""
    agent = get_mcp_agent()
    return await agent.execute(request, options)

async def stream_mcp_task(request: str, **options):
    """Función de conveniencia para streaming de tareas MCP"""
    agent = get_mcp_agent()
    async for chunk in agent.stream_execute(request, options):
        yield chunk

def get_mcp_graph_info() -> Dict[str, Any]:
    """Obtiene información del grafo MCP"""
    agent = get_mcp_agent()
    return {
        'visualization': agent.get_graph_visualization(),
        'nodes': list(agent.graph.nodes.keys()),
        'compiled': agent.compiled_graph is not None
    }

# ============================================================================
# Exportar
# ============================================================================

__all__ = [
    'MCPAgent',
    'get_mcp_agent',
    'execute_mcp_task',
    'stream_mcp_task',
    'get_mcp_graph_info',
    'create_mcp_agent_graph'
]

