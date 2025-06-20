#!/usr/bin/env python3
"""
Complete Webhook System and Agent End Task Implementation
Sistema completo de webhooks y mecanismo agent_end_task para MCP Enterprise
"""

import asyncio
import json
import time
import uuid
import hmac
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import logging
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import threading
import queue
from contextlib import asynccontextmanager
import ssl
import certifi

from mcp_payload_schemas import (
    PayloadValidator, PayloadType, 
    create_agent_end_task_payload,
    create_notification_payload
)

class WebhookEventType(Enum):
    TASK_LIFECYCLE = "task_lifecycle"
    AGENT_STATUS = "agent_status"
    SYSTEM_EVENT = "system_event"
    ERROR_EVENT = "error_event"
    PERFORMANCE_METRIC = "performance_metric"

class AgentEndTaskReason(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
    RESOURCE_EXHAUSTED = "resource_exhausted"

@dataclass
class WebhookDeliveryAttempt:
    """Registro de intento de entrega de webhook"""
    attempt_id: str
    webhook_id: str
    endpoint_url: str
    payload: Dict[str, Any]
    timestamp: str
    success: bool
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None

@dataclass
class AgentEndTaskEvent:
    """Evento de finalización de tarea de agente"""
    task_id: str
    agent_id: str
    reason: AgentEndTaskReason
    timestamp: str
    execution_summary: Dict[str, Any]
    cleanup_actions: List[str]
    next_steps: List[str]
    metadata: Dict[str, Any]

class WebhookManager:
    """
    Gestor avanzado de webhooks con persistencia, reintentos y monitoreo
    """
    
    def __init__(self, db_path: str = "/tmp/webhook_system.db"):
        self.db_path = db_path
        self.active_webhooks: Dict[str, Dict[str, Any]] = {}
        self.delivery_queue = asyncio.Queue()
        self.retry_queue = asyncio.Queue()
        self.failed_deliveries: Dict[str, WebhookDeliveryAttempt] = {}
        
        # Configuración de reintentos
        self.retry_config = {
            "max_retries": 5,
            "initial_delay": 1,  # segundos
            "max_delay": 300,    # 5 minutos
            "backoff_multiplier": 2.0,
            "jitter": True
        }
        
        # Configuración de timeouts
        self.timeout_config = {
            "connect_timeout": 10,
            "read_timeout": 30,
            "total_timeout": 60
        }
        
        self.logger = logging.getLogger(__name__)
        self._init_database()
        self._start_workers()
    
    def _init_database(self):
        """Inicializar base de datos para webhooks"""
        with sqlite3.connect(self.db_path) as conn:
            # Tabla de webhooks registrados
            conn.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    webhook_id TEXT PRIMARY KEY,
                    endpoint_url TEXT NOT NULL,
                    secret TEXT,
                    event_types TEXT NOT NULL,
                    filters TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_delivery_at TEXT,
                    total_deliveries INTEGER DEFAULT 0,
                    successful_deliveries INTEGER DEFAULT 0,
                    failed_deliveries INTEGER DEFAULT 0
                )
            """)
            
            # Tabla de intentos de entrega
            conn.execute("""
                CREATE TABLE IF NOT EXISTS delivery_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    webhook_id TEXT NOT NULL,
                    endpoint_url TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    response_code INTEGER,
                    response_body TEXT,
                    error_message TEXT,
                    duration_ms INTEGER,
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (webhook_id) REFERENCES webhooks (webhook_id)
                )
            """)
            
            # Tabla de eventos agent_end_task
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_end_task_events (
                    event_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    execution_summary TEXT NOT NULL,
                    cleanup_actions TEXT NOT NULL,
                    next_steps TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    webhook_sent BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Tabla de métricas de performance
            conn.execute("""
                CREATE TABLE IF NOT EXISTS webhook_metrics (
                    metric_id TEXT PRIMARY KEY,
                    webhook_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    delivery_time_ms INTEGER,
                    success_rate REAL,
                    error_rate REAL,
                    throughput REAL,
                    FOREIGN KEY (webhook_id) REFERENCES webhooks (webhook_id)
                )
            """)
    
    def _start_workers(self):
        """Iniciar workers asíncronos para procesamiento de webhooks"""
        # Worker principal de entrega
        asyncio.create_task(self._delivery_worker())
        
        # Worker de reintentos
        asyncio.create_task(self._retry_worker())
        
        # Worker de métricas
        asyncio.create_task(self._metrics_worker())
    
    async def _delivery_worker(self):
        """Worker principal para entrega de webhooks"""
        while True:
            try:
                delivery_task = await self.delivery_queue.get()
                await self._process_webhook_delivery(delivery_task)
                self.delivery_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error in delivery worker: {e}")
                await asyncio.sleep(1)
    
    async def _retry_worker(self):
        """Worker para reintentos de webhooks fallidos"""
        while True:
            try:
                retry_task = await self.retry_queue.get()
                await self._process_retry(retry_task)
                self.retry_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error in retry worker: {e}")
                await asyncio.sleep(5)
    
    async def _metrics_worker(self):
        """Worker para cálculo de métricas"""
        while True:
            try:
                await self._calculate_metrics()
                await asyncio.sleep(60)  # Calcular métricas cada minuto
            except Exception as e:
                self.logger.error(f"Error in metrics worker: {e}")
                await asyncio.sleep(60)
    
    def register_webhook(self, webhook_id: str, endpoint_url: str, 
                        event_types: List[str], secret: Optional[str] = None,
                        filters: Optional[Dict[str, Any]] = None) -> bool:
        """Registrar nuevo webhook"""
        try:
            webhook_data = {
                "webhook_id": webhook_id,
                "endpoint_url": endpoint_url,
                "secret": secret,
                "event_types": json.dumps(event_types),
                "filters": json.dumps(filters) if filters else None,
                "active": True
            }
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO webhooks 
                    (webhook_id, endpoint_url, secret, event_types, filters, active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    webhook_id, endpoint_url, secret, 
                    json.dumps(event_types),
                    json.dumps(filters) if filters else None,
                    True, datetime.now().isoformat()
                ))
            
            self.active_webhooks[webhook_id] = webhook_data
            self.logger.info(f"Registered webhook: {webhook_id} -> {endpoint_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering webhook {webhook_id}: {e}")
            return False
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """Desregistrar webhook"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE webhooks SET active = FALSE WHERE webhook_id = ?",
                    (webhook_id,)
                )
            
            if webhook_id in self.active_webhooks:
                del self.active_webhooks[webhook_id]
            
            self.logger.info(f"Unregistered webhook: {webhook_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering webhook {webhook_id}: {e}")
            return False
    
    async def send_webhook(self, event_type: WebhookEventType, 
                          payload: Dict[str, Any], 
                          target_webhooks: Optional[List[str]] = None):
        """Enviar webhook a endpoints registrados"""
        try:
            # Determinar webhooks objetivo
            if target_webhooks:
                webhooks = {wid: self.active_webhooks[wid] 
                           for wid in target_webhooks 
                           if wid in self.active_webhooks}
            else:
                webhooks = self.active_webhooks
            
            # Filtrar webhooks por tipo de evento
            filtered_webhooks = {}
            for webhook_id, webhook_data in webhooks.items():
                event_types = json.loads(webhook_data.get("event_types", "[]"))
                if event_type.value in event_types or "all" in event_types:
                    filtered_webhooks[webhook_id] = webhook_data
            
            # Crear tareas de entrega
            for webhook_id, webhook_data in filtered_webhooks.items():
                delivery_task = {
                    "webhook_id": webhook_id,
                    "webhook_data": webhook_data,
                    "event_type": event_type.value,
                    "payload": payload,
                    "attempt_id": str(uuid.uuid4()),
                    "retry_count": 0
                }
                
                await self.delivery_queue.put(delivery_task)
            
            self.logger.info(f"Queued webhook delivery for {len(filtered_webhooks)} endpoints")
            
        except Exception as e:
            self.logger.error(f"Error sending webhook: {e}")
    
    async def _process_webhook_delivery(self, delivery_task: Dict[str, Any]):
        """Procesar entrega individual de webhook"""
        webhook_id = delivery_task["webhook_id"]
        webhook_data = delivery_task["webhook_data"]
        payload = delivery_task["payload"]
        attempt_id = delivery_task["attempt_id"]
        
        start_time = time.time()
        
        try:
            # Preparar headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "MCP-Enterprise-Webhook/1.0",
                "X-Webhook-ID": webhook_id,
                "X-Event-Type": delivery_task["event_type"],
                "X-Delivery-ID": attempt_id,
                "X-Timestamp": datetime.now().isoformat()
            }
            
            # Añadir signature si hay secret
            if webhook_data.get("secret"):
                payload_str = json.dumps(payload, sort_keys=True)
                signature = hmac.new(
                    webhook_data["secret"].encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Signature-SHA256"] = f"sha256={signature}"
            
            # Configurar SSL context
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            # Realizar request HTTP
            timeout = aiohttp.ClientTimeout(
                connect=self.timeout_config["connect_timeout"],
                sock_read=self.timeout_config["read_timeout"],
                total=self.timeout_config["total_timeout"]
            )
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            ) as session:
                async with session.post(
                    webhook_data["endpoint_url"],
                    json=payload,
                    headers=headers
                ) as response:
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    response_body = await response.text()
                    
                    # Registrar intento de entrega
                    attempt = WebhookDeliveryAttempt(
                        attempt_id=attempt_id,
                        webhook_id=webhook_id,
                        endpoint_url=webhook_data["endpoint_url"],
                        payload=payload,
                        timestamp=datetime.now().isoformat(),
                        success=response.status in [200, 201, 202, 204],
                        response_code=response.status,
                        response_body=response_body[:1000],  # Limitar tamaño
                        duration_ms=duration_ms
                    )
                    
                    await self._record_delivery_attempt(attempt)
                    
                    if not attempt.success:
                        # Programar reintento si es necesario
                        retry_count = delivery_task.get("retry_count", 0)
                        if retry_count < self.retry_config["max_retries"]:
                            await self._schedule_retry(delivery_task, retry_count + 1)
                    
                    self.logger.info(f"Webhook delivery: {webhook_id} -> {response.status} ({duration_ms}ms)")
                    
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Registrar intento fallido
            attempt = WebhookDeliveryAttempt(
                attempt_id=attempt_id,
                webhook_id=webhook_id,
                endpoint_url=webhook_data["endpoint_url"],
                payload=payload,
                timestamp=datetime.now().isoformat(),
                success=False,
                error_message=str(e),
                duration_ms=duration_ms
            )
            
            await self._record_delivery_attempt(attempt)
            
            # Programar reintento
            retry_count = delivery_task.get("retry_count", 0)
            if retry_count < self.retry_config["max_retries"]:
                await self._schedule_retry(delivery_task, retry_count + 1)
            
            self.logger.error(f"Webhook delivery failed: {webhook_id} -> {str(e)}")
    
    async def _schedule_retry(self, delivery_task: Dict[str, Any], retry_count: int):
        """Programar reintento de webhook"""
        # Calcular delay con exponential backoff
        base_delay = self.retry_config["initial_delay"]
        max_delay = self.retry_config["max_delay"]
        multiplier = self.retry_config["backoff_multiplier"]
        
        delay = min(base_delay * (multiplier ** (retry_count - 1)), max_delay)
        
        # Añadir jitter si está habilitado
        if self.retry_config["jitter"]:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        # Programar reintento
        retry_task = delivery_task.copy()
        retry_task["retry_count"] = retry_count
        retry_task["scheduled_time"] = time.time() + delay
        retry_task["attempt_id"] = str(uuid.uuid4())
        
        await self.retry_queue.put(retry_task)
        
        self.logger.info(f"Scheduled retry {retry_count} for webhook {delivery_task['webhook_id']} in {delay:.1f}s")
    
    async def _process_retry(self, retry_task: Dict[str, Any]):
        """Procesar reintento de webhook"""
        scheduled_time = retry_task.get("scheduled_time", 0)
        current_time = time.time()
        
        # Esperar hasta el momento programado
        if current_time < scheduled_time:
            await asyncio.sleep(scheduled_time - current_time)
        
        # Procesar entrega
        await self._process_webhook_delivery(retry_task)
    
    async def _record_delivery_attempt(self, attempt: WebhookDeliveryAttempt):
        """Registrar intento de entrega en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO delivery_attempts 
                    (attempt_id, webhook_id, endpoint_url, payload, timestamp, 
                     success, response_code, response_body, error_message, duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    attempt.attempt_id,
                    attempt.webhook_id,
                    attempt.endpoint_url,
                    json.dumps(attempt.payload),
                    attempt.timestamp,
                    attempt.success,
                    attempt.response_code,
                    attempt.response_body,
                    attempt.error_message,
                    attempt.duration_ms
                ))
                
                # Actualizar estadísticas del webhook
                conn.execute("""
                    UPDATE webhooks SET 
                        total_deliveries = total_deliveries + 1,
                        successful_deliveries = successful_deliveries + ?,
                        failed_deliveries = failed_deliveries + ?,
                        last_delivery_at = ?
                    WHERE webhook_id = ?
                """, (
                    1 if attempt.success else 0,
                    0 if attempt.success else 1,
                    attempt.timestamp,
                    attempt.webhook_id
                ))
                
        except Exception as e:
            self.logger.error(f"Error recording delivery attempt: {e}")
    
    async def _calculate_metrics(self):
        """Calcular métricas de performance de webhooks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Calcular métricas por webhook
                cursor = conn.execute("""
                    SELECT 
                        webhook_id,
                        AVG(duration_ms) as avg_delivery_time,
                        COUNT(*) as total_attempts,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_attempts
                    FROM delivery_attempts 
                    WHERE timestamp >= datetime('now', '-1 hour')
                    GROUP BY webhook_id
                """)
                
                for row in cursor.fetchall():
                    webhook_id, avg_time, total, successful, failed = row
                    
                    success_rate = successful / total if total > 0 else 0
                    error_rate = failed / total if total > 0 else 0
                    throughput = total / 3600  # requests per second
                    
                    # Guardar métricas
                    conn.execute("""
                        INSERT INTO webhook_metrics 
                        (metric_id, webhook_id, timestamp, delivery_time_ms, 
                         success_rate, error_rate, throughput)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        webhook_id,
                        datetime.now().isoformat(),
                        avg_time,
                        success_rate,
                        error_rate,
                        throughput
                    ))
                
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
    
    def get_webhook_stats(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de un webhook específico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM webhooks WHERE webhook_id = ?
                """, (webhook_id,))
                
                webhook_row = cursor.fetchone()
                if not webhook_row:
                    return None
                
                columns = [desc[0] for desc in cursor.description]
                webhook_data = dict(zip(columns, webhook_row))
                
                # Obtener métricas recientes
                cursor = conn.execute("""
                    SELECT * FROM webhook_metrics 
                    WHERE webhook_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 24
                """, (webhook_id,))
                
                metrics = []
                for row in cursor.fetchall():
                    metric_columns = [desc[0] for desc in cursor.description]
                    metrics.append(dict(zip(metric_columns, row)))
                
                webhook_data["recent_metrics"] = metrics
                
                return webhook_data
                
        except Exception as e:
            self.logger.error(f"Error getting webhook stats: {e}")
            return None

class AgentEndTaskManager:
    """
    Gestor del mecanismo agent_end_task
    """
    
    def __init__(self, webhook_manager: WebhookManager):
        self.webhook_manager = webhook_manager
        self.logger = logging.getLogger(__name__)
        self.cleanup_handlers: Dict[str, Callable] = {}
        self.notification_handlers: Dict[str, Callable] = {}
    
    def register_cleanup_handler(self, task_type: str, handler: Callable):
        """Registrar handler de cleanup para tipo de tarea específico"""
        self.cleanup_handlers[task_type] = handler
    
    def register_notification_handler(self, reason: AgentEndTaskReason, handler: Callable):
        """Registrar handler de notificación para razón específica"""
        self.notification_handlers[reason.value] = handler
    
    async def end_task(self, task_id: str, agent_id: str, 
                      reason: AgentEndTaskReason,
                      execution_summary: Dict[str, Any],
                      cleanup_actions: Optional[List[str]] = None,
                      next_steps: Optional[List[str]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Finalizar tarea de agente con cleanup y notificaciones
        """
        try:
            # Crear evento de finalización
            end_task_event = AgentEndTaskEvent(
                task_id=task_id,
                agent_id=agent_id,
                reason=reason,
                timestamp=datetime.now().isoformat(),
                execution_summary=execution_summary,
                cleanup_actions=cleanup_actions or [],
                next_steps=next_steps or [],
                metadata=metadata or {}
            )
            
            # Persistir evento
            await self._persist_end_task_event(end_task_event)
            
            # Ejecutar cleanup
            cleanup_results = await self._execute_cleanup(end_task_event)
            
            # Enviar notificaciones
            notification_results = await self._send_notifications(end_task_event)
            
            # Crear payload para webhook
            webhook_payload = create_agent_end_task_payload(
                task_id=task_id,
                agent_id=agent_id,
                completion_status=reason.value,
                result_data=execution_summary,
                execution_metrics=metadata.get("execution_metrics", {}),
                quality_assessment=metadata.get("quality_assessment", {}),
                next_actions={
                    "cleanup_required": len(cleanup_actions or []) > 0,
                    "follow_up_tasks": next_steps or [],
                    "escalation_needed": reason == AgentEndTaskReason.ESCALATED,
                    "user_notification_required": reason in [
                        AgentEndTaskReason.FAILURE, 
                        AgentEndTaskReason.ESCALATED
                    ]
                }
            )
            
            # Enviar webhook
            await self.webhook_manager.send_webhook(
                WebhookEventType.TASK_LIFECYCLE,
                webhook_payload
            )
            
            self.logger.info(f"Task ended: {task_id} - Reason: {reason.value}")
            
            return {
                "status": "task_ended",
                "task_id": task_id,
                "reason": reason.value,
                "cleanup_results": cleanup_results,
                "notification_results": notification_results,
                "timestamp": end_task_event.timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Error ending task {task_id}: {e}")
            return {
                "status": "error",
                "task_id": task_id,
                "error": str(e)
            }
    
    async def _persist_end_task_event(self, event: AgentEndTaskEvent):
        """Persistir evento de finalización"""
        try:
            with sqlite3.connect(self.webhook_manager.db_path) as conn:
                conn.execute("""
                    INSERT INTO agent_end_task_events 
                    (event_id, task_id, agent_id, reason, timestamp, 
                     execution_summary, cleanup_actions, next_steps, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    event.task_id,
                    event.agent_id,
                    event.reason.value,
                    event.timestamp,
                    json.dumps(event.execution_summary),
                    json.dumps(event.cleanup_actions),
                    json.dumps(event.next_steps),
                    json.dumps(event.metadata)
                ))
                
        except Exception as e:
            self.logger.error(f"Error persisting end task event: {e}")
    
    async def _execute_cleanup(self, event: AgentEndTaskEvent) -> Dict[str, Any]:
        """Ejecutar acciones de cleanup"""
        cleanup_results = {
            "actions_executed": [],
            "actions_failed": [],
            "cleanup_successful": True
        }
        
        try:
            # Ejecutar acciones de cleanup específicas
            for action in event.cleanup_actions:
                try:
                    # Aquí se ejecutarían las acciones reales de cleanup
                    # Por ejemplo: limpiar archivos temporales, cerrar conexiones, etc.
                    self.logger.info(f"Executing cleanup action: {action}")
                    cleanup_results["actions_executed"].append(action)
                    
                except Exception as e:
                    self.logger.error(f"Cleanup action failed: {action} - {e}")
                    cleanup_results["actions_failed"].append({
                        "action": action,
                        "error": str(e)
                    })
                    cleanup_results["cleanup_successful"] = False
            
            # Ejecutar handler de cleanup específico del tipo de tarea
            task_type = event.metadata.get("task_type", "general")
            if task_type in self.cleanup_handlers:
                try:
                    handler_result = await self.cleanup_handlers[task_type](event)
                    cleanup_results["handler_result"] = handler_result
                except Exception as e:
                    self.logger.error(f"Cleanup handler failed for {task_type}: {e}")
                    cleanup_results["handler_error"] = str(e)
                    cleanup_results["cleanup_successful"] = False
            
        except Exception as e:
            self.logger.error(f"Error in cleanup execution: {e}")
            cleanup_results["cleanup_successful"] = False
            cleanup_results["general_error"] = str(e)
        
        return cleanup_results
    
    async def _send_notifications(self, event: AgentEndTaskEvent) -> Dict[str, Any]:
        """Enviar notificaciones de finalización"""
        notification_results = {
            "notifications_sent": [],
            "notifications_failed": [],
            "notification_successful": True
        }
        
        try:
            # Crear notificación estándar
            notification_payload = create_notification_payload(
                notification_type="task_completed" if event.reason == AgentEndTaskReason.SUCCESS else "task_failed",
                task_id=event.task_id,
                agent_id=event.agent_id,
                status="completed" if event.reason == AgentEndTaskReason.SUCCESS else "failed",
                data={
                    "completion_reason": event.reason.value,
                    "execution_summary": event.execution_summary,
                    "cleanup_actions": event.cleanup_actions,
                    "next_steps": event.next_steps
                },
                metadata=event.metadata
            )
            
            # Enviar notificación vía webhook
            await self.webhook_manager.send_webhook(
                WebhookEventType.TASK_LIFECYCLE,
                notification_payload
            )
            
            notification_results["notifications_sent"].append("webhook_notification")
            
            # Ejecutar handler de notificación específico
            if event.reason.value in self.notification_handlers:
                try:
                    handler_result = await self.notification_handlers[event.reason.value](event)
                    notification_results["handler_result"] = handler_result
                except Exception as e:
                    self.logger.error(f"Notification handler failed for {event.reason.value}: {e}")
                    notification_results["handler_error"] = str(e)
                    notification_results["notification_successful"] = False
            
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")
            notification_results["notification_successful"] = False
            notification_results["general_error"] = str(e)
        
        return notification_results

# Instancias globales
webhook_manager = WebhookManager()
agent_end_task_manager = AgentEndTaskManager(webhook_manager)

# Flask app para gestión de webhooks
app = Flask(__name__)
CORS(app)

@app.route('/webhooks', methods=['POST'])
def register_webhook():
    """Registrar nuevo webhook"""
    try:
        data = request.get_json()
        
        webhook_id = data.get("webhook_id")
        endpoint_url = data.get("endpoint_url")
        event_types = data.get("event_types", ["all"])
        secret = data.get("secret")
        filters = data.get("filters")
        
        if not webhook_id or not endpoint_url:
            return jsonify({
                "error": "webhook_id and endpoint_url are required"
            }), 400
        
        success = webhook_manager.register_webhook(
            webhook_id, endpoint_url, event_types, secret, filters
        )
        
        if success:
            return jsonify({
                "status": "webhook_registered",
                "webhook_id": webhook_id,
                "endpoint_url": endpoint_url,
                "event_types": event_types
            })
        else:
            return jsonify({
                "error": "Failed to register webhook"
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/webhooks/<webhook_id>', methods=['DELETE'])
def unregister_webhook(webhook_id: str):
    """Desregistrar webhook"""
    try:
        success = webhook_manager.unregister_webhook(webhook_id)
        
        if success:
            return jsonify({
                "status": "webhook_unregistered",
                "webhook_id": webhook_id
            })
        else:
            return jsonify({
                "error": "Failed to unregister webhook"
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/webhooks/<webhook_id>/stats', methods=['GET'])
def get_webhook_stats(webhook_id: str):
    """Obtener estadísticas de webhook"""
    try:
        stats = webhook_manager.get_webhook_stats(webhook_id)
        
        if stats:
            return jsonify(stats)
        else:
            return jsonify({"error": "Webhook not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/agent/end-task', methods=['POST'])
async def end_task():
    """Endpoint para finalizar tarea de agente"""
    try:
        data = request.get_json()
        
        task_id = data.get("task_id")
        agent_id = data.get("agent_id")
        reason = data.get("reason", "success")
        execution_summary = data.get("execution_summary", {})
        cleanup_actions = data.get("cleanup_actions", [])
        next_steps = data.get("next_steps", [])
        metadata = data.get("metadata", {})
        
        if not task_id or not agent_id:
            return jsonify({
                "error": "task_id and agent_id are required"
            }), 400
        
        try:
            reason_enum = AgentEndTaskReason(reason)
        except ValueError:
            return jsonify({
                "error": f"Invalid reason: {reason}",
                "valid_reasons": [r.value for r in AgentEndTaskReason]
            }), 400
        
        result = await agent_end_task_manager.end_task(
            task_id, agent_id, reason_enum, execution_summary,
            cleanup_actions, next_steps, metadata
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/webhooks/test', methods=['POST'])
async def test_webhook():
    """Endpoint para probar envío de webhooks"""
    try:
        data = request.get_json()
        
        event_type = data.get("event_type", "system_event")
        payload = data.get("payload", {"test": True})
        target_webhooks = data.get("target_webhooks")
        
        try:
            event_type_enum = WebhookEventType(event_type)
        except ValueError:
            return jsonify({
                "error": f"Invalid event_type: {event_type}",
                "valid_types": [e.value for e in WebhookEventType]
            }), 400
        
        await webhook_manager.send_webhook(
            event_type_enum, payload, target_webhooks
        )
        
        return jsonify({
            "status": "webhook_sent",
            "event_type": event_type,
            "target_webhooks": target_webhooks or "all"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "webhook_system",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Registrar webhooks por defecto
    webhook_manager.register_webhook(
        "manus_primary",
        "http://65.109.54.94:3000/webhook/sam",
        ["task_lifecycle", "agent_status"],
        "manus_sam_webhook_secret_2024"
    )
    
    # Iniciar servidor Flask
    app.run(host="0.0.0.0", port=3003, debug=False)

