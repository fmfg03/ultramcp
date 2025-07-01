"""
Task Router MCP-Aware para Chain-of-Debate SuperMCP

Router inteligente que integra el sistema Chain-of-Debate con el ecosistema MCP,
proporcionando enrutamiento contextual, priorización automática y orchestración
de recursos basada en la carga de trabajo y disponibilidad del sistema.

Funcionalidades MCP:
- Integración con MCP Broker para events
- Routing basado en capabilities MCP
- Load balancing across MCP servers
- Resource-aware task distribution
- Priority queue management

Patrones de Routing:
- Content requests → Content generation pipeline
- Proposal requests → Business logic pipeline  
- Contract requests → Legal compliance pipeline
- Technical requests → Architecture analysis pipeline
- Strategy requests → Executive planning pipeline

Beneficios Empresariales:
- Automatic workload distribution
- SLA-aware routing decisions
- Cost optimization through intelligent routing
- Integration with existing MCP infrastructure
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
from collections import defaultdict, deque
import heapq

# MCP Integration imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP not available - using fallback routing")

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Tipos de tareas que puede manejar el router"""
    PROPOSAL = "proposal"
    CONTENT = "content" 
    CONTRACT = "contract"
    STRATEGY = "strategy"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    MARKETING = "marketing"
    LEGAL = "legal"

class Priority(Enum):
    """Niveles de prioridad"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BATCH = 5

class RouteStatus(Enum):
    """Estados de routing"""
    PENDING = "pending"
    ROUTED = "routed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class TaskRequest:
    """Request de tarea para routing"""
    task_id: str
    task_type: TaskType
    priority: Priority
    content: str
    context: Dict[str, Any]
    client_id: str
    deadline: Optional[datetime] = None
    resource_requirements: Dict[str, Any] = None
    mcp_context: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.resource_requirements is None:
            self.resource_requirements = {}
        if self.mcp_context is None:
            self.mcp_context = {}

@dataclass
class RouteDestination:
    """Destino de routing para una tarea"""
    destination_id: str
    destination_type: str  # "chain_of_debate", "mcp_server", "direct_llm"
    server_uri: Optional[str] = None
    capabilities: List[str] = None
    load_score: float = 0.0
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    cost_per_request: float = 0.0

@dataclass
class RoutingDecision:
    """Decisión de routing tomada por el sistema"""
    task_id: str
    destination: RouteDestination
    routing_reason: str
    confidence: float
    estimated_completion: datetime
    fallback_destinations: List[RouteDestination]
    routing_metadata: Dict[str, Any]

class MCPServerManager:
    """Manager para servidores MCP disponibles"""
    
    def __init__(self):
        self.available_servers = {}
        self.server_capabilities = {}
        self.server_health = {}
        self.load_metrics = defaultdict(float)
        
    async def discover_mcp_servers(self) -> List[Dict[str, Any]]:
        """Descubrir servidores MCP disponibles"""
        
        if not MCP_AVAILABLE:
            logger.warning("MCP not available - returning empty server list")
            return []
        
        # En producción, esto consultaría el MCP registry
        mock_servers = [
            {
                "id": "content-generator",
                "uri": "stdio://content-generator-server",
                "capabilities": ["content_generation", "copywriting", "blog_posts"],
                "priority_domains": ["content", "marketing"]
            },
            {
                "id": "contract-analyzer", 
                "uri": "stdio://contract-analyzer-server",
                "capabilities": ["contract_analysis", "legal_review", "compliance_check"],
                "priority_domains": ["contract", "legal"]
            },
            {
                "id": "strategy-advisor",
                "uri": "stdio://strategy-advisor-server", 
                "capabilities": ["strategic_planning", "market_analysis", "competitive_intel"],
                "priority_domains": ["strategy", "financial"]
            },
            {
                "id": "technical-architect",
                "uri": "stdio://technical-architect-server",
                "capabilities": ["system_design", "code_review", "architecture_planning"],
                "priority_domains": ["technical"]
            }
        ]
        
        for server in mock_servers:
            self.available_servers[server["id"]] = server
            self.server_capabilities[server["id"]] = server["capabilities"]
            self.server_health[server["id"]] = {
                "status": "healthy",
                "last_check": datetime.now(),
                "response_time": 2.5,
                "success_rate": 0.95
            }
        
        logger.info(f"🔍 Discovered {len(mock_servers)} MCP servers")
        return mock_servers
    
    async def check_server_health(self, server_id: str) -> Dict[str, Any]:
        """Verificar salud de un servidor MCP específico"""
        
        if server_id not in self.available_servers:
            return {"status": "not_found"}
        
        # Simular health check
        health = self.server_health.get(server_id, {})
        health["last_check"] = datetime.now()
        
        # Simular variación en health metrics
        import random
        health["response_time"] = random.uniform(1.0, 5.0)
        health["success_rate"] = random.uniform(0.85, 0.99)
        
        if health["success_rate"] > 0.95:
            health["status"] = "healthy"
        elif health["success_rate"] > 0.85:
            health["status"] = "degraded"
        else:
            health["status"] = "unhealthy"
        
        self.server_health[server_id] = health
        return health
    
    def get_servers_for_capability(self, capability: str) -> List[str]:
        """Obtener servidores que tienen una capability específica"""
        
        matching_servers = []
        for server_id, capabilities in self.server_capabilities.items():
            if capability in capabilities:
                matching_servers.append(server_id)
        
        return matching_servers
    
    def update_load_metrics(self, server_id: str, load_delta: float):
        """Actualizar métricas de carga de un servidor"""
        self.load_metrics[server_id] += load_delta
        
        # Decay load over time
        if self.load_metrics[server_id] > 0:
            self.load_metrics[server_id] *= 0.95

class TaskRouter:
    """
    Router principal MCP-aware para Chain-of-Debate
    """
    
    def __init__(self):
        self.mcp_manager = MCPServerManager()
        self.routing_rules = self._load_routing_rules()
        self.task_queue = []  # Priority queue
        self.active_tasks = {}
        self.completed_tasks = deque(maxlen=1000)
        
        # Métricas de routing
        self.routing_metrics = {
            "total_routed": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "avg_routing_time": 0.0,
            "load_distribution": defaultdict(int)
        }
        
        # Chain-of-Debate destination (always available)
        self.chain_of_debate_destination = RouteDestination(
            destination_id="chain_of_debate",
            destination_type="chain_of_debate",
            capabilities=["multi_llm_debate", "consensus_building", "quality_assurance"],
            load_score=0.0,
            success_rate=0.95,
            avg_response_time=120.0,  # 2 minutes average
            cost_per_request=0.50
        )
        
        # Inicializar MCP discovery
        asyncio.create_task(self._initialize_mcp_discovery())
        
        logger.info("🧭 Task Router MCP-Aware initialized")
    
    async def _initialize_mcp_discovery(self):
        """Inicializar discovery de servidores MCP"""
        try:
            await self.mcp_manager.discover_mcp_servers()
            logger.info("✅ MCP servers discovery completed")
        except Exception as e:
            logger.error(f"MCP discovery error: {e}")
    
    def _load_routing_rules(self) -> Dict[str, Any]:
        """Cargar reglas de routing"""
        
        return {
            # Reglas por tipo de tarea
            "task_type_routing": {
                TaskType.PROPOSAL: {
                    "preferred_destinations": ["chain_of_debate", "strategy-advisor"],
                    "required_capabilities": ["strategic_planning", "consensus_building"],
                    "quality_threshold": 0.8,
                    "timeout_minutes": 10
                },
                TaskType.CONTENT: {
                    "preferred_destinations": ["content-generator", "chain_of_debate"],
                    "required_capabilities": ["content_generation", "copywriting"],
                    "quality_threshold": 0.75,
                    "timeout_minutes": 5
                },
                TaskType.CONTRACT: {
                    "preferred_destinations": ["contract-analyzer", "chain_of_debate"],
                    "required_capabilities": ["contract_analysis", "legal_review"],
                    "quality_threshold": 0.9,
                    "timeout_minutes": 15
                },
                TaskType.STRATEGY: {
                    "preferred_destinations": ["strategy-advisor", "chain_of_debate"],
                    "required_capabilities": ["strategic_planning", "market_analysis"],
                    "quality_threshold": 0.85,
                    "timeout_minutes": 12
                },
                TaskType.TECHNICAL: {
                    "preferred_destinations": ["technical-architect", "chain_of_debate"],
                    "required_capabilities": ["system_design", "architecture_planning"],
                    "quality_threshold": 0.8,
                    "timeout_minutes": 8
                }
            },
            
            # Reglas de prioridad
            "priority_routing": {
                Priority.CRITICAL: {
                    "route_to_chain_of_debate": True,
                    "bypass_queue": True,
                    "max_response_time": 300  # 5 minutes
                },
                Priority.HIGH: {
                    "prefer_fast_destinations": True,
                    "max_response_time": 600  # 10 minutes
                },
                Priority.MEDIUM: {
                    "cost_optimize": True,
                    "max_response_time": 1800  # 30 minutes
                },
                Priority.LOW: {
                    "batch_process": True,
                    "max_response_time": 3600  # 1 hour
                }
            },
            
            # Fallback rules
            "fallback_strategy": {
                "max_fallback_attempts": 3,
                "fallback_timeout": 30,
                "always_fallback_to_chain_of_debate": True
            }
        }
    
    async def route_task(self, task_request: TaskRequest) -> RoutingDecision:
        """
        Enrutar una tarea al destino más apropiado
        
        Args:
            task_request: Request de la tarea a enrutar
            
        Returns:
            Decisión de routing con destino y metadata
        """
        
        routing_start = time.time()
        
        try:
            logger.info(f"🧭 Routing task {task_request.task_id} ({task_request.task_type.value})")
            
            # Agregar a queue si no es crítico
            if task_request.priority != Priority.CRITICAL:
                heapq.heappush(self.task_queue, (
                    task_request.priority.value,
                    task_request.created_at.timestamp(),
                    task_request
                ))
            
            # Obtener destinos candidatos
            candidate_destinations = await self._get_candidate_destinations(task_request)
            
            # Evaluar y ranking de destinos
            ranked_destinations = await self._rank_destinations(task_request, candidate_destinations)
            
            if not ranked_destinations:
                # Fallback a Chain-of-Debate si no hay otros destinos
                ranked_destinations = [self.chain_of_debate_destination]
                routing_reason = "No specialized destinations available - using Chain-of-Debate fallback"
            else:
                routing_reason = f"Routed to best destination based on {len(candidate_destinations)} candidates"
            
            # Seleccionar mejor destino
            best_destination = ranked_destinations[0]
            fallback_destinations = ranked_destinations[1:3]  # Top 2 fallbacks
            
            # Estimar tiempo de completion
            estimated_completion = datetime.now() + timedelta(
                seconds=best_destination.avg_response_time
            )
            
            # Crear decisión de routing
            routing_decision = RoutingDecision(
                task_id=task_request.task_id,
                destination=best_destination,
                routing_reason=routing_reason,
                confidence=self._calculate_routing_confidence(task_request, best_destination),
                estimated_completion=estimated_completion,
                fallback_destinations=fallback_destinations,
                routing_metadata={
                    "routing_time": time.time() - routing_start,
                    "candidates_evaluated": len(candidate_destinations),
                    "queue_position": len(self.task_queue) if task_request.priority != Priority.CRITICAL else 0,
                    "load_balancing_factor": best_destination.load_score
                }
            )
            
            # Actualizar métricas
            self._update_routing_metrics(routing_decision)
            
            # Registrar tarea activa
            self.active_tasks[task_request.task_id] = {
                "request": task_request,
                "routing_decision": routing_decision,
                "status": RouteStatus.ROUTED,
                "routed_at": datetime.now()
            }
            
            logger.info(f"✅ Task {task_request.task_id} routed to {best_destination.destination_id}")
            
            return routing_decision
            
        except Exception as e:
            logger.error(f"Routing error for task {task_request.task_id}: {e}")
            
            # Emergency fallback to Chain-of-Debate
            emergency_decision = RoutingDecision(
                task_id=task_request.task_id,
                destination=self.chain_of_debate_destination,
                routing_reason=f"Emergency fallback due to routing error: {str(e)}",
                confidence=0.7,
                estimated_completion=datetime.now() + timedelta(minutes=5),
                fallback_destinations=[],
                routing_metadata={"error": str(e), "emergency_fallback": True}
            )
            
            return emergency_decision
    
    async def _get_candidate_destinations(self, task_request: TaskRequest) -> List[RouteDestination]:
        """Obtener destinos candidatos para una tarea"""
        
        candidates = []
        
        # Siempre incluir Chain-of-Debate como opción
        candidates.append(self.chain_of_debate_destination)
        
        # Buscar servidores MCP especializados
        task_rules = self.routing_rules["task_type_routing"].get(task_request.task_type, {})
        preferred_destinations = task_rules.get("preferred_destinations", [])
        
        for dest_id in preferred_destinations:
            if dest_id == "chain_of_debate":
                continue  # Ya agregado
            
            if dest_id in self.mcp_manager.available_servers:
                server_info = self.mcp_manager.available_servers[dest_id]
                health = await self.mcp_manager.check_server_health(dest_id)
                
                if health["status"] in ["healthy", "degraded"]:
                    candidate = RouteDestination(
                        destination_id=dest_id,
                        destination_type="mcp_server",
                        server_uri=server_info["uri"],
                        capabilities=server_info["capabilities"],
                        load_score=self.mcp_manager.load_metrics[dest_id],
                        success_rate=health["success_rate"],
                        avg_response_time=health["response_time"],
                        cost_per_request=self._estimate_mcp_cost(dest_id)
                    )
                    candidates.append(candidate)
        
        logger.debug(f"Found {len(candidates)} candidate destinations for {task_request.task_type.value}")
        return candidates
    
    async def _rank_destinations(
        self, 
        task_request: TaskRequest, 
        candidates: List[RouteDestination]
    ) -> List[RouteDestination]:
        """Ranking de destinos basado en múltiples factores"""
        
        scored_destinations = []
        
        for destination in candidates:
            score = await self._calculate_destination_score(task_request, destination)
            scored_destinations.append((score, destination))
        
        # Ordenar por score (mayor es mejor)
        scored_destinations.sort(key=lambda x: x[0], reverse=True)
        
        return [dest for score, dest in scored_destinations]
    
    async def _calculate_destination_score(
        self,
        task_request: TaskRequest, 
        destination: RouteDestination
    ) -> float:
        """Calcular score de un destino para una tarea específica"""
        
        score_factors = []
        
        # Factor 1: Capability match (40%)
        capability_score = self._calculate_capability_match(task_request, destination)
        score_factors.append(("capability", capability_score, 0.4))
        
        # Factor 2: Performance (25%)
        performance_score = destination.success_rate * (1 / max(destination.avg_response_time, 1))
        normalized_performance = min(1.0, performance_score / 0.5)  # Normalize
        score_factors.append(("performance", normalized_performance, 0.25))
        
        # Factor 3: Load balancing (20%)
        load_score = max(0, 1.0 - destination.load_score)
        score_factors.append(("load", load_score, 0.2))
        
        # Factor 4: Cost efficiency (15%)
        cost_score = max(0, 1.0 - (destination.cost_per_request / 2.0))  # Normalize to $2 max
        score_factors.append(("cost", cost_score, 0.15))
        
        # Calcular score final ponderado
        final_score = sum(score * weight for name, score, weight in score_factors)
        
        # Aplicar bonificaciones por prioridad
        if task_request.priority == Priority.CRITICAL:
            if destination.destination_id == "chain_of_debate":
                final_score *= 1.2  # Bonus for Chain-of-Debate en crítico
        
        logger.debug(f"Destination {destination.destination_id} score: {final_score:.3f}")
        return final_score
    
    def _calculate_capability_match(
        self, 
        task_request: TaskRequest, 
        destination: RouteDestination
    ) -> float:
        """Calcular qué tan bien match las capabilities del destino con la tarea"""
        
        task_rules = self.routing_rules["task_type_routing"].get(task_request.task_type, {})
        required_capabilities = task_rules.get("required_capabilities", [])
        
        if not required_capabilities:
            return 0.8  # Score neutral si no hay requirements específicos
        
        if not destination.capabilities:
            return 0.5  # Score bajo si destino no tiene capabilities definidas
        
        # Calcular overlap
        matching_capabilities = set(required_capabilities) & set(destination.capabilities)
        match_ratio = len(matching_capabilities) / len(required_capabilities)
        
        # Bonus por capabilities adicionales relevantes
        task_keywords = {
            TaskType.PROPOSAL: ["strategic", "business", "planning"],
            TaskType.CONTENT: ["content", "writing", "marketing"],
            TaskType.CONTRACT: ["legal", "compliance", "analysis"],
            TaskType.STRATEGY: ["strategic", "market", "competitive"],
            TaskType.TECHNICAL: ["technical", "system", "architecture"]
        }
        
        relevant_keywords = task_keywords.get(task_request.task_type, [])
        bonus_capabilities = 0
        
        for capability in destination.capabilities:
            for keyword in relevant_keywords:
                if keyword in capability.lower():
                    bonus_capabilities += 0.1
                    break
        
        final_match_score = min(1.0, match_ratio + bonus_capabilities)
        return final_match_score
    
    def _estimate_mcp_cost(self, server_id: str) -> float:
        """Estimar costo de usar un servidor MCP específico"""
        
        # Costs basados en tipo de servidor
        cost_estimates = {
            "content-generator": 0.25,
            "contract-analyzer": 0.45, 
            "strategy-advisor": 0.35,
            "technical-architect": 0.30
        }
        
        return cost_estimates.get(server_id, 0.40)
    
    def _calculate_routing_confidence(
        self, 
        task_request: TaskRequest, 
        destination: RouteDestination
    ) -> float:
        """Calcular confianza en la decisión de routing"""
        
        confidence_factors = []
        
        # Factor 1: Match de capabilities
        capability_match = self._calculate_capability_match(task_request, destination)
        confidence_factors.append(capability_match * 0.4)
        
        # Factor 2: Health del destino
        if destination.destination_type == "chain_of_debate":
            health_score = 0.95  # Chain-of-Debate siempre confiable
        else:
            health_score = destination.success_rate
        confidence_factors.append(health_score * 0.3)
        
        # Factor 3: Experiencia con tipo de tarea
        task_experience = self._get_destination_task_experience(destination, task_request.task_type)
        confidence_factors.append(task_experience * 0.2)
        
        # Factor 4: Load actual
        load_factor = max(0.5, 1.0 - destination.load_score)
        confidence_factors.append(load_factor * 0.1)
        
        return sum(confidence_factors)
    
    def _get_destination_task_experience(
        self, 
        destination: RouteDestination, 
        task_type: TaskType
    ) -> float:
        """Obtener experiencia de un destino con un tipo de tarea"""
        
        # Simular basado en tasks completadas exitosamente
        experience_data = {
            "chain_of_debate": {
                TaskType.PROPOSAL: 0.95,
                TaskType.STRATEGY: 0.92,
                TaskType.CONTRACT: 0.88,
                TaskType.CONTENT: 0.85,
                TaskType.TECHNICAL: 0.90
            },
            "content-generator": {
                TaskType.CONTENT: 0.95,
                TaskType.MARKETING: 0.90
            },
            "contract-analyzer": {
                TaskType.CONTRACT: 0.98,
                TaskType.LEGAL: 0.95
            }
        }
        
        dest_experience = experience_data.get(destination.destination_id, {})
        return dest_experience.get(task_type, 0.7)  # Default experience
    
    def _update_routing_metrics(self, routing_decision: RoutingDecision):
        """Actualizar métricas de routing"""
        
        self.routing_metrics["total_routed"] += 1
        self.routing_metrics["load_distribution"][routing_decision.destination.destination_id] += 1
        
        routing_time = routing_decision.routing_metadata.get("routing_time", 0)
        
        # Calcular promedio de routing time
        current_avg = self.routing_metrics["avg_routing_time"]
        total_routed = self.routing_metrics["total_routed"]
        
        self.routing_metrics["avg_routing_time"] = (
            (current_avg * (total_routed - 1) + routing_time) / total_routed
        )
    
    async def process_task_queue(self):
        """Procesar queue de tareas de forma continua"""
        
        while True:
            try:
                if self.task_queue:
                    # Obtener task de mayor prioridad
                    priority, timestamp, task_request = heapq.heappop(self.task_queue)
                    
                    # Verificar si no ha expirado
                    if task_request.deadline and datetime.now() > task_request.deadline:
                        logger.warning(f"Task {task_request.task_id} expired - skipping")
                        continue
                    
                    # Procesar task
                    routing_decision = await self.route_task(task_request)
                    await self._execute_routing_decision(task_request, routing_decision)
                
                # Sleep corto para no consumir CPU
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Task queue processing error: {e}")
                await asyncio.sleep(5)
    
    async def _execute_routing_decision(
        self, 
        task_request: TaskRequest, 
        routing_decision: RoutingDecision
    ):
        """Ejecutar una decisión de routing"""
        
        try:
            destination = routing_decision.destination
            
            if destination.destination_type == "chain_of_debate":
                # Enrutar a Chain-of-Debate local
                await self._route_to_chain_of_debate(task_request, routing_decision)
            
            elif destination.destination_type == "mcp_server":
                # Enrutar a servidor MCP
                await self._route_to_mcp_server(task_request, routing_decision)
            
            else:
                logger.error(f"Unknown destination type: {destination.destination_type}")
                # Fallback to Chain-of-Debate
                await self._route_to_chain_of_debate(task_request, routing_decision)
                
        except Exception as e:
            logger.error(f"Routing execution error for {task_request.task_id}: {e}")
            # Intentar fallback
            await self._execute_fallback_routing(task_request, routing_decision)
    
    async def _route_to_chain_of_debate(
        self, 
        task_request: TaskRequest, 
        routing_decision: RoutingDecision
    ):
        """Enrutar tarea al sistema Chain-of-Debate local"""
        
        try:
            # Importar componentes locales
            from entrypoint import submit_debate_task
            
            # Preparar request para Chain-of-Debate
            debate_request = {
                "content": task_request.content,
                "domain": task_request.task_type.value,
                "context": {
                    **task_request.context,
                    "router_metadata": {
                        "routed_from": "task_router",
                        "routing_confidence": routing_decision.confidence,
                        "client_id": task_request.client_id
                    }
                },
                "priority": task_request.priority.value,
                "deadline": task_request.deadline.isoformat() if task_request.deadline else None
            }
            
            # Ejecutar debate (esto sería async en producción)
            logger.info(f"🎪 Routing {task_request.task_id} to Chain-of-Debate")
            # En producción, esto sería una llamada async al sistema de debate
            
            # Actualizar métricas
            self.mcp_manager.update_load_metrics("chain_of_debate", 1.0)
            
        except Exception as e:
            logger.error(f"Chain-of-Debate routing error: {e}")
            raise
    
    async def _route_to_mcp_server(
        self, 
        task_request: TaskRequest, 
        routing_decision: RoutingDecision
    ):
        """Enrutar tarea a servidor MCP"""
        
        if not MCP_AVAILABLE:
            logger.warning("MCP not available - falling back to Chain-of-Debate")
            await self._route_to_chain_of_debate(task_request, routing_decision)
            return
        
        try:
            destination = routing_decision.destination
            server_id = destination.destination_id
            
            logger.info(f"🔌 Routing {task_request.task_id} to MCP server {server_id}")
            
            # En producción, esto establecería conexión MCP real
            # async with stdio_client(StdioServerParameters(
            #     command=destination.server_uri
            # )) as (read, write):
            #     async with ClientSession(read, write) as session:
            #         result = await session.call_tool("process_task", {
            #             "task_content": task_request.content,
            #             "task_type": task_request.task_type.value,
            #             "context": task_request.context
            #         })
            
            # Simular procesamiento MCP
            await asyncio.sleep(destination.avg_response_time / 10)  # Simular latencia
            
            # Actualizar métricas
            self.mcp_manager.update_load_metrics(server_id, 1.0)
            
            logger.info(f"✅ Task {task_request.task_id} processed by MCP server {server_id}")
            
        except Exception as e:
            logger.error(f"MCP server routing error: {e}")
            raise
    
    async def _execute_fallback_routing(
        self, 
        task_request: TaskRequest, 
        original_routing_decision: RoutingDecision
    ):
        """Ejecutar routing de fallback"""
        
        fallback_destinations = original_routing_decision.fallback_destinations
        
        for fallback_dest in fallback_destinations:
            try:
                logger.info(f"🔄 Attempting fallback to {fallback_dest.destination_id}")
                
                fallback_decision = RoutingDecision(
                    task_id=task_request.task_id,
                    destination=fallback_dest,
                    routing_reason="Fallback after primary destination failed",
                    confidence=original_routing_decision.confidence * 0.8,
                    estimated_completion=datetime.now() + timedelta(seconds=fallback_dest.avg_response_time),
                    fallback_destinations=[],
                    routing_metadata={"is_fallback": True}
                )
                
                await self._execute_routing_decision(task_request, fallback_decision)
                return  # Success - exit fallback loop
                
            except Exception as e:
                logger.warning(f"Fallback to {fallback_dest.destination_id} also failed: {e}")
                continue
        
        # Si todos los fallbacks fallan, usar Chain-of-Debate como último recurso
        logger.error(f"All fallbacks failed for {task_request.task_id} - using emergency Chain-of-Debate")
        await self._route_to_chain_of_debate(task_request, original_routing_decision)
    
    # API Methods públicos
    
    def get_routing_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de routing de una tarea"""
        
        if task_id in self.active_tasks:
            task_info = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task_info["status"].value,
                "destination": task_info["routing_decision"].destination.destination_id,
                "routed_at": task_info["routed_at"].isoformat(),
                "confidence": task_info["routing_decision"].confidence,
                "estimated_completion": task_info["routing_decision"].estimated_completion.isoformat()
            }
        
        return None
    
    def get_router_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del router"""
        
        return {
            **self.routing_metrics,
            "active_tasks": len(self.active_tasks),
            "queue_length": len(self.task_queue),
            "available_destinations": len(self.mcp_manager.available_servers) + 1,  # +1 for Chain-of-Debate
            "mcp_servers_health": {
                server_id: health["status"] 
                for server_id, health in self.mcp_manager.server_health.items()
            },
            "load_distribution_percentage": self._calculate_load_distribution()
        }
    
    def _calculate_load_distribution(self) -> Dict[str, float]:
        """Calcular distribución porcentual de carga"""
        
        total_load = sum(self.routing_metrics["load_distribution"].values())
        
        if total_load == 0:
            return {}
        
        return {
            dest_id: (count / total_load) * 100 
            for dest_id, count in self.routing_metrics["load_distribution"].items()
        }
    
    def get_mcp_server_status(self) -> Dict[str, Any]:
        """Obtener estado de servidores MCP"""
        
        return {
            "total_servers": len(self.mcp_manager.available_servers),
            "healthy_servers": len([
                h for h in self.mcp_manager.server_health.values() 
                if h["status"] == "healthy"
            ]),
            "server_details": {
                server_id: {
                    "capabilities": self.mcp_manager.server_capabilities.get(server_id, []),
                    "health": self.mcp_manager.server_health.get(server_id, {}),
                    "current_load": self.mcp_manager.load_metrics.get(server_id, 0.0)
                }
                for server_id in self.mcp_manager.available_servers.keys()
            }
        }
    
    async def optimize_routing_rules(self) -> Dict[str, Any]:
        """Optimizar reglas de routing basado en performance histórico"""
        
        # Analizar performance de destinos por tipo de tarea
        performance_analysis = defaultdict(lambda: defaultdict(list))
        
        for task_info in list(self.completed_tasks):
            if "routing_decision" in task_info:
                task_type = task_info["request"].task_type
                destination = task_info["routing_decision"].destination.destination_id
                success = task_info.get("success", True)
                
                performance_analysis[task_type][destination].append(success)
        
        # Generar recomendaciones de optimización
        recommendations = []
        
        for task_type, destinations in performance_analysis.items():
            best_destination = None
            best_success_rate = 0
            
            for destination, results in destinations.items():
                if results:
                    success_rate = sum(results) / len(results)
                    if success_rate > best_success_rate:
                        best_success_rate = success_rate
                        best_destination = destination
            
            if best_destination and best_success_rate > 0.9:
                recommendations.append(
                    f"Consider prioritizing {best_destination} for {task_type.value} tasks "
                    f"(success rate: {best_success_rate:.1%})"
                )
        
        return {
            "analysis_completed": True,
            "tasks_analyzed": len(self.completed_tasks),
            "optimization_recommendations": recommendations,
            "performance_summary": dict(performance_analysis)
        }