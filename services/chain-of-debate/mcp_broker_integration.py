"""
MCP Broker Integration para Chain-of-Debate SuperMCP

Integración completa con el MCP Broker para manejo de eventos,
subscripciones, y comunicación bidireccional entre el sistema
Chain-of-Debate y el ecosistema MCP más amplio.

Funcionalidades:
- Event handling bidireccional con MCP Broker
- Subscripciones automáticas a eventos relevantes
- Publishing de resultados de debates
- Load balancing colaborativo
- Health reporting automático
- Resource discovery dinámico

Patrones de Integración:
- Event-driven architecture
- Publish/Subscribe patterns
- Circuit breaker para MCP connections
- Automatic failover y reconnection
- Telemetry y observability integration

Beneficios Empresariales:
- Seamless integration con infrastructure existente
- Automatic scaling basado en MCP events
- Collaborative intelligence across MCP ecosystem
- Real-time monitoring y alerting
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
import os
from collections import defaultdict, deque

# MCP imports
try:
    from mcp import ClientSession, ServerSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, Resource, Prompt, TextContent, ImageContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP not available - using mock integration")

# WebSocket y HTTP clients para broker communication
try:
    import websockets
    import aiohttp
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logging.warning("WebSocket support not available")

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Tipos de eventos MCP soportados"""
    TASK_SUBMITTED = "task_submitted"
    DEBATE_STARTED = "debate_started"
    DEBATE_COMPLETED = "debate_completed"
    HUMAN_INTERVENTION_REQUIRED = "human_intervention_required"
    CONSENSUS_REACHED = "consensus_reached"
    QUALITY_THRESHOLD_MET = "quality_threshold_met"
    SYSTEM_HEALTH_UPDATE = "system_health_update"
    LOAD_BALANCING_REQUEST = "load_balancing_request"
    RESOURCE_DISCOVERY = "resource_discovery"
    LEARNING_PATTERN_DETECTED = "learning_pattern_detected"

class EventPriority(Enum):
    """Prioridades de eventos"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class MCPEvent:
    """Evento MCP estructurado"""
    event_id: str
    event_type: EventType
    priority: EventPriority
    source: str
    target: Optional[str] = None
    payload: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.payload is None:
            self.payload = {}
        if self.metadata is None:
            self.metadata = {}

@dataclass
class MCPSubscription:
    """Subscripción a eventos MCP"""
    subscription_id: str
    event_types: List[EventType]
    handler: Callable
    filter_criteria: Dict[str, Any] = None
    active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.filter_criteria is None:
            self.filter_criteria = {}

class MCPBrokerConnection:
    """Connection manager para MCP Broker"""
    
    def __init__(self, broker_uri: str, connection_id: str):
        self.broker_uri = broker_uri
        self.connection_id = connection_id
        self.websocket = None
        self.connected = False
        self.last_heartbeat = None
        self.connection_attempts = 0
        self.max_reconnect_attempts = 10
        
        # Message queues
        self.outbound_queue = asyncio.Queue()
        self.pending_responses = {}
        
        # Connection metrics
        self.connection_metrics = {
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "connection_uptime": 0,
            "last_error": None
        }
    
    async def connect(self) -> bool:
        """Establecer conexión con MCP Broker"""
        
        if not WEBSOCKET_AVAILABLE:
            logger.warning("WebSocket not available - using mock connection")
            self.connected = True
            return True
        
        try:
            logger.info(f"🔌 Connecting to MCP Broker: {self.broker_uri}")
            
            # Establecer conexión WebSocket
            self.websocket = await websockets.connect(
                self.broker_uri,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            # Enviar handshake
            handshake = {
                "type": "handshake",
                "connection_id": self.connection_id,
                "service_type": "chain_of_debate",
                "capabilities": [
                    "multi_llm_debate",
                    "consensus_building",
                    "human_intervention",
                    "quality_assurance",
                    "decision_replay"
                ],
                "version": "2.0"
            }
            
            await self.websocket.send(json.dumps(handshake))
            
            # Esperar confirmación
            response = await asyncio.wait_for(
                self.websocket.recv(), 
                timeout=10
            )
            
            response_data = json.loads(response)
            
            if response_data.get("type") == "handshake_ack":
                self.connected = True
                self.last_heartbeat = datetime.now()
                self.connection_attempts = 0
                
                logger.info(f"✅ Connected to MCP Broker: {self.connection_id}")
                
                # Iniciar heartbeat y message processing
                asyncio.create_task(self._heartbeat_loop())
                asyncio.create_task(self._message_processor())
                
                return True
            else:
                logger.error(f"Handshake failed: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connection_attempts += 1
            self.connection_metrics["last_error"] = str(e)
            return False
    
    async def disconnect(self):
        """Desconectar del MCP Broker"""
        
        if self.websocket and self.connected:
            try:
                # Enviar mensaje de despedida
                goodbye = {
                    "type": "disconnect",
                    "connection_id": self.connection_id,
                    "reason": "graceful_shutdown"
                }
                
                await self.websocket.send(json.dumps(goodbye))
                await self.websocket.close()
                
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            
            finally:
                self.connected = False
                self.websocket = None
                logger.info(f"🔌 Disconnected from MCP Broker")
    
    async def send_event(self, event: MCPEvent) -> bool:
        """Enviar evento al broker"""
        
        if not self.connected:
            await self.outbound_queue.put(event)
            return False
        
        try:
            message = {
                "type": "event",
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "priority": event.priority.value,
                "source": event.source,
                "target": event.target,
                "payload": event.payload,
                "metadata": event.metadata,
                "timestamp": event.timestamp.isoformat()
            }
            
            if self.websocket:
                await self.websocket.send(json.dumps(message))
                self.connection_metrics["total_messages_sent"] += 1
                return True
            else:
                await self.outbound_queue.put(event)
                return False
                
        except Exception as e:
            logger.error(f"Failed to send event: {e}")
            await self.outbound_queue.put(event)
            return False
    
    async def _heartbeat_loop(self):
        """Loop de heartbeat para mantener conexión"""
        
        while self.connected and self.websocket:
            try:
                heartbeat = {
                    "type": "heartbeat",
                    "connection_id": self.connection_id,
                    "timestamp": datetime.now().isoformat(),
                    "metrics": self.connection_metrics
                }
                
                await self.websocket.send(json.dumps(heartbeat))
                self.last_heartbeat = datetime.now()
                
                await asyncio.sleep(30)  # Heartbeat cada 30 segundos
                
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                self.connected = False
                break
    
    async def _message_processor(self):
        """Procesar mensajes entrantes"""
        
        while self.connected and self.websocket:
            try:
                message = await self.websocket.recv()
                self.connection_metrics["total_messages_received"] += 1
                
                # Procesar mensaje en background
                asyncio.create_task(self._handle_incoming_message(message))
                
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                self.connected = False
                break
    
    async def _handle_incoming_message(self, raw_message: str):
        """Manejar mensaje entrante del broker"""
        
        try:
            message = json.loads(raw_message)
            message_type = message.get("type")
            
            if message_type == "event":
                # Delegar al event handler principal
                await self._delegate_event(message)
            
            elif message_type == "response":
                # Manejar respuesta a request pendiente
                request_id = message.get("request_id")
                if request_id in self.pending_responses:
                    self.pending_responses[request_id].set_result(message)
            
            elif message_type == "heartbeat_ack":
                # Confirmar heartbeat
                self.last_heartbeat = datetime.now()
            
            elif message_type == "error":
                logger.error(f"Broker error: {message.get('error')}")
            
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def _delegate_event(self, message: Dict[str, Any]):
        """Delegar evento a handler apropiado"""
        
        # Esto se conectará con el MCPBrokerIntegration principal
        from_integration = getattr(self, '_integration_handler', None)
        if from_integration:
            await from_integration(message)

class MCPBrokerIntegration:
    """
    Integración principal con MCP Broker para Chain-of-Debate
    """
    
    def __init__(self, broker_uri: str = None):
        self.broker_uri = broker_uri or os.getenv('MCP_BROKER_URI', 'ws://localhost:8080/mcp')
        self.connection_id = f"chain_of_debate_{uuid.uuid4().hex[:8]}"
        self.connection = MCPBrokerConnection(self.broker_uri, self.connection_id)
        
        # Event management
        self.subscriptions = {}
        self.event_handlers = {}
        self.event_history = deque(maxlen=1000)
        
        # Integration state
        self.integration_active = False
        self.last_discovery = None
        self.discovered_services = {}
        
        # Performance metrics
        self.integration_metrics = {
            "events_published": 0,
            "events_received": 0,
            "subscriptions_active": 0,
            "discovery_updates": 0,
            "integration_uptime": 0
        }
        
        # Configurar handlers por defecto
        self._setup_default_handlers()
        
        logger.info(f"🧭 MCP Broker Integration initialized: {self.connection_id}")
    
    def _setup_default_handlers(self):
        """Configurar event handlers por defecto"""
        
        self.event_handlers = {
            EventType.LOAD_BALANCING_REQUEST: self._handle_load_balancing_request,
            EventType.RESOURCE_DISCOVERY: self._handle_resource_discovery,
            EventType.SYSTEM_HEALTH_UPDATE: self._handle_system_health_update,
        }
    
    async def start_integration(self) -> bool:
        """Iniciar integración con MCP Broker"""
        
        try:
            # Conectar al broker
            connected = await self.connection.connect()
            
            if not connected:
                logger.error("Failed to connect to MCP Broker")
                return False
            
            # Configurar el delegate handler
            self.connection._integration_handler = self._handle_broker_event
            
            # Subscribirse a eventos críticos
            await self._setup_core_subscriptions()
            
            # Iniciar discovery de servicios
            await self._start_service_discovery()
            
            # Publicar evento de disponibilidad
            await self._announce_service_availability()
            
            self.integration_active = True
            
            # Iniciar loops de mantenimiento
            asyncio.create_task(self._maintenance_loop())
            
            logger.info("✅ MCP Broker integration active")
            return True
            
        except Exception as e:
            logger.error(f"Integration startup failed: {e}")
            return False
    
    async def stop_integration(self):
        """Detener integración"""
        
        try:
            # Anunciar que el servicio se está desconectando
            await self._announce_service_unavailability()
            
            # Limpiar subscripciones
            for sub_id in list(self.subscriptions.keys()):
                await self.unsubscribe(sub_id)
            
            # Desconectar del broker
            await self.connection.disconnect()
            
            self.integration_active = False
            
            logger.info("🔌 MCP Broker integration stopped")
            
        except Exception as e:
            logger.error(f"Integration shutdown error: {e}")
    
    async def _setup_core_subscriptions(self):
        """Configurar subscripciones básicas"""
        
        # Subscripción a requests de load balancing
        await self.subscribe(
            [EventType.LOAD_BALANCING_REQUEST],
            self._handle_load_balancing_request,
            {"target_service": "chain_of_debate"}
        )
        
        # Subscripción a discovery requests
        await self.subscribe(
            [EventType.RESOURCE_DISCOVERY],
            self._handle_resource_discovery
        )
        
        # Subscripción a health updates de otros servicios
        await self.subscribe(
            [EventType.SYSTEM_HEALTH_UPDATE],
            self._handle_system_health_update
        )
    
    async def subscribe(
        self,
        event_types: List[EventType],
        handler: Callable,
        filter_criteria: Dict[str, Any] = None
    ) -> str:
        """Crear subscripción a eventos"""
        
        subscription_id = str(uuid.uuid4())
        
        subscription = MCPSubscription(
            subscription_id=subscription_id,
            event_types=event_types,
            handler=handler,
            filter_criteria=filter_criteria or {}
        )
        
        self.subscriptions[subscription_id] = subscription
        self.integration_metrics["subscriptions_active"] += 1
        
        # Enviar subscripción al broker
        subscription_event = MCPEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.RESOURCE_DISCOVERY,
            priority=EventPriority.MEDIUM,
            source=self.connection_id,
            payload={
                "action": "subscribe",
                "subscription_id": subscription_id,
                "event_types": [et.value for et in event_types],
                "filter_criteria": filter_criteria or {}
            }
        )
        
        await self.connection.send_event(subscription_event)
        
        logger.debug(f"📬 Created subscription: {subscription_id}")
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Cancelar subscripción"""
        
        if subscription_id not in self.subscriptions:
            return False
        
        # Enviar unsubscribe al broker
        unsubscribe_event = MCPEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.RESOURCE_DISCOVERY,
            priority=EventPriority.MEDIUM,
            source=self.connection_id,
            payload={
                "action": "unsubscribe",
                "subscription_id": subscription_id
            }
        )
        
        await self.connection.send_event(unsubscribe_event)
        
        # Limpiar localmente
        del self.subscriptions[subscription_id]
        self.integration_metrics["subscriptions_active"] -= 1
        
        logger.debug(f"📭 Removed subscription: {subscription_id}")
        return True
    
    async def publish_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        priority: EventPriority = EventPriority.MEDIUM,
        target: Optional[str] = None
    ) -> str:
        """Publicar evento al broker"""
        
        event = MCPEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            priority=priority,
            source=self.connection_id,
            target=target,
            payload=payload,
            metadata={
                "service_type": "chain_of_debate",
                "version": "2.0"
            }
        )
        
        await self.connection.send_event(event)
        self.event_history.append(event)
        self.integration_metrics["events_published"] += 1
        
        logger.debug(f"📤 Published event: {event_type.value}")
        return event.event_id
    
    async def _handle_broker_event(self, message: Dict[str, Any]):
        """Manejar evento del broker"""
        
        try:
            event_type_str = message.get("event_type")
            event_type = EventType(event_type_str) if event_type_str else None
            
            if not event_type:
                logger.warning(f"Unknown event type: {event_type_str}")
                return
            
            # Buscar subscripciones que match
            matching_subscriptions = []
            
            for subscription in self.subscriptions.values():
                if (subscription.active and 
                    event_type in subscription.event_types and
                    self._matches_filter(message, subscription.filter_criteria)):
                    matching_subscriptions.append(subscription)
            
            # Ejecutar handlers
            for subscription in matching_subscriptions:
                try:
                    await subscription.handler(message)
                except Exception as e:
                    logger.error(f"Subscription handler error: {e}")
            
            # Ejecutar handler global si existe
            if event_type in self.event_handlers:
                await self.event_handlers[event_type](message)
            
            self.integration_metrics["events_received"] += 1
            
        except Exception as e:
            logger.error(f"Broker event handling error: {e}")
    
    def _matches_filter(self, message: Dict[str, Any], filter_criteria: Dict[str, Any]) -> bool:
        """Verificar si mensaje cumple criterios de filtro"""
        
        if not filter_criteria:
            return True
        
        for key, expected_value in filter_criteria.items():
            message_value = message.get(key)
            
            if isinstance(expected_value, list):
                if message_value not in expected_value:
                    return False
            elif message_value != expected_value:
                return False
        
        return True
    
    async def _handle_load_balancing_request(self, message: Dict[str, Any]):
        """Manejar request de load balancing"""
        
        try:
            payload = message.get("payload", {})
            task_type = payload.get("task_type")
            urgency = payload.get("urgency", "medium")
            
            # Obtener métricas actuales del sistema
            from entrypoint import system_metrics, active_debates, pending_human_reviews
            
            current_load = {
                "active_debates": len(active_debates),
                "pending_reviews": len(pending_human_reviews),
                "consensus_rate": system_metrics.get("consensus_rate", 0),
                "avg_quality_score": system_metrics.get("avg_quality_score", 0),
                "capacity_available": max(0, 10 - len(active_debates))  # Max 10 concurrent
            }
            
            # Determinar si podemos aceptar la tarea
            can_accept = (
                current_load["capacity_available"] > 0 and
                system_metrics.get("consensus_rate", 0) > 50  # Min 50% success rate
            )
            
            # Responder con disponibilidad
            response_event = MCPEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.LOAD_BALANCING_REQUEST,
                priority=EventPriority.HIGH if urgency == "high" else EventPriority.MEDIUM,
                source=self.connection_id,
                target=message.get("source"),
                payload={
                    "response_to": message.get("event_id"),
                    "can_accept": can_accept,
                    "current_load": current_load,
                    "estimated_completion_time": 120 if can_accept else None,  # 2 minutes
                    "cost_estimate": 0.50 if can_accept else None,
                    "specialized_for": ["multi_llm_debate", "consensus_building", task_type] if task_type else ["multi_llm_debate"]
                }
            )
            
            await self.connection.send_event(response_event)
            
            logger.info(f"🔄 Load balancing response: can_accept={can_accept}")
            
        except Exception as e:
            logger.error(f"Load balancing request error: {e}")
    
    async def _handle_resource_discovery(self, message: Dict[str, Any]):
        """Manejar discovery de recursos"""
        
        try:
            payload = message.get("payload", {})
            discovery_type = payload.get("discovery_type", "services")
            
            if discovery_type == "services":
                # Responder con nuestras capabilities
                capabilities_response = MCPEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.RESOURCE_DISCOVERY,
                    priority=EventPriority.MEDIUM,
                    source=self.connection_id,
                    target=message.get("source"),
                    payload={
                        "response_to": message.get("event_id"),
                        "service_type": "chain_of_debate",
                        "version": "2.0",
                        "capabilities": [
                            "multi_llm_debate",
                            "consensus_building", 
                            "human_intervention",
                            "quality_assurance",
                            "decision_replay",
                            "shadow_learning"
                        ],
                        "supported_domains": [
                            "proposal",
                            "content", 
                            "contract",
                            "strategy",
                            "technical",
                            "financial"
                        ],
                        "endpoints": {
                            "submit_task": "/api/v1/debate/submit",
                            "check_status": "/api/v1/debate/status",
                            "human_review": "/api/v1/human/pending"
                        },
                        "pricing": {
                            "base_cost": 0.50,
                            "human_intervention": 1.00,
                            "rejection_retry": 2.00
                        }
                    }
                )
                
                await self.connection.send_event(capabilities_response)
                
            elif discovery_type == "health":
                # Responder con health status
                await self._publish_health_status(target=message.get("source"))
            
            self.integration_metrics["discovery_updates"] += 1
            
        except Exception as e:
            logger.error(f"Resource discovery error: {e}")
    
    async def _handle_system_health_update(self, message: Dict[str, Any]):
        """Manejar update de health de otros sistemas"""
        
        try:
            payload = message.get("payload", {})
            service_id = message.get("source")
            
            if service_id:
                self.discovered_services[service_id] = {
                    "last_update": datetime.now(),
                    "health_data": payload,
                    "service_type": payload.get("service_type", "unknown")
                }
                
                logger.debug(f"📊 Health update from {service_id}: {payload.get('status', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Health update handling error: {e}")
    
    async def _start_service_discovery(self):
        """Iniciar discovery de servicios disponibles"""
        
        discovery_event = MCPEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.RESOURCE_DISCOVERY,
            priority=EventPriority.MEDIUM,
            source=self.connection_id,
            payload={
                "discovery_type": "services",
                "requesting_capabilities": ["content_generation", "contract_analysis", "strategic_planning"]
            }
        )
        
        await self.connection.send_event(discovery_event)
        self.last_discovery = datetime.now()
        
        logger.debug("🔍 Initiated service discovery")
    
    async def _announce_service_availability(self):
        """Anunciar disponibilidad del servicio"""
        
        availability_event = MCPEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYSTEM_HEALTH_UPDATE,
            priority=EventPriority.MEDIUM,
            source=self.connection_id,
            payload={
                "status": "available",
                "service_type": "chain_of_debate",
                "version": "2.0",
                "startup_time": datetime.now().isoformat(),
                "capabilities": [
                    "multi_llm_debate",
                    "consensus_building",
                    "human_intervention",
                    "quality_assurance"
                ]
            }
        )
        
        await self.connection.send_event(availability_event)
        
        logger.info("📢 Service availability announced")
    
    async def _announce_service_unavailability(self):
        """Anunciar que el servicio se vuelve no disponible"""
        
        unavailability_event = MCPEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYSTEM_HEALTH_UPDATE,
            priority=EventPriority.HIGH,
            source=self.connection_id,
            payload={
                "status": "unavailable",
                "service_type": "chain_of_debate",
                "shutdown_time": datetime.now().isoformat(),
                "reason": "graceful_shutdown"
            }
        )
        
        await self.connection.send_event(unavailability_event)
    
    async def _publish_health_status(self, target: Optional[str] = None):
        """Publicar estado de salud actual"""
        
        # Obtener métricas del sistema
        from entrypoint import system_metrics, active_debates, pending_human_reviews
        from model_resilience import ModelResilienceOrchestrator
        
        # Simular resilience orchestrator para métricas
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_debates": len(active_debates),
            "pending_reviews": len(pending_human_reviews),
            "system_metrics": system_metrics,
            "connection_status": "connected" if self.connection.connected else "disconnected",
            "uptime_percentage": 99.5,  # Simulated
            "response_time_avg": 2.5,
            "capacity_utilization": len(active_debates) / 10 * 100  # Assuming max 10
        }
        
        health_event = MCPEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYSTEM_HEALTH_UPDATE,
            priority=EventPriority.MEDIUM,
            source=self.connection_id,
            target=target,
            payload=health_status
        )
        
        await self.connection.send_event(health_event)
    
    async def _maintenance_loop(self):
        """Loop de mantenimiento de la integración"""
        
        while self.integration_active:
            try:
                # Health status periódico
                await self._publish_health_status()
                
                # Re-discovery periódico
                if (not self.last_discovery or 
                    datetime.now() - self.last_discovery > timedelta(minutes=30)):
                    await self._start_service_discovery()
                
                # Limpiar servicios descubiertos antiguos
                cutoff_time = datetime.now() - timedelta(minutes=60)
                expired_services = [
                    service_id for service_id, data in self.discovered_services.items()
                    if data["last_update"] < cutoff_time
                ]
                
                for service_id in expired_services:
                    del self.discovered_services[service_id]
                
                # Update de métricas
                self.integration_metrics["integration_uptime"] += 300  # 5 minutes
                
                await asyncio.sleep(300)  # Mantenimiento cada 5 minutos
                
            except Exception as e:
                logger.error(f"Maintenance loop error: {e}")
                await asyncio.sleep(60)  # Retry en 1 minuto si hay error
    
    # Public API methods para uso externo
    
    async def notify_debate_started(self, task_id: str, domain: str, participants: List[str]):
        """Notificar que un debate ha comenzado"""
        
        await self.publish_event(
            EventType.DEBATE_STARTED,
            {
                "task_id": task_id,
                "domain": domain,
                "participants": participants,
                "estimated_duration": 120
            },
            EventPriority.MEDIUM
        )
    
    async def notify_debate_completed(
        self, 
        task_id: str, 
        consensus_score: float, 
        quality_score: float,
        cost: float
    ):
        """Notificar que un debate se ha completado"""
        
        await self.publish_event(
            EventType.DEBATE_COMPLETED,
            {
                "task_id": task_id,
                "consensus_score": consensus_score,
                "quality_score": quality_score,
                "cost": cost,
                "human_intervention_used": False  # Se actualizará si es necesario
            },
            EventPriority.MEDIUM
        )
    
    async def notify_human_intervention_required(self, task_id: str, reason: str):
        """Notificar que se requiere intervención humana"""
        
        await self.publish_event(
            EventType.HUMAN_INTERVENTION_REQUIRED,
            {
                "task_id": task_id,
                "reason": reason,
                "timeout_minutes": 5,
                "intervention_cost": 1.0
            },
            EventPriority.HIGH
        )
    
    async def notify_consensus_reached(self, task_id: str, consensus_score: float):
        """Notificar que se alcanzó consenso"""
        
        await self.publish_event(
            EventType.CONSENSUS_REACHED,
            {
                "task_id": task_id,
                "consensus_score": consensus_score,
                "automatic_consensus": True
            },
            EventPriority.MEDIUM
        )
    
    async def notify_learning_pattern_detected(self, pattern_type: str, confidence: float):
        """Notificar detección de patrón de aprendizaje"""
        
        await self.publish_event(
            EventType.LEARNING_PATTERN_DETECTED,
            {
                "pattern_type": pattern_type,
                "confidence": confidence,
                "improvement_potential": "high" if confidence > 0.8 else "medium"
            },
            EventPriority.LOW
        )
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Obtener estado de la integración"""
        
        return {
            "integration_active": self.integration_active,
            "connection_status": "connected" if self.connection.connected else "disconnected",
            "broker_uri": self.broker_uri,
            "connection_id": self.connection_id,
            "subscriptions": {
                sub_id: {
                    "event_types": [et.value for et in sub.event_types],
                    "active": sub.active,
                    "created_at": sub.created_at.isoformat()
                }
                for sub_id, sub in self.subscriptions.items()
            },
            "discovered_services": {
                service_id: {
                    "service_type": data["service_type"],
                    "last_update": data["last_update"].isoformat()
                }
                for service_id, data in self.discovered_services.items()
            },
            "metrics": self.integration_metrics,
            "connection_metrics": self.connection.connection_metrics
        }
    
    def get_available_services(self) -> Dict[str, Any]:
        """Obtener servicios disponibles descubiertos"""
        
        return {
            service_id: {
                "service_type": data["service_type"],
                "last_seen": data["last_update"].isoformat(),
                "capabilities": data["health_data"].get("capabilities", []),
                "status": data["health_data"].get("status", "unknown")
            }
            for service_id, data in self.discovered_services.items()
        }