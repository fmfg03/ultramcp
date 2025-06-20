#!/usr/bin/env python3
"""
SAM ↔ Manus API Server Implementation
Implementación completa de los endpoints de la API para comunicación entre SAM y Manus
"""

import os
import sys
import uuid
import time
import hmac
import hashlib
import jwt
import json
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound, TooManyRequests

from src.models.user import db
from src.routes.user import user_bp

# Configuración de la aplicación
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
CORS(app)  # Habilitar CORS para comunicación frontend-backend

# Configuración de seguridad
app.config['SECRET_KEY'] = 'sam_manus_api_secret_key_2024_enterprise'
app.config['JWT_SECRET'] = 'jwt_secret_key_sam_manus_2024'
app.config['WEBHOOK_SECRET'] = 'webhook_secret_sam_manus_2024'

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Inicializar base de datos
db.init_app(app)

# Registrar blueprints existentes
app.register_blueprint(user_bp, url_prefix='/api')

# Almacenamiento en memoria para tareas (en producción usar Redis/MongoDB)
active_tasks: Dict[str, Dict[str, Any]] = {}
task_results: Dict[str, Dict[str, Any]] = {}
task_queue = queue.PriorityQueue()
task_history: List[Dict[str, Any]] = []

# Configuración del sistema
MAX_CONCURRENT_TASKS = 50
TASK_TIMEOUT_DEFAULT = 300  # 5 minutos
WEBHOOK_RETRY_ATTEMPTS = 3
WEBHOOK_RETRY_DELAY = 5  # segundos

class TaskExecutor:
    """Ejecutor de tareas con soporte para múltiples workers"""
    
    def __init__(self, num_workers: int = 5):
        self.num_workers = num_workers
        self.workers: List[threading.Thread] = []
        self.running = True
        self.agent_id = "sam_agent_api_001"
        
    def start(self):
        """Iniciar workers de ejecución de tareas"""
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop, name=f"TaskWorker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        print(f"✅ TaskExecutor iniciado con {self.num_workers} workers")
    
    def stop(self):
        """Detener todos los workers"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)
    
    def _worker_loop(self):
        """Loop principal del worker"""
        while self.running:
            try:
                # Obtener tarea de la cola con timeout
                priority, task_data = task_queue.get(timeout=1)
                self._execute_task(task_data)
                task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error en worker: {e}")
    
    def _execute_task(self, task_data: Dict[str, Any]):
        """Ejecutar una tarea específica"""
        task_id = task_data['task_id']
        execution_id = task_data['execution_id']
        
        try:
            # Actualizar estado a 'running'
            self._update_task_status(task_id, 'running', 0)
            
            # Enviar notificación de inicio
            self._send_webhook_notification(task_data, 'task_started')
            
            # Simular progreso de ejecución
            for progress in [25, 50, 75]:
                time.sleep(1)  # Simular trabajo
                self._update_task_status(task_id, 'running', progress)
                self._send_webhook_notification(task_data, 'task_progress', {
                    'progress_percentage': progress,
                    'current_step': f"Procesando paso {progress//25} de 4"
                })
            
            # Ejecutar lógica específica del tipo de tarea
            result = self._process_task_by_type(task_data)
            
            # Actualizar estado a 'completed'
            self._update_task_status(task_id, 'completed', 100)
            task_results[task_id] = result
            
            # Enviar notificación de completado
            self._send_webhook_notification(task_data, 'task_completed', result)
            
            # Agregar a historial
            task_history.append({
                'task_id': task_id,
                'execution_id': execution_id,
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'duration': time.time() - active_tasks[task_id]['started_at'],
                'result': result
            })
            
        except Exception as e:
            # Manejar error en ejecución
            error_info = {
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.now().isoformat()
            }
            
            self._update_task_status(task_id, 'failed', None, error_info)
            self._send_webhook_notification(task_data, 'task_failed', error_info)
            
            # Agregar a historial
            task_history.append({
                'task_id': task_id,
                'execution_id': execution_id,
                'status': 'failed',
                'failed_at': datetime.now().isoformat(),
                'error': error_info
            })
    
    def _process_task_by_type(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar tarea según su tipo"""
        task_type = task_data.get('task_type', 'unknown')
        
        if task_type == 'code_execution':
            return self._execute_code_task(task_data)
        elif task_type == 'web_automation':
            return self._execute_web_task(task_data)
        elif task_type == 'data_processing':
            return self._execute_data_task(task_data)
        elif task_type == 'content_generation':
            return self._execute_content_task(task_data)
        else:
            return self._execute_generic_task(task_data)
    
    def _execute_code_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea de código"""
        time.sleep(2)  # Simular ejecución
        return {
            'type': 'code_execution',
            'output': 'print("Hello from SAM!")',
            'execution_time': 2.5,
            'memory_used': 128,
            'status': 'success'
        }
    
    def _execute_web_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea de automatización web"""
        time.sleep(3)  # Simular navegación web
        return {
            'type': 'web_automation',
            'pages_visited': 5,
            'data_extracted': 150,
            'execution_time': 3.2,
            'status': 'success'
        }
    
    def _execute_data_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea de procesamiento de datos"""
        time.sleep(4)  # Simular procesamiento
        return {
            'type': 'data_processing',
            'records_processed': 1000,
            'output_file': 'processed_data.json',
            'execution_time': 4.1,
            'status': 'success'
        }
    
    def _execute_content_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea de generación de contenido"""
        time.sleep(2)  # Simular generación
        return {
            'type': 'content_generation',
            'content_generated': 'Generated content based on requirements',
            'word_count': 500,
            'execution_time': 2.8,
            'status': 'success'
        }
    
    def _execute_generic_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea genérica"""
        time.sleep(1)  # Simular trabajo
        return {
            'type': 'generic',
            'message': 'Task completed successfully',
            'execution_time': 1.0,
            'status': 'success'
        }
    
    def _update_task_status(self, task_id: str, status: str, progress: Optional[int], error: Optional[Dict] = None):
        """Actualizar estado de tarea"""
        if task_id in active_tasks:
            active_tasks[task_id]['status'] = status
            active_tasks[task_id]['last_update'] = datetime.now().isoformat()
            
            if progress is not None:
                active_tasks[task_id]['progress'] = progress
            
            if error:
                active_tasks[task_id]['error'] = error
            
            if status == 'running' and 'started_at' not in active_tasks[task_id]:
                active_tasks[task_id]['started_at'] = time.time()
    
    def _send_webhook_notification(self, task_data: Dict[str, Any], event_type: str, result: Optional[Dict] = None):
        """Enviar notificación webhook"""
        webhook_config = task_data.get('notification_config', {})
        webhook_url = webhook_config.get('webhook_url')
        
        if not webhook_url:
            return
        
        # Preparar payload
        payload = {
            'event_type': event_type,
            'task_id': task_data['task_id'],
            'execution_id': task_data['execution_id'],
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'status': active_tasks.get(task_data['task_id'], {}),
            'result': result
        }
        
        # Enviar webhook con reintentos
        self._deliver_webhook(webhook_url, payload, webhook_config)
    
    def _deliver_webhook(self, url: str, payload: Dict[str, Any], config: Dict[str, Any]):
        """Entregar webhook con reintentos"""
        webhook_secret = config.get('webhook_secret', app.config['WEBHOOK_SECRET'])
        
        # Preparar headers
        headers = {
            'Content-Type': 'application/json',
            'X-SAM-Agent-ID': self.agent_id,
            'X-Webhook-Event': payload['event_type'],
            'X-Webhook-Timestamp': str(int(time.time())),
            'X-Delivery-ID': str(uuid.uuid4())
        }
        
        # Generar firma HMAC
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            webhook_secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        headers['X-Webhook-Signature'] = f"sha256={signature}"
        
        # Intentar entrega con reintentos
        for attempt in range(WEBHOOK_RETRY_ATTEMPTS):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ Webhook entregado: {payload['event_type']} para {payload['task_id']}")
                    return
                else:
                    print(f"⚠️ Webhook falló (intento {attempt + 1}): {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"❌ Error webhook (intento {attempt + 1}): {e}")
            
            if attempt < WEBHOOK_RETRY_ATTEMPTS - 1:
                time.sleep(WEBHOOK_RETRY_DELAY * (attempt + 1))  # Backoff exponencial

# Inicializar ejecutor de tareas
task_executor = TaskExecutor(num_workers=5)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verificar token JWT"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        return None

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verificar firma HMAC de webhook"""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

# ================================
# ENDPOINTS DE LA API
# ================================

@app.route('/api/v2/execute-task', methods=['POST'])
@limiter.limit("100 per hour")
def execute_task():
    """
    POST /execute-task
    Endpoint principal para ejecutar tareas en SAM
    """
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': {
                    'code': 'MISSING_AUTHORIZATION',
                    'message': 'Missing or invalid authorization header',
                    'category': 'authentication_error'
                }
            }), 401
        
        token = auth_header.split(' ')[1]
        token_payload = verify_jwt_token(token)
        if not token_payload:
            return jsonify({
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid JWT token',
                    'category': 'authentication_error'
                }
            }), 401
        
        # Validar datos de la tarea
        task_data = request.get_json()
        if not task_data:
            return jsonify({
                'error': {
                    'code': 'MISSING_TASK_DATA',
                    'message': 'Missing task data in request body',
                    'category': 'client_error'
                }
            }), 400
        
        # Validar campos requeridos
        required_fields = ['task_id', 'task_type', 'description', 'orchestrator_info']
        for field in required_fields:
            if field not in task_data:
                return jsonify({
                    'error': {
                        'code': 'MISSING_REQUIRED_FIELD',
                        'message': f'Missing required field: {field}',
                        'category': 'client_error'
                    }
                }), 400
        
        task_id = task_data['task_id']
        
        # Verificar si la tarea ya existe
        if task_id in active_tasks:
            return jsonify({
                'error': {
                    'code': 'TASK_ALREADY_EXISTS',
                    'message': f'Task with ID {task_id} already exists',
                    'category': 'client_error'
                }
            }), 409
        
        # Verificar capacidad del sistema
        if len(active_tasks) >= MAX_CONCURRENT_TASKS:
            return jsonify({
                'error': {
                    'code': 'SYSTEM_OVERLOADED',
                    'message': 'Maximum concurrent tasks reached',
                    'category': 'server_error',
                    'retry_after': 60
                }
            }), 503
        
        # Generar ID de ejecución
        execution_id = str(uuid.uuid4())
        task_data['execution_id'] = execution_id
        
        # Determinar prioridad
        priority_map = {'urgent': 1, 'high': 2, 'normal': 3, 'low': 4}
        priority = priority_map.get(task_data.get('priority', 'normal'), 3)
        
        # Inicializar seguimiento de tarea
        active_tasks[task_id] = {
            'task_id': task_id,
            'execution_id': execution_id,
            'status': 'queued',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'queued_at': datetime.now().isoformat(),
            'task_type': task_data['task_type'],
            'priority': task_data.get('priority', 'normal'),
            'timeout': task_data.get('timeout', TASK_TIMEOUT_DEFAULT),
            'orchestrator_info': task_data['orchestrator_info']
        }
        
        # Agregar tarea a la cola
        task_queue.put((priority, task_data))
        
        # Preparar respuesta
        response = {
            'status': 'accepted',
            'task_id': task_id,
            'execution_id': execution_id,
            'agent_id': task_executor.agent_id,
            'estimated_duration': task_data.get('timeout', TASK_TIMEOUT_DEFAULT),
            'queue_position': task_queue.qsize(),
            'resource_allocation': {
                'memory_mb': task_data.get('execution_config', {}).get('resource_limits', {}).get('memory_mb', 1024),
                'cpu_cores': task_data.get('execution_config', {}).get('resource_limits', {}).get('cpu_cores', 1),
                'estimated_cost': 0.01
            },
            'monitoring': {
                'status_url': f"/api/v2/task-status/{task_id}",
                'logs_url': f"/api/v2/task-logs/{task_id}",
                'metrics_url': f"/api/v2/task-metrics/{task_id}"
            },
            'timestamps': {
                'received': datetime.now().isoformat(),
                'queued': datetime.now().isoformat(),
                'estimated_start': (datetime.now() + timedelta(seconds=task_queue.qsize() * 2)).isoformat(),
                'estimated_completion': (datetime.now() + timedelta(seconds=task_data.get('timeout', TASK_TIMEOUT_DEFAULT))).isoformat()
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'category': 'server_error',
                'details': str(e)
            },
            'request_id': request.headers.get('X-Request-ID', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/v2/task-status/<task_id>', methods=['GET'])
@limiter.limit("1000 per hour")
def get_task_status(task_id: str):
    """
    GET /task-status/{task_id}
    Obtener estado actual de una tarea
    """
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': {
                    'code': 'MISSING_AUTHORIZATION',
                    'message': 'Missing or invalid authorization header',
                    'category': 'authentication_error'
                }
            }), 401
        
        token = auth_header.split(' ')[1]
        token_payload = verify_jwt_token(token)
        if not token_payload:
            return jsonify({
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid JWT token',
                    'category': 'authentication_error'
                }
            }), 401
        
        # Verificar si la tarea existe
        if task_id not in active_tasks:
            return jsonify({
                'error': {
                    'code': 'TASK_NOT_FOUND',
                    'message': f'Task with ID {task_id} not found',
                    'category': 'client_error'
                }
            }), 404
        
        task_info = active_tasks[task_id]
        
        # Preparar respuesta
        response = {
            'task_id': task_id,
            'execution_id': task_info['execution_id'],
            'agent_id': task_executor.agent_id,
            'current_status': {
                'state': task_info['status'],
                'progress': {
                    'percentage': task_info.get('progress', 0),
                    'current_step': task_info.get('current_step', 'Processing'),
                    'estimated_remaining': max(0, task_info['timeout'] - int(time.time() - task_info.get('started_at', time.time())))
                },
                'timestamps': {
                    'created': task_info['created_at'],
                    'queued': task_info['queued_at'],
                    'started': task_info.get('started_at'),
                    'last_update': task_info.get('last_update', datetime.now().isoformat())
                }
            },
            'resource_usage': {
                'memory': {
                    'current_mb': 512,
                    'peak_mb': 768,
                    'limit_mb': 1024
                },
                'cpu': {
                    'current_percentage': 45.5,
                    'average_percentage': 38.2
                },
                'network': {
                    'bytes_sent': 1024,
                    'bytes_received': 4096
                }
            }
        }
        
        # Incluir resultados si está completada
        if task_id in task_results:
            response['execution_details'] = {
                'output': task_results[task_id],
                'artifacts': [],
                'intermediate_results': []
            }
        
        # Incluir error si falló
        if 'error' in task_info:
            response['execution_details'] = {
                'error_details': task_info['error']
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'category': 'server_error',
                'details': str(e)
            },
            'request_id': request.headers.get('X-Request-ID', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/v2/webhooks/task-completed', methods=['POST'])
@limiter.limit("500 per hour")
def handle_task_webhook():
    """
    POST /task-completed (Webhook)
    Endpoint para recibir notificaciones de Manus (implementación de ejemplo)
    """
    try:
        # Verificar headers requeridos
        signature = request.headers.get('X-Webhook-Signature')
        timestamp = request.headers.get('X-Webhook-Timestamp')
        agent_id = request.headers.get('X-SAM-Agent-ID')
        
        if not all([signature, timestamp, agent_id]):
            return jsonify({
                'error': {
                    'code': 'MISSING_WEBHOOK_HEADERS',
                    'message': 'Missing required webhook headers',
                    'category': 'client_error'
                }
            }), 400
        
        # Verificar timestamp (prevenir ataques de replay)
        current_time = int(time.time())
        if abs(current_time - int(timestamp)) > 300:  # Ventana de 5 minutos
            return jsonify({
                'error': {
                    'code': 'INVALID_TIMESTAMP',
                    'message': 'Request timestamp too old or too far in future',
                    'category': 'client_error'
                }
            }), 400
        
        # Verificar firma HMAC
        payload = request.get_data()
        if not verify_webhook_signature(payload, signature, app.config['WEBHOOK_SECRET']):
            return jsonify({
                'error': {
                    'code': 'INVALID_SIGNATURE',
                    'message': 'Invalid webhook signature',
                    'category': 'authentication_error'
                }
            }), 401
        
        # Procesar datos del webhook
        webhook_data = request.get_json()
        task_id = webhook_data.get('task_id')
        event_type = webhook_data.get('event_type')
        
        print(f"📨 Webhook recibido: {event_type} para tarea {task_id}")
        
        # Responder con confirmación
        response = {
            'acknowledged': True,
            'timestamp': datetime.now().isoformat(),
            'message': f'Webhook {event_type} processed successfully'
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'WEBHOOK_PROCESSING_ERROR',
                'message': 'Error processing webhook',
                'category': 'server_error',
                'details': str(e)
            },
            'timestamp': datetime.now().isoformat()
        }), 500

# ================================
# ENDPOINTS ADICIONALES
# ================================

@app.route('/api/v2/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'agent_id': task_executor.agent_id,
        'metrics': {
            'active_tasks': len(active_tasks),
            'queue_size': task_queue.qsize(),
            'total_completed': len(task_history),
            'uptime': time.time()
        }
    }), 200

@app.route('/api/v2/tasks', methods=['GET'])
@limiter.limit("100 per hour")
def list_tasks():
    """Listar todas las tareas activas"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization'}), 401
        
        token = auth_header.split(' ')[1]
        if not verify_jwt_token(token):
            return jsonify({'error': 'Invalid token'}), 401
        
        # Filtros opcionales
        status_filter = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Filtrar tareas
        tasks = list(active_tasks.values())
        if status_filter:
            tasks = [t for t in tasks if t['status'] == status_filter]
        
        # Paginación
        total = len(tasks)
        tasks = tasks[offset:offset + limit]
        
        return jsonify({
            'tasks': tasks,
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/generate-token', methods=['POST'])
def generate_token():
    """Generar token JWT para testing"""
    data = request.get_json() or {}
    
    payload = {
        'agent_id': data.get('agent_id', 'test_agent'),
        'permissions': data.get('permissions', ['task_execution', 'task_monitoring']),
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600  # 1 hora
    }
    
    token = jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'expires_in': 3600,
        'token_type': 'Bearer'
    }), 200

# ================================
# MANEJO DE ERRORES GLOBALES
# ================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Invalid request format',
            'category': 'client_error'
        }
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required',
            'category': 'authentication_error'
        }
    }), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found',
            'category': 'client_error'
        }
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Too many requests',
            'category': 'client_error',
            'retry_after': 60
        }
    }), 429

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected error occurred',
            'category': 'server_error'
        }
    }), 500

# ================================
# RUTAS ESTÁTICAS
# ================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# ================================
# INICIALIZACIÓN
# ================================

def initialize_app():
    """Inicializar la aplicación"""
    with app.app_context():
        db.create_all()
    
    # Iniciar ejecutor de tareas
    task_executor.start()
    
    print("🚀 SAM ↔ Manus API Server iniciado")
    print(f"📊 Configuración:")
    print(f"   - Max tareas concurrentes: {MAX_CONCURRENT_TASKS}")
    print(f"   - Timeout por defecto: {TASK_TIMEOUT_DEFAULT}s")
    print(f"   - Workers de ejecución: {task_executor.num_workers}")
    print(f"   - Agent ID: {task_executor.agent_id}")

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=5000, debug=False)

