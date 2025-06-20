#!/usr/bin/env python3
"""
SAM → Manus Notification Protocol Implementation
Sistema completo de notificaciones bidireccionales entre SAM y Manus
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import queue
import sqlite3
from contextlib import contextmanager

class NotificationType(Enum):
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_ESCALATED = "task_escalated"
    AGENT_STATUS = "agent_status"
    SYSTEM_ALERT = "system_alert"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"

@dataclass
class NotificationPayload:
    """Estructura estándar para notificaciones SAM → Manus"""
    notification_id: str
    notification_type: NotificationType
    task_id: str
    agent_id: str
    timestamp: str
    status: TaskStatus
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class WebhookEndpoint:
    """Configuración de endpoint webhook"""
    url: str
    secret: Optional[str] = None
    timeout: int = 30
    retry_policy: Dict[str, Any] = None
    active: bool = True

class NotificationManager:
    """
    Gestor central de notificaciones SAM → Manus
    Maneja webhooks, reintentos, y persistencia
    """
    
    def __init__(self, db_path: str = "/tmp/notifications.db"):
        self.db_path = db_path
        self.webhook_endpoints: Dict[str, WebhookEndpoint] = {}
        self.notification_queue = queue.Queue()
        self.failed_notifications = queue.Queue()
        self.notification_handlers: Dict[NotificationType, List[Callable]] = {}
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Inicializar base de datos
        self._init_database()
        
        # Iniciar worker threads
        self._start_workers()
    
    def _init_database(self):
        """Inicializar base de datos SQLite para persistencia"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    notification_type TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    delivered BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS webhook_endpoints (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    secret TEXT,
                    timeout INTEGER DEFAULT 30,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS delivery_attempts (
                    id TEXT PRIMARY KEY,
                    notification_id TEXT NOT NULL,
                    endpoint_url TEXT NOT NULL,
                    attempt_time TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    response_code INTEGER,
                    error_message TEXT,
                    FOREIGN KEY (notification_id) REFERENCES notifications (id)
                )
            """)
    
    def _start_workers(self):
        """Iniciar threads workers para procesamiento de notificaciones"""
        # Worker para procesar notificaciones
        notification_worker = threading.Thread(
            target=self._notification_worker,
            daemon=True
        )
        notification_worker.start()
        
        # Worker para reintentos
        retry_worker = threading.Thread(
            target=self._retry_worker,
            daemon=True
        )
        retry_worker.start()
    
    def register_webhook(self, endpoint_id: str, webhook_config: WebhookEndpoint):
        """Registrar endpoint webhook para notificaciones"""
        self.webhook_endpoints[endpoint_id] = webhook_config
        
        # Persistir en base de datos
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO webhook_endpoints 
                (id, url, secret, timeout, active)
                VALUES (?, ?, ?, ?, ?)
            """, (
                endpoint_id,
                webhook_config.url,
                webhook_config.secret,
                webhook_config.timeout,
                webhook_config.active
            ))
        
        self.logger.info(f"Registered webhook endpoint: {endpoint_id} -> {webhook_config.url}")
    
    def unregister_webhook(self, endpoint_id: str):
        """Desregistrar endpoint webhook"""
        if endpoint_id in self.webhook_endpoints:
            del self.webhook_endpoints[endpoint_id]
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE webhook_endpoints SET active = FALSE WHERE id = ?",
                    (endpoint_id,)
                )
            
            self.logger.info(f"Unregistered webhook endpoint: {endpoint_id}")
    
    def send_notification(self, notification: NotificationPayload):
        """Enviar notificación a la cola de procesamiento"""
        # Persistir notificación
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO notifications 
                (id, notification_type, task_id, agent_id, timestamp, status, payload, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification.notification_id,
                notification.notification_type.value,
                notification.task_id,
                notification.agent_id,
                notification.timestamp,
                notification.status.value,
                json.dumps(asdict(notification)),
                notification.retry_count
            ))
        
        # Añadir a cola de procesamiento
        self.notification_queue.put(notification)
        
        self.logger.info(f"Queued notification: {notification.notification_id} - {notification.notification_type.value}")
    
    def _notification_worker(self):
        """Worker thread para procesar notificaciones"""
        while True:
            try:
                notification = self.notification_queue.get(timeout=1)
                asyncio.run(self._process_notification(notification))
                self.notification_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in notification worker: {e}")
    
    async def _process_notification(self, notification: NotificationPayload):
        """Procesar una notificación individual"""
        success_count = 0
        total_endpoints = len(self.webhook_endpoints)
        
        for endpoint_id, webhook in self.webhook_endpoints.items():
            if not webhook.active:
                continue
                
            try:
                success = await self._send_webhook(notification, webhook)
                if success:
                    success_count += 1
                    
                # Registrar intento de entrega
                self._log_delivery_attempt(
                    notification.notification_id,
                    webhook.url,
                    success,
                    None,
                    None
                )
                
            except Exception as e:
                self.logger.error(f"Error sending webhook to {webhook.url}: {e}")
                self._log_delivery_attempt(
                    notification.notification_id,
                    webhook.url,
                    False,
                    None,
                    str(e)
                )
        
        # Marcar como entregada si al menos un webhook fue exitoso
        if success_count > 0:
            self._mark_notification_delivered(notification.notification_id)
        else:
            # Añadir a cola de reintentos si falló completamente
            if notification.retry_count < notification.max_retries:
                notification.retry_count += 1
                self.failed_notifications.put(notification)
    
    async def _send_webhook(self, notification: NotificationPayload, webhook: WebhookEndpoint) -> bool:
        """Enviar webhook HTTP a endpoint específico"""
        try:
            payload = asdict(notification)
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "SAM-Notification-System/1.0",
                "X-Notification-ID": notification.notification_id,
                "X-Notification-Type": notification.notification_type.value,
                "X-Task-ID": notification.task_id,
                "X-Agent-ID": notification.agent_id
            }
            
            # Añadir signature si hay secret
            if webhook.secret:
                import hmac
                import hashlib
                
                payload_str = json.dumps(payload, sort_keys=True)
                signature = hmac.new(
                    webhook.secret.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Signature-SHA256"] = f"sha256={signature}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=webhook.timeout)
                ) as response:
                    
                    if response.status in [200, 201, 202]:
                        self.logger.info(f"Webhook delivered successfully to {webhook.url}")
                        return True
                    else:
                        self.logger.warning(f"Webhook failed with status {response.status}: {webhook.url}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.error(f"Webhook timeout to {webhook.url}")
            return False
        except Exception as e:
            self.logger.error(f"Webhook error to {webhook.url}: {e}")
            return False
    
    def _retry_worker(self):
        """Worker thread para procesar reintentos"""
        while True:
            try:
                notification = self.failed_notifications.get(timeout=5)
                
                # Esperar antes del reintento (exponential backoff)
                wait_time = min(300, 2 ** notification.retry_count)  # Max 5 minutos
                time.sleep(wait_time)
                
                # Reenviar notificación
                asyncio.run(self._process_notification(notification))
                
                self.failed_notifications.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in retry worker: {e}")
    
    def _log_delivery_attempt(self, notification_id: str, endpoint_url: str, 
                            success: bool, response_code: Optional[int], 
                            error_message: Optional[str]):
        """Registrar intento de entrega en base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO delivery_attempts 
                (id, notification_id, endpoint_url, attempt_time, success, response_code, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                notification_id,
                endpoint_url,
                datetime.now().isoformat(),
                success,
                response_code,
                error_message
            ))
    
    def _mark_notification_delivered(self, notification_id: str):
        """Marcar notificación como entregada"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE notifications SET delivered = TRUE WHERE id = ?",
                (notification_id,)
            )
    
    def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de una notificación específica"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT n.*, 
                       COUNT(da.id) as delivery_attempts,
                       COUNT(CASE WHEN da.success = 1 THEN 1 END) as successful_deliveries
                FROM notifications n
                LEFT JOIN delivery_attempts da ON n.id = da.notification_id
                WHERE n.id = ?
                GROUP BY n.id
            """, (notification_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
        
        return None
    
    def get_delivery_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener estadísticas de entrega de las últimas N horas"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_notifications,
                    COUNT(CASE WHEN delivered = 1 THEN 1 END) as delivered_notifications,
                    COUNT(CASE WHEN delivered = 0 THEN 1 END) as pending_notifications,
                    AVG(retry_count) as avg_retry_count
                FROM notifications 
                WHERE created_at >= ?
            """, (since,))
            
            stats = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))
            
            # Estadísticas por tipo
            cursor = conn.execute("""
                SELECT notification_type, COUNT(*) as count
                FROM notifications 
                WHERE created_at >= ?
                GROUP BY notification_type
            """, (since,))
            
            stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            return stats

# Instancia global del gestor de notificaciones
notification_manager = NotificationManager()

class SAMNotificationSender:
    """
    Clase para que SAM envíe notificaciones a Manus
    Se integra con el sistema de ejecución de SAM
    """
    
    def __init__(self, agent_id: str = "sam_autonomous"):
        self.agent_id = agent_id
        self.notification_manager = notification_manager
    
    def notify_task_started(self, task_id: str, task_data: Dict[str, Any]):
        """Notificar que una tarea ha comenzado"""
        notification = NotificationPayload(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.TASK_STARTED,
            task_id=task_id,
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            status=TaskStatus.RUNNING,
            data={
                "task_type": task_data.get("task_type", "unknown"),
                "description": task_data.get("description", ""),
                "estimated_duration": task_data.get("estimated_duration"),
                "complexity": task_data.get("complexity", "medium")
            },
            metadata={
                "start_time": datetime.now().isoformat(),
                "agent_version": "1.0.0",
                "execution_mode": "autonomous"
            }
        )
        
        self.notification_manager.send_notification(notification)
    
    def notify_task_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """Notificar progreso de una tarea"""
        notification = NotificationPayload(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.TASK_PROGRESS,
            task_id=task_id,
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            status=TaskStatus.RUNNING,
            data={
                "progress_percentage": progress_data.get("progress", 0),
                "current_step": progress_data.get("current_step", ""),
                "steps_completed": progress_data.get("steps_completed", 0),
                "total_steps": progress_data.get("total_steps", 0),
                "intermediate_results": progress_data.get("results", {})
            },
            metadata={
                "update_time": datetime.now().isoformat(),
                "execution_time_elapsed": progress_data.get("elapsed_time", 0)
            }
        )
        
        self.notification_manager.send_notification(notification)
    
    def notify_task_completed(self, task_id: str, result_data: Dict[str, Any]):
        """Notificar que una tarea se ha completado exitosamente"""
        notification = NotificationPayload(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.TASK_COMPLETED,
            task_id=task_id,
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            status=TaskStatus.COMPLETED,
            data={
                "result": result_data.get("result", {}),
                "output_files": result_data.get("output_files", []),
                "metrics": result_data.get("metrics", {}),
                "quality_score": result_data.get("quality_score", 0.0),
                "execution_summary": result_data.get("summary", "")
            },
            metadata={
                "completion_time": datetime.now().isoformat(),
                "total_execution_time": result_data.get("execution_time", 0),
                "tokens_used": result_data.get("tokens_used", 0),
                "cost": result_data.get("cost", 0.0),
                "model_used": result_data.get("model", "unknown")
            }
        )
        
        self.notification_manager.send_notification(notification)
    
    def notify_task_failed(self, task_id: str, error_data: Dict[str, Any]):
        """Notificar que una tarea ha fallado"""
        notification = NotificationPayload(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.TASK_FAILED,
            task_id=task_id,
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            status=TaskStatus.FAILED,
            data={
                "error_type": error_data.get("error_type", "unknown"),
                "error_message": error_data.get("error_message", ""),
                "error_details": error_data.get("error_details", {}),
                "partial_results": error_data.get("partial_results", {}),
                "recovery_suggestions": error_data.get("recovery_suggestions", [])
            },
            metadata={
                "failure_time": datetime.now().isoformat(),
                "execution_time_before_failure": error_data.get("execution_time", 0),
                "retry_count": error_data.get("retry_count", 0),
                "escalation_required": error_data.get("escalation_required", False)
            }
        )
        
        self.notification_manager.send_notification(notification)
    
    def notify_task_escalated(self, task_id: str, escalation_data: Dict[str, Any]):
        """Notificar que una tarea ha sido escalada"""
        notification = NotificationPayload(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType.TASK_ESCALATED,
            task_id=task_id,
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            status=TaskStatus.ESCALATED,
            data={
                "escalation_reason": escalation_data.get("reason", ""),
                "escalation_level": escalation_data.get("level", "human"),
                "context": escalation_data.get("context", {}),
                "attempted_solutions": escalation_data.get("attempted_solutions", []),
                "recommended_actions": escalation_data.get("recommended_actions", [])
            },
            metadata={
                "escalation_time": datetime.now().isoformat(),
                "attempts_before_escalation": escalation_data.get("attempts", 0),
                "urgency": escalation_data.get("urgency", "medium")
            }
        )
        
        self.notification_manager.send_notification(notification)

# Crear instancia global del notificador de SAM
sam_notifier = SAMNotificationSender()

# Flask app para recibir webhooks de Manus
app = Flask(__name__)
CORS(app)

@app.route('/webhook/manus', methods=['POST'])
def receive_manus_webhook():
    """Endpoint para recibir webhooks de Manus"""
    try:
        data = request.get_json()
        
        # Validar webhook
        if not data or 'notification_id' not in data:
            return jsonify({"error": "Invalid webhook payload"}), 400
        
        # Procesar webhook de Manus
        # Aquí se puede implementar lógica específica para responder a notificaciones de Manus
        
        return jsonify({
            "status": "received",
            "notification_id": data.get("notification_id"),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/notifications/register', methods=['POST'])
def register_webhook_endpoint():
    """Registrar nuevo endpoint webhook"""
    try:
        data = request.get_json()
        
        endpoint_id = data.get("endpoint_id")
        url = data.get("url")
        secret = data.get("secret")
        timeout = data.get("timeout", 30)
        
        if not endpoint_id or not url:
            return jsonify({"error": "endpoint_id and url are required"}), 400
        
        webhook_config = WebhookEndpoint(
            url=url,
            secret=secret,
            timeout=timeout,
            active=True
        )
        
        notification_manager.register_webhook(endpoint_id, webhook_config)
        
        return jsonify({
            "status": "registered",
            "endpoint_id": endpoint_id,
            "url": url
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/notifications/status/<notification_id>', methods=['GET'])
def get_notification_status(notification_id: str):
    """Obtener estado de una notificación"""
    try:
        status = notification_manager.get_notification_status(notification_id)
        
        if status:
            return jsonify(status)
        else:
            return jsonify({"error": "Notification not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/notifications/stats', methods=['GET'])
def get_delivery_stats():
    """Obtener estadísticas de entrega"""
    try:
        hours = request.args.get('hours', 24, type=int)
        stats = notification_manager.get_delivery_stats(hours)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Registrar webhook de Manus por defecto
    manus_webhook = WebhookEndpoint(
        url="http://65.109.54.94:3000/webhook/sam",  # Endpoint de Manus
        secret="manus_sam_webhook_secret_2024",
        timeout=30,
        active=True
    )
    notification_manager.register_webhook("manus_primary", manus_webhook)
    
    # Iniciar servidor Flask
    app.run(host="0.0.0.0", port=3002, debug=False)

