#!/usr/bin/env python3
"""
ReasoningShell Integration con Memory Analyzer
Integra la búsqueda semántica en el proceso de razonamiento de Sam
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Importar sistemas existentes
try:
    from sam_memory_analyzer import search_relevant_memories, analyze_and_store_memory
    from agent_autonomy_system import ReasoningShell as BaseReasoningShell, Task
    from memory_injection_system import MemoryInjectionSystem
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")

class EnhancedReasoningShell(BaseReasoningShell):
    """
    ReasoningShell mejorado con capacidades de memoria semántica
    """
    
    def __init__(self):
        super().__init__()
        self.memory_enabled = True
        self.memory_threshold = 0.75
        self.max_memories_per_task = 5
        self.logger = self._setup_memory_logging()
        
        # Métricas de memoria
        self.memory_metrics = {
            "tasks_with_memory": 0,
            "tasks_without_memory": 0,
            "memory_hits": 0,
            "memory_misses": 0,
            "successful_with_memory": 0,
            "successful_without_memory": 0
        }
    
    def _setup_memory_logging(self) -> logging.Logger:
        """Configura logging específico para memoria"""
        logger = logging.getLogger("EnhancedReasoningShell")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("/root/supermcp/logs/reasoning_memory.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def can_execute_autonomously_with_memory(
        self, 
        task: Task, 
        context: Dict[str, Any]
    ) -> Tuple[bool, float, str, List[Dict[str, Any]]]:
        """
        Versión mejorada que incluye búsqueda de memoria semántica
        """
        # Ejecutar análisis base
        can_execute, confidence, reasoning = self.can_execute_autonomously(task, context)
        
        # Buscar memorias relevantes
        relevant_memories = []
        memory_boost = 0.0
        
        if self.memory_enabled:
            try:
                # Buscar memorias similares
                search_results = await search_relevant_memories(
                    task.description, 
                    self.max_memories_per_task
                )
                
                if search_results:
                    self.memory_metrics["memory_hits"] += 1
                    
                    # Procesar memorias encontradas
                    for result in search_results:
                        memory_data = {
                            "summary": result.memory.summary,
                            "memory_type": result.memory.memory_type.value,
                            "success_score": result.memory.success_score,
                            "similarity_score": result.similarity_score,
                            "relevance_reason": result.relevance_reason,
                            "tags": result.memory.tags,
                            "created_at": result.memory.created_at.isoformat()
                        }
                        relevant_memories.append(memory_data)
                    
                    # Calcular boost de confianza basado en memorias
                    memory_boost = self._calculate_memory_boost(search_results)
                    confidence = min(1.0, confidence + memory_boost)
                    
                    # Actualizar reasoning con información de memoria
                    memory_info = self._format_memory_info(search_results)
                    reasoning += f" | Memory boost: +{memory_boost:.2f} ({memory_info})"
                    
                    self.memory_metrics["tasks_with_memory"] += 1
                    self.logger.info(f"Task {task.id}: Found {len(search_results)} relevant memories, boost: +{memory_boost:.2f}")
                else:
                    self.memory_metrics["memory_misses"] += 1
                    self.memory_metrics["tasks_without_memory"] += 1
                    self.logger.info(f"Task {task.id}: No relevant memories found")
                    
            except Exception as e:
                self.logger.error(f"Error in memory search for task {task.id}: {e}")
                self.memory_metrics["tasks_without_memory"] += 1
        
        return can_execute, confidence, reasoning, relevant_memories
    
    def _calculate_memory_boost(self, search_results) -> float:
        """
        Calcula boost de confianza basado en memorias relevantes
        """
        if not search_results:
            return 0.0
        
        total_boost = 0.0
        
        for result in search_results:
            memory = result.memory
            similarity = result.similarity_score
            
            # Boost base por similitud
            base_boost = similarity * 0.1
            
            # Multiplicador por tipo de memoria
            type_multiplier = {
                "success": 1.5,
                "critical": 1.3,
                "learning": 1.0,
                "escalation": 0.8,
                "failure": 0.5  # Los fallos dan boost negativo para evitar repetir errores
            }.get(memory.memory_type.value, 1.0)
            
            # Multiplicador por success score
            success_multiplier = 0.5 + memory.success_score
            
            # Boost final para esta memoria
            memory_boost = base_boost * type_multiplier * success_multiplier
            total_boost += memory_boost
        
        # Limitar boost total
        return min(0.3, total_boost)  # Máximo 30% de boost
    
    def _format_memory_info(self, search_results) -> str:
        """
        Formatea información de memorias para el reasoning
        """
        if not search_results:
            return "no memories"
        
        memory_types = [result.memory.memory_type.value for result in search_results]
        type_counts = {}
        for mem_type in memory_types:
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
        
        type_summary = ", ".join([f"{count} {mem_type}" for mem_type, count in type_counts.items()])
        avg_similarity = sum(result.similarity_score for result in search_results) / len(search_results)
        
        return f"{len(search_results)} memories ({type_summary}), avg similarity: {avg_similarity:.2f}"
    
    async def post_execution_memory_storage(
        self, 
        task: Task, 
        execution_result: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]]
    ):
        """
        Almacena la experiencia de ejecución en memoria para aprendizaje futuro
        """
        try:
            # Preparar datos del log para análisis
            log_data = {
                "task_id": task.id,
                "timestamp": datetime.now().isoformat(),
                "input": {
                    "task_type": task.task_type,
                    "prompt": task.description,
                    "priority": task.priority.value,
                    "context": task.context
                },
                "output": execution_result,
                "relevant_memories_used": relevant_memories,
                "memory_assisted": len(relevant_memories) > 0
            }
            
            # Analizar y almacenar en memoria
            memory_id = await analyze_and_store_memory(log_data)
            
            if memory_id:
                self.logger.info(f"Task {task.id} stored in memory: {memory_id}")
                
                # Actualizar métricas
                if execution_result.get("success"):
                    if relevant_memories:
                        self.memory_metrics["successful_with_memory"] += 1
                    else:
                        self.memory_metrics["successful_without_memory"] += 1
                
                return memory_id
            else:
                self.logger.error(f"Failed to store task {task.id} in memory")
                return None
                
        except Exception as e:
            self.logger.error(f"Error storing memory for task {task.id}: {e}")
            return None
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas de uso de memoria
        """
        total_tasks = self.memory_metrics["tasks_with_memory"] + self.memory_metrics["tasks_without_memory"]
        
        if total_tasks == 0:
            return self.memory_metrics
        
        # Calcular tasas
        memory_usage_rate = self.memory_metrics["tasks_with_memory"] / total_tasks
        memory_hit_rate = self.memory_metrics["memory_hits"] / (self.memory_metrics["memory_hits"] + self.memory_metrics["memory_misses"]) if (self.memory_metrics["memory_hits"] + self.memory_metrics["memory_misses"]) > 0 else 0
        
        # Calcular tasas de éxito
        success_with_memory_rate = self.memory_metrics["successful_with_memory"] / self.memory_metrics["tasks_with_memory"] if self.memory_metrics["tasks_with_memory"] > 0 else 0
        success_without_memory_rate = self.memory_metrics["successful_without_memory"] / self.memory_metrics["tasks_without_memory"] if self.memory_metrics["tasks_without_memory"] > 0 else 0
        
        return {
            **self.memory_metrics,
            "memory_usage_rate": memory_usage_rate,
            "memory_hit_rate": memory_hit_rate,
            "success_with_memory_rate": success_with_memory_rate,
            "success_without_memory_rate": success_without_memory_rate,
            "memory_effectiveness": success_with_memory_rate - success_without_memory_rate
        }

class MemoryEnhancedAutonomySystem:
    """
    Sistema de autonomía mejorado con capacidades de memoria semántica
    """
    
    def __init__(self):
        self.enhanced_reasoning_shell = EnhancedReasoningShell()
        self.memory_injection_system = MemoryInjectionSystem()
        self.logger = logging.getLogger("MemoryEnhancedAutonomy")
    
    async def execute_task_with_memory(
        self, 
        task: Task, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea usando el sistema mejorado con memoria
        """
        try:
            # 1. Análisis con memoria semántica
            can_execute, confidence, reasoning, relevant_memories = await self.enhanced_reasoning_shell.can_execute_autonomously_with_memory(
                task, context
            )
            
            self.logger.info(f"Task {task.id} analysis: can_execute={can_execute}, confidence={confidence:.2f}, memories={len(relevant_memories)}")
            
            # 2. Preparar contexto enriquecido con memorias
            enriched_context = await self._enrich_context_with_memories(context, relevant_memories)
            
            # 3. Ejecutar tarea (aquí iría la lógica de ejecución real)
            execution_result = await self._execute_task_logic(task, enriched_context)
            
            # 4. Almacenar experiencia en memoria
            memory_id = await self.enhanced_reasoning_shell.post_execution_memory_storage(
                task, execution_result, relevant_memories
            )
            
            # 5. Preparar resultado final
            result = {
                **execution_result,
                "memory_analysis": {
                    "can_execute": can_execute,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "relevant_memories_count": len(relevant_memories),
                    "memory_id": memory_id
                },
                "relevant_memories": relevant_memories
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing task {task.id} with memory: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_analysis": {
                    "can_execute": False,
                    "confidence": 0.0,
                    "reasoning": f"Error in memory-enhanced execution: {str(e)}",
                    "relevant_memories_count": 0,
                    "memory_id": None
                }
            }
    
    async def _enrich_context_with_memories(
        self, 
        base_context: Dict[str, Any], 
        relevant_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enriquece el contexto base con información de memorias relevantes
        """
        enriched_context = base_context.copy()
        
        if relevant_memories:
            # Crear sección de memoria en el contexto
            memory_context = {
                "relevant_experiences": [],
                "learned_patterns": [],
                "success_strategies": [],
                "failure_patterns": []
            }
            
            for memory_data in relevant_memories:
                experience = {
                    "summary": memory_data["summary"],
                    "outcome": memory_data["memory_type"],
                    "success_score": memory_data["success_score"],
                    "relevance": memory_data["similarity_score"],
                    "tags": memory_data["tags"]
                }
                
                memory_context["relevant_experiences"].append(experience)
                
                # Categorizar por tipo
                if memory_data["memory_type"] == "success" and memory_data["success_score"] > 0.8:
                    memory_context["success_strategies"].append(memory_data["summary"])
                elif memory_data["memory_type"] == "failure":
                    memory_context["failure_patterns"].append(memory_data["summary"])
            
            enriched_context["semantic_memory"] = memory_context
            
            # Crear system message enriquecido
            memory_system_message = self._create_memory_system_message(relevant_memories)
            enriched_context["memory_system_message"] = memory_system_message
        
        return enriched_context
    
    def _create_memory_system_message(self, relevant_memories: List[Dict[str, Any]]) -> str:
        """
        Crea un system message que incluye las memorias relevantes
        """
        if not relevant_memories:
            return ""
        
        message_parts = [
            "## RELEVANT PAST EXPERIENCES:",
            "Based on your previous experiences, here are similar situations you've encountered:\n"
        ]
        
        for i, memory_data in enumerate(relevant_memories[:3], 1):  # Top 3 memorias
            memory_type_emoji = {
                "success": "✅",
                "failure": "❌", 
                "escalation": "⚠️",
                "critical": "🔥",
                "learning": "📚"
            }.get(memory_data["memory_type"], "📝")
            
            message_parts.append(
                f"{i}. {memory_type_emoji} **{memory_data['memory_type'].upper()}** "
                f"(similarity: {memory_data['similarity_score']:.2f}, "
                f"success: {memory_data['success_score']:.2f})\n"
                f"   {memory_data['summary']}\n"
                f"   Reason: {memory_data['relevance_reason']}\n"
            )
        
        message_parts.append(
            "\n**Use these experiences to inform your approach. "
            "Learn from successes and avoid repeating failures.**"
        )
        
        return "\n".join(message_parts)
    
    async def _execute_task_logic(self, task: Task, enriched_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lógica de ejecución de tarea (placeholder - aquí iría la integración real)
        """
        # Aquí se integraría con el sistema de ejecución real
        # Por ahora, simulamos una ejecución exitosa
        
        await asyncio.sleep(0.1)  # Simular procesamiento
        
        return {
            "success": True,
            "result": {
                "content": f"Task '{task.description}' executed successfully with memory enhancement",
                "model_used": "memory_enhanced_system",
                "execution_time": 0.1,
                "cost": 0.0
            }
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del sistema mejorado
        """
        return {
            "memory_metrics": self.enhanced_reasoning_shell.get_memory_metrics(),
            "reasoning_shell_config": {
                "memory_enabled": self.enhanced_reasoning_shell.memory_enabled,
                "memory_threshold": self.enhanced_reasoning_shell.memory_threshold,
                "max_memories_per_task": self.enhanced_reasoning_shell.max_memories_per_task
            }
        }

# Instancia global del sistema mejorado
memory_enhanced_autonomy = MemoryEnhancedAutonomySystem()

# Funciones de conveniencia
async def execute_task_with_semantic_memory(task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
    """Función de conveniencia para ejecutar tarea con memoria semántica"""
    return await memory_enhanced_autonomy.execute_task_with_memory(task, context)

def get_memory_enhanced_stats() -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas"""
    return memory_enhanced_autonomy.get_system_stats()

if __name__ == "__main__":
    # Test del sistema mejorado
    async def test_memory_enhanced_system():
        print("=== MEMORY ENHANCED REASONING SHELL TEST ===")
        
        # Crear tarea de prueba
        from agent_autonomy_system import Task, TaskPriority
        
        test_task = Task(
            id="test-memory-123",
            description="Write a Python function to process JSON data efficiently",
            task_type="coding",
            priority=TaskPriority.MEDIUM
        )
        
        # Contexto de prueba
        test_context = {
            "system_info": {"domain": "sam.chat"},
            "agent_status": {"local_models": {"qwen": "loaded"}}
        }
        
        # Ejecutar con memoria
        result = await execute_task_with_semantic_memory(test_task, test_context)
        
        print(f"Execution result: {json.dumps(result, indent=2)}")
        
        # Estadísticas
        stats = get_memory_enhanced_stats()
        print(f"System stats: {json.dumps(stats, indent=2)}")
    
    # Ejecutar test
    asyncio.run(test_memory_enhanced_system())

