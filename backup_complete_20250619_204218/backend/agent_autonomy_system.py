#!/usr/bin/env python3
"""
Agent Autonomy System - Recurrent Loop for Continuous Execution
Sistema que permite a Sam ejecutar tareas de forma autónoma sin intervención constante
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    PAUSED = "paused"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class AutonomyLevel(Enum):
    SUPERVISED = "supervised"      # Requiere confirmación para cada paso
    SEMI_AUTONOMOUS = "semi_autonomous"  # Puede ejecutar tareas simples sin confirmación
    FULLY_AUTONOMOUS = "fully_autonomous"  # Ejecuta todo sin confirmación

@dataclass
class Task:
    id: str
    description: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    error_message: Optional[str] = None
    execution_attempts: int = 0
    max_attempts: int = 3
    estimated_duration: Optional[int] = None  # en segundos
    actual_duration: Optional[int] = None

@dataclass
class BatchExecution:
    id: str
    tasks: List[Task]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0

class ReasoningShell:
    """
    Shell de razonamiento que evalúa si Sam puede ejecutar tareas sin ayuda
    """
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.ambiguity_keywords = [
            "maybe", "perhaps", "unclear", "ambiguous", "not sure",
            "depends", "might", "could be", "uncertain"
        ]
        
    def can_execute_autonomously(self, task: Task, context: Dict[str, Any]) -> tuple[bool, float, str]:
        """
        Evalúa si una tarea puede ejecutarse de forma autónoma
        Returns: (can_execute, confidence_score, reasoning)
        """
        confidence_score = 1.0
        reasoning_factors = []
        
        # Factor 1: Claridad de la descripción
        description_clarity = self._evaluate_description_clarity(task.description)
        confidence_score *= description_clarity
        reasoning_factors.append(f"Description clarity: {description_clarity:.2f}")
        
        # Factor 2: Disponibilidad de contexto
        context_availability = self._evaluate_context_availability(task, context)
        confidence_score *= context_availability
        reasoning_factors.append(f"Context availability: {context_availability:.2f}")
        
        # Factor 3: Complejidad de la tarea
        task_complexity = self._evaluate_task_complexity(task)
        confidence_score *= task_complexity
        reasoning_factors.append(f"Task complexity factor: {task_complexity:.2f}")
        
        # Factor 4: Recursos necesarios
        resource_availability = self._evaluate_resource_availability(task, context)
        confidence_score *= resource_availability
        reasoning_factors.append(f"Resource availability: {resource_availability:.2f}")
        
        can_execute = confidence_score >= self.confidence_threshold
        reasoning = f"Confidence: {confidence_score:.2f} ({'PASS' if can_execute else 'FAIL'}). " + \
                   f"Factors: {'; '.join(reasoning_factors)}"
        
        return can_execute, confidence_score, reasoning
    
    def _evaluate_description_clarity(self, description: str) -> float:
        """Evalúa la claridad de la descripción de la tarea"""
        if not description or len(description.strip()) < 10:
            return 0.2
        
        # Buscar palabras que indican ambigüedad
        ambiguity_count = sum(1 for keyword in self.ambiguity_keywords 
                             if keyword.lower() in description.lower())
        
        # Penalizar por ambigüedad
        clarity_score = max(0.3, 1.0 - (ambiguity_count * 0.2))
        
        # Bonus por especificidad
        if any(word in description.lower() for word in ["specific", "exactly", "precisely"]):
            clarity_score = min(1.0, clarity_score + 0.1)
        
        return clarity_score
    
    def _evaluate_context_availability(self, task: Task, context: Dict[str, Any]) -> float:
        """Evalúa si hay suficiente contexto para ejecutar la tarea"""
        if not context:
            return 0.4
        
        # Verificar contexto específico de la tarea
        task_context_score = 0.5
        if task.context:
            task_context_score = 0.8
        
        # Verificar contexto global del sistema
        system_context_score = 0.5
        required_context_keys = ["system_info", "file_structure", "agent_status"]
        available_keys = sum(1 for key in required_context_keys if key in context)
        system_context_score = available_keys / len(required_context_keys)
        
        return (task_context_score + system_context_score) / 2
    
    def _evaluate_task_complexity(self, task: Task) -> float:
        """Evalúa la complejidad de la tarea"""
        complexity_indicators = {
            "simple": ["list", "show", "display", "get", "fetch", "read"],
            "medium": ["analyze", "process", "generate", "create", "write"],
            "complex": ["integrate", "deploy", "configure", "optimize", "debug"]
        }
        
        description_lower = task.description.lower()
        
        # Buscar indicadores de complejidad
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                if complexity == "simple":
                    return 0.9
                elif complexity == "medium":
                    return 0.7
                else:  # complex
                    return 0.5
        
        # Si no se encuentra indicador específico, evaluar por longitud
        if len(task.description) < 50:
            return 0.8
        elif len(task.description) < 200:
            return 0.6
        else:
            return 0.4
    
    def _evaluate_resource_availability(self, task: Task, context: Dict[str, Any]) -> float:
        """Evalúa si los recursos necesarios están disponibles"""
        # Verificar disponibilidad de modelos
        models_available = context.get("agent_status", {}).get("local_models", {})
        if not models_available:
            return 0.6
        
        # Verificar servicios activos
        services = context.get("agent_status", {}).get("services", {})
        active_services = sum(1 for status in services.values() if status == "active")
        service_score = min(1.0, active_services / 5)  # Asumiendo 5 servicios críticos
        
        return service_score

class AgentAutonomySystem:
    """
    Sistema principal de autonomía para Sam
    """
    
    def __init__(self, autonomy_level: AutonomyLevel = AutonomyLevel.SEMI_AUTONOMOUS):
        self.autonomy_level = autonomy_level
        self.task_queue: List[Task] = []
        self.active_batches: Dict[str, BatchExecution] = {}
        self.completed_batches: List[BatchExecution] = []
        self.reasoning_shell = ReasoningShell()
        self.logger = self._setup_logging()
        self.execution_callbacks: Dict[str, Callable] = {}
        self.pause_execution = False
        self.max_concurrent_tasks = 3
        
    def _setup_logging(self) -> logging.Logger:
        """Configura logging para el sistema de autonomía"""
        logger = logging.getLogger("AgentAutonomy")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("/root/supermcp/logs/agent_autonomy.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def add_task(self, description: str, task_type: str, priority: TaskPriority = TaskPriority.MEDIUM,
                 deadline: Optional[datetime] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Añade una nueva tarea a la cola
        """
        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            task_type=task_type,
            priority=priority,
            deadline=deadline,
            context=context or {}
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: (t.priority.value, t.created_at), reverse=True)
        
        self.logger.info(f"Added task {task.id}: {description}")
        return task.id
    
    def add_batch_tasks(self, tasks_data: List[Dict[str, Any]]) -> str:
        """
        Añade un lote de tareas relacionadas
        """
        batch_id = str(uuid.uuid4())
        tasks = []
        
        for task_data in tasks_data:
            task = Task(
                id=str(uuid.uuid4()),
                description=task_data["description"],
                task_type=task_data.get("task_type", "general"),
                priority=TaskPriority(task_data.get("priority", 2)),
                deadline=task_data.get("deadline"),
                context=task_data.get("context", {}),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
            self.task_queue.append(task)
        
        batch = BatchExecution(
            id=batch_id,
            tasks=tasks,
            total_tasks=len(tasks)
        )
        
        self.active_batches[batch_id] = batch
        self.logger.info(f"Added batch {batch_id} with {len(tasks)} tasks")
        
        return batch_id
    
    async def execute_autonomous_loop(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Loop principal de ejecución autónoma
        """
        self.logger.info("Starting autonomous execution loop")
        execution_summary = {
            "started_at": datetime.now().isoformat(),
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_escalated": 0,
            "execution_log": []
        }
        
        while self.task_queue and not self.pause_execution:
            # Obtener tareas ejecutables
            executable_tasks = self._get_executable_tasks(context)
            
            if not executable_tasks:
                self.logger.info("No executable tasks found, checking for escalations")
                self._handle_escalations(context)
                break
            
            # Ejecutar tareas en paralelo (limitado)
            concurrent_tasks = executable_tasks[:self.max_concurrent_tasks]
            
            # Crear tasks asyncio para ejecución paralela
            execution_tasks = []
            for task in concurrent_tasks:
                execution_tasks.append(self._execute_single_task(task, context))
            
            # Esperar a que todas las tareas terminen
            results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # Procesar resultados
            for i, result in enumerate(results):
                task = concurrent_tasks[i]
                execution_summary["tasks_processed"] += 1
                
                if isinstance(result, Exception):
                    task.status = TaskStatus.FAILED
                    task.error_message = str(result)
                    execution_summary["tasks_failed"] += 1
                    self.logger.error(f"Task {task.id} failed: {str(result)}")
                else:
                    if result["success"]:
                        task.status = TaskStatus.COMPLETED
                        task.result = result["result"]
                        execution_summary["tasks_completed"] += 1
                        self.logger.info(f"Task {task.id} completed successfully")
                    else:
                        if result.get("escalate", False):
                            task.status = TaskStatus.ESCALATED
                            execution_summary["tasks_escalated"] += 1
                            self.logger.warning(f"Task {task.id} escalated: {result.get('reason')}")
                        else:
                            task.status = TaskStatus.FAILED
                            task.error_message = result.get("error", "Unknown error")
                            execution_summary["tasks_failed"] += 1
                            self.logger.error(f"Task {task.id} failed: {result.get('error')}")
                
                # Log de ejecución
                execution_summary["execution_log"].append({
                    "task_id": task.id,
                    "description": task.description,
                    "status": task.status.value,
                    "execution_time": result.get("execution_time") if not isinstance(result, Exception) else None,
                    "error": task.error_message
                })
                
                # Remover de la cola
                if task in self.task_queue:
                    self.task_queue.remove(task)
            
            # Actualizar batches
            self._update_batch_status()
            
            # Pequeña pausa entre iteraciones
            await asyncio.sleep(1)
        
        execution_summary["completed_at"] = datetime.now().isoformat()
        self.logger.info(f"Autonomous loop completed: {execution_summary}")
        
        return execution_summary
    
    def _get_executable_tasks(self, context: Dict[str, Any]) -> List[Task]:
        """
        Obtiene tareas que pueden ejecutarse de forma autónoma
        """
        executable_tasks = []
        
        for task in self.task_queue:
            if task.status != TaskStatus.PENDING:
                continue
            
            # Verificar dependencias
            if not self._dependencies_satisfied(task):
                continue
            
            # Evaluar autonomía
            can_execute, confidence, reasoning = self.reasoning_shell.can_execute_autonomously(task, context)
            
            if can_execute or self.autonomy_level == AutonomyLevel.FULLY_AUTONOMOUS:
                task.status = TaskStatus.IN_PROGRESS
                executable_tasks.append(task)
                self.logger.info(f"Task {task.id} marked as executable: {reasoning}")
            else:
                self.logger.info(f"Task {task.id} requires escalation: {reasoning}")
        
        return executable_tasks
    
    def _dependencies_satisfied(self, task: Task) -> bool:
        """
        Verifica si las dependencias de una tarea están satisfechas
        """
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            # Buscar la tarea dependencia
            dep_task = None
            for t in self.task_queue:
                if t.id == dep_id:
                    dep_task = t
                    break
            
            # Si no se encuentra o no está completada
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _execute_single_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una sola tarea
        """
        start_time = time.time()
        task.execution_attempts += 1
        
        try:
            # Importar el sistema de toolchain
            from preferred_toolchain_system import execute_with_local_priority, TaskType
            
            # Preparar system message con contexto
            from memory_injection_system import MemoryInjectionSystem
            memory_system = MemoryInjectionSystem()
            system_message = memory_system.create_system_message()
            
            # Determinar tipo de tarea
            task_type_mapping = {
                "coding": "coding",
                "research": "research", 
                "analysis": "analysis",
                "creative": "creative",
                "general": "reasoning"
            }
            
            task_type = task_type_mapping.get(task.task_type.lower(), "reasoning")
            
            # Ejecutar con el sistema de toolchain
            result = await execute_with_local_priority(
                prompt=task.description,
                task_type=task_type,
                temperature=0.7,
                system_message=system_message
            )
            
            execution_time = time.time() - start_time
            task.actual_duration = int(execution_time)
            
            if result.success:
                return {
                    "success": True,
                    "result": result.response,
                    "model_used": result.model_used,
                    "execution_time": execution_time,
                    "tokens_used": result.tokens_used,
                    "cost": result.cost
                }
            else:
                # Decidir si escalar o fallar
                if task.execution_attempts >= task.max_attempts:
                    return {
                        "success": False,
                        "escalate": True,
                        "reason": f"Max attempts reached ({task.max_attempts}). Last error: {result.error}",
                        "execution_time": execution_time
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error,
                        "execution_time": execution_time
                    }
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Exception executing task {task.id}: {str(e)}")
            
            if task.execution_attempts >= task.max_attempts:
                return {
                    "success": False,
                    "escalate": True,
                    "reason": f"Exception after {task.max_attempts} attempts: {str(e)}",
                    "execution_time": execution_time
                }
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "execution_time": execution_time
                }
    
    def _handle_escalations(self, context: Dict[str, Any]):
        """
        Maneja tareas que necesitan escalación
        """
        escalated_tasks = [task for task in self.task_queue if task.status == TaskStatus.ESCALATED]
        
        if escalated_tasks:
            self.logger.warning(f"Found {len(escalated_tasks)} escalated tasks")
            
            # Aquí se podría implementar notificación a Manus
            # Por ahora, solo log
            for task in escalated_tasks:
                self.logger.warning(f"Escalated task {task.id}: {task.description}")
    
    def _update_batch_status(self):
        """
        Actualiza el estado de los batches activos
        """
        for batch_id, batch in list(self.active_batches.items()):
            completed = sum(1 for task in batch.tasks if task.status == TaskStatus.COMPLETED)
            failed = sum(1 for task in batch.tasks if task.status == TaskStatus.FAILED)
            
            batch.completed_tasks = completed
            batch.failed_tasks = failed
            
            if completed + failed == batch.total_tasks:
                batch.status = TaskStatus.COMPLETED
                batch.completed_at = datetime.now()
                self.completed_batches.append(batch)
                del self.active_batches[batch_id]
                self.logger.info(f"Batch {batch_id} completed: {completed} successful, {failed} failed")
    
    def pause(self):
        """Pausa la ejecución autónoma"""
        self.pause_execution = True
        self.logger.info("Autonomous execution paused")
    
    def resume(self):
        """Reanuda la ejecución autónoma"""
        self.pause_execution = False
        self.logger.info("Autonomous execution resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del sistema de autonomía
        """
        return {
            "autonomy_level": self.autonomy_level.value,
            "paused": self.pause_execution,
            "pending_tasks": len([t for t in self.task_queue if t.status == TaskStatus.PENDING]),
            "in_progress_tasks": len([t for t in self.task_queue if t.status == TaskStatus.IN_PROGRESS]),
            "escalated_tasks": len([t for t in self.task_queue if t.status == TaskStatus.ESCALATED]),
            "active_batches": len(self.active_batches),
            "completed_batches": len(self.completed_batches),
            "max_concurrent_tasks": self.max_concurrent_tasks
        }
    
    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene detalles de una tarea específica
        """
        for task in self.task_queue:
            if task.id == task_id:
                return {
                    "id": task.id,
                    "description": task.description,
                    "task_type": task.task_type,
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                    "dependencies": task.dependencies,
                    "result": task.result,
                    "error_message": task.error_message,
                    "execution_attempts": task.execution_attempts,
                    "max_attempts": task.max_attempts,
                    "estimated_duration": task.estimated_duration,
                    "actual_duration": task.actual_duration
                }
        
        return None

# Instancia global del sistema de autonomía
autonomy_system = AgentAutonomySystem()

# Funciones de conveniencia
def add_autonomous_task(description: str, task_type: str = "general", 
                       priority: str = "medium", context: Optional[Dict[str, Any]] = None) -> str:
    """
    Función de conveniencia para añadir tareas autónomas
    """
    priority_enum = TaskPriority.MEDIUM
    if priority.lower() == "low":
        priority_enum = TaskPriority.LOW
    elif priority.lower() == "high":
        priority_enum = TaskPriority.HIGH
    elif priority.lower() == "critical":
        priority_enum = TaskPriority.CRITICAL
    
    return autonomy_system.add_task(description, task_type, priority_enum, context=context)

async def execute_autonomous_batch(tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de conveniencia para ejecutar un lote de tareas autónomas
    """
    batch_id = autonomy_system.add_batch_tasks(tasks)
    result = await autonomy_system.execute_autonomous_loop(context)
    result["batch_id"] = batch_id
    return result

def get_autonomy_status() -> Dict[str, Any]:
    """
    Función de conveniencia para obtener el estado del sistema
    """
    return autonomy_system.get_status()

if __name__ == "__main__":
    # Test del sistema
    async def test_autonomy_system():
        print("=== AGENT AUTONOMY SYSTEM TEST ===")
        
        # Crear contexto de prueba
        test_context = {
            "system_info": {"domain": "sam.chat"},
            "agent_status": {
                "local_models": {"mistral": "loaded", "llama": "loaded"},
                "services": {"backend": "active", "frontend": "active"}
            }
        }
        
        # Añadir tareas de prueba
        task1_id = autonomy_system.add_task(
            "List the available local models",
            "general",
            TaskPriority.HIGH
        )
        
        task2_id = autonomy_system.add_task(
            "Write a simple Python function to add two numbers",
            "coding",
            TaskPriority.MEDIUM
        )
        
        print(f"Added tasks: {task1_id}, {task2_id}")
        
        # Ejecutar loop autónomo
        result = await autonomy_system.execute_autonomous_loop(test_context)
        
        print(f"Execution result: {json.dumps(result, indent=2)}")
        
        # Mostrar estado
        status = autonomy_system.get_status()
        print(f"System status: {json.dumps(status, indent=2)}")
    
    # Ejecutar test
    asyncio.run(test_autonomy_system())

