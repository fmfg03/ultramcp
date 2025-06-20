#!/usr/bin/env python3
"""
API Validation Middleware
Middleware de validación para endpoints del sistema MCP Enterprise

Este módulo proporciona validación automática de:
- Esquemas de request/response
- Autenticación y autorización
- Rate limiting
- Input sanitization
- Logging de seguridad
- Métricas de API
"""

import json
import time
import hashlib
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from functools import wraps
from dataclasses import dataclass
import asyncio
from collections import defaultdict, deque

# Imports para frameworks web
try:
    from flask import Flask, request, jsonify, g
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    from fastapi import FastAPI, Request, HTTPException, Depends
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from aiohttp import web, ClientSession
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Imports para validación
try:
    from pydantic import BaseModel, ValidationError, validator
    from jsonschema import validate, ValidationError as JSONSchemaError
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationRule:
    """Regla de validación para un endpoint"""
    endpoint: str
    method: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    auth_required: bool = True
    rate_limit: Optional[int] = None  # requests per minute
    roles_required: Optional[List[str]] = None
    sanitize_input: bool = True
    log_requests: bool = True

@dataclass
class RateLimitConfig:
    """Configuración de rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    
class SecurityConfig:
    """Configuración de seguridad"""
    
    # Patrones de input peligroso
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'(union|select|insert|update|delete|drop|create|alter)\s+',  # SQL injection
        r'(\.\./){2,}',  # Path traversal
        r'eval\s*\(',  # Code injection
        r'exec\s*\(',  # Code execution
        r'system\s*\(',  # System calls
    ]
    
    # Headers de seguridad requeridos
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Configuración de CORS
    CORS_CONFIG = {
        'origins': ['*'],  # En producción, especificar dominios exactos
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'headers': ['Content-Type', 'Authorization', 'X-API-Key']
    }

class RateLimiter:
    """Sistema de rate limiting con ventanas deslizantes"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = defaultdict(lambda: {
            'minute': deque(),
            'hour': deque(),
            'day': deque()
        })
    
    def is_allowed(self, client_id: str) -> tuple[bool, Dict[str, Any]]:
        """
        Verifica si una request está permitida
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Limpiar requests antiguas
        self._cleanup_old_requests(client_requests, now)
        
        # Verificar límites
        minute_count = len(client_requests['minute'])
        hour_count = len(client_requests['hour'])
        day_count = len(client_requests['day'])
        
        rate_limit_info = {
            'requests_per_minute': minute_count,
            'requests_per_hour': hour_count,
            'requests_per_day': day_count,
            'limits': {
                'minute': self.config.requests_per_minute,
                'hour': self.config.requests_per_hour,
                'day': self.config.requests_per_day
            }
        }
        
        # Verificar si excede límites
        if (minute_count >= self.config.requests_per_minute or
            hour_count >= self.config.requests_per_hour or
            day_count >= self.config.requests_per_day):
            return False, rate_limit_info
        
        # Registrar nueva request
        client_requests['minute'].append(now)
        client_requests['hour'].append(now)
        client_requests['day'].append(now)
        
        return True, rate_limit_info
    
    def _cleanup_old_requests(self, client_requests: Dict[str, deque], now: float):
        """Limpia requests antiguas de las ventanas deslizantes"""
        # Limpiar requests de más de 1 minuto
        while (client_requests['minute'] and 
               now - client_requests['minute'][0] > 60):
            client_requests['minute'].popleft()
        
        # Limpiar requests de más de 1 hora
        while (client_requests['hour'] and 
               now - client_requests['hour'][0] > 3600):
            client_requests['hour'].popleft()
        
        # Limpiar requests de más de 1 día
        while (client_requests['day'] and 
               now - client_requests['day'][0] > 86400):
            client_requests['day'].popleft()

class InputSanitizer:
    """Sanitizador de input para prevenir ataques"""
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitiza un string removiendo contenido peligroso"""
        if not isinstance(value, str):
            return str(value)
        
        # Remover patrones peligrosos
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        # Escapar caracteres HTML
        value = (value.replace('&', '&amp;')
                     .replace('<', '&lt;')
                     .replace('>', '&gt;')
                     .replace('"', '&quot;')
                     .replace("'", '&#x27;'))
        
        return value.strip()
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza recursivamente un diccionario"""
        sanitized = {}
        for key, value in data.items():
            # Sanitizar la clave
            clean_key = InputSanitizer.sanitize_string(key)
            
            # Sanitizar el valor según su tipo
            if isinstance(value, str):
                sanitized[clean_key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[clean_key] = InputSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[clean_key] = InputSanitizer.sanitize_list(value)
            else:
                sanitized[clean_key] = value
        
        return sanitized
    
    @staticmethod
    def sanitize_list(data: List[Any]) -> List[Any]:
        """Sanitiza recursivamente una lista"""
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(InputSanitizer.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(InputSanitizer.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(InputSanitizer.sanitize_list(item))
            else:
                sanitized.append(item)
        
        return sanitized

class SchemaValidator:
    """Validador de esquemas JSON"""
    
    @staticmethod
    def validate_json_schema(data: Any, schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Valida datos contra un esquema JSON
        
        Returns:
            (is_valid, error_message)
        """
        if not VALIDATION_AVAILABLE:
            logger.warning("Validation libraries not available, skipping schema validation")
            return True, None
        
        try:
            validate(instance=data, schema=schema)
            return True, None
        except JSONSchemaError as e:
            return False, str(e)
    
    @staticmethod
    def validate_pydantic_model(data: Any, model_class: type) -> tuple[bool, Optional[str], Optional[Any]]:
        """
        Valida datos contra un modelo Pydantic
        
        Returns:
            (is_valid, error_message, validated_data)
        """
        if not VALIDATION_AVAILABLE:
            logger.warning("Pydantic not available, skipping model validation")
            return True, None, data
        
        try:
            validated = model_class(**data) if isinstance(data, dict) else model_class(data)
            return True, None, validated
        except ValidationError as e:
            return False, str(e), None

class APIMetrics:
    """Sistema de métricas para APIs"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'validation_errors': 0,
            'auth_failures': 0,
            'rate_limit_hits': 0,
            'average_response_time': 0.0,
            'endpoints': defaultdict(lambda: {
                'requests': 0,
                'errors': 0,
                'avg_response_time': 0.0
            })
        }
        self.response_times = deque(maxlen=1000)  # Últimas 1000 requests
    
    def record_request(self, endpoint: str, method: str, response_time: float, 
                      status_code: int, error_type: Optional[str] = None):
        """Registra métricas de una request"""
        self.metrics['total_requests'] += 1
        
        if 200 <= status_code < 300:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
            
            if error_type == 'validation':
                self.metrics['validation_errors'] += 1
            elif error_type == 'auth':
                self.metrics['auth_failures'] += 1
            elif error_type == 'rate_limit':
                self.metrics['rate_limit_hits'] += 1
        
        # Métricas de tiempo de respuesta
        self.response_times.append(response_time)
        self.metrics['average_response_time'] = sum(self.response_times) / len(self.response_times)
        
        # Métricas por endpoint
        endpoint_key = f"{method} {endpoint}"
        endpoint_metrics = self.metrics['endpoints'][endpoint_key]
        endpoint_metrics['requests'] += 1
        
        if status_code >= 400:
            endpoint_metrics['errors'] += 1
        
        # Actualizar tiempo promedio del endpoint
        if endpoint_metrics['requests'] == 1:
            endpoint_metrics['avg_response_time'] = response_time
        else:
            # Media móvil simple
            current_avg = endpoint_metrics['avg_response_time']
            count = endpoint_metrics['requests']
            endpoint_metrics['avg_response_time'] = (current_avg * (count - 1) + response_time) / count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene todas las métricas"""
        return dict(self.metrics)

class APIValidationMiddleware:
    """Middleware principal de validación de APIs"""
    
    def __init__(self, 
                 rate_limit_config: Optional[RateLimitConfig] = None,
                 security_config: Optional[SecurityConfig] = None):
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.security_config = security_config or SecurityConfig()
        self.metrics = APIMetrics()
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.auth_handlers: List[Callable] = []
    
    def add_validation_rule(self, rule: ValidationRule):
        """Añade una regla de validación"""
        key = f"{rule.method}:{rule.endpoint}"
        self.validation_rules[key] = rule
        logger.info(f"Added validation rule for {key}")
    
    def add_auth_handler(self, handler: Callable):
        """Añade un handler de autenticación"""
        self.auth_handlers.append(handler)
    
    def get_client_id(self, request_data: Dict[str, Any]) -> str:
        """Extrae un identificador único del cliente"""
        # Prioridad: API key > IP address > User agent hash
        api_key = request_data.get('headers', {}).get('X-API-Key')
        if api_key:
            return f"api_key:{hashlib.md5(api_key.encode()).hexdigest()[:8]}"
        
        ip_address = request_data.get('remote_addr', 'unknown')
        user_agent = request_data.get('headers', {}).get('User-Agent', '')
        
        return f"ip:{ip_address}:ua:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
    
    def validate_request(self, endpoint: str, method: str, 
                        request_data: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """
        Valida una request completa
        
        Returns:
            (is_valid, response_data)
        """
        start_time = time.time()
        client_id = self.get_client_id(request_data)
        
        try:
            # Buscar regla de validación
            rule_key = f"{method}:{endpoint}"
            rule = self.validation_rules.get(rule_key)
            
            if not rule:
                # Sin regla específica, aplicar validaciones básicas
                rule = ValidationRule(endpoint=endpoint, method=method)
            
            # 1. Rate limiting
            if rule.rate_limit or True:  # Siempre aplicar rate limiting básico
                is_allowed, rate_info = self.rate_limiter.is_allowed(client_id)
                if not is_allowed:
                    self._record_metrics(endpoint, method, start_time, 429, 'rate_limit')
                    return False, {
                        'error': 'Rate limit exceeded',
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'rate_limit_info': rate_info,
                        'retry_after': 60
                    }
            
            # 2. Autenticación
            if rule.auth_required:
                auth_result = self._validate_authentication(request_data)
                if not auth_result['valid']:
                    self._record_metrics(endpoint, method, start_time, 401, 'auth')
                    return False, {
                        'error': 'Authentication failed',
                        'code': 'AUTH_FAILED',
                        'details': auth_result.get('error', 'Invalid credentials')
                    }
            
            # 3. Autorización (roles)
            if rule.roles_required:
                auth_info = request_data.get('auth_info', {})
                user_roles = auth_info.get('roles', [])
                if not any(role in user_roles for role in rule.roles_required):
                    self._record_metrics(endpoint, method, start_time, 403, 'auth')
                    return False, {
                        'error': 'Insufficient permissions',
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'required_roles': rule.roles_required
                    }
            
            # 4. Sanitización de input
            if rule.sanitize_input and 'json' in request_data:
                request_data['json'] = InputSanitizer.sanitize_dict(request_data['json'])
            
            # 5. Validación de esquema
            if rule.request_schema and 'json' in request_data:
                is_valid, error_msg = SchemaValidator.validate_json_schema(
                    request_data['json'], 
                    rule.request_schema
                )
                if not is_valid:
                    self._record_metrics(endpoint, method, start_time, 400, 'validation')
                    return False, {
                        'error': 'Request validation failed',
                        'code': 'VALIDATION_ERROR',
                        'details': error_msg
                    }
            
            # Request válida
            self._record_metrics(endpoint, method, start_time, 200)
            return True, {
                'status': 'valid',
                'client_id': client_id,
                'rate_limit_info': rate_info if 'rate_info' in locals() else None
            }
            
        except Exception as e:
            logger.error(f"Error in request validation: {e}")
            self._record_metrics(endpoint, method, start_time, 500, 'internal')
            return False, {
                'error': 'Internal validation error',
                'code': 'INTERNAL_ERROR'
            }
    
    def _validate_authentication(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida la autenticación de la request"""
        headers = request_data.get('headers', {})
        
        # Verificar API key
        api_key = headers.get('X-API-Key') or headers.get('Authorization', '').replace('Bearer ', '')
        if not api_key:
            return {'valid': False, 'error': 'Missing API key'}
        
        # Ejecutar handlers de autenticación personalizados
        for handler in self.auth_handlers:
            try:
                result = handler(api_key, request_data)
                if not result.get('valid', False):
                    return result
            except Exception as e:
                logger.error(f"Auth handler error: {e}")
                return {'valid': False, 'error': 'Authentication handler failed'}
        
        # Autenticación básica por defecto (en producción usar sistema real)
        if api_key.startswith('mcp_') and len(api_key) > 10:
            return {
                'valid': True,
                'user_id': 'default_user',
                'roles': ['user']
            }
        
        return {'valid': False, 'error': 'Invalid API key format'}
    
    def _record_metrics(self, endpoint: str, method: str, start_time: float, 
                       status_code: int, error_type: Optional[str] = None):
        """Registra métricas de la request"""
        response_time = time.time() - start_time
        self.metrics.record_request(endpoint, method, response_time, status_code, error_type)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Obtiene headers de seguridad"""
        return self.security_config.SECURITY_HEADERS.copy()

# Decoradores para diferentes frameworks

def flask_validation_middleware(middleware: APIValidationMiddleware):
    """Decorador para Flask"""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask not available")
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extraer datos de la request
            request_data = {
                'endpoint': request.endpoint or request.path,
                'method': request.method,
                'headers': dict(request.headers),
                'remote_addr': request.remote_addr,
                'json': request.get_json(silent=True) if request.is_json else None,
                'args': dict(request.args),
                'form': dict(request.form) if request.form else None
            }
            
            # Validar request
            is_valid, response_data = middleware.validate_request(
                request_data['endpoint'], 
                request_data['method'], 
                request_data
            )
            
            if not is_valid:
                response = jsonify(response_data)
                response.status_code = 400 if response_data.get('code') == 'VALIDATION_ERROR' else 401
                
                # Añadir headers de seguridad
                for header, value in middleware.get_security_headers().items():
                    response.headers[header] = value
                
                return response
            
            # Ejecutar función original
            result = f(*args, **kwargs)
            
            # Añadir headers de seguridad a la respuesta
            if hasattr(result, 'headers'):
                for header, value in middleware.get_security_headers().items():
                    result.headers[header] = value
            
            return result
        
        return decorated_function
    return decorator

def fastapi_validation_dependency(middleware: APIValidationMiddleware):
    """Dependency para FastAPI"""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not available")
    
    async def validate_request(request: Request):
        # Extraer datos de la request
        body = None
        try:
            body = await request.json()
        except:
            pass
        
        request_data = {
            'endpoint': str(request.url.path),
            'method': request.method,
            'headers': dict(request.headers),
            'remote_addr': request.client.host if request.client else 'unknown',
            'json': body,
            'query_params': dict(request.query_params)
        }
        
        # Validar request
        is_valid, response_data = middleware.validate_request(
            request_data['endpoint'], 
            request_data['method'], 
            request_data
        )
        
        if not is_valid:
            status_code = 429 if response_data.get('code') == 'RATE_LIMIT_EXCEEDED' else 400
            raise HTTPException(status_code=status_code, detail=response_data)
        
        return response_data
    
    return validate_request

# Funciones de utilidad para configuración rápida

def create_basic_middleware() -> APIValidationMiddleware:
    """Crea un middleware con configuración básica"""
    middleware = APIValidationMiddleware()
    
    # Añadir handler de autenticación básico
    def basic_auth_handler(api_key: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        # En producción, verificar contra base de datos
        if api_key.startswith('mcp_') and len(api_key) >= 20:
            return {
                'valid': True,
                'user_id': f"user_{api_key[-8:]}",
                'roles': ['user']
            }
        return {'valid': False, 'error': 'Invalid API key'}
    
    middleware.add_auth_handler(basic_auth_handler)
    
    return middleware

def create_production_middleware() -> APIValidationMiddleware:
    """Crea un middleware con configuración de producción"""
    rate_config = RateLimitConfig(
        requests_per_minute=100,
        requests_per_hour=5000,
        requests_per_day=50000,
        burst_limit=20
    )
    
    middleware = APIValidationMiddleware(rate_limit_config=rate_config)
    
    # Configurar reglas de validación comunes
    common_rules = [
        ValidationRule(
            endpoint="/api/tools/execute",
            method="POST",
            request_schema={
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "parameters": {"type": "object"}
                },
                "required": ["tool", "parameters"]
            },
            rate_limit=30,  # 30 requests per minute
            auth_required=True
        ),
        ValidationRule(
            endpoint="/api/tools",
            method="GET",
            auth_required=False,
            rate_limit=60
        )
    ]
    
    for rule in common_rules:
        middleware.add_validation_rule(rule)
    
    return middleware

# Ejemplo de uso
if __name__ == "__main__":
    # Crear middleware
    middleware = create_production_middleware()
    
    # Ejemplo de validación manual
    test_request = {
        'endpoint': '/api/tools/execute',
        'method': 'POST',
        'headers': {'X-API-Key': 'mcp_test_key_1234567890'},
        'remote_addr': '127.0.0.1',
        'json': {
            'tool': 'firecrawl',
            'parameters': {'url': 'https://example.com'}
        }
    }
    
    is_valid, response = middleware.validate_request(
        test_request['endpoint'],
        test_request['method'],
        test_request
    )
    
    print(f"Validation result: {is_valid}")
    print(f"Response: {json.dumps(response, indent=2)}")
    
    # Mostrar métricas
    print(f"Metrics: {json.dumps(middleware.metrics.get_metrics(), indent=2)}")

