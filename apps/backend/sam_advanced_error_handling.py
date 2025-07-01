#!/usr/bin/env python3
"""
SAM Advanced Error Handling and Retry System
Sistema avanzado de manejo de errores, timeouts y políticas de reintento para SAM
"""

import asyncio
import aiohttp
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
import random
import math
from contextlib import asynccontextmanager
import weakref
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import signal
import sys

class ErrorType(Enum):
    """Tipos de errores del sistema"""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_ERROR = "resource_error"
    EXECUTION_ERROR = "execution_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"

class RetryStrategy(Enum):
    """Estrategias de reintento"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    CUSTOM = "custom"

class CircuitBreakerState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Bloqueando requests
    HALF_OPEN = "half_open"  # Probando si se recuperó

@dataclass
class ErrorContext:
    """Contexto de un error"""
    error_id: str
    error_type: ErrorType
    message: str
    timestamp: str
    stack_trace: Optional[str] = None
    request_id: Optional[str] = None
    agent_id: Optional[str] = None
    endpoint: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetryPolicy:
    """Política de reintentos"""
    max_retries: int
    strategy: RetryStrategy
    base_delay: float  # segundos
    max_delay: float   # segundos
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on_errors: List[ErrorType] = field(default_factory=list)
    timeout_per_attempt: float = 30.0
    
    def __post_init__(self):
        if not self.retry_on_errors:
            self.retry_on_errors = [
                ErrorType.NETWORK_ERROR,
                ErrorType.TIMEOUT_ERROR,
                ErrorType.SYSTEM_ERROR
            ]

@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # segundos
    success_threshold: int = 3  # para half-open -> closed
    timeout: float = 30.0

@dataclass
class EndpointHealth:
    """Estado de salud de un endpoint"""
    endpoint: str
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    average_response_time: float = 0.0
    circuit_breaker_state: CircuitBreakerState = CircuitBreakerState.CLOSED
    last_state_change: str = field(default_factory=lambda: datetime.now().isoformat())

class TimeoutManager:
    """Gestor de timeouts avanzado"""
    
    def __init__(self):
        self.active_timeouts: Dict[str, asyncio.Task] = {}
        self.timeout_callbacks: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
    
    async def with_timeout(self, 
                          coro, 
                          timeout: float, 
                          timeout_id: Optional[str] = None,
                          on_timeout: Optional[Callable] = None) -> Any:
        """Ejecutar corrutina con timeout personalizado"""
        if timeout_id is None:
            timeout_id = str(uuid.uuid4())
        
        if on_timeout:
            self.timeout_callbacks[timeout_id] = on_timeout
        
        try:
            # Crear task con timeout
            task = asyncio.create_task(coro)
            self.active_timeouts[timeout_id] = task
            
            result = await asyncio.wait_for(task, timeout=timeout)
            return result
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout occurred for {timeout_id} after {timeout}s")
            
            # Ejecutar callback si existe
            if timeout_id in self.timeout_callbacks:
                try:
                    await self.timeout_callbacks[timeout_id]()
                except Exception as e:
                    self.logger.error(f"Error in timeout callback: {e}")
            
            raise
            
        finally:
            # Limpiar
            self.active_timeouts.pop(timeout_id, None)
            self.timeout_callbacks.pop(timeout_id, None)
    
    def cancel_timeout(self, timeout_id: str) -> bool:
        """Cancelar timeout específico"""
        if timeout_id in self.active_timeouts:
            task = self.active_timeouts[timeout_id]
            task.cancel()
            del self.active_timeouts[timeout_id]
            self.timeout_callbacks.pop(timeout_id, None)
            return True
        return False
    
    def get_active_timeouts(self) -> List[str]:
        """Obtener lista de timeouts activos"""
        return list(self.active_timeouts.keys())

class RetryEngine:
    """Motor de reintentos avanzado"""
    
    def __init__(self, db_path: str = "/tmp/sam_retries.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos de reintentos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS retry_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    delay_used REAL NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT FALSE,
                    response_time REAL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS retry_policies (
                    policy_id TEXT PRIMARY KEY,
                    endpoint TEXT NOT NULL,
                    max_retries INTEGER NOT NULL,
                    strategy TEXT NOT NULL,
                    base_delay REAL NOT NULL,
                    max_delay REAL NOT NULL,
                    backoff_multiplier REAL DEFAULT 2.0,
                    jitter BOOLEAN DEFAULT TRUE,
                    retry_on_errors TEXT NOT NULL,
                    timeout_per_attempt REAL DEFAULT 30.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def calculate_delay(self, 
                       attempt: int, 
                       policy: RetryPolicy, 
                       last_error: Optional[ErrorContext] = None) -> float:
        """Calcular delay para el siguiente intento"""
        if policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = policy.base_delay * (policy.backoff_multiplier ** (attempt - 1))
        elif policy.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = policy.base_delay * attempt
        elif policy.strategy == RetryStrategy.FIXED_INTERVAL:
            delay = policy.base_delay
        elif policy.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            delay = policy.base_delay * self._fibonacci(attempt)
        else:  # CUSTOM
            delay = self._custom_delay_calculation(attempt, policy, last_error)
        
        # Aplicar límite máximo
        delay = min(delay, policy.max_delay)
        
        # Aplicar jitter si está habilitado
        if policy.jitter:
            jitter_range = delay * 0.1  # 10% de jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calcular número de Fibonacci"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def _custom_delay_calculation(self, 
                                 attempt: int, 
                                 policy: RetryPolicy, 
                                 last_error: Optional[ErrorContext]) -> float:
        """Cálculo personalizado de delay"""
        # Implementación personalizada basada en tipo de error
        if last_error:
            if last_error.error_type == ErrorType.NETWORK_ERROR:
                return policy.base_delay * (1.5 ** attempt)
            elif last_error.error_type == ErrorType.TIMEOUT_ERROR:
                return policy.base_delay * (2.0 ** attempt)
            elif last_error.error_type == ErrorType.RESOURCE_ERROR:
                return policy.base_delay * attempt * 2
        
        return policy.base_delay * policy.backoff_multiplier ** (attempt - 1)
    
    async def execute_with_retry(self,
                                func: Callable,
                                policy: RetryPolicy,
                                request_id: str,
                                *args,
                                **kwargs) -> Any:
        """Ejecutar función con política de reintentos"""
        last_error = None
        
        for attempt in range(1, policy.max_retries + 2):  # +1 para intento inicial
            try:
                # Registrar intento
                attempt_id = str(uuid.uuid4())
                start_time = time.time()
                
                # Ejecutar función con timeout
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=policy.timeout_per_attempt
                    )
                else:
                    result = func(*args, **kwargs)
                
                response_time = time.time() - start_time
                
                # Registrar éxito
                self._record_attempt(
                    attempt_id, request_id, attempt, None, None, 
                    0, True, response_time
                )
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                error_context = self._create_error_context(e, request_id, attempt)
                last_error = error_context
                
                # Verificar si debemos reintentar este tipo de error
                if error_context.error_type not in policy.retry_on_errors:
                    self.logger.info(f"Error type {error_context.error_type.value} not in retry policy")
                    raise
                
                # Si es el último intento, no calcular delay
                if attempt > policy.max_retries:
                    self.logger.error(f"Max retries ({policy.max_retries}) exceeded for {request_id}")
                    raise
                
                # Calcular delay para siguiente intento
                delay = self.calculate_delay(attempt, policy, error_context)
                
                # Registrar intento fallido
                self._record_attempt(
                    str(uuid.uuid4()), request_id, attempt, 
                    error_context.error_type.value, error_context.message,
                    delay, False, response_time
                )
                
                self.logger.warning(
                    f"Attempt {attempt} failed for {request_id}: {error_context.message}. "
                    f"Retrying in {delay:.2f}s"
                )
                
                # Esperar antes del siguiente intento
                if delay > 0:
                    await asyncio.sleep(delay)
        
        # Si llegamos aquí, todos los intentos fallaron
        if last_error:
            raise Exception(f"All retry attempts failed. Last error: {last_error.message}")
        else:
            raise Exception("All retry attempts failed with unknown error")
    
    def _create_error_context(self, 
                             exception: Exception, 
                             request_id: str, 
                             attempt: int) -> ErrorContext:
        """Crear contexto de error a partir de excepción"""
        error_type = self._classify_error(exception)
        
        return ErrorContext(
            error_id=str(uuid.uuid4()),
            error_type=error_type,
            message=str(exception),
            timestamp=datetime.now().isoformat(),
            stack_trace=None,  # Se podría añadir traceback aquí
            request_id=request_id,
            retry_count=attempt,
            metadata={"exception_type": type(exception).__name__}
        )
    
    def _classify_error(self, exception: Exception) -> ErrorType:
        """Clasificar tipo de error"""
        if isinstance(exception, (asyncio.TimeoutError, TimeoutError, FutureTimeoutError)):
            return ErrorType.TIMEOUT_ERROR
        elif isinstance(exception, (aiohttp.ClientError, ConnectionError)):
            return ErrorType.NETWORK_ERROR
        elif isinstance(exception, PermissionError):
            return ErrorType.AUTHENTICATION_ERROR
        elif isinstance(exception, ValueError):
            return ErrorType.VALIDATION_ERROR
        elif isinstance(exception, (MemoryError, OSError)):
            return ErrorType.RESOURCE_ERROR
        elif isinstance(exception, RuntimeError):
            return ErrorType.EXECUTION_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _record_attempt(self,
                       attempt_id: str,
                       request_id: str,
                       attempt_number: int,
                       error_type: Optional[str],
                       error_message: Optional[str],
                       delay_used: float,
                       success: bool,
                       response_time: float):
        """Registrar intento en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO retry_attempts 
                    (attempt_id, request_id, attempt_number, error_type, error_message,
                     delay_used, success, response_time, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    attempt_id,
                    request_id,
                    attempt_number,
                    error_type or "",
                    error_message or "",
                    delay_used,
                    success,
                    response_time,
                    json.dumps({"timestamp": datetime.now().isoformat()})
                ))
        except Exception as e:
            self.logger.error(f"Error recording retry attempt: {e}")

class CircuitBreaker:
    """Implementación de Circuit Breaker pattern"""
    
    def __init__(self, config: CircuitBreakerConfig, endpoint: str):
        self.config = config
        self.endpoint = endpoint
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecutar función a través del circuit breaker"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.logger.info(f"Circuit breaker for {self.endpoint} moved to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker is OPEN for {self.endpoint}")
        
        try:
            # Ejecutar función
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            else:
                result = func(*args, **kwargs)
            
            # Registrar éxito
            self._on_success()
            return result
            
        except Exception as e:
            # Registrar fallo
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si debemos intentar resetear el circuit breaker"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _on_success(self):
        """Manejar éxito"""
        with self._lock:
            self.success_count += 1
            self.last_success_time = time.time()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.logger.info(f"Circuit breaker for {self.endpoint} moved to CLOSED")
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0  # Reset failure count on success
    
    def _on_failure(self):
        """Manejar fallo"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker for {self.endpoint} moved to OPEN (failure in half-open)")
            elif (self.state == CircuitBreakerState.CLOSED and 
                  self.failure_count >= self.config.failure_threshold):
                self.state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker for {self.endpoint} moved to OPEN (threshold reached)")
    
    def get_state(self) -> Dict[str, Any]:
        """Obtener estado actual del circuit breaker"""
        return {
            "endpoint": self.endpoint,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "config": asdict(self.config)
        }

class EndpointHealthMonitor:
    """Monitor de salud de endpoints"""
    
    def __init__(self, db_path: str = "/tmp/sam_health.db"):
        self.db_path = db_path
        self.endpoints: Dict[str, EndpointHealth] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Iniciar monitoreo en background
        asyncio.create_task(self._health_monitor_loop())
    
    def _init_database(self):
        """Inicializar base de datos de salud"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS endpoint_health (
                    endpoint TEXT PRIMARY KEY,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_success TEXT,
                    last_failure TEXT,
                    average_response_time REAL DEFAULT 0.0,
                    circuit_breaker_state TEXT DEFAULT 'closed',
                    last_state_change TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_events (
                    event_id TEXT PRIMARY KEY,
                    endpoint TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    response_time REAL,
                    error_message TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
    
    def register_endpoint(self, 
                         endpoint: str, 
                         circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        """Registrar endpoint para monitoreo"""
        if endpoint not in self.endpoints:
            self.endpoints[endpoint] = EndpointHealth(endpoint=endpoint)
            
            # Crear circuit breaker si se proporciona configuración
            if circuit_breaker_config:
                self.circuit_breakers[endpoint] = CircuitBreaker(circuit_breaker_config, endpoint)
            
            # Persistir en base de datos
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO endpoint_health (endpoint)
                    VALUES (?)
                """, (endpoint,))
            
            self.logger.info(f"Registered endpoint for monitoring: {endpoint}")
    
    async def execute_with_monitoring(self,
                                    endpoint: str,
                                    func: Callable,
                                    *args,
                                    **kwargs) -> Any:
        """Ejecutar función con monitoreo de salud"""
        if endpoint not in self.endpoints:
            self.register_endpoint(endpoint)
        
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            # Usar circuit breaker si está disponible
            if endpoint in self.circuit_breakers:
                result = await self.circuit_breakers[endpoint].call(func, *args, **kwargs)
            else:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            
            success = True
            return result
            
        except Exception as e:
            error_message = str(e)
            raise
            
        finally:
            response_time = time.time() - start_time
            self._record_health_event(endpoint, success, response_time, error_message)
    
    def _record_health_event(self,
                           endpoint: str,
                           success: bool,
                           response_time: float,
                           error_message: Optional[str] = None):
        """Registrar evento de salud"""
        try:
            # Actualizar estadísticas del endpoint
            health = self.endpoints[endpoint]
            
            if success:
                health.success_count += 1
                health.last_success = datetime.now().isoformat()
            else:
                health.failure_count += 1
                health.last_failure = datetime.now().isoformat()
            
            # Actualizar tiempo promedio de respuesta
            total_requests = health.success_count + health.failure_count
            if total_requests > 1:
                health.average_response_time = (
                    (health.average_response_time * (total_requests - 1) + response_time) / total_requests
                )
            else:
                health.average_response_time = response_time
            
            # Actualizar estado del circuit breaker
            if endpoint in self.circuit_breakers:
                cb_state = self.circuit_breakers[endpoint].state
                if cb_state != health.circuit_breaker_state:
                    health.circuit_breaker_state = cb_state
                    health.last_state_change = datetime.now().isoformat()
            
            # Persistir en base de datos
            with sqlite3.connect(self.db_path) as conn:
                # Actualizar salud del endpoint
                conn.execute("""
                    UPDATE endpoint_health SET
                        success_count = ?, failure_count = ?, last_success = ?,
                        last_failure = ?, average_response_time = ?,
                        circuit_breaker_state = ?, updated_at = ?
                    WHERE endpoint = ?
                """, (
                    health.success_count,
                    health.failure_count,
                    health.last_success,
                    health.last_failure,
                    health.average_response_time,
                    health.circuit_breaker_state.value,
                    datetime.now().isoformat(),
                    endpoint
                ))
                
                # Registrar evento
                conn.execute("""
                    INSERT INTO health_events
                    (event_id, endpoint, event_type, success, response_time, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    endpoint,
                    "api_call",
                    success,
                    response_time,
                    error_message
                ))
                
        except Exception as e:
            self.logger.error(f"Error recording health event: {e}")
    
    async def _health_monitor_loop(self):
        """Loop de monitoreo de salud en background"""
        while True:
            try:
                await self._check_endpoint_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_endpoint_health(self):
        """Verificar salud de todos los endpoints"""
        for endpoint, health in self.endpoints.items():
            try:
                # Calcular métricas de salud
                total_requests = health.success_count + health.failure_count
                if total_requests > 0:
                    success_rate = health.success_count / total_requests
                    
                    # Alertar si la tasa de éxito es muy baja
                    if success_rate < 0.5 and total_requests > 10:
                        self.logger.warning(
                            f"Low success rate for {endpoint}: {success_rate:.2%} "
                            f"({health.success_count}/{total_requests})"
                        )
                    
                    # Alertar si el tiempo de respuesta es muy alto
                    if health.average_response_time > 30.0:
                        self.logger.warning(
                            f"High response time for {endpoint}: {health.average_response_time:.2f}s"
                        )
                
            except Exception as e:
                self.logger.error(f"Error checking health for {endpoint}: {e}")
    
    def get_endpoint_health(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Obtener salud de un endpoint específico"""
        if endpoint not in self.endpoints:
            return None
        
        health = self.endpoints[endpoint]
        result = asdict(health)
        
        # Añadir información del circuit breaker si existe
        if endpoint in self.circuit_breakers:
            result["circuit_breaker"] = self.circuit_breakers[endpoint].get_state()
        
        return result
    
    def get_all_health(self) -> Dict[str, Any]:
        """Obtener salud de todos los endpoints"""
        return {
            endpoint: self.get_endpoint_health(endpoint)
            for endpoint in self.endpoints.keys()
        }

class SAMErrorHandler:
    """Manejador principal de errores para SAM"""
    
    def __init__(self, 
                 default_retry_policy: Optional[RetryPolicy] = None,
                 default_circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        
        self.timeout_manager = TimeoutManager()
        self.retry_engine = RetryEngine()
        self.health_monitor = EndpointHealthMonitor()
        
        # Políticas por defecto
        self.default_retry_policy = default_retry_policy or RetryPolicy(
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
            jitter=True,
            timeout_per_attempt=30.0
        )
        
        self.default_circuit_breaker_config = default_circuit_breaker_config or CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0,
            success_threshold=3,
            timeout=30.0
        )
        
        # Políticas específicas por endpoint
        self.endpoint_policies: Dict[str, RetryPolicy] = {}
        self.endpoint_circuit_configs: Dict[str, CircuitBreakerConfig] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def configure_endpoint(self,
                          endpoint: str,
                          retry_policy: Optional[RetryPolicy] = None,
                          circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        """Configurar políticas específicas para un endpoint"""
        if retry_policy:
            self.endpoint_policies[endpoint] = retry_policy
        
        if circuit_breaker_config:
            self.endpoint_circuit_configs[endpoint] = circuit_breaker_config
            self.health_monitor.register_endpoint(endpoint, circuit_breaker_config)
        else:
            self.health_monitor.register_endpoint(endpoint, self.default_circuit_breaker_config)
    
    async def execute_with_error_handling(self,
                                        func: Callable,
                                        endpoint: str,
                                        request_id: Optional[str] = None,
                                        timeout: Optional[float] = None,
                                        custom_retry_policy: Optional[RetryPolicy] = None,
                                        *args,
                                        **kwargs) -> Any:
        """Ejecutar función con manejo completo de errores"""
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Determinar política de reintentos
        retry_policy = (custom_retry_policy or 
                       self.endpoint_policies.get(endpoint) or 
                       self.default_retry_policy)
        
        # Determinar timeout
        if timeout is None:
            timeout = retry_policy.timeout_per_attempt
        
        # Función wrapper que combina timeout y monitoreo de salud
        async def wrapped_func(*args, **kwargs):
            return await self.health_monitor.execute_with_monitoring(
                endpoint, func, *args, **kwargs
            )
        
        # Función wrapper con timeout
        async def timed_func(*args, **kwargs):
            return await self.timeout_manager.with_timeout(
                wrapped_func(*args, **kwargs),
                timeout,
                f"{request_id}_{endpoint}"
            )
        
        # Ejecutar con reintentos
        return await self.retry_engine.execute_with_retry(
            timed_func,
            retry_policy,
            request_id,
            *args,
            **kwargs
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del sistema completo"""
        return {
            "timestamp": datetime.now().isoformat(),
            "endpoints": self.health_monitor.get_all_health(),
            "active_timeouts": len(self.timeout_manager.get_active_timeouts()),
            "default_policies": {
                "retry_policy": asdict(self.default_retry_policy),
                "circuit_breaker_config": asdict(self.default_circuit_breaker_config)
            }
        }

# Instancia global del manejador de errores
error_handler = SAMErrorHandler()

# Configuraciones predefinidas para endpoints comunes
def configure_manus_endpoints():
    """Configurar endpoints de Manus con políticas optimizadas"""
    
    # Endpoint principal de Manus
    manus_retry_policy = RetryPolicy(
        max_retries=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=2.0,
        max_delay=120.0,
        backoff_multiplier=2.0,
        jitter=True,
        retry_on_errors=[
            ErrorType.NETWORK_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.SYSTEM_ERROR
        ],
        timeout_per_attempt=45.0
    )
    
    manus_circuit_config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=45.0
    )
    
    error_handler.configure_endpoint(
        "http://65.109.54.94:3000/execute",
        manus_retry_policy,
        manus_circuit_config
    )
    
    # Webhook endpoint
    webhook_retry_policy = RetryPolicy(
        max_retries=3,
        strategy=RetryStrategy.FIXED_INTERVAL,
        base_delay=5.0,
        max_delay=30.0,
        timeout_per_attempt=15.0
    )
    
    error_handler.configure_endpoint(
        "http://65.109.54.94:3000/webhook/sam",
        webhook_retry_policy
    )

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configurar endpoints
    configure_manus_endpoints()
    
    # Ejemplo de uso
    async def demo():
        # Simular función que puede fallar
        async def unreliable_api_call(data: Dict[str, Any]) -> Dict[str, Any]:
            # Simular fallo ocasional
            if random.random() < 0.3:
                raise aiohttp.ClientError("Simulated network error")
            
            await asyncio.sleep(0.5)  # Simular trabajo
            return {"status": "success", "data": data}
        
        # Ejecutar con manejo de errores
        try:
            result = await error_handler.execute_with_error_handling(
                unreliable_api_call,
                "http://65.109.54.94:3000/execute",
                data={"task": "test"}
            )
            print(f"Success: {result}")
            
        except Exception as e:
            print(f"Final failure: {e}")
        
        # Mostrar estado de salud
        health = error_handler.get_system_health()
        print(json.dumps(health, indent=2))
    
    # Ejecutar demo
    asyncio.run(demo())

