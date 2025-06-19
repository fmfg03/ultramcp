#!/usr/bin/env python3
"""
LangGraph Integration - Sam as MCP Tool
Integra Sam como una herramienta MCP dentro del ecosistema LangGraph de Manus
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

# Definición de la herramienta Sam para LangGraph
SAM_TOOL_DEFINITION = {
    "name": "sam_executor_agent",
    "description": """
    Sam es un agente especializado capaz de ejecutar tareas complejas de forma autónoma.
    
    Capacidades principales:
    - Investigación avanzada usando Perplexity API
    - Generación y análisis de código con LLMs locales (Mistral, Llama, DeepSeek, Qwen)
    - Procesamiento de datos y análisis
    - Ejecución autónoma con fallback automático entre modelos
    - Contexto completo del proyecto MCP
    
    Sam prioriza modelos locales sobre APIs externas para máxima eficiencia y privacidad.
    Puede ejecutar múltiples tareas en lote y manejar dependencias automáticamente.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "task_type": {
                "type": "string",
                "enum": ["research", "coding", "analysis", "creative", "reasoning", "batch"],
                "description": "Tipo de tarea a ejecutar"
            },
            "prompt": {
                "type": "string",
                "description": "Instrucción detallada para Sam"
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "temperature": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.7,
                        "description": "Temperatura para generación (creatividad vs precisión)"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "minimum": 100,
                        "maximum": 16384,
                        "description": "Máximo número de tokens a generar"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium",
                        "description": "Prioridad de la tarea"
                    },
                    "autonomy_level": {
                        "type": "string",
                        "enum": ["supervised", "semi_autonomous", "fully_autonomous"],
                        "default": "semi_autonomous",
                        "description": "Nivel de autonomía para la ejecución"
                    },
                    "preferred_models": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de modelos preferidos en orden de prioridad"
                    },
                    "context": {
                        "type": "object",
                        "description": "Contexto adicional específico para la tarea"
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "IDs de tareas de las que depende esta tarea"
                    },
                    "deadline": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Fecha límite para completar la tarea"
                    },
                    "batch_tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "task_type": {"type": "string"},
                                "priority": {"type": "string"},
                                "context": {"type": "object"}
                            },
                            "required": ["description"]
                        },
                        "description": "Lista de tareas para ejecución en lote (solo para task_type='batch')"
                    }
                },
                "description": "Parámetros específicos de la tarea"
            }
        },
        "required": ["task_type", "prompt"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["success", "error", "escalated", "in_progress"],
                "description": "Estado de la ejecución"
            },
            "result": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Resultado principal de la tarea"
                    },
                    "model_used": {
                        "type": "string",
                        "description": "Modelo que ejecutó la tarea"
                    },
                    "execution_time": {
                        "type": "number",
                        "description": "Tiempo de ejecución en segundos"
                    },
                    "tokens_used": {
                        "type": "integer",
                        "description": "Número de tokens utilizados"
                    },
                    "cost": {
                        "type": "number",
                        "description": "Costo de la ejecución (0 para modelos locales)"
                    },
                    "confidence_score": {
                        "type": "number",
                        "description": "Puntuación de confianza en el resultado"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Metadatos adicionales de la ejecución"
                    }
                },
                "required": ["content"]
            },
            "task_id": {
                "type": "string",
                "description": "ID único de la tarea ejecutada"
            },
            "batch_id": {
                "type": "string",
                "description": "ID del lote (solo para tareas en lote)"
            },
            "error_message": {
                "type": "string",
                "description": "Mensaje de error si la tarea falló"
            },
            "escalation_reason": {
                "type": "string",
                "description": "Razón de escalación si la tarea fue escalada"
            },
            "next_actions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Acciones sugeridas para continuar"
            }
        },
        "required": ["status", "task_id"]
    }
}

@dataclass
class LangGraphNode:
    """Definición de un nodo en LangGraph"""
    id: str
    name: str
    type: str  # "tool", "condition", "start", "end"
    tool_name: Optional[str] = None
    conditions: Optional[Dict[str, str]] = None
    next_nodes: List[str] = None
    
    def __post_init__(self):
        if self.next_nodes is None:
            self.next_nodes = []

@dataclass
class LangGraphEdge:
    """Definición de una arista en LangGraph"""
    from_node: str
    to_node: str
    condition: Optional[str] = None
    condition_value: Optional[str] = None

class SamMCPIntegration:
    """
    Clase principal para integrar Sam como herramienta MCP en LangGraph
    """
    
    def __init__(self):
        self.tool_definition = SAM_TOOL_DEFINITION
        self.execution_history: List[Dict[str, Any]] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Retorna la definición de la herramienta Sam para LangGraph
        """
        return self.tool_definition
    
    async def execute_sam_tool(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la herramienta Sam con los datos de entrada
        """
        try:
            # Validar entrada
            validation_result = self._validate_input(input_data)
            if not validation_result["valid"]:
                return {
                    "status": "error",
                    "task_id": str(uuid.uuid4()),
                    "error_message": validation_result["error"]
                }
            
            # Extraer parámetros
            task_type = input_data["task_type"]
            prompt = input_data["prompt"]
            parameters = input_data.get("parameters", {})
            
            # Generar ID de tarea
            task_id = str(uuid.uuid4())
            
            # Preparar contexto para Sam
            context = await self._prepare_sam_context(parameters.get("context", {}))
            
            # Ejecutar según el tipo de tarea
            if task_type == "batch":
                result = await self._execute_batch_tasks(task_id, parameters, context)
            else:
                result = await self._execute_single_task(task_id, task_type, prompt, parameters, context)
            
            # Registrar ejecución
            self._log_execution(task_id, input_data, result)
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "task_id": str(uuid.uuid4()),
                "error_message": f"Unexpected error: {str(e)}"
            }
            self._log_execution(error_result["task_id"], input_data, error_result)
            return error_result
    
    def _validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida los datos de entrada contra el schema
        """
        required_fields = ["task_type", "prompt"]
        
        for field in required_fields:
            if field not in input_data:
                return {
                    "valid": False,
                    "error": f"Missing required field: {field}"
                }
        
        # Validar task_type
        valid_task_types = ["research", "coding", "analysis", "creative", "reasoning", "batch"]
        if input_data["task_type"] not in valid_task_types:
            return {
                "valid": False,
                "error": f"Invalid task_type. Must be one of: {valid_task_types}"
            }
        
        # Validar batch_tasks si es necesario
        if input_data["task_type"] == "batch":
            parameters = input_data.get("parameters", {})
            if "batch_tasks" not in parameters or not parameters["batch_tasks"]:
                return {
                    "valid": False,
                    "error": "batch_tasks required for task_type='batch'"
                }
        
        return {"valid": True}
    
    async def _prepare_sam_context(self, additional_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara el contexto completo para Sam usando Memory Injection
        """
        try:
            # Importar sistema de memory injection
            import sys
            sys.path.append('/root/supermcp/backend')
            from memory_injection_system import MemoryInjectionSystem
            
            memory_system = MemoryInjectionSystem()
            base_context = memory_system.get_project_state()
            
            # Combinar con contexto adicional
            base_context.update(additional_context)
            
            return base_context
            
        except Exception as e:
            # Fallback a contexto básico
            return {
                "system_info": {"domain": "sam.chat"},
                "agent_status": {"local_models": {}, "services": {}},
                "error": f"Could not load full context: {str(e)}",
                **additional_context
            }
    
    async def _execute_single_task(self, task_id: str, task_type: str, prompt: str, 
                                 parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una sola tarea usando el sistema de autonomía de Sam
        """
        try:
            # Importar sistemas de Sam
            import sys
            sys.path.append('/root/supermcp/backend')
            from agent_autonomy_system import add_autonomous_task, autonomy_system
            from memory_injection_system import MemoryInjectionSystem
            
            # Configurar nivel de autonomía
            autonomy_level = parameters.get("autonomy_level", "semi_autonomous")
            if autonomy_level == "fully_autonomous":
                from agent_autonomy_system import AutonomyLevel
                autonomy_system.autonomy_level = AutonomyLevel.FULLY_AUTONOMOUS
            
            # Añadir tarea al sistema de autonomía
            priority = parameters.get("priority", "medium")
            task_context = {
                "mcp_integration": True,
                "langraph_task_id": task_id,
                **parameters.get("context", {})
            }
            
            sam_task_id = add_autonomous_task(prompt, task_type, priority, task_context)
            
            # Ejecutar loop autónomo
            execution_result = await autonomy_system.execute_autonomous_loop(context)
            
            # Buscar el resultado de nuestra tarea específica
            task_result = None
            for log_entry in execution_result.get("execution_log", []):
                if log_entry.get("task_id") == sam_task_id:
                    task_result = log_entry
                    break
            
            if not task_result:
                return {
                    "status": "error",
                    "task_id": task_id,
                    "error_message": "Task not found in execution log"
                }
            
            # Formatear resultado
            if task_result["status"] == "completed":
                # Obtener detalles completos de la tarea
                task_details = autonomy_system.get_task_details(sam_task_id)
                
                return {
                    "status": "success",
                    "task_id": task_id,
                    "result": {
                        "content": task_details.get("result", ""),
                        "model_used": "sam_autonomous_system",
                        "execution_time": task_result.get("execution_time", 0),
                        "confidence_score": 0.8,  # Score por defecto para tareas completadas
                        "metadata": {
                            "sam_task_id": sam_task_id,
                            "execution_attempts": task_details.get("execution_attempts", 1),
                            "autonomy_level": autonomy_level
                        }
                    }
                }
            elif task_result["status"] == "escalated":
                return {
                    "status": "escalated",
                    "task_id": task_id,
                    "escalation_reason": task_result.get("error", "Task requires manual intervention"),
                    "next_actions": [
                        "Review task requirements",
                        "Provide additional context",
                        "Break down into smaller tasks"
                    ]
                }
            else:  # failed
                return {
                    "status": "error",
                    "task_id": task_id,
                    "error_message": task_result.get("error", "Task execution failed")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "task_id": task_id,
                "error_message": f"Execution error: {str(e)}"
            }
    
    async def _execute_batch_tasks(self, batch_id: str, parameters: Dict[str, Any], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta un lote de tareas usando el sistema de autonomía de Sam
        """
        try:
            # Importar sistemas de Sam
            import sys
            sys.path.append('/root/supermcp/backend')
            from agent_autonomy_system import execute_autonomous_batch
            
            # Preparar tareas para el lote
            batch_tasks = parameters.get("batch_tasks", [])
            formatted_tasks = []
            
            for task_data in batch_tasks:
                formatted_task = {
                    "description": task_data["description"],
                    "task_type": task_data.get("task_type", "general"),
                    "priority": task_data.get("priority", "medium"),
                    "context": {
                        "mcp_integration": True,
                        "langraph_batch_id": batch_id,
                        **task_data.get("context", {})
                    }
                }
                formatted_tasks.append(formatted_task)
            
            # Ejecutar lote
            batch_result = await execute_autonomous_batch(formatted_tasks, context)
            
            # Formatear resultado del lote
            return {
                "status": "success" if batch_result["tasks_failed"] == 0 else "error",
                "task_id": batch_id,
                "batch_id": batch_result.get("batch_id"),
                "result": {
                    "content": f"Batch execution completed: {batch_result['tasks_completed']} successful, {batch_result['tasks_failed']} failed",
                    "model_used": "sam_batch_system",
                    "execution_time": 0,  # Calculado por el sistema de autonomía
                    "metadata": {
                        "total_tasks": batch_result["tasks_processed"],
                        "completed_tasks": batch_result["tasks_completed"],
                        "failed_tasks": batch_result["tasks_failed"],
                        "escalated_tasks": batch_result["tasks_escalated"],
                        "execution_log": batch_result["execution_log"]
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "task_id": batch_id,
                "error_message": f"Batch execution error: {str(e)}"
            }
    
    def _log_execution(self, task_id: str, input_data: Dict[str, Any], result: Dict[str, Any]):
        """
        Registra la ejecución para análisis posterior
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "input": input_data,
            "output": result,
            "status": result.get("status"),
            "execution_time": result.get("result", {}).get("execution_time", 0)
        }
        
        self.execution_history.append(log_entry)
        
        # Mantener solo los últimos 1000 logs
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de ejecución de la herramienta Sam
        """
        if not self.execution_history:
            return {"message": "No execution history available"}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for entry in self.execution_history if entry["status"] == "success")
        failed_executions = sum(1 for entry in self.execution_history if entry["status"] == "error")
        escalated_executions = sum(1 for entry in self.execution_history if entry["status"] == "escalated")
        
        # Estadísticas por tipo de tarea
        task_type_stats = {}
        for entry in self.execution_history:
            task_type = entry["input"].get("task_type", "unknown")
            if task_type not in task_type_stats:
                task_type_stats[task_type] = {"total": 0, "successful": 0, "failed": 0}
            
            task_type_stats[task_type]["total"] += 1
            if entry["status"] == "success":
                task_type_stats[task_type]["successful"] += 1
            elif entry["status"] == "error":
                task_type_stats[task_type]["failed"] += 1
        
        # Tiempo promedio de ejecución
        execution_times = [entry["execution_time"] for entry in self.execution_history if entry["execution_time"] > 0]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "escalated_executions": escalated_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "escalation_rate": escalated_executions / total_executions if total_executions > 0 else 0,
            "avg_execution_time": avg_execution_time,
            "task_type_stats": task_type_stats
        }

def create_langgraph_nodes_for_sam() -> List[LangGraphNode]:
    """
    Crea los nodos de LangGraph para integrar Sam
    """
    nodes = [
        # Nodo de inicio
        LangGraphNode(
            id="start",
            name="Start",
            type="start",
            next_nodes=["reasoning_shell"]
        ),
        
        # Shell de razonamiento para evaluar si usar Sam
        LangGraphNode(
            id="reasoning_shell",
            name="Reasoning Shell",
            type="condition",
            conditions={
                "use_sam": "Task requires specialized execution or autonomous processing",
                "use_other": "Task can be handled by other tools or direct LLM"
            },
            next_nodes=["invoke_sam", "alternative_processing"]
        ),
        
        # Nodo para invocar Sam
        LangGraphNode(
            id="invoke_sam",
            name="Invoke Sam Tool",
            type="tool",
            tool_name="sam_executor_agent",
            next_nodes=["evaluate_sam_result"]
        ),
        
        # Evaluación del resultado de Sam
        LangGraphNode(
            id="evaluate_sam_result",
            name="Evaluate Sam Result",
            type="condition",
            conditions={
                "success": "Sam completed task successfully",
                "escalated": "Sam escalated task back to Manus",
                "retry": "Sam failed but can retry with different parameters",
                "failed": "Sam failed and cannot retry"
            },
            next_nodes=["format_success", "handle_escalation", "retry_sam", "handle_failure"]
        ),
        
        # Formatear resultado exitoso
        LangGraphNode(
            id="format_success",
            name="Format Success Result",
            type="tool",
            next_nodes=["end"]
        ),
        
        # Manejar escalación
        LangGraphNode(
            id="handle_escalation",
            name="Handle Escalation",
            type="tool",
            next_nodes=["alternative_processing"]
        ),
        
        # Reintentar con Sam
        LangGraphNode(
            id="retry_sam",
            name="Retry Sam with Modified Parameters",
            type="tool",
            tool_name="sam_executor_agent",
            next_nodes=["evaluate_sam_result"]
        ),
        
        # Manejar fallo
        LangGraphNode(
            id="handle_failure",
            name="Handle Failure",
            type="tool",
            next_nodes=["alternative_processing"]
        ),
        
        # Procesamiento alternativo
        LangGraphNode(
            id="alternative_processing",
            name="Alternative Processing",
            type="tool",
            next_nodes=["end"]
        ),
        
        # Nodo final
        LangGraphNode(
            id="end",
            name="End",
            type="end"
        )
    ]
    
    return nodes

def create_langgraph_edges_for_sam() -> List[LangGraphEdge]:
    """
    Crea las aristas de LangGraph para el flujo con Sam
    """
    edges = [
        # Flujo principal
        LangGraphEdge("start", "reasoning_shell"),
        
        # Desde reasoning shell
        LangGraphEdge("reasoning_shell", "invoke_sam", "condition", "use_sam"),
        LangGraphEdge("reasoning_shell", "alternative_processing", "condition", "use_other"),
        
        # Desde invoke_sam
        LangGraphEdge("invoke_sam", "evaluate_sam_result"),
        
        # Desde evaluate_sam_result
        LangGraphEdge("evaluate_sam_result", "format_success", "condition", "success"),
        LangGraphEdge("evaluate_sam_result", "handle_escalation", "condition", "escalated"),
        LangGraphEdge("evaluate_sam_result", "retry_sam", "condition", "retry"),
        LangGraphEdge("evaluate_sam_result", "handle_failure", "condition", "failed"),
        
        # Flujos de manejo
        LangGraphEdge("format_success", "end"),
        LangGraphEdge("handle_escalation", "alternative_processing"),
        LangGraphEdge("retry_sam", "evaluate_sam_result"),
        LangGraphEdge("handle_failure", "alternative_processing"),
        LangGraphEdge("alternative_processing", "end")
    ]
    
    return edges

def generate_langgraph_config() -> Dict[str, Any]:
    """
    Genera la configuración completa de LangGraph para Sam
    """
    nodes = create_langgraph_nodes_for_sam()
    edges = create_langgraph_edges_for_sam()
    
    config = {
        "graph_name": "manus_sam_orchestration",
        "description": "LangGraph configuration for Manus-Sam orchestration with autonomous execution",
        "version": "1.0.0",
        "tools": [SAM_TOOL_DEFINITION],
        "nodes": [asdict(node) for node in nodes],
        "edges": [asdict(edge) for edge in edges],
        "entry_point": "start",
        "exit_points": ["end"],
        "configuration": {
            "max_iterations": 10,
            "timeout": 300,  # 5 minutos
            "retry_limit": 3,
            "escalation_threshold": 0.7
        }
    }
    
    return config

# Instancia global de la integración
sam_mcp_integration = SamMCPIntegration()

# Funciones de conveniencia
async def execute_sam_from_langgraph(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de conveniencia para ejecutar Sam desde LangGraph
    """
    return await sam_mcp_integration.execute_sam_tool(input_data)

def get_sam_tool_definition() -> Dict[str, Any]:
    """
    Función de conveniencia para obtener la definición de la herramienta Sam
    """
    return sam_mcp_integration.get_tool_definition()

def get_sam_execution_stats() -> Dict[str, Any]:
    """
    Función de conveniencia para obtener estadísticas de Sam
    """
    return sam_mcp_integration.get_execution_stats()

if __name__ == "__main__":
    # Test de la integración
    async def test_sam_integration():
        print("=== SAM MCP INTEGRATION TEST ===")
        
        # Test de definición de herramienta
        tool_def = get_sam_tool_definition()
        print(f"Tool definition: {tool_def['name']}")
        print(f"Description length: {len(tool_def['description'])} characters")
        
        # Test de ejecución
        test_input = {
            "task_type": "reasoning",
            "prompt": "Explain the benefits of local LLM models vs external APIs",
            "parameters": {
                "temperature": 0.7,
                "priority": "medium",
                "autonomy_level": "semi_autonomous"
            }
        }
        
        result = await execute_sam_from_langgraph(test_input)
        print(f"Execution result: {result['status']}")
        print(f"Task ID: {result['task_id']}")
        
        # Test de configuración LangGraph
        config = generate_langgraph_config()
        print(f"LangGraph config generated with {len(config['nodes'])} nodes and {len(config['edges'])} edges")
        
        # Guardar configuración
        with open("/tmp/sam_langgraph_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("LangGraph configuration saved to /tmp/sam_langgraph_config.json")
        
        # Estadísticas
        stats = get_sam_execution_stats()
        print(f"Execution stats: {json.dumps(stats, indent=2)}")
    
    # Ejecutar test
    asyncio.run(test_sam_integration())

