#!/usr/bin/env python3
"""
MCP Enterprise - Sistema de Monitoreo Activo Post-Webhook
Sistema completo de monitoreo activo, reintentos inteligentes y backup plans
"""

import asyncio
import json
import time
import logging
import threading
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import hmac
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookStatus(Enum):
    """Estados de webhook"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    ABANDONED = "abandoned"

class TaskStatus(Enum):
    """Estados de tarea"""
    CREATED = "created"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class MonitoringLevel(Enum):
    """Niveles de monitoreo"""
    BASIC = "basic"
    STANDARD = "standard"
    INTENSIVE = "intensive"
    REAL_TIME = "real_time"

@dataclass
class WebhookEvent:
    """Evento de webhook"""
    id: str
    task_id: str
    webhook_url: str
    payload: Dict[str, Any]
    status: WebhookStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 5
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None

@dataclass
class TaskMonitoring:
    """Monitoreo de tarea"""
    task_id: str
    agent_id: str
    status: TaskStatus
    created_at: datetime
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    monitoring_level: MonitoringLevel = MonitoringLevel.STANDARD
    timeout_seconds: int = 3600  # 1 hora por defecto
    heartbeat_interval: int = 30  # 30 segundos
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ActiveWebhookMonitor:
    """Monitor activo de webhooks con reintentos inteligentes"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.db_path = self.config.get("db_path", "webhook_monitor.db")
        
        # Inicializar base de datos
        self._init_database()
        
        # Cola de webhooks pendientes
        self.webhook_queue = []
        self.queue_lock = threading.Lock()
        
        # Configuración de reintentos
        self.retry_delays = [5, 15, 60, 300, 900]  # 5s, 15s, 1m, 5m, 15m
        
        # Workers para procesamiento
        self.webhook_workers = []
        self.monitoring_active = False
        
        # Callbacks para eventos
        self.event_callbacks = {
            "webhook_sent": [],
            "webhook_delivered": [],
            "webhook_failed": [],
            "webhook_abandoned": [],
            "task_timeout": [],
            "heartbeat_missed": []
        }
        
        # Iniciar servicios
        self.start_monitoring()
    
    def _init_database(self):
        """Inicializar base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_events (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                webhook_url TEXT,
                payload TEXT,
                status TEXT,
                created_at TEXT,
                sent_at TEXT,
                delivered_at TEXT,
                failed_at TEXT,
                retry_count INTEGER,
                max_retries INTEGER,
                next_retry_at TEXT,
                error_message TEXT,
                response_code INTEGER,
                response_body TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_monitoring (
                task_id TEXT PRIMARY KEY,
                agent_id TEXT,
                status TEXT,
                created_at TEXT,
                assigned_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                last_heartbeat TEXT,
                monitoring_level TEXT,
                timeout_seconds INTEGER,
                heartbeat_interval INTEGER,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_events (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                event_type TEXT,
                event_data TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_monitoring(self):
        """Iniciar monitoreo activo"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Iniciar workers de webhook
        for i in range(3):  # 3 workers concurrentes
            worker = threading.Thread(target=self._webhook_worker, args=(i,))
            worker.daemon = True
            worker.start()
            self.webhook_workers.append(worker)
        
        # Iniciar monitor de reintentos
        retry_monitor = threading.Thread(target=self._retry_monitor)
        retry_monitor.daemon = True
        retry_monitor.start()
        
        # Iniciar monitor de timeouts
        timeout_monitor = threading.Thread(target=self._timeout_monitor)
        timeout_monitor.daemon = True
        timeout_monitor.start()
        
        # Iniciar monitor de heartbeats
        heartbeat_monitor = threading.Thread(target=self._heartbeat_monitor)
        heartbeat_monitor.daemon = True
        heartbeat_monitor.start()
        
        logger.info("Active webhook monitoring started")
    
    def register_webhook(self, task_id: str, webhook_url: str, 
                        payload: Dict[str, Any], max_retries: int = 5) -> str:
        """Registrar webhook para monitoreo activo"""
        webhook_event = WebhookEvent(
            id=str(uuid.uuid4()),
            task_id=task_id,
            webhook_url=webhook_url,
            payload=payload,
            status=WebhookStatus.PENDING,
            created_at=datetime.now(),
            max_retries=max_retries
        )
        
        # Guardar en base de datos
        self._save_webhook_event(webhook_event)
        
        # Añadir a cola de procesamiento
        with self.queue_lock:
            self.webhook_queue.append(webhook_event)
        
        logger.info(f"Webhook registered for task {task_id}: {webhook_event.id}")
        return webhook_event.id
    
    def register_task_monitoring(self, task_id: str, agent_id: str, 
                                monitoring_level: MonitoringLevel = MonitoringLevel.STANDARD,
                                timeout_seconds: int = 3600) -> bool:
        """Registrar tarea para monitoreo activo"""
        task_monitoring = TaskMonitoring(
            task_id=task_id,
            agent_id=agent_id,
            status=TaskStatus.CREATED,
            created_at=datetime.now(),
            monitoring_level=monitoring_level,
            timeout_seconds=timeout_seconds
        )
        
        # Guardar en base de datos
        self._save_task_monitoring(task_monitoring)
        
        # Registrar evento
        self._log_monitoring_event(task_id, "task_registered", {
            "agent_id": agent_id,
            "monitoring_level": monitoring_level.value,
            "timeout_seconds": timeout_seconds
        })
        
        logger.info(f"Task monitoring registered: {task_id} -> {agent_id}")
        return True
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          metadata: Dict[str, Any] = None):
        """Actualizar estado de tarea"""
        task_monitoring = self._get_task_monitoring(task_id)
        if not task_monitoring:
            logger.warning(f"Task monitoring not found: {task_id}")
            return
        
        # Actualizar estado
        old_status = task_monitoring.status
        task_monitoring.status = status
        
        # Actualizar timestamps según estado
        now = datetime.now()
        if status == TaskStatus.ASSIGNED:
            task_monitoring.assigned_at = now
        elif status == TaskStatus.EXECUTING:
            task_monitoring.started_at = now
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task_monitoring.completed_at = now
        
        # Actualizar metadata
        if metadata:
            task_monitoring.metadata.update(metadata)
        
        # Guardar cambios
        self._save_task_monitoring(task_monitoring)
        
        # Registrar evento
        self._log_monitoring_event(task_id, "status_changed", {
            "old_status": old_status.value,
            "new_status": status.value,
            "metadata": metadata
        })
        
        # Ejecutar callbacks
        if status == TaskStatus.COMPLETED:
            self._execute_callbacks("task_completed", task_id, task_monitoring)
        elif status == TaskStatus.FAILED:
            self._execute_callbacks("task_failed", task_id, task_monitoring)
        
        logger.info(f"Task {task_id} status updated: {old_status.value} -> {status.value}")
    
    def send_heartbeat(self, task_id: str, metadata: Dict[str, Any] = None):
        """Enviar heartbeat de tarea"""
        task_monitoring = self._get_task_monitoring(task_id)
        if not task_monitoring:
            logger.warning(f"Task monitoring not found: {task_id}")
            return
        
        # Actualizar último heartbeat
        task_monitoring.last_heartbeat = datetime.now()
        
        # Actualizar metadata si se proporciona
        if metadata:
            task_monitoring.metadata.update(metadata)
        
        # Guardar cambios
        self._save_task_monitoring(task_monitoring)
        
        # Registrar evento si es monitoreo intensivo
        if task_monitoring.monitoring_level in [MonitoringLevel.INTENSIVE, MonitoringLevel.REAL_TIME]:
            self._log_monitoring_event(task_id, "heartbeat", metadata or {})
        
        logger.debug(f"Heartbeat received for task {task_id}")
    
    def _webhook_worker(self, worker_id: int):
        """Worker para procesar webhooks"""
        logger.info(f"Webhook worker {worker_id} started")
        
        while self.monitoring_active:
            try:
                webhook_event = None
                
                # Obtener webhook de la cola
                with self.queue_lock:
                    if self.webhook_queue:
                        webhook_event = self.webhook_queue.pop(0)
                
                if webhook_event:
                    # Procesar webhook
                    self._process_webhook(webhook_event)
                else:
                    # No hay webhooks, esperar
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in webhook worker {worker_id}: {e}")
                time.sleep(1)
    
    def _process_webhook(self, webhook_event: WebhookEvent):
        """Procesar webhook individual"""
        try:
            # Marcar como enviando
            webhook_event.status = WebhookStatus.SENT
            webhook_event.sent_at = datetime.now()
            self._save_webhook_event(webhook_event)
            
            # Preparar headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "MCP-Enterprise-Webhook/1.0"
            }
            
            # Añadir firma HMAC si hay secret
            webhook_secret = self.config.get("webhook_secret")
            if webhook_secret:
                payload_str = json.dumps(webhook_event.payload, sort_keys=True)
                signature = hmac.new(
                    webhook_secret.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-MCP-Signature"] = f"sha256={signature}"
            
            # Enviar webhook
            response = requests.post(
                webhook_event.webhook_url,
                json=webhook_event.payload,
                headers=headers,
                timeout=30
            )
            
            # Procesar respuesta
            webhook_event.response_code = response.status_code
            webhook_event.response_body = response.text[:1000]  # Limitar tamaño
            
            if response.status_code == 200:
                webhook_event.status = WebhookStatus.DELIVERED
                webhook_event.delivered_at = datetime.now()
                self._execute_callbacks("webhook_delivered", webhook_event.task_id, webhook_event)
                logger.info(f"Webhook delivered successfully: {webhook_event.id}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
        except Exception as e:
            # Manejar fallo
            webhook_event.status = WebhookStatus.FAILED
            webhook_event.failed_at = datetime.now()
            webhook_event.error_message = str(e)
            
            # Programar reintento si no se han agotado
            if webhook_event.retry_count < webhook_event.max_retries:
                webhook_event.status = WebhookStatus.RETRYING
                webhook_event.retry_count += 1
                
                # Calcular próximo reintento con backoff exponencial
                delay_index = min(webhook_event.retry_count - 1, len(self.retry_delays) - 1)
                delay_seconds = self.retry_delays[delay_index]
                webhook_event.next_retry_at = datetime.now() + timedelta(seconds=delay_seconds)
                
                logger.warning(f"Webhook failed, scheduling retry {webhook_event.retry_count}/{webhook_event.max_retries} in {delay_seconds}s: {webhook_event.id}")
            else:
                webhook_event.status = WebhookStatus.ABANDONED
                self._execute_callbacks("webhook_abandoned", webhook_event.task_id, webhook_event)
                logger.error(f"Webhook abandoned after {webhook_event.max_retries} retries: {webhook_event.id}")
            
            self._execute_callbacks("webhook_failed", webhook_event.task_id, webhook_event)
        
        finally:
            # Guardar estado final
            self._save_webhook_event(webhook_event)
    
    def _retry_monitor(self):
        """Monitor de reintentos de webhooks"""
        logger.info("Retry monitor started")
        
        while self.monitoring_active:
            try:
                # Buscar webhooks listos para reintento
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM webhook_events 
                    WHERE status = ? AND next_retry_at <= ?
                ''', (WebhookStatus.RETRYING.value, datetime.now().isoformat()))
                
                rows = cursor.fetchall()
                conn.close()
                
                # Procesar reintentos
                for row in rows:
                    webhook_event = self._row_to_webhook_event(row)
                    
                    # Añadir a cola de procesamiento
                    with self.queue_lock:
                        self.webhook_queue.append(webhook_event)
                    
                    logger.info(f"Webhook queued for retry: {webhook_event.id}")
                
                time.sleep(10)  # Revisar cada 10 segundos
                
            except Exception as e:
                logger.error(f"Error in retry monitor: {e}")
                time.sleep(30)
    
    def _timeout_monitor(self):
        """Monitor de timeouts de tareas"""
        logger.info("Timeout monitor started")
        
        while self.monitoring_active:
            try:
                # Buscar tareas que han excedido timeout
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Tareas en ejecución que han excedido timeout
                cursor.execute('''
                    SELECT * FROM task_monitoring 
                    WHERE status IN (?, ?) 
                    AND datetime(created_at, '+' || timeout_seconds || ' seconds') <= datetime('now')
                ''', (TaskStatus.EXECUTING.value, TaskStatus.ASSIGNED.value))
                
                rows = cursor.fetchall()
                conn.close()
                
                # Procesar timeouts
                for row in rows:
                    task_monitoring = self._row_to_task_monitoring(row)
                    
                    # Marcar como timeout
                    self.update_task_status(task_monitoring.task_id, TaskStatus.TIMEOUT, {
                        "timeout_reason": "execution_timeout",
                        "timeout_seconds": task_monitoring.timeout_seconds
                    })
                    
                    # Ejecutar callbacks
                    self._execute_callbacks("task_timeout", task_monitoring.task_id, task_monitoring)
                    
                    logger.warning(f"Task timeout detected: {task_monitoring.task_id}")
                
                time.sleep(60)  # Revisar cada minuto
                
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}")
                time.sleep(60)
    
    def _heartbeat_monitor(self):
        """Monitor de heartbeats perdidos"""
        logger.info("Heartbeat monitor started")
        
        while self.monitoring_active:
            try:
                # Buscar tareas con heartbeats perdidos
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Tareas en ejecución sin heartbeat reciente
                cursor.execute('''
                    SELECT * FROM task_monitoring 
                    WHERE status = ? 
                    AND last_heartbeat IS NOT NULL
                    AND datetime(last_heartbeat, '+' || (heartbeat_interval * 3) || ' seconds') <= datetime('now')
                ''', (TaskStatus.EXECUTING.value,))
                
                rows = cursor.fetchall()
                conn.close()
                
                # Procesar heartbeats perdidos
                for row in rows:
                    task_monitoring = self._row_to_task_monitoring(row)
                    
                    # Registrar evento
                    self._log_monitoring_event(task_monitoring.task_id, "heartbeat_missed", {
                        "last_heartbeat": task_monitoring.last_heartbeat.isoformat() if task_monitoring.last_heartbeat else None,
                        "expected_interval": task_monitoring.heartbeat_interval
                    })
                    
                    # Ejecutar callbacks
                    self._execute_callbacks("heartbeat_missed", task_monitoring.task_id, task_monitoring)
                    
                    logger.warning(f"Heartbeat missed for task: {task_monitoring.task_id}")
                
                time.sleep(30)  # Revisar cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                time.sleep(60)
    
    def _save_webhook_event(self, webhook_event: WebhookEvent):
        """Guardar evento de webhook en base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO webhook_events 
            (id, task_id, webhook_url, payload, status, created_at, sent_at, 
             delivered_at, failed_at, retry_count, max_retries, next_retry_at, 
             error_message, response_code, response_body)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            webhook_event.id,
            webhook_event.task_id,
            webhook_event.webhook_url,
            json.dumps(webhook_event.payload),
            webhook_event.status.value,
            webhook_event.created_at.isoformat(),
            webhook_event.sent_at.isoformat() if webhook_event.sent_at else None,
            webhook_event.delivered_at.isoformat() if webhook_event.delivered_at else None,
            webhook_event.failed_at.isoformat() if webhook_event.failed_at else None,
            webhook_event.retry_count,
            webhook_event.max_retries,
            webhook_event.next_retry_at.isoformat() if webhook_event.next_retry_at else None,
            webhook_event.error_message,
            webhook_event.response_code,
            webhook_event.response_body
        ))
        
        conn.commit()
        conn.close()
    
    def _save_task_monitoring(self, task_monitoring: TaskMonitoring):
        """Guardar monitoreo de tarea en base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_monitoring 
            (task_id, agent_id, status, created_at, assigned_at, started_at, 
             completed_at, last_heartbeat, monitoring_level, timeout_seconds, 
             heartbeat_interval, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_monitoring.task_id,
            task_monitoring.agent_id,
            task_monitoring.status.value,
            task_monitoring.created_at.isoformat(),
            task_monitoring.assigned_at.isoformat() if task_monitoring.assigned_at else None,
            task_monitoring.started_at.isoformat() if task_monitoring.started_at else None,
            task_monitoring.completed_at.isoformat() if task_monitoring.completed_at else None,
            task_monitoring.last_heartbeat.isoformat() if task_monitoring.last_heartbeat else None,
            task_monitoring.monitoring_level.value,
            task_monitoring.timeout_seconds,
            task_monitoring.heartbeat_interval,
            json.dumps(task_monitoring.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def _log_monitoring_event(self, task_id: str, event_type: str, event_data: Dict[str, Any]):
        """Registrar evento de monitoreo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitoring_events (id, task_id, event_type, event_data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            task_id,
            event_type,
            json.dumps(event_data),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _get_task_monitoring(self, task_id: str) -> Optional[TaskMonitoring]:
        """Obtener monitoreo de tarea"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM task_monitoring WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_task_monitoring(row)
        return None
    
    def _row_to_webhook_event(self, row) -> WebhookEvent:
        """Convertir fila de DB a WebhookEvent"""
        return WebhookEvent(
            id=row[0],
            task_id=row[1],
            webhook_url=row[2],
            payload=json.loads(row[3]),
            status=WebhookStatus(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            sent_at=datetime.fromisoformat(row[6]) if row[6] else None,
            delivered_at=datetime.fromisoformat(row[7]) if row[7] else None,
            failed_at=datetime.fromisoformat(row[8]) if row[8] else None,
            retry_count=row[9],
            max_retries=row[10],
            next_retry_at=datetime.fromisoformat(row[11]) if row[11] else None,
            error_message=row[12],
            response_code=row[13],
            response_body=row[14]
        )
    
    def _row_to_task_monitoring(self, row) -> TaskMonitoring:
        """Convertir fila de DB a TaskMonitoring"""
        return TaskMonitoring(
            task_id=row[0],
            agent_id=row[1],
            status=TaskStatus(row[2]),
            created_at=datetime.fromisoformat(row[3]),
            assigned_at=datetime.fromisoformat(row[4]) if row[4] else None,
            started_at=datetime.fromisoformat(row[5]) if row[5] else None,
            completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
            last_heartbeat=datetime.fromisoformat(row[7]) if row[7] else None,
            monitoring_level=MonitoringLevel(row[8]),
            timeout_seconds=row[9],
            heartbeat_interval=row[10],
            metadata=json.loads(row[11])
        )
    
    def _execute_callbacks(self, event_type: str, task_id: str, data: Any):
        """Ejecutar callbacks registrados"""
        for callback in self.event_callbacks.get(event_type, []):
            try:
                callback(task_id, data)
            except Exception as e:
                logger.error(f"Error executing callback for {event_type}: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """Registrar callback para evento"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            logger.info(f"Callback registered for {event_type}")
    
    def get_webhook_status(self, webhook_id: str) -> Optional[WebhookEvent]:
        """Obtener estado de webhook"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM webhook_events WHERE id = ?', (webhook_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_webhook_event(row)
        return None
    
    def get_task_status(self, task_id: str) -> Optional[TaskMonitoring]:
        """Obtener estado de tarea"""
        return self._get_task_monitoring(task_id)
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de monitoreo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estadísticas de webhooks
        cursor.execute('SELECT status, COUNT(*) FROM webhook_events GROUP BY status')
        webhook_stats = dict(cursor.fetchall())
        
        # Estadísticas de tareas
        cursor.execute('SELECT status, COUNT(*) FROM task_monitoring GROUP BY status')
        task_stats = dict(cursor.fetchall())
        
        # Eventos recientes
        cursor.execute('''
            SELECT event_type, COUNT(*) FROM monitoring_events 
            WHERE timestamp >= datetime('now', '-1 hour')
            GROUP BY event_type
        ''')
        recent_events = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "webhook_stats": webhook_stats,
            "task_stats": task_stats,
            "recent_events": recent_events,
            "monitoring_active": self.monitoring_active,
            "worker_count": len(self.webhook_workers)
        }

# Flask API para monitoreo
app = Flask(__name__)
CORS(app)

# Instancia global del monitor
monitor = None

def init_monitoring_system(config: Dict[str, Any] = None):
    """Inicializar sistema de monitoreo"""
    global monitor
    
    if monitor is None:
        monitor = ActiveWebhookMonitor(config)

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/webhook/register', methods=['POST'])
def register_webhook():
    """Registrar webhook para monitoreo"""
    data = request.json
    
    webhook_id = monitor.register_webhook(
        task_id=data['task_id'],
        webhook_url=data['webhook_url'],
        payload=data['payload'],
        max_retries=data.get('max_retries', 5)
    )
    
    return jsonify({"webhook_id": webhook_id, "status": "registered"})

@app.route('/api/task/register', methods=['POST'])
def register_task():
    """Registrar tarea para monitoreo"""
    data = request.json
    
    success = monitor.register_task_monitoring(
        task_id=data['task_id'],
        agent_id=data['agent_id'],
        monitoring_level=MonitoringLevel(data.get('monitoring_level', 'standard')),
        timeout_seconds=data.get('timeout_seconds', 3600)
    )
    
    return jsonify({"status": "registered" if success else "failed"})

@app.route('/api/task/<task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Actualizar estado de tarea"""
    data = request.json
    
    monitor.update_task_status(
        task_id=task_id,
        status=TaskStatus(data['status']),
        metadata=data.get('metadata')
    )
    
    return jsonify({"status": "updated"})

@app.route('/api/task/<task_id>/heartbeat', methods=['POST'])
def send_heartbeat(task_id):
    """Enviar heartbeat de tarea"""
    data = request.json
    
    monitor.send_heartbeat(task_id, data.get('metadata'))
    
    return jsonify({"status": "heartbeat_received"})

@app.route('/api/webhook/<webhook_id>/status')
def get_webhook_status(webhook_id):
    """Obtener estado de webhook"""
    webhook_event = monitor.get_webhook_status(webhook_id)
    
    if webhook_event:
        return jsonify(asdict(webhook_event))
    else:
        return jsonify({"error": "Webhook not found"}), 404

@app.route('/api/task/<task_id>/status')
def get_task_status(task_id):
    """Obtener estado de tarea"""
    task_monitoring = monitor.get_task_status(task_id)
    
    if task_monitoring:
        return jsonify(asdict(task_monitoring))
    else:
        return jsonify({"error": "Task not found"}), 404

@app.route('/api/monitoring/stats')
def get_monitoring_stats():
    """Obtener estadísticas de monitoreo"""
    return jsonify(monitor.get_monitoring_stats())

def main():
    """Función principal"""
    print("🔍 Iniciando Sistema de Monitoreo Activo Post-Webhook...")
    
    # Configuración
    config = {
        "db_path": "webhook_monitor.db",
        "webhook_secret": "mcp_webhook_secret_2024"
    }
    
    # Inicializar sistema
    init_monitoring_system(config)
    
    print("✅ Sistema de monitoreo activo iniciado")
    print("🌐 API disponible en: http://localhost:8125")
    print("📊 Endpoints disponibles:")
    print("   POST /api/webhook/register - Registrar webhook")
    print("   POST /api/task/register - Registrar tarea")
    print("   PUT /api/task/<id>/status - Actualizar estado")
    print("   POST /api/task/<id>/heartbeat - Enviar heartbeat")
    print("   GET /api/webhook/<id>/status - Estado webhook")
    print("   GET /api/task/<id>/status - Estado tarea")
    print("   GET /api/monitoring/stats - Estadísticas")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=8125, debug=False)

if __name__ == "__main__":
    main()

