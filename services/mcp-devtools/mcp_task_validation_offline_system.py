#!/usr/bin/env python3
"""
MCP Enterprise - Sistema de Validación Cruzada y Persistencia Offline
Sistema completo de validación de task_id y manejo de persistencia offline
"""

import json
import sqlite3
import time
import hashlib
import uuid
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskValidationStatus(Enum):
    """Estados de validación de tarea"""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    DUPLICATE = "duplicate"
    EXPIRED = "expired"
    UNKNOWN = "unknown"

class OfflineMode(Enum):
    """Modos de operación offline"""
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    RECOVERY = "recovery"

@dataclass
class TaskValidationResult:
    """Resultado de validación de tarea"""
    task_id: str
    status: TaskValidationStatus
    exists_in_manus: bool
    exists_locally: bool
    validation_timestamp: datetime
    manus_response_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class OfflineTask:
    """Tarea almacenada offline"""
    task_id: str
    agent_id: str
    task_data: Dict[str, Any]
    created_at: datetime
    priority: int = 5  # 1-10, 1 = más alta
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    sync_status: str = "pending"  # pending, syncing, synced, failed
    error_message: Optional[str] = None

class TaskValidationSystem:
    """Sistema de validación cruzada de task_id"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.db_path = self.config.get("db_path", "task_validation.db")
        self.manus_base_url = self.config.get("manus_base_url", "http://localhost:3000")
        self.validation_timeout = self.config.get("validation_timeout", 5.0)
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutos
        
        # Estado del sistema
        self.offline_mode = OfflineMode.ONLINE
        self.last_manus_contact = datetime.now()
        self.connectivity_check_interval = 30  # segundos
        
        # Cache de validaciones
        self.validation_cache = {}
        self.cache_lock = threading.Lock()
        
        # Inicializar base de datos
        self._init_database()
        
        # Iniciar monitor de conectividad
        self._start_connectivity_monitor()
    
    def _init_database(self):
        """Inicializar base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de validaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_validations (
                task_id TEXT PRIMARY KEY,
                status TEXT,
                exists_in_manus BOOLEAN,
                exists_locally BOOLEAN,
                validation_timestamp TEXT,
                manus_response_time REAL,
                error_message TEXT,
                metadata TEXT
            )
        ''')
        
        # Tabla de tareas offline
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_tasks (
                task_id TEXT PRIMARY KEY,
                agent_id TEXT,
                task_data TEXT,
                created_at TEXT,
                priority INTEGER,
                retry_count INTEGER,
                max_retries INTEGER,
                next_retry_at TEXT,
                sync_status TEXT,
                error_message TEXT
            )
        ''')
        
        # Tabla de estado del sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        # Tabla de logs de conectividad
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connectivity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                offline_mode TEXT,
                manus_reachable BOOLEAN,
                response_time REAL,
                error_message TEXT
            )
        ''')
        
        # Índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_validations_timestamp ON task_validations(validation_timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offline_tasks_priority ON offline_tasks(priority, created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_connectivity_logs_timestamp ON connectivity_logs(timestamp)')
        
        conn.commit()
        conn.close()
    
    def _start_connectivity_monitor(self):
        """Iniciar monitor de conectividad"""
        def connectivity_monitor():
            while True:
                try:
                    self._check_manus_connectivity()
                    time.sleep(self.connectivity_check_interval)
                except Exception as e:
                    logger.error(f"Error in connectivity monitor: {e}")
                    time.sleep(60)  # Esperar más tiempo si hay error
        
        monitor_thread = threading.Thread(target=connectivity_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logger.info("Connectivity monitor started")
    
    def _check_manus_connectivity(self):
        """Verificar conectividad con Manus"""
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.manus_base_url}/health",
                timeout=self.validation_timeout
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Manus está disponible
                old_mode = self.offline_mode
                self.offline_mode = OfflineMode.ONLINE
                self.last_manus_contact = datetime.now()
                
                # Log cambio de estado
                self._log_connectivity(True, response_time)
                
                # Si estábamos offline, iniciar recuperación
                if old_mode in [OfflineMode.OFFLINE, OfflineMode.DEGRADED]:
                    self.offline_mode = OfflineMode.RECOVERY
                    self._start_offline_sync()
                    logger.info("Manus connectivity restored, starting recovery")
                
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            # Manus no está disponible
            self._log_connectivity(False, None, str(e))
            
            # Determinar modo offline
            time_since_contact = datetime.now() - self.last_manus_contact
            
            if time_since_contact.total_seconds() > 300:  # 5 minutos
                if self.offline_mode != OfflineMode.OFFLINE:
                    logger.warning("Switching to offline mode")
                self.offline_mode = OfflineMode.OFFLINE
            elif time_since_contact.total_seconds() > 60:  # 1 minuto
                if self.offline_mode != OfflineMode.DEGRADED:
                    logger.warning("Switching to degraded mode")
                self.offline_mode = OfflineMode.DEGRADED
    
    def _log_connectivity(self, reachable: bool, response_time: Optional[float], 
                         error_message: Optional[str] = None):
        """Registrar log de conectividad"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO connectivity_logs 
            (timestamp, offline_mode, manus_reachable, response_time, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            self.offline_mode.value,
            reachable,
            response_time,
            error_message
        ))
        
        conn.commit()
        conn.close()
    
    def validate_task_id(self, task_id: str, agent_id: str = None) -> TaskValidationResult:
        """Validar task_id con verificación cruzada"""
        
        # Verificar cache primero
        with self.cache_lock:
            if task_id in self.validation_cache:
                cached_result, cached_time = self.validation_cache[task_id]
                if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                    logger.debug(f"Task validation cache hit: {task_id}")
                    return cached_result
        
        # Verificar existencia local
        exists_locally = self._check_task_exists_locally(task_id)
        
        # Verificar existencia en Manus (si está online)
        exists_in_manus = False
        manus_response_time = None
        error_message = None
        
        if self.offline_mode == OfflineMode.ONLINE:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{self.manus_base_url}/api/tasks/{task_id}/exists",
                    timeout=self.validation_timeout
                )
                manus_response_time = time.time() - start_time
                
                if response.status_code == 200:
                    exists_in_manus = response.json().get("exists", False)
                elif response.status_code == 404:
                    exists_in_manus = False
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                error_message = str(e)
                logger.warning(f"Failed to validate task_id with Manus: {e}")
                
                # Cambiar a modo degradado si hay errores repetidos
                if self.offline_mode == OfflineMode.ONLINE:
                    self.offline_mode = OfflineMode.DEGRADED
        
        # Determinar estado de validación
        status = self._determine_validation_status(
            exists_locally, exists_in_manus, error_message
        )
        
        # Crear resultado
        result = TaskValidationResult(
            task_id=task_id,
            status=status,
            exists_in_manus=exists_in_manus,
            exists_locally=exists_locally,
            validation_timestamp=datetime.now(),
            manus_response_time=manus_response_time,
            error_message=error_message,
            metadata={"agent_id": agent_id, "offline_mode": self.offline_mode.value}
        )
        
        # Guardar en base de datos
        self._save_validation_result(result)
        
        # Actualizar cache
        with self.cache_lock:
            self.validation_cache[task_id] = (result, datetime.now())
        
        logger.info(f"Task validation completed: {task_id} -> {status.value}")
        return result
    
    def _check_task_exists_locally(self, task_id: str) -> bool:
        """Verificar si la tarea existe localmente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar en validaciones previas
        cursor.execute(
            'SELECT COUNT(*) FROM task_validations WHERE task_id = ? AND exists_locally = 1',
            (task_id,)
        )
        local_validations = cursor.fetchone()[0]
        
        # Verificar en tareas offline
        cursor.execute(
            'SELECT COUNT(*) FROM offline_tasks WHERE task_id = ?',
            (task_id,)
        )
        offline_tasks = cursor.fetchone()[0]
        
        conn.close()
        
        return local_validations > 0 or offline_tasks > 0
    
    def _determine_validation_status(self, exists_locally: bool, 
                                   exists_in_manus: bool, 
                                   error_message: Optional[str]) -> TaskValidationStatus:
        """Determinar estado de validación"""
        
        if error_message and self.offline_mode == OfflineMode.OFFLINE:
            # En modo offline, confiar en datos locales
            return TaskValidationStatus.VALID if exists_locally else TaskValidationStatus.UNKNOWN
        
        if error_message:
            return TaskValidationStatus.UNKNOWN
        
        if exists_locally and exists_in_manus:
            return TaskValidationStatus.DUPLICATE
        
        if exists_in_manus:
            return TaskValidationStatus.VALID
        
        if exists_locally and self.offline_mode != OfflineMode.ONLINE:
            # En modo degradado/offline, aceptar tareas locales
            return TaskValidationStatus.VALID
        
        return TaskValidationStatus.INVALID
    
    def _save_validation_result(self, result: TaskValidationResult):
        """Guardar resultado de validación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_validations 
            (task_id, status, exists_in_manus, exists_locally, validation_timestamp, 
             manus_response_time, error_message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.task_id,
            result.status.value,
            result.exists_in_manus,
            result.exists_locally,
            result.validation_timestamp.isoformat(),
            result.manus_response_time,
            result.error_message,
            json.dumps(result.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def store_task_offline(self, task_id: str, agent_id: str, 
                          task_data: Dict[str, Any], priority: int = 5) -> bool:
        """Almacenar tarea para procesamiento offline"""
        
        offline_task = OfflineTask(
            task_id=task_id,
            agent_id=agent_id,
            task_data=task_data,
            created_at=datetime.now(),
            priority=priority
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO offline_tasks 
            (task_id, agent_id, task_data, created_at, priority, retry_count, 
             max_retries, next_retry_at, sync_status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            offline_task.task_id,
            offline_task.agent_id,
            json.dumps(offline_task.task_data),
            offline_task.created_at.isoformat(),
            offline_task.priority,
            offline_task.retry_count,
            offline_task.max_retries,
            offline_task.next_retry_at.isoformat() if offline_task.next_retry_at else None,
            offline_task.sync_status,
            offline_task.error_message
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Task stored offline: {task_id}")
        return True
    
    def _start_offline_sync(self):
        """Iniciar sincronización de tareas offline"""
        def sync_worker():
            try:
                self._sync_offline_tasks()
            except Exception as e:
                logger.error(f"Error in offline sync: {e}")
        
        sync_thread = threading.Thread(target=sync_worker)
        sync_thread.daemon = True
        sync_thread.start()
    
    def _sync_offline_tasks(self):
        """Sincronizar tareas offline con Manus"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener tareas pendientes de sincronización
        cursor.execute('''
            SELECT * FROM offline_tasks 
            WHERE sync_status IN ('pending', 'failed') 
            AND (next_retry_at IS NULL OR next_retry_at <= ?)
            ORDER BY priority ASC, created_at ASC
            LIMIT 10
        ''', (datetime.now().isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            offline_task = self._row_to_offline_task(row)
            
            try:
                # Intentar sincronizar con Manus
                self._sync_single_task(offline_task)
                
            except Exception as e:
                logger.error(f"Failed to sync task {offline_task.task_id}: {e}")
                
                # Actualizar contador de reintentos
                offline_task.retry_count += 1
                offline_task.error_message = str(e)
                
                if offline_task.retry_count >= offline_task.max_retries:
                    offline_task.sync_status = "failed"
                else:
                    # Programar reintento con backoff exponencial
                    delay_seconds = min(300, 30 * (2 ** offline_task.retry_count))
                    offline_task.next_retry_at = datetime.now() + timedelta(seconds=delay_seconds)
                    offline_task.sync_status = "pending"
                
                self._update_offline_task(offline_task)
    
    def _sync_single_task(self, offline_task: OfflineTask):
        """Sincronizar una tarea individual"""
        
        # Marcar como sincronizando
        offline_task.sync_status = "syncing"
        self._update_offline_task(offline_task)
        
        # Enviar a Manus
        response = requests.post(
            f"{self.manus_base_url}/api/tasks/sync",
            json={
                "task_id": offline_task.task_id,
                "agent_id": offline_task.agent_id,
                "task_data": offline_task.task_data,
                "created_at": offline_task.created_at.isoformat(),
                "priority": offline_task.priority
            },
            timeout=30
        )
        
        if response.status_code == 200:
            # Sincronización exitosa
            offline_task.sync_status = "synced"
            offline_task.error_message = None
            self._update_offline_task(offline_task)
            
            logger.info(f"Task synced successfully: {offline_task.task_id}")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
    
    def _update_offline_task(self, offline_task: OfflineTask):
        """Actualizar tarea offline"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE offline_tasks 
            SET retry_count = ?, next_retry_at = ?, sync_status = ?, error_message = ?
            WHERE task_id = ?
        ''', (
            offline_task.retry_count,
            offline_task.next_retry_at.isoformat() if offline_task.next_retry_at else None,
            offline_task.sync_status,
            offline_task.error_message,
            offline_task.task_id
        ))
        
        conn.commit()
        conn.close()
    
    def _row_to_offline_task(self, row) -> OfflineTask:
        """Convertir fila de DB a OfflineTask"""
        return OfflineTask(
            task_id=row[0],
            agent_id=row[1],
            task_data=json.loads(row[2]),
            created_at=datetime.fromisoformat(row[3]),
            priority=row[4],
            retry_count=row[5],
            max_retries=row[6],
            next_retry_at=datetime.fromisoformat(row[7]) if row[7] else None,
            sync_status=row[8],
            error_message=row[9]
        )
    
    def get_offline_tasks(self, status: str = None, limit: int = 100) -> List[OfflineTask]:
        """Obtener tareas offline"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM offline_tasks"
        params = []
        
        if status:
            query += " WHERE sync_status = ?"
            params.append(status)
        
        query += " ORDER BY priority ASC, created_at ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_offline_task(row) for row in rows]
    
    def get_validation_history(self, task_id: str = None, limit: int = 100) -> List[TaskValidationResult]:
        """Obtener historial de validaciones"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM task_validations"
        params = []
        
        if task_id:
            query += " WHERE task_id = ?"
            params.append(task_id)
        
        query += " ORDER BY validation_timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir a objetos
        results = []
        for row in rows:
            result = TaskValidationResult(
                task_id=row[0],
                status=TaskValidationStatus(row[1]),
                exists_in_manus=bool(row[2]),
                exists_locally=bool(row[3]),
                validation_timestamp=datetime.fromisoformat(row[4]),
                manus_response_time=row[5],
                error_message=row[6],
                metadata=json.loads(row[7]) if row[7] else {}
            )
            results.append(result)
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estadísticas de validaciones
        cursor.execute('SELECT status, COUNT(*) FROM task_validations GROUP BY status')
        validation_stats = dict(cursor.fetchall())
        
        # Estadísticas de tareas offline
        cursor.execute('SELECT sync_status, COUNT(*) FROM offline_tasks GROUP BY sync_status')
        offline_stats = dict(cursor.fetchall())
        
        # Conectividad reciente
        cursor.execute('''
            SELECT manus_reachable, AVG(response_time) FROM connectivity_logs 
            WHERE timestamp >= datetime('now', '-1 hour')
            GROUP BY manus_reachable
        ''')
        connectivity_stats = {}
        for row in cursor.fetchall():
            connectivity_stats[f"reachable_{row[0]}"] = row[1]
        
        conn.close()
        
        return {
            "offline_mode": self.offline_mode.value,
            "last_manus_contact": self.last_manus_contact.isoformat(),
            "validation_stats": validation_stats,
            "offline_stats": offline_stats,
            "connectivity_stats": connectivity_stats,
            "cache_size": len(self.validation_cache),
            "timestamp": datetime.now().isoformat()
        }

# Flask API
app = Flask(__name__)
CORS(app)

# Instancia global del sistema
validation_system = None

def init_validation_system(config: Dict[str, Any] = None):
    """Inicializar sistema de validación"""
    global validation_system
    
    if validation_system is None:
        validation_system = TaskValidationSystem(config)

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/validate/<task_id>', methods=['GET'])
def validate_task(task_id):
    """Validar task_id"""
    agent_id = request.args.get('agent_id')
    
    result = validation_system.validate_task_id(task_id, agent_id)
    
    return jsonify(asdict(result))

@app.route('/api/tasks/offline', methods=['POST'])
def store_task_offline():
    """Almacenar tarea offline"""
    data = request.json
    
    success = validation_system.store_task_offline(
        task_id=data['task_id'],
        agent_id=data['agent_id'],
        task_data=data['task_data'],
        priority=data.get('priority', 5)
    )
    
    return jsonify({"status": "stored" if success else "failed"})

@app.route('/api/tasks/offline', methods=['GET'])
def get_offline_tasks():
    """Obtener tareas offline"""
    status = request.args.get('status')
    limit = int(request.args.get('limit', 100))
    
    tasks = validation_system.get_offline_tasks(status, limit)
    
    return jsonify([asdict(task) for task in tasks])

@app.route('/api/validations', methods=['GET'])
def get_validation_history():
    """Obtener historial de validaciones"""
    task_id = request.args.get('task_id')
    limit = int(request.args.get('limit', 100))
    
    history = validation_system.get_validation_history(task_id, limit)
    
    return jsonify([asdict(result) for result in history])

@app.route('/api/system/status')
def get_system_status():
    """Obtener estado del sistema"""
    return jsonify(validation_system.get_system_status())

@app.route('/api/system/mode', methods=['POST'])
def set_offline_mode():
    """Cambiar modo offline manualmente"""
    data = request.json
    mode = data.get('mode')
    
    if mode in [m.value for m in OfflineMode]:
        validation_system.offline_mode = OfflineMode(mode)
        return jsonify({"status": "updated", "mode": mode})
    else:
        return jsonify({"error": "Invalid mode"}), 400

def main():
    """Función principal"""
    print("🔍 Iniciando Sistema de Validación Cruzada y Persistencia Offline...")
    
    # Configuración
    config = {
        "db_path": "task_validation.db",
        "manus_base_url": "http://localhost:3000",
        "validation_timeout": 5.0,
        "cache_ttl": 300
    }
    
    # Inicializar sistema
    init_validation_system(config)
    
    print("✅ Sistema de validación iniciado")
    print("🌐 API disponible en: http://localhost:8127")
    print("📊 Endpoints disponibles:")
    print("   GET  /api/validate/<task_id> - Validar task_id")
    print("   POST /api/tasks/offline - Almacenar tarea offline")
    print("   GET  /api/tasks/offline - Obtener tareas offline")
    print("   GET  /api/validations - Historial de validaciones")
    print("   GET  /api/system/status - Estado del sistema")
    print("   POST /api/system/mode - Cambiar modo offline")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=8127, debug=False)

if __name__ == "__main__":
    main()

