#!/usr/bin/env python3
"""
SAM ↔ Manus Notification Protocol
Sistema de notificaciones bidireccional entre SAM y Manus

Este módulo implementa el protocolo de comunicación en tiempo real
entre el sistema SAM (Semantic Agent Manager) y Manus para:
- Notificaciones de estado de tareas
- Actualizaciones de progreso en tiempo real
- Sincronización de contexto entre sistemas
- Manejo de eventos críticos y alertas
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import aiohttp
import redis.asyncio as redis
from pydantic import BaseModel, Field, validator

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Tipos de notificaciones del protocolo SAM-Manus"""
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    CONTEXT_UPDATE = "context_update"
    AGENT_STATUS = "agent_status"
    SYSTEM_ALERT = "system_alert"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class Priority(Enum):
    """Niveles de prioridad para notificaciones"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class NotificationPayload:
    """Estructura de datos para notificaciones"""
    id: str
    type: NotificationType
    priority: Priority
    source: str  # 'sam' o 'manus'
    target: str  # 'sam' o 'manus'
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la notificación a diccionario para serialización"""
        return {
            'id': self.id,
            'type': self.type.value,
            'priority': self.priority.value,
            'source': self.source,
            'target': self.target,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'metadata': self.metadata or {},
            'retry_count': self.retry_count,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationPayload':
        """Crea una notificación desde un diccionario"""
        return cls(
            id=data['id'],
            type=NotificationType(data['type']),
            priority=Priority(data['priority']),
            source=data['source'],
            target=data['target'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            data=data['data'],
            metadata=data.get('metadata'),
            retry_count=data.get('retry_count', 0),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )

class NotificationHandler:
    """Manejador base para notificaciones"""
    
    def __init__(self, handler_id: str):
        self.handler_id = handler_id
        self.is_active = True
    
    async def handle(self, notification: NotificationPayload) -> bool:
        """
        Maneja una notificación específica
        Returns: True si se manejó exitosamente, False en caso contrario
        """
        raise NotImplementedError("Subclasses must implement handle method")
    
    def can_handle(self, notification: NotificationPayload) -> bool:
        """Determina si este handler puede manejar la notificación"""
        return True

class TaskProgressHandler(NotificationHandler):
    """Handler específico para notificaciones de progreso de tareas"""
    
    def __init__(self):
        super().__init__("task_progress_handler")
        self.active_tasks = {}
    
    def can_handle(self, notification: NotificationPayload) -> bool:
        return notification.type in [
            NotificationType.TASK_STARTED,
            NotificationType.TASK_PROGRESS,
            NotificationType.TASK_COMPLETED,
            NotificationType.TASK_FAILED
        ]
    
    async def handle(self, notification: NotificationPayload) -> bool:
        try:
            task_id = notification.data.get('task_id')
            if not task_id:
                logger.warning(f"Task notification without task_id: {notification.id}")
                return False
            
            if notification.type == NotificationType.TASK_STARTED:
                self.active_tasks[task_id] = {
                    'started_at': notification.timestamp,
                    'progress': 0,
                    'status': 'running'
                }
                logger.info(f"Task {task_id} started")
            
            elif notification.type == NotificationType.TASK_PROGRESS:
                if task_id in self.active_tasks:
                    progress = notification.data.get('progress', 0)
                    self.active_tasks[task_id]['progress'] = progress
                    logger.info(f"Task {task_id} progress: {progress}%")
            
            elif notification.type in [NotificationType.TASK_COMPLETED, NotificationType.TASK_FAILED]:
                if task_id in self.active_tasks:
                    self.active_tasks[task_id]['status'] = 'completed' if notification.type == NotificationType.TASK_COMPLETED else 'failed'
                    self.active_tasks[task_id]['completed_at'] = notification.timestamp
                    logger.info(f"Task {task_id} {self.active_tasks[task_id]['status']}")
            
            return True
        except Exception as e:
            logger.error(f"Error handling task notification: {e}")
            return False

class SystemAlertHandler(NotificationHandler):
    """Handler para alertas críticas del sistema"""
    
    def __init__(self):
        super().__init__("system_alert_handler")
    
    def can_handle(self, notification: NotificationPayload) -> bool:
        return notification.type == NotificationType.SYSTEM_ALERT or notification.priority == Priority.CRITICAL
    
    async def handle(self, notification: NotificationPayload) -> bool:
        try:
            alert_type = notification.data.get('alert_type', 'unknown')
            message = notification.data.get('message', 'No message provided')
            
            logger.critical(f"SYSTEM ALERT [{alert_type}]: {message}")
            
            # Aquí se pueden agregar integraciones con sistemas de alertas externos
            # como Slack, PagerDuty, email, etc.
            
            return True
        except Exception as e:
            logger.error(f"Error handling system alert: {e}")
            return False

class SAMManusNotificationProtocol:
    """
    Protocolo principal de notificaciones entre SAM y Manus
    
    Características:
    - Comunicación bidireccional WebSocket + HTTP
    - Sistema de retry automático
    - Persistencia en Redis
    - Handlers pluggables
    - Métricas y monitoreo
    """
    
    def __init__(self, 
                 system_id: str,
                 redis_url: str = "redis://localhost:6379",
                 websocket_port: int = 8765,
                 http_port: int = 8766):
        self.system_id = system_id
        self.redis_url = redis_url
        self.websocket_port = websocket_port
        self.http_port = http_port
        
        # Componentes internos
        self.redis_client = None
        self.websocket_server = None
        self.http_server = None
        self.connected_clients = set()
        self.handlers: List[NotificationHandler] = []
        self.metrics = {
            'notifications_sent': 0,
            'notifications_received': 0,
            'notifications_failed': 0,
            'active_connections': 0
        }
        
        # Configuración
        self.max_retry_attempts = 3
        self.retry_delay = 1.0
        self.notification_ttl = 3600  # 1 hora
        
        # Registrar handlers por defecto
        self.register_handler(TaskProgressHandler())
        self.register_handler(SystemAlertHandler())
    
    async def initialize(self):
        """Inicializa el protocolo de notificaciones"""
        try:
            # Conectar a Redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis")
            
            # Iniciar servidor WebSocket
            await self.start_websocket_server()
            
            # Iniciar servidor HTTP
            await self.start_http_server()
            
            logger.info(f"SAM-Manus Notification Protocol initialized for {self.system_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize notification protocol: {e}")
            raise
    
    async def start_websocket_server(self):
        """Inicia el servidor WebSocket para comunicación en tiempo real"""
        async def handle_websocket(websocket, path):
            self.connected_clients.add(websocket)
            self.metrics['active_connections'] = len(self.connected_clients)
            logger.info(f"New WebSocket connection from {websocket.remote_address}")
            
            try:
                async for message in websocket:
                    await self.handle_websocket_message(websocket, message)
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"WebSocket connection closed: {websocket.remote_address}")
            finally:
                self.connected_clients.discard(websocket)
                self.metrics['active_connections'] = len(self.connected_clients)
        
        self.websocket_server = await websockets.serve(
            handle_websocket, 
            "0.0.0.0", 
            self.websocket_port
        )
        logger.info(f"WebSocket server started on port {self.websocket_port}")
    
    async def start_http_server(self):
        """Inicia el servidor HTTP para APIs REST"""
        from aiohttp import web
        
        app = web.Application()
        app.router.add_post('/notify', self.handle_http_notification)
        app.router.add_get('/status', self.handle_status_request)
        app.router.add_get('/metrics', self.handle_metrics_request)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.http_port)
        await site.start()
        
        logger.info(f"HTTP server started on port {self.http_port}")
    
    async def handle_websocket_message(self, websocket, message: str):
        """Maneja mensajes recibidos por WebSocket"""
        try:
            data = json.loads(message)
            notification = NotificationPayload.from_dict(data)
            await self.process_notification(notification)
            self.metrics['notifications_received'] += 1
            
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await websocket.send(json.dumps({
                'error': 'Invalid message format',
                'details': str(e)
            }))
    
    async def handle_http_notification(self, request):
        """Maneja notificaciones recibidas por HTTP"""
        try:
            data = await request.json()
            notification = NotificationPayload.from_dict(data)
            await self.process_notification(notification)
            self.metrics['notifications_received'] += 1
            
            return web.json_response({
                'status': 'success',
                'notification_id': notification.id
            })
            
        except Exception as e:
            logger.error(f"Error processing HTTP notification: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=400)
    
    async def handle_status_request(self, request):
        """Endpoint de estado del sistema"""
        return web.json_response({
            'system_id': self.system_id,
            'status': 'active',
            'active_connections': len(self.connected_clients),
            'registered_handlers': len(self.handlers),
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        })
    
    async def handle_metrics_request(self, request):
        """Endpoint de métricas del sistema"""
        return web.json_response(self.metrics)
    
    def register_handler(self, handler: NotificationHandler):
        """Registra un nuevo handler de notificaciones"""
        self.handlers.append(handler)
        logger.info(f"Registered notification handler: {handler.handler_id}")
    
    async def send_notification(self, 
                              target: str,
                              notification_type: NotificationType,
                              data: Dict[str, Any],
                              priority: Priority = Priority.MEDIUM,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Envía una notificación al sistema objetivo
        
        Args:
            target: Sistema objetivo ('sam' o 'manus')
            notification_type: Tipo de notificación
            data: Datos de la notificación
            priority: Prioridad de la notificación
            metadata: Metadatos adicionales
            
        Returns:
            ID de la notificación enviada
        """
        notification = NotificationPayload(
            id=str(uuid.uuid4()),
            type=notification_type,
            priority=priority,
            source=self.system_id,
            target=target,
            timestamp=datetime.now(timezone.utc),
            data=data,
            metadata=metadata
        )
        
        try:
            # Persistir en Redis
            await self.persist_notification(notification)
            
            # Enviar por WebSocket si hay conexiones activas
            if self.connected_clients:
                await self.broadcast_websocket(notification)
            
            # Enviar por HTTP como fallback
            await self.send_http_notification(notification)
            
            self.metrics['notifications_sent'] += 1
            logger.info(f"Notification sent: {notification.id}")
            
            return notification.id
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            self.metrics['notifications_failed'] += 1
            raise
    
    async def process_notification(self, notification: NotificationPayload):
        """Procesa una notificación recibida"""
        logger.info(f"Processing notification: {notification.id} ({notification.type.value})")
        
        # Verificar si la notificación ha expirado
        if notification.expires_at and datetime.now(timezone.utc) > notification.expires_at:
            logger.warning(f"Notification {notification.id} has expired")
            return
        
        # Procesar con handlers registrados
        handled = False
        for handler in self.handlers:
            if handler.is_active and handler.can_handle(notification):
                try:
                    success = await handler.handle(notification)
                    if success:
                        handled = True
                        logger.debug(f"Notification {notification.id} handled by {handler.handler_id}")
                except Exception as e:
                    logger.error(f"Handler {handler.handler_id} failed to process notification {notification.id}: {e}")
        
        if not handled:
            logger.warning(f"No handler processed notification {notification.id}")
        
        # Marcar como procesada en Redis
        await self.mark_notification_processed(notification.id)
    
    async def persist_notification(self, notification: NotificationPayload):
        """Persiste una notificación en Redis"""
        key = f"notification:{notification.id}"
        data = json.dumps(notification.to_dict())
        await self.redis_client.setex(key, self.notification_ttl, data)
    
    async def mark_notification_processed(self, notification_id: str):
        """Marca una notificación como procesada"""
        key = f"notification:{notification_id}:processed"
        await self.redis_client.setex(key, self.notification_ttl, "true")
    
    async def broadcast_websocket(self, notification: NotificationPayload):
        """Envía una notificación a todas las conexiones WebSocket activas"""
        if not self.connected_clients:
            return
        
        message = json.dumps(notification.to_dict())
        disconnected = set()
        
        for client in self.connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Limpiar conexiones cerradas
        self.connected_clients -= disconnected
        self.metrics['active_connections'] = len(self.connected_clients)
    
    async def send_http_notification(self, notification: NotificationPayload):
        """Envía una notificación por HTTP"""
        # Esta función se implementaría para enviar a endpoints HTTP específicos
        # basados en el target de la notificación
        pass
    
    async def send_task_started(self, task_id: str, task_name: str, estimated_duration: Optional[int] = None):
        """Envía notificación de inicio de tarea"""
        data = {
            'task_id': task_id,
            'task_name': task_name,
            'estimated_duration': estimated_duration
        }
        return await self.send_notification(
            target='manus',
            notification_type=NotificationType.TASK_STARTED,
            data=data,
            priority=Priority.MEDIUM
        )
    
    async def send_task_progress(self, task_id: str, progress: int, message: Optional[str] = None):
        """Envía notificación de progreso de tarea"""
        data = {
            'task_id': task_id,
            'progress': progress,
            'message': message
        }
        return await self.send_notification(
            target='manus',
            notification_type=NotificationType.TASK_PROGRESS,
            data=data,
            priority=Priority.LOW
        )
    
    async def send_task_completed(self, task_id: str, result: Dict[str, Any]):
        """Envía notificación de tarea completada"""
        data = {
            'task_id': task_id,
            'result': result,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        return await self.send_notification(
            target='manus',
            notification_type=NotificationType.TASK_COMPLETED,
            data=data,
            priority=Priority.HIGH
        )
    
    async def send_system_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Envía alerta del sistema"""
        data = {
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'system_id': self.system_id
        }
        priority = Priority.CRITICAL if severity == 'critical' else Priority.HIGH
        return await self.send_notification(
            target='manus',
            notification_type=NotificationType.SYSTEM_ALERT,
            data=data,
            priority=priority
        )
    
    async def shutdown(self):
        """Cierra el protocolo de notificaciones"""
        logger.info("Shutting down SAM-Manus Notification Protocol")
        
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Notification protocol shutdown complete")

# Funciones de utilidad para uso directo
async def create_sam_protocol(system_id: str = "sam") -> SAMManusNotificationProtocol:
    """Crea e inicializa un protocolo para el sistema SAM"""
    protocol = SAMManusNotificationProtocol(system_id)
    await protocol.initialize()
    return protocol

async def create_manus_protocol(system_id: str = "manus") -> SAMManusNotificationProtocol:
    """Crea e inicializa un protocolo para el sistema Manus"""
    protocol = SAMManusNotificationProtocol(system_id)
    await protocol.initialize()
    return protocol

# Ejemplo de uso
if __name__ == "__main__":
    async def main():
        # Crear protocolo para SAM
        sam_protocol = await create_sam_protocol()
        
        try:
            # Enviar algunas notificaciones de ejemplo
            await sam_protocol.send_task_started("task_001", "Análisis de documentos", 300)
            await asyncio.sleep(1)
            
            await sam_protocol.send_task_progress("task_001", 25, "Procesando archivos...")
            await asyncio.sleep(1)
            
            await sam_protocol.send_task_progress("task_001", 75, "Generando resumen...")
            await asyncio.sleep(1)
            
            await sam_protocol.send_task_completed("task_001", {
                "summary": "Análisis completado exitosamente",
                "files_processed": 15,
                "insights_generated": 8
            })
            
            # Mantener el servidor activo
            logger.info("Notification protocol running. Press Ctrl+C to stop.")
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await sam_protocol.shutdown()
    
    asyncio.run(main())

