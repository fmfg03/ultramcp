#!/usr/bin/env python3
"""
Manus Webhook Receiver - Receptor de notificaciones de SAM
Sistema para que Manus reciba y procese notificaciones de SAM
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hmac
import hashlib
import threading
import queue

class NotificationAction(Enum):
    ACKNOWLEDGE = "acknowledge"
    REQUEST_UPDATE = "request_update"
    CANCEL_TASK = "cancel_task"
    ESCALATE = "escalate"
    RETRY = "retry"

@dataclass
class ReceivedNotification:
    """Estructura para notificaciones recibidas de SAM"""
    notification_id: str
    task_id: str
    agent_id: str
    notification_type: str
    status: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    received_at: str
    processed: bool = False
    action_taken: Optional[str] = None

class ManusWebhookReceiver:
    """
    Receptor de webhooks para Manus
    Procesa notificaciones de SAM y toma acciones apropiadas
    """
    
    def __init__(self, db_path: str = "/tmp/manus_notifications.db"):
        self.db_path = db_path
        self.webhook_secret = "manus_sam_webhook_secret_2024"
        self.notification_handlers = {}
        self.action_queue = queue.Queue()
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Inicializar base de datos
        self._init_database()
        
        # Iniciar worker para procesar acciones
        self._start_action_worker()
    
    def _init_database(self):
        """Inicializar base de datos para notificaciones recibidas"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS received_notifications (
                    notification_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    data TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    action_taken TEXT,
                    processed_at TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_tracking (
                    task_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completion_time TEXT,
                    result_data TEXT,
                    error_data TEXT
                )
            """)
    
    def _start_action_worker(self):
        """Iniciar worker thread para procesar acciones"""
        action_worker = threading.Thread(
            target=self._action_worker,
            daemon=True
        )
        action_worker.start()
    
    def _action_worker(self):
        """Worker thread para procesar acciones en respuesta a notificaciones"""
        while True:
            try:
                action_data = self.action_queue.get(timeout=1)
                asyncio.run(self._process_action(action_data))
                self.action_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in action worker: {e}")
    
    async def _process_action(self, action_data: Dict[str, Any]):
        """Procesar una acción específica"""
        action_type = action_data.get("action")
        task_id = action_data.get("task_id")
        
        try:
            if action_type == NotificationAction.ACKNOWLEDGE.value:
                await self._send_acknowledgment(task_id, action_data)
            elif action_type == NotificationAction.REQUEST_UPDATE.value:
                await self._request_task_update(task_id, action_data)
            elif action_type == NotificationAction.CANCEL_TASK.value:
                await self._cancel_task(task_id, action_data)
            elif action_type == NotificationAction.ESCALATE.value:
                await self._escalate_task(task_id, action_data)
            elif action_type == NotificationAction.RETRY.value:
                await self._retry_task(task_id, action_data)
                
        except Exception as e:
            self.logger.error(f"Error processing action {action_type} for task {task_id}: {e}")
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verificar firma del webhook"""
        if not signature.startswith("sha256="):
            return False
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        received_signature = signature[7:]  # Remove "sha256=" prefix
        
        return hmac.compare_digest(expected_signature, received_signature)
    
    def process_notification(self, notification_data: Dict[str, Any], 
                           signature: Optional[str] = None) -> Dict[str, Any]:
        """Procesar notificación recibida de SAM"""
        try:
            # Verificar firma si está presente
            if signature:
                payload_str = json.dumps(notification_data, sort_keys=True)
                if not self.verify_webhook_signature(payload_str, signature):
                    raise ValueError("Invalid webhook signature")
            
            # Crear objeto de notificación recibida
            received_notification = ReceivedNotification(
                notification_id=notification_data.get("notification_id"),
                task_id=notification_data.get("task_id"),
                agent_id=notification_data.get("agent_id"),
                notification_type=notification_data.get("notification_type"),
                status=notification_data.get("status"),
                data=notification_data.get("data", {}),
                metadata=notification_data.get("metadata", {}),
                received_at=datetime.now().isoformat()
            )
            
            # Persistir notificación
            self._store_notification(received_notification)
            
            # Actualizar tracking de tarea
            self._update_task_tracking(received_notification)
            
            # Determinar acción a tomar
            action = self._determine_action(received_notification)
            
            if action:
                # Añadir acción a la cola de procesamiento
                action_data = {
                    "action": action.value,
                    "task_id": received_notification.task_id,
                    "notification_id": received_notification.notification_id,
                    "notification_data": notification_data
                }
                self.action_queue.put(action_data)
            
            # Marcar como procesada
            self._mark_notification_processed(
                received_notification.notification_id,
                action.value if action else None
            )
            
            self.logger.info(f"Processed notification {received_notification.notification_id} - Action: {action}")
            
            return {
                "status": "processed",
                "notification_id": received_notification.notification_id,
                "action_taken": action.value if action else "none",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing notification: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _store_notification(self, notification: ReceivedNotification):
        """Almacenar notificación en base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO received_notifications 
                (notification_id, task_id, agent_id, notification_type, status, 
                 data, metadata, received_at, processed, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification.notification_id,
                notification.task_id,
                notification.agent_id,
                notification.notification_type,
                notification.status,
                json.dumps(notification.data),
                json.dumps(notification.metadata),
                notification.received_at,
                notification.processed,
                notification.action_taken
            ))
    
    def _update_task_tracking(self, notification: ReceivedNotification):
        """Actualizar tracking del estado de la tarea"""
        with sqlite3.connect(self.db_path) as conn:
            # Verificar si la tarea ya existe
            cursor = conn.execute(
                "SELECT task_id FROM task_tracking WHERE task_id = ?",
                (notification.task_id,)
            )
            
            if cursor.fetchone():
                # Actualizar tarea existente
                update_data = {
                    "status": notification.status,
                    "updated_at": datetime.now().isoformat()
                }
                
                if notification.notification_type == "task_completed":
                    update_data["completion_time"] = notification.received_at
                    update_data["result_data"] = json.dumps(notification.data)
                elif notification.notification_type == "task_failed":
                    update_data["error_data"] = json.dumps(notification.data)
                
                # Construir query dinámicamente
                set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
                values = list(update_data.values()) + [notification.task_id]
                
                conn.execute(
                    f"UPDATE task_tracking SET {set_clause} WHERE task_id = ?",
                    values
                )
            else:
                # Crear nueva entrada de tarea
                conn.execute("""
                    INSERT INTO task_tracking 
                    (task_id, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    notification.task_id,
                    notification.status,
                    notification.received_at,
                    datetime.now().isoformat()
                ))
    
    def _determine_action(self, notification: ReceivedNotification) -> Optional[NotificationAction]:
        """Determinar qué acción tomar basándose en la notificación"""
        notification_type = notification.notification_type
        status = notification.status
        
        # Lógica de decisión basada en tipo de notificación
        if notification_type == "task_started":
            return NotificationAction.ACKNOWLEDGE
        
        elif notification_type == "task_progress":
            # Solo acknowledger, no acción adicional necesaria
            return NotificationAction.ACKNOWLEDGE
        
        elif notification_type == "task_completed":
            # Acknowledger y posiblemente solicitar resultados detallados
            return NotificationAction.ACKNOWLEDGE
        
        elif notification_type == "task_failed":
            # Determinar si reintentar o escalar
            retry_count = notification.metadata.get("retry_count", 0)
            if retry_count < 2:  # Máximo 2 reintentos
                return NotificationAction.RETRY
            else:
                return NotificationAction.ESCALATE
        
        elif notification_type == "task_escalated":
            # Acknowledger escalación
            return NotificationAction.ACKNOWLEDGE
        
        return None
    
    def _mark_notification_processed(self, notification_id: str, action_taken: Optional[str]):
        """Marcar notificación como procesada"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE received_notifications 
                SET processed = TRUE, action_taken = ?, processed_at = ?
                WHERE notification_id = ?
            """, (action_taken, datetime.now().isoformat(), notification_id))
    
    async def _send_acknowledgment(self, task_id: str, action_data: Dict[str, Any]):
        """Enviar acknowledgment a SAM"""
        # Implementar llamada HTTP a SAM para acknowledger
        sam_endpoint = "http://65.109.54.94:3002/webhook/manus"
        
        ack_payload = {
            "action": "acknowledge",
            "task_id": task_id,
            "notification_id": action_data.get("notification_id"),
            "timestamp": datetime.now().isoformat(),
            "manus_agent_id": "manus_orchestrator"
        }
        
        # Aquí se implementaría la llamada HTTP real
        self.logger.info(f"Sending acknowledgment for task {task_id}")
    
    async def _request_task_update(self, task_id: str, action_data: Dict[str, Any]):
        """Solicitar actualización de estado de tarea"""
        # Implementar solicitud de update a SAM
        self.logger.info(f"Requesting update for task {task_id}")
    
    async def _cancel_task(self, task_id: str, action_data: Dict[str, Any]):
        """Cancelar tarea en SAM"""
        # Implementar cancelación de tarea
        self.logger.info(f"Cancelling task {task_id}")
    
    async def _escalate_task(self, task_id: str, action_data: Dict[str, Any]):
        """Escalar tarea a intervención humana"""
        # Implementar escalación
        self.logger.info(f"Escalating task {task_id}")
    
    async def _retry_task(self, task_id: str, action_data: Dict[str, Any]):
        """Reintentar tarea fallida"""
        # Implementar reintento
        self.logger.info(f"Retrying task {task_id}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado actual de una tarea"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM task_tracking WHERE task_id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
        
        return None
    
    def get_task_notifications(self, task_id: str) -> List[Dict[str, Any]]:
        """Obtener todas las notificaciones de una tarea"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM received_notifications 
                WHERE task_id = ? 
                ORDER BY received_at ASC
            """, (task_id,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Instancia global del receptor
manus_webhook_receiver = ManusWebhookReceiver()

# Flask app para recibir webhooks de SAM
app = Flask(__name__)
CORS(app)

@app.route('/webhook/sam', methods=['POST'])
def receive_sam_webhook():
    """Endpoint principal para recibir webhooks de SAM"""
    try:
        # Obtener datos del webhook
        notification_data = request.get_json()
        signature = request.headers.get('X-Signature-SHA256')
        
        if not notification_data:
            return jsonify({"error": "No JSON payload received"}), 400
        
        # Procesar notificación
        result = manus_webhook_receiver.process_notification(
            notification_data, 
            signature
        )
        
        if result.get("status") == "error":
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/tasks/<task_id>/status', methods=['GET'])
def get_task_status(task_id: str):
    """Obtener estado de una tarea específica"""
    try:
        status = manus_webhook_receiver.get_task_status(task_id)
        
        if status:
            return jsonify(status)
        else:
            return jsonify({"error": "Task not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/<task_id>/notifications', methods=['GET'])
def get_task_notifications(task_id: str):
    """Obtener todas las notificaciones de una tarea"""
    try:
        notifications = manus_webhook_receiver.get_task_notifications(task_id)
        return jsonify({
            "task_id": task_id,
            "notifications": notifications,
            "count": len(notifications)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id: str):
    """Cancelar una tarea específica"""
    try:
        # Añadir acción de cancelación a la cola
        action_data = {
            "action": NotificationAction.CANCEL_TASK.value,
            "task_id": task_id,
            "requested_by": "manus_api",
            "timestamp": datetime.now().isoformat()
        }
        
        manus_webhook_receiver.action_queue.put(action_data)
        
        return jsonify({
            "status": "cancellation_requested",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "manus_webhook_receiver",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Iniciar servidor Flask
    app.run(host="0.0.0.0", port=3000, debug=False)

