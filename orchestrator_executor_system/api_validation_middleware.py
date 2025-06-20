#!/usr/bin/env python3
"""
API Validation Middleware for MCP Orchestrator-Executor System
Middleware para validación automática de payloads en endpoints
"""

from functools import wraps
from flask import request, jsonify, g
import json
import time
from typing import Dict, Any, Optional, Callable
import logging
from mcp_payload_schemas import PayloadValidator, PayloadType

class APIValidationMiddleware:
    """
    Middleware para validación automática de APIs
    """
    
    def __init__(self, app=None):
        self.app = app
        self.validator = PayloadValidator()
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar middleware con Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.errorhandler(400)(self.handle_validation_error)
    
    def before_request(self):
        """Ejecutar antes de cada request"""
        g.request_start_time = time.time()
        g.validation_result = None
        
        # Log de request entrante
        self.logger.info(f"Incoming request: {request.method} {request.path}")
    
    def after_request(self, response):
        """Ejecutar después de cada request"""
        duration = time.time() - g.request_start_time
        
        # Log de response
        self.logger.info(f"Request completed: {request.method} {request.path} - "
                        f"Status: {response.status_code} - Duration: {duration:.3f}s")
        
        # Añadir headers de respuesta
        response.headers['X-Request-Duration'] = f"{duration:.3f}"
        response.headers['X-API-Version'] = "1.0.0"
        
        return response
    
    def handle_validation_error(self, error):
        """Manejar errores de validación"""
        return jsonify({
            "error": "Validation failed",
            "details": str(error),
            "timestamp": time.time()
        }), 400

def validate_payload(payload_type: PayloadType, required: bool = True):
    """
    Decorador para validar payloads de entrada
    
    Args:
        payload_type: Tipo de payload a validar
        required: Si la validación es requerida (falla si no es válido)
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            validator = PayloadValidator()
            
            # Obtener datos del request
            if request.is_json:
                payload = request.get_json()
            else:
                if required:
                    return jsonify({
                        "error": "JSON payload required",
                        "payload_type": payload_type.value
                    }), 400
                payload = {}
            
            # Validar payload
            validation_result = validator.validate_payload(payload, payload_type)
            g.validation_result = validation_result
            
            if not validation_result["valid"] and required:
                return jsonify({
                    "error": "Payload validation failed",
                    "validation_details": validation_result,
                    "payload_type": payload_type.value
                }), 400
            
            # Añadir payload validado al request
            g.validated_payload = payload
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_fields(*fields):
    """
    Decorador para requerir campos específicos en el payload
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    "error": "JSON payload required",
                    "required_fields": list(fields)
                }), 400
            
            payload = request.get_json()
            missing_fields = []
            
            for field in fields:
                if field not in payload:
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    "error": "Missing required fields",
                    "missing_fields": missing_fields,
                    "required_fields": list(fields)
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_task_id(f: Callable) -> Callable:
    """
    Decorador para validar formato de task_id
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        task_id = kwargs.get('task_id') or request.view_args.get('task_id')
        
        if task_id:
            # Validar formato de task_id
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', task_id):
                return jsonify({
                    "error": "Invalid task_id format",
                    "task_id": task_id,
                    "expected_format": "alphanumeric, underscore, and dash only"
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(requests_per_minute: int = 60):
    """
    Decorador para rate limiting básico
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implementación básica de rate limiting
            # En producción se usaría Redis o similar
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Por simplicidad, solo log del rate limiting
            # En implementación real se mantendría estado en Redis
            logging.getLogger(__name__).info(
                f"Rate limit check: {client_ip} - {requests_per_minute} req/min"
            )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_api_call(include_payload: bool = False):
    """
    Decorador para logging detallado de llamadas API
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger = logging.getLogger(__name__)
            
            # Log de entrada
            log_data = {
                "endpoint": request.endpoint,
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.headers.get('User-Agent', ''),
                "timestamp": time.time()
            }
            
            if include_payload and request.is_json:
                log_data["payload"] = request.get_json()
            
            logger.info(f"API Call: {json.dumps(log_data)}")
            
            # Ejecutar función
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log de salida exitosa
                logger.info(f"API Success: {request.endpoint} - Duration: {duration:.3f}s")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log de error
                logger.error(f"API Error: {request.endpoint} - Duration: {duration:.3f}s - Error: {str(e)}")
                
                raise
        
        return decorated_function
    return decorator

# Ejemplo de uso con Flask
if __name__ == "__main__":
    from flask import Flask
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    # Inicializar middleware
    validation_middleware = APIValidationMiddleware(app)
    
    @app.route('/api/v1/tasks', methods=['POST'])
    @validate_payload(PayloadType.TASK_EXECUTION, required=True)
    @rate_limit(requests_per_minute=30)
    @log_api_call(include_payload=True)
    def create_task():
        """Crear nueva tarea"""
        payload = g.validated_payload
        
        return jsonify({
            "status": "task_created",
            "task_id": payload.get("task_id"),
            "validation_result": g.validation_result
        })
    
    @app.route('/api/v1/tasks/<task_id>/status', methods=['GET'])
    @validate_task_id
    @rate_limit(requests_per_minute=100)
    @log_api_call()
    def get_task_status(task_id: str):
        """Obtener estado de tarea"""
        return jsonify({
            "task_id": task_id,
            "status": "running",
            "progress": 45
        })
    
    @app.route('/api/v1/notifications', methods=['POST'])
    @validate_payload(PayloadType.NOTIFICATION, required=True)
    @require_fields("notification_type", "task_id", "agent_id")
    @log_api_call(include_payload=True)
    def receive_notification():
        """Recibir notificación"""
        payload = g.validated_payload
        
        return jsonify({
            "status": "notification_received",
            "notification_id": payload.get("notification_id")
        })
    
    @app.route('/api/v1/webhooks', methods=['POST'])
    @validate_payload(PayloadType.WEBHOOK_REGISTRATION, required=True)
    @log_api_call(include_payload=True)
    def register_webhook():
        """Registrar webhook"""
        payload = g.validated_payload
        
        return jsonify({
            "status": "webhook_registered",
            "endpoint_id": payload.get("endpoint_id")
        })
    
    @app.route('/api/v1/agent/end-task', methods=['POST'])
    @validate_payload(PayloadType.AGENT_END_TASK, required=True)
    @log_api_call(include_payload=True)
    def agent_end_task():
        """Finalizar tarea de agente"""
        payload = g.validated_payload
        
        return jsonify({
            "status": "task_ended",
            "task_id": payload.get("task_id"),
            "completion_status": payload.get("completion_status")
        })
    
    @app.route('/api/v1/schemas', methods=['GET'])
    def get_schemas():
        """Obtener todos los schemas disponibles"""
        validator = PayloadValidator()
        return jsonify({
            "schemas": validator.get_all_schemas()
        })
    
    @app.route('/api/v1/schemas/<payload_type>', methods=['GET'])
    def get_schema(payload_type: str):
        """Obtener schema específico"""
        try:
            pt = PayloadType(payload_type)
            validator = PayloadValidator()
            schema = validator.get_schema(pt)
            
            if schema:
                return jsonify(schema)
            else:
                return jsonify({"error": "Schema not found"}), 404
                
        except ValueError:
            return jsonify({
                "error": "Invalid payload type",
                "available_types": [pt.value for pt in PayloadType]
            }), 400
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)

