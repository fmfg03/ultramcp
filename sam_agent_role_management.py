#!/usr/bin/env python3
"""
SAM Agent Role Management System
Sistema avanzado de gestión de roles y escalabilidad para agentes SAM
"""

import asyncio
import json
import time
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
from contextlib import asynccontextmanager
import queue
import weakref

class AgentRole(Enum):
    """Roles disponibles para agentes SAM"""
    EXECUTOR = "executor"           # Ejecuta tareas directamente
    DELEGATE = "delegate"           # Delega tareas a otros agentes
    COORDINATOR = "coordinator"     # Coordina múltiples agentes
    SPECIALIST = "specialist"       # Especialista en dominio específico
    MONITOR = "monitor"            # Monitorea y supervisa otros agentes
    BACKUP = "backup"              # Agente de respaldo/failover

class TaskPriority(Enum):
    """Niveles de prioridad para tareas"""
    CRITICAL = "critical"          # Máxima prioridad
    HIGH = "high"                  # Alta prioridad
    NORMAL = "normal"              # Prioridad normal
    LOW = "low"                    # Baja prioridad
    BACKGROUND = "background"      # Procesamiento en background

class AgentStatus(Enum):
    """Estados posibles de un agente"""
    IDLE = "idle"                  # Disponible para nuevas tareas
    BUSY = "busy"                  # Ejecutando tarea
    OVERLOADED = "overloaded"      # Sobrecargado
    MAINTENANCE = "maintenance"    # En mantenimiento
    ERROR = "error"                # Estado de error
    OFFLINE = "offline"            # Fuera de línea

class TaskStatus(Enum):
    """Estados de las tareas"""
    PENDING = "pending"            # En cola
    ASSIGNED = "assigned"          # Asignada a agente
    RUNNING = "running"            # En ejecución
    COMPLETED = "completed"        # Completada
    FAILED = "failed"              # Falló
    CANCELLED = "cancelled"        # Cancelada
    ESCALATED = "escalated"        # Escalada

@dataclass
class AgentCapability:
    """Capacidad específica de un agente"""
    name: str
    level: int  # 1-10, donde 10 es experto
    domains: List[str]
    max_concurrent_tasks: int
    estimated_performance: float  # tasks per hour

@dataclass
class AgentProfile:
    """Perfil completo de un agente SAM"""
    agent_id: str
    role: AgentRole
    status: AgentStatus
    capabilities: List[AgentCapability]
    current_load: int
    max_load: int
    performance_metrics: Dict[str, float]
    last_heartbeat: str
    metadata: Dict[str, Any]

@dataclass
class Task:
    """Definición de tarea para el sistema"""
    task_id: str
    task_type: str
    priority: TaskPriority
    description: str
    requirements: List[str]
    estimated_duration: int  # segundos
    max_retries: int
    timeout: int  # segundos
    payload: Dict[str, Any]
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    error_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.error_history is None:
            self.error_history = []

class AgentRoleManager:
    """
    Gestor avanzado de roles y escalabilidad para agentes SAM
    """
    
    def __init__(self, db_path: str = "/tmp/sam_roles.db"):
        self.db_path = db_path
        self.agents: Dict[str, AgentProfile] = {}
        self.task_queue = asyncio.Queue()
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        
        # Configuración de escalabilidad
        self.max_agents_per_role = {
            AgentRole.EXECUTOR: 10,
            AgentRole.DELEGATE: 5,
            AgentRole.COORDINATOR: 3,
            AgentRole.SPECIALIST: 8,
            AgentRole.MONITOR: 2,
            AgentRole.BACKUP: 5
        }
        
        # Pool de threads para ejecución paralela
        self.executor_pool = ThreadPoolExecutor(max_workers=20)
        
        # Configuración de load balancing
        self.load_balancing_strategy = "least_loaded"  # round_robin, capability_based
        
        self.logger = logging.getLogger(__name__)
        self._init_database()
        self._start_background_workers()
    
    def _init_database(self):
        """Inicializar base de datos para gestión de roles"""
        with sqlite3.connect(self.db_path) as conn:
            # Tabla de agentes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    capabilities TEXT NOT NULL,
                    current_load INTEGER DEFAULT 0,
                    max_load INTEGER DEFAULT 5,
                    performance_metrics TEXT DEFAULT '{}',
                    last_heartbeat TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de tareas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    description TEXT NOT NULL,
                    requirements TEXT NOT NULL,
                    estimated_duration INTEGER NOT NULL,
                    max_retries INTEGER DEFAULT 3,
                    timeout INTEGER DEFAULT 300,
                    payload TEXT NOT NULL,
                    assigned_agent TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    started_at TEXT,
                    completed_at TEXT,
                    retry_count INTEGER DEFAULT 0,
                    error_history TEXT DEFAULT '[]',
                    FOREIGN KEY (assigned_agent) REFERENCES agents (agent_id)
                )
            """)
            
            # Tabla de métricas de performance
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    task_id TEXT,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id),
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            """)
            
            # Tabla de eventos de escalabilidad
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scaling_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    agent_id TEXT,
                    role TEXT,
                    reason TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
    
    def _start_background_workers(self):
        """Iniciar workers en background"""
        # Worker para procesamiento de tareas
        asyncio.create_task(self._task_processor())
        
        # Worker para monitoreo de agentes
        asyncio.create_task(self._agent_monitor())
        
        # Worker para auto-scaling
        asyncio.create_task(self._auto_scaler())
        
        # Worker para limpieza de métricas
        asyncio.create_task(self._metrics_cleaner())
    
    async def _task_processor(self):
        """Worker principal para procesamiento de tareas"""
        while True:
            try:
                task = await self.task_queue.get()
                await self._process_task(task)
                self.task_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(1)
    
    async def _agent_monitor(self):
        """Worker para monitoreo de agentes"""
        while True:
            try:
                await self._check_agent_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in agent monitor: {e}")
                await asyncio.sleep(30)
    
    async def _auto_scaler(self):
        """Worker para auto-scaling de agentes"""
        while True:
            try:
                await self._evaluate_scaling_needs()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in auto scaler: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_cleaner(self):
        """Worker para limpieza de métricas antiguas"""
        while True:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(3600)  # Clean every hour
            except Exception as e:
                self.logger.error(f"Error in metrics cleaner: {e}")
                await asyncio.sleep(3600)
    
    def register_agent(self, agent_profile: AgentProfile) -> bool:
        """Registrar nuevo agente en el sistema"""
        try:
            # Validar que no exceda límites por rol
            current_count = sum(1 for agent in self.agents.values() 
                              if agent.role == agent_profile.role)
            
            if current_count >= self.max_agents_per_role[agent_profile.role]:
                self.logger.warning(f"Maximum agents for role {agent_profile.role.value} reached")
                return False
            
            # Persistir en base de datos
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO agents 
                    (agent_id, role, status, capabilities, current_load, max_load, 
                     performance_metrics, last_heartbeat, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_profile.agent_id,
                    agent_profile.role.value,
                    agent_profile.status.value,
                    json.dumps([asdict(cap) for cap in agent_profile.capabilities]),
                    agent_profile.current_load,
                    agent_profile.max_load,
                    json.dumps(agent_profile.performance_metrics),
                    agent_profile.last_heartbeat,
                    json.dumps(agent_profile.metadata),
                    datetime.now().isoformat()
                ))
            
            # Añadir a memoria
            self.agents[agent_profile.agent_id] = agent_profile
            
            self.logger.info(f"Agent {agent_profile.agent_id} registered with role {agent_profile.role.value}")
            
            # Registrar evento de scaling
            self._record_scaling_event("agent_registered", agent_profile.agent_id, 
                                     agent_profile.role, "Manual registration")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering agent {agent_profile.agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Desregistrar agente del sistema"""
        try:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            
            # Reasignar tareas activas
            self._reassign_agent_tasks(agent_id)
            
            # Actualizar estado en base de datos
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE agents SET status = ?, updated_at = ?
                    WHERE agent_id = ?
                """, (AgentStatus.OFFLINE.value, datetime.now().isoformat(), agent_id))
            
            # Remover de memoria
            del self.agents[agent_id]
            
            self.logger.info(f"Agent {agent_id} unregistered")
            
            # Registrar evento de scaling
            self._record_scaling_event("agent_unregistered", agent_id, 
                                     agent.role, "Manual unregistration")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False
    
    async def submit_task(self, task: Task) -> str:
        """Enviar tarea al sistema para procesamiento"""
        try:
            # Persistir tarea
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO tasks 
                    (task_id, task_type, priority, description, requirements, 
                     estimated_duration, max_retries, timeout, payload, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.task_id,
                    task.task_type,
                    task.priority.value,
                    task.description,
                    json.dumps(task.requirements),
                    task.estimated_duration,
                    task.max_retries,
                    task.timeout,
                    json.dumps(task.payload),
                    task.status.value
                ))
            
            # Añadir a cola de procesamiento
            await self.task_queue.put(task)
            
            self.logger.info(f"Task {task.task_id} submitted with priority {task.priority.value}")
            
            return task.task_id
            
        except Exception as e:
            self.logger.error(f"Error submitting task {task.task_id}: {e}")
            raise
    
    async def _process_task(self, task: Task):
        """Procesar una tarea individual"""
        try:
            # Encontrar agente apropiado
            agent = self._find_best_agent(task)
            
            if not agent:
                # No hay agentes disponibles, reencolar
                await asyncio.sleep(5)
                await self.task_queue.put(task)
                return
            
            # Asignar tarea al agente
            task.assigned_agent = agent.agent_id
            task.status = TaskStatus.ASSIGNED
            task.started_at = datetime.now().isoformat()
            
            # Actualizar carga del agente
            agent.current_load += 1
            
            # Persistir cambios
            self._update_task_status(task)
            self._update_agent_load(agent.agent_id, agent.current_load)
            
            # Añadir a tareas en ejecución
            self.running_tasks[task.task_id] = task
            
            # Ejecutar tarea en thread pool
            future = self.executor_pool.submit(self._execute_task, task, agent)
            
            # Monitorear ejecución
            asyncio.create_task(self._monitor_task_execution(task, future))
            
        except Exception as e:
            self.logger.error(f"Error processing task {task.task_id}: {e}")
            task.status = TaskStatus.FAILED
            self._update_task_status(task)
    
    def _find_best_agent(self, task: Task) -> Optional[AgentProfile]:
        """Encontrar el mejor agente para una tarea"""
        available_agents = [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE and agent.current_load < agent.max_load
        ]
        
        if not available_agents:
            return None
        
        # Filtrar por capacidades requeridas
        capable_agents = []
        for agent in available_agents:
            if self._agent_can_handle_task(agent, task):
                capable_agents.append(agent)
        
        if not capable_agents:
            return None
        
        # Aplicar estrategia de load balancing
        if self.load_balancing_strategy == "least_loaded":
            return min(capable_agents, key=lambda a: a.current_load)
        elif self.load_balancing_strategy == "capability_based":
            return max(capable_agents, key=lambda a: self._calculate_agent_score(a, task))
        else:  # round_robin
            return capable_agents[0]
    
    def _agent_can_handle_task(self, agent: AgentProfile, task: Task) -> bool:
        """Verificar si un agente puede manejar una tarea"""
        # Verificar capacidades
        agent_capabilities = {cap.name for cap in agent.capabilities}
        required_capabilities = set(task.requirements)
        
        if not required_capabilities.issubset(agent_capabilities):
            return False
        
        # Verificar rol apropiado
        if task.task_type == "coordination" and agent.role not in [AgentRole.COORDINATOR, AgentRole.DELEGATE]:
            return False
        
        if task.task_type == "specialized" and agent.role != AgentRole.SPECIALIST:
            return False
        
        return True
    
    def _calculate_agent_score(self, agent: AgentProfile, task: Task) -> float:
        """Calcular score de un agente para una tarea específica"""
        score = 0.0
        
        # Score basado en capacidades
        for requirement in task.requirements:
            for capability in agent.capabilities:
                if capability.name == requirement:
                    score += capability.level * 10
        
        # Penalizar por carga actual
        load_penalty = agent.current_load * 5
        score -= load_penalty
        
        # Bonus por performance histórica
        if "success_rate" in agent.performance_metrics:
            score += agent.performance_metrics["success_rate"] * 20
        
        return score
    
    def _execute_task(self, task: Task, agent: AgentProfile) -> Dict[str, Any]:
        """Ejecutar tarea (simulación - en implementación real llamaría al agente)"""
        try:
            # Simular ejecución de tarea
            time.sleep(min(task.estimated_duration, 10))  # Simular trabajo
            
            # Simular resultado exitoso (90% de probabilidad)
            import random
            if random.random() < 0.9:
                return {
                    "status": "success",
                    "result": f"Task {task.task_id} completed successfully by {agent.agent_id}",
                    "execution_time": task.estimated_duration,
                    "quality_score": random.uniform(0.7, 1.0)
                }
            else:
                raise Exception("Simulated task failure")
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time": task.estimated_duration
            }
    
    async def _monitor_task_execution(self, task: Task, future):
        """Monitorear ejecución de tarea"""
        try:
            # Esperar resultado con timeout
            result = await asyncio.wait_for(
                asyncio.wrap_future(future), 
                timeout=task.timeout
            )
            
            # Procesar resultado
            if result["status"] == "success":
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                
                # Actualizar métricas del agente
                self._update_agent_metrics(task.assigned_agent, task, result)
                
            else:
                task.status = TaskStatus.FAILED
                task.error_history.append({
                    "error": result.get("error", "Unknown error"),
                    "timestamp": datetime.now().isoformat(),
                    "retry_count": task.retry_count
                })
                
                # Intentar reintento si es posible
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.PENDING
                    await self.task_queue.put(task)
                
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error_history.append({
                "error": "Task timeout",
                "timestamp": datetime.now().isoformat(),
                "retry_count": task.retry_count
            })
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_history.append({
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "retry_count": task.retry_count
            })
            
        finally:
            # Limpiar estado
            if task.assigned_agent:
                agent = self.agents.get(task.assigned_agent)
                if agent:
                    agent.current_load = max(0, agent.current_load - 1)
                    self._update_agent_load(agent.agent_id, agent.current_load)
            
            # Mover de running a completed
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
            
            self.completed_tasks[task.task_id] = task
            
            # Persistir estado final
            self._update_task_status(task)
    
    def _update_task_status(self, task: Task):
        """Actualizar estado de tarea en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE tasks SET 
                        assigned_agent = ?, status = ?, started_at = ?, 
                        completed_at = ?, retry_count = ?, error_history = ?
                    WHERE task_id = ?
                """, (
                    task.assigned_agent,
                    task.status.value,
                    task.started_at,
                    task.completed_at,
                    task.retry_count,
                    json.dumps(task.error_history),
                    task.task_id
                ))
        except Exception as e:
            self.logger.error(f"Error updating task status: {e}")
    
    def _update_agent_load(self, agent_id: str, current_load: int):
        """Actualizar carga actual del agente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE agents SET current_load = ?, updated_at = ?
                    WHERE agent_id = ?
                """, (current_load, datetime.now().isoformat(), agent_id))
        except Exception as e:
            self.logger.error(f"Error updating agent load: {e}")
    
    def _update_agent_metrics(self, agent_id: str, task: Task, result: Dict[str, Any]):
        """Actualizar métricas de performance del agente"""
        try:
            # Registrar métricas específicas
            metrics = [
                ("execution_time", result.get("execution_time", 0)),
                ("quality_score", result.get("quality_score", 0)),
                ("success", 1 if result["status"] == "success" else 0)
            ]
            
            with sqlite3.connect(self.db_path) as conn:
                for metric_type, value in metrics:
                    conn.execute("""
                        INSERT INTO performance_metrics 
                        (metric_id, agent_id, task_id, metric_type, value)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        agent_id,
                        task.task_id,
                        metric_type,
                        value
                    ))
            
            # Actualizar métricas agregadas del agente
            self._recalculate_agent_metrics(agent_id)
            
        except Exception as e:
            self.logger.error(f"Error updating agent metrics: {e}")
    
    def _recalculate_agent_metrics(self, agent_id: str):
        """Recalcular métricas agregadas del agente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Calcular métricas de los últimos 7 días
                cursor = conn.execute("""
                    SELECT metric_type, AVG(value) as avg_value, COUNT(*) as count
                    FROM performance_metrics 
                    WHERE agent_id = ? AND timestamp >= datetime('now', '-7 days')
                    GROUP BY metric_type
                """, (agent_id,))
                
                metrics = {}
                for row in cursor.fetchall():
                    metric_type, avg_value, count = row
                    metrics[f"avg_{metric_type}"] = avg_value
                    metrics[f"count_{metric_type}"] = count
                
                # Calcular tasa de éxito
                if "count_success" in metrics and metrics["count_success"] > 0:
                    total_tasks = metrics["count_success"]
                    success_rate = metrics["avg_success"]
                    metrics["success_rate"] = success_rate
                
                # Actualizar agente
                if agent_id in self.agents:
                    self.agents[agent_id].performance_metrics = metrics
                
                # Persistir en base de datos
                conn.execute("""
                    UPDATE agents SET performance_metrics = ?, updated_at = ?
                    WHERE agent_id = ?
                """, (json.dumps(metrics), datetime.now().isoformat(), agent_id))
                
        except Exception as e:
            self.logger.error(f"Error recalculating agent metrics: {e}")
    
    async def _check_agent_health(self):
        """Verificar salud de todos los agentes"""
        current_time = datetime.now()
        
        for agent_id, agent in list(self.agents.items()):
            try:
                # Verificar último heartbeat
                last_heartbeat = datetime.fromisoformat(agent.last_heartbeat)
                time_diff = (current_time - last_heartbeat).total_seconds()
                
                if time_diff > 300:  # 5 minutos sin heartbeat
                    self.logger.warning(f"Agent {agent_id} missed heartbeat")
                    agent.status = AgentStatus.ERROR
                    
                    # Reasignar tareas si es necesario
                    self._reassign_agent_tasks(agent_id)
                
                # Verificar sobrecarga
                if agent.current_load > agent.max_load * 0.9:
                    agent.status = AgentStatus.OVERLOADED
                elif agent.current_load == 0:
                    agent.status = AgentStatus.IDLE
                else:
                    agent.status = AgentStatus.BUSY
                
                # Actualizar en base de datos
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE agents SET status = ?, updated_at = ?
                        WHERE agent_id = ?
                    """, (agent.status.value, current_time.isoformat(), agent_id))
                
            except Exception as e:
                self.logger.error(f"Error checking health for agent {agent_id}: {e}")
    
    async def _evaluate_scaling_needs(self):
        """Evaluar necesidades de auto-scaling"""
        try:
            # Calcular métricas del sistema
            total_agents = len(self.agents)
            busy_agents = sum(1 for agent in self.agents.values() 
                            if agent.status == AgentStatus.BUSY)
            queue_size = self.task_queue.qsize()
            
            # Determinar si necesitamos más agentes
            if total_agents > 0:
                utilization = busy_agents / total_agents
                
                # Scale up si utilización > 80% y hay tareas en cola
                if utilization > 0.8 and queue_size > 5:
                    await self._scale_up()
                
                # Scale down si utilización < 20% y no hay tareas en cola
                elif utilization < 0.2 and queue_size == 0:
                    await self._scale_down()
            
        except Exception as e:
            self.logger.error(f"Error evaluating scaling needs: {e}")
    
    async def _scale_up(self):
        """Escalar hacia arriba (añadir agentes)"""
        try:
            # Determinar qué tipo de agente necesitamos más
            role_demand = self._calculate_role_demand()
            
            for role, demand in role_demand.items():
                current_count = sum(1 for agent in self.agents.values() 
                                  if agent.role == role)
                max_count = self.max_agents_per_role[role]
                
                if demand > 0 and current_count < max_count:
                    # Crear nuevo agente (en implementación real, esto activaría un nuevo proceso)
                    new_agent_id = f"sam_{role.value}_{int(time.time())}"
                    
                    new_agent = AgentProfile(
                        agent_id=new_agent_id,
                        role=role,
                        status=AgentStatus.IDLE,
                        capabilities=self._get_default_capabilities(role),
                        current_load=0,
                        max_load=5,
                        performance_metrics={},
                        last_heartbeat=datetime.now().isoformat(),
                        metadata={"auto_scaled": True}
                    )
                    
                    if self.register_agent(new_agent):
                        self.logger.info(f"Auto-scaled up: created agent {new_agent_id} with role {role.value}")
                        
                        # Registrar evento
                        self._record_scaling_event("scale_up", new_agent_id, role, 
                                                 f"High demand for {role.value} agents")
            
        except Exception as e:
            self.logger.error(f"Error scaling up: {e}")
    
    async def _scale_down(self):
        """Escalar hacia abajo (remover agentes)"""
        try:
            # Encontrar agentes candidatos para remoción
            candidates = [
                agent for agent in self.agents.values()
                if (agent.status == AgentStatus.IDLE and 
                    agent.current_load == 0 and
                    agent.metadata.get("auto_scaled", False))
            ]
            
            # Remover hasta 1 agente por ciclo para evitar over-scaling
            if candidates:
                agent_to_remove = candidates[0]
                
                if self.unregister_agent(agent_to_remove.agent_id):
                    self.logger.info(f"Auto-scaled down: removed agent {agent_to_remove.agent_id}")
                    
                    # Registrar evento
                    self._record_scaling_event("scale_down", agent_to_remove.agent_id, 
                                             agent_to_remove.role, "Low system utilization")
            
        except Exception as e:
            self.logger.error(f"Error scaling down: {e}")
    
    def _calculate_role_demand(self) -> Dict[AgentRole, int]:
        """Calcular demanda por tipo de rol"""
        # Analizar tareas en cola y determinar qué roles se necesitan
        demand = {role: 0 for role in AgentRole}
        
        # En implementación real, esto analizaría las tareas en cola
        # Por ahora, simulamos demanda basada en carga actual
        for agent in self.agents.values():
            if agent.current_load >= agent.max_load * 0.8:
                demand[agent.role] += 1
        
        return demand
    
    def _get_default_capabilities(self, role: AgentRole) -> List[AgentCapability]:
        """Obtener capacidades por defecto para un rol"""
        base_capabilities = {
            AgentRole.EXECUTOR: [
                AgentCapability("code_generation", 8, ["python", "javascript"], 3, 2.0),
                AgentCapability("data_analysis", 7, ["pandas", "numpy"], 2, 1.5),
                AgentCapability("web_scraping", 6, ["requests", "selenium"], 2, 1.0)
            ],
            AgentRole.DELEGATE: [
                AgentCapability("task_coordination", 9, ["management"], 5, 3.0),
                AgentCapability("resource_allocation", 8, ["optimization"], 3, 2.5)
            ],
            AgentRole.COORDINATOR: [
                AgentCapability("multi_agent_coordination", 10, ["orchestration"], 10, 5.0),
                AgentCapability("workflow_management", 9, ["processes"], 8, 4.0)
            ],
            AgentRole.SPECIALIST: [
                AgentCapability("domain_expertise", 10, ["specialized"], 2, 1.0),
                AgentCapability("deep_analysis", 9, ["research"], 1, 0.5)
            ],
            AgentRole.MONITOR: [
                AgentCapability("system_monitoring", 10, ["observability"], 20, 10.0),
                AgentCapability("performance_analysis", 9, ["metrics"], 15, 8.0)
            ],
            AgentRole.BACKUP: [
                AgentCapability("failover_handling", 8, ["reliability"], 5, 2.0),
                AgentCapability("emergency_response", 9, ["incident"], 3, 1.5)
            ]
        }
        
        return base_capabilities.get(role, [])
    
    def _reassign_agent_tasks(self, agent_id: str):
        """Reasignar tareas de un agente que falló"""
        try:
            # Encontrar tareas asignadas al agente
            tasks_to_reassign = [
                task for task in self.running_tasks.values()
                if task.assigned_agent == agent_id
            ]
            
            for task in tasks_to_reassign:
                # Resetear asignación
                task.assigned_agent = None
                task.status = TaskStatus.PENDING
                task.retry_count += 1
                
                # Añadir error al historial
                task.error_history.append({
                    "error": f"Agent {agent_id} became unavailable",
                    "timestamp": datetime.now().isoformat(),
                    "retry_count": task.retry_count
                })
                
                # Reencolar si no ha excedido reintentos
                if task.retry_count <= task.max_retries:
                    asyncio.create_task(self.task_queue.put(task))
                else:
                    task.status = TaskStatus.FAILED
                
                # Actualizar en base de datos
                self._update_task_status(task)
                
                # Remover de running tasks
                if task.task_id in self.running_tasks:
                    del self.running_tasks[task.task_id]
            
            self.logger.info(f"Reassigned {len(tasks_to_reassign)} tasks from agent {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Error reassigning tasks from agent {agent_id}: {e}")
    
    def _record_scaling_event(self, event_type: str, agent_id: str, role: AgentRole, reason: str):
        """Registrar evento de scaling"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO scaling_events 
                    (event_id, event_type, agent_id, role, reason, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    event_type,
                    agent_id,
                    role.value,
                    reason,
                    json.dumps({"timestamp": datetime.now().isoformat()})
                ))
        except Exception as e:
            self.logger.error(f"Error recording scaling event: {e}")
    
    async def _cleanup_old_metrics(self):
        """Limpiar métricas antiguas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Eliminar métricas más antiguas de 30 días
                conn.execute("""
                    DELETE FROM performance_metrics 
                    WHERE timestamp < datetime('now', '-30 days')
                """)
                
                # Eliminar eventos de scaling más antiguos de 90 días
                conn.execute("""
                    DELETE FROM scaling_events 
                    WHERE timestamp < datetime('now', '-90 days')
                """)
                
                # Eliminar tareas completadas más antiguas de 7 días
                conn.execute("""
                    DELETE FROM tasks 
                    WHERE status IN ('completed', 'failed', 'cancelled') 
                    AND created_at < datetime('now', '-7 days')
                """)
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old metrics: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        try:
            # Estadísticas de agentes
            agent_stats = {}
            for role in AgentRole:
                agents_of_role = [a for a in self.agents.values() if a.role == role]
                agent_stats[role.value] = {
                    "total": len(agents_of_role),
                    "idle": sum(1 for a in agents_of_role if a.status == AgentStatus.IDLE),
                    "busy": sum(1 for a in agents_of_role if a.status == AgentStatus.BUSY),
                    "overloaded": sum(1 for a in agents_of_role if a.status == AgentStatus.OVERLOADED),
                    "error": sum(1 for a in agents_of_role if a.status == AgentStatus.ERROR)
                }
            
            # Estadísticas de tareas
            task_stats = {
                "pending": self.task_queue.qsize(),
                "running": len(self.running_tasks),
                "completed": len([t for t in self.completed_tasks.values() 
                               if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in self.completed_tasks.values() 
                             if t.status == TaskStatus.FAILED])
            }
            
            # Métricas de performance
            total_agents = len(self.agents)
            busy_agents = sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY)
            utilization = (busy_agents / total_agents) if total_agents > 0 else 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "agent_statistics": agent_stats,
                "task_statistics": task_stats,
                "system_metrics": {
                    "total_agents": total_agents,
                    "utilization": utilization,
                    "queue_size": self.task_queue.qsize(),
                    "load_balancing_strategy": self.load_balancing_strategy
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    def update_agent_heartbeat(self, agent_id: str) -> bool:
        """Actualizar heartbeat de un agente"""
        try:
            if agent_id in self.agents:
                self.agents[agent_id].last_heartbeat = datetime.now().isoformat()
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE agents SET last_heartbeat = ?, updated_at = ?
                        WHERE agent_id = ?
                    """, (
                        self.agents[agent_id].last_heartbeat,
                        datetime.now().isoformat(),
                        agent_id
                    ))
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating heartbeat for agent {agent_id}: {e}")
            return False

# Instancia global del gestor de roles
role_manager = AgentRoleManager()

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejemplo de uso
    async def demo():
        # Registrar algunos agentes
        executor_agent = AgentProfile(
            agent_id="sam_executor_001",
            role=AgentRole.EXECUTOR,
            status=AgentStatus.IDLE,
            capabilities=[
                AgentCapability("code_generation", 8, ["python"], 3, 2.0),
                AgentCapability("data_analysis", 7, ["pandas"], 2, 1.5)
            ],
            current_load=0,
            max_load=5,
            performance_metrics={},
            last_heartbeat=datetime.now().isoformat(),
            metadata={}
        )
        
        role_manager.register_agent(executor_agent)
        
        # Crear y enviar una tarea
        task = Task(
            task_id="task_001",
            task_type="code_generation",
            priority=TaskPriority.HIGH,
            description="Generate a Python function",
            requirements=["code_generation"],
            estimated_duration=30,
            max_retries=3,
            timeout=60,
            payload={"language": "python", "function": "fibonacci"}
        )
        
        await role_manager.submit_task(task)
        
        # Esperar un poco y mostrar estado
        await asyncio.sleep(5)
        status = role_manager.get_system_status()
        print(json.dumps(status, indent=2))
    
    # Ejecutar demo
    asyncio.run(demo())

