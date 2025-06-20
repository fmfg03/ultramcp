# Advanced Monitoring and Observability for MCP System
# Enterprise-grade monitoring with Prometheus, Grafana, and custom metrics

import asyncio
import time
import json
import logging
import psutil
import aiohttp
import aioredis
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry
import structlog
import opentelemetry
from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
import asyncpg
import numpy as np
from collections import defaultdict, deque
import threading
import queue
import socket
import os

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MonitoringComponent(Enum):
    """Components being monitored"""
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    APPLICATION = "application"

@dataclass
class MetricDefinition:
    """Definition of a metric"""
    name: str
    type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None
    unit: str = ""

@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    component: MonitoringComponent
    condition: str
    threshold: float
    duration: int  # seconds
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    component: MonitoringComponent
    check_function: Callable
    interval: int = 30  # seconds
    timeout: int = 10  # seconds
    enabled: bool = True

class MetricsCollector:
    """Collect and manage application metrics"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or prometheus_client.REGISTRY
        self.metrics: Dict[str, Any] = {}
        self.logger = structlog.get_logger(__name__)
        
        # Initialize core metrics
        self._initialize_core_metrics()
    
    def _initialize_core_metrics(self):
        """Initialize core application metrics"""
        
        # API metrics
        self.metrics['http_requests_total'] = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.metrics['http_request_duration'] = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.metrics['http_request_size'] = Histogram(
            'http_request_size_bytes',
            'HTTP request size',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.metrics['http_response_size'] = Histogram(
            'http_response_size_bytes',
            'HTTP response size',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Database metrics
        self.metrics['db_connections_active'] = Gauge(
            'db_connections_active',
            'Active database connections',
            ['database'],
            registry=self.registry
        )
        
        self.metrics['db_query_duration'] = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['database', 'operation'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )
        
        self.metrics['db_queries_total'] = Counter(
            'db_queries_total',
            'Total database queries',
            ['database', 'operation', 'status'],
            registry=self.registry
        )
        
        # Cache metrics
        self.metrics['cache_operations_total'] = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.metrics['cache_hit_ratio'] = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio',
            ['cache_name'],
            registry=self.registry
        )
        
        # System metrics
        self.metrics['system_cpu_usage'] = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.metrics['system_memory_usage'] = Gauge(
            'system_memory_usage_bytes',
            'System memory usage',
            ['type'],
            registry=self.registry
        )
        
        self.metrics['system_disk_usage'] = Gauge(
            'system_disk_usage_bytes',
            'System disk usage',
            ['device', 'type'],
            registry=self.registry
        )
        
        # Application metrics
        self.metrics['active_sessions'] = Gauge(
            'active_sessions',
            'Number of active user sessions',
            registry=self.registry
        )
        
        self.metrics['background_tasks'] = Gauge(
            'background_tasks',
            'Number of background tasks',
            ['status'],
            registry=self.registry
        )
        
        self.metrics['llm_requests_total'] = Counter(
            'llm_requests_total',
            'Total LLM API requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.metrics['llm_request_duration'] = Histogram(
            'llm_request_duration_seconds',
            'LLM request duration',
            ['provider', 'model'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
            registry=self.registry
        )
        
        self.metrics['llm_tokens_used'] = Counter(
            'llm_tokens_used_total',
            'Total LLM tokens used',
            ['provider', 'model', 'type'],
            registry=self.registry
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float, request_size: int = 0, response_size: int = 0):
        """Record HTTP request metrics"""
        self.metrics['http_requests_total'].labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.metrics['http_request_duration'].labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if request_size > 0:
            self.metrics['http_request_size'].labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size > 0:
            self.metrics['http_response_size'].labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)
    
    def record_db_query(self, database: str, operation: str, duration: float, status: str = "success"):
        """Record database query metrics"""
        self.metrics['db_queries_total'].labels(
            database=database,
            operation=operation,
            status=status
        ).inc()
        
        self.metrics['db_query_duration'].labels(
            database=database,
            operation=operation
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, status: str, cache_name: str = "default"):
        """Record cache operation metrics"""
        self.metrics['cache_operations_total'].labels(
            operation=operation,
            status=status
        ).inc()
    
    def update_cache_hit_ratio(self, cache_name: str, hit_ratio: float):
        """Update cache hit ratio"""
        self.metrics['cache_hit_ratio'].labels(cache_name=cache_name).set(hit_ratio)
    
    def record_llm_request(self, provider: str, model: str, duration: float, status: str, input_tokens: int = 0, output_tokens: int = 0):
        """Record LLM request metrics"""
        self.metrics['llm_requests_total'].labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        self.metrics['llm_request_duration'].labels(
            provider=provider,
            model=model
        ).observe(duration)
        
        if input_tokens > 0:
            self.metrics['llm_tokens_used'].labels(
                provider=provider,
                model=model,
                type="input"
            ).inc(input_tokens)
        
        if output_tokens > 0:
            self.metrics['llm_tokens_used'].labels(
                provider=provider,
                model=model,
                type="output"
            ).inc(output_tokens)
    
    def update_system_metrics(self):
        """Update system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.metrics['system_cpu_usage'].set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics['system_memory_usage'].labels(type="used").set(memory.used)
        self.metrics['system_memory_usage'].labels(type="available").set(memory.available)
        self.metrics['system_memory_usage'].labels(type="total").set(memory.total)
        
        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                device = partition.device.replace('/', '_')
                self.metrics['system_disk_usage'].labels(device=device, type="used").set(usage.used)
                self.metrics['system_disk_usage'].labels(device=device, type="free").set(usage.free)
                self.metrics['system_disk_usage'].labels(device=device, type="total").set(usage.total)
            except PermissionError:
                continue

class PerformanceMonitor:
    """Monitor application performance and detect anomalies"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.logger = structlog.get_logger(__name__)
        
        # Performance thresholds
        self.thresholds = {
            'response_time_p95': 2.0,  # seconds
            'error_rate': 0.05,  # 5%
            'cpu_usage': 80.0,  # percent
            'memory_usage': 85.0,  # percent
            'disk_usage': 90.0,  # percent
        }
    
    def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a metric value"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        self.metrics_history[metric_name].append({
            'value': value,
            'timestamp': timestamp
        })
    
    def get_percentile(self, metric_name: str, percentile: float) -> Optional[float]:
        """Get percentile value for a metric"""
        if metric_name not in self.metrics_history:
            return None
        
        values = [entry['value'] for entry in self.metrics_history[metric_name]]
        if not values:
            return None
        
        return np.percentile(values, percentile)
    
    def get_average(self, metric_name: str, time_window: Optional[timedelta] = None) -> Optional[float]:
        """Get average value for a metric"""
        if metric_name not in self.metrics_history:
            return None
        
        entries = list(self.metrics_history[metric_name])
        if not entries:
            return None
        
        if time_window:
            cutoff_time = datetime.utcnow() - time_window
            entries = [e for e in entries if e['timestamp'] >= cutoff_time]
        
        if not entries:
            return None
        
        return sum(e['value'] for e in entries) / len(entries)
    
    def detect_anomalies(self, metric_name: str) -> List[Dict[str, Any]]:
        """Detect anomalies in metric values"""
        if metric_name not in self.metrics_history:
            return []
        
        values = [entry['value'] for entry in self.metrics_history[metric_name]]
        if len(values) < 10:  # Need minimum data points
            return []
        
        # Calculate z-score for anomaly detection
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            return []
        
        anomalies = []
        for i, entry in enumerate(self.metrics_history[metric_name]):
            z_score = abs((entry['value'] - mean_val) / std_val)
            if z_score > 3:  # 3 standard deviations
                anomalies.append({
                    'timestamp': entry['timestamp'],
                    'value': entry['value'],
                    'z_score': z_score,
                    'severity': 'high' if z_score > 4 else 'medium'
                })
        
        return anomalies
    
    def check_thresholds(self) -> List[Dict[str, Any]]:
        """Check if any metrics exceed thresholds"""
        violations = []
        
        for metric_name, threshold in self.thresholds.items():
            current_value = self.get_average(metric_name, timedelta(minutes=5))
            if current_value is not None and current_value > threshold:
                violations.append({
                    'metric': metric_name,
                    'current_value': current_value,
                    'threshold': threshold,
                    'severity': 'critical' if current_value > threshold * 1.2 else 'warning'
                })
        
        return violations

class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.alerts: Dict[str, Alert] = {}
        self.active_alerts: Dict[str, datetime] = {}
        self.logger = structlog.get_logger(__name__)
        
        # Notification channels
        self.notification_channels = {
            'slack': self._send_slack_notification,
            'email': self._send_email_notification,
            'webhook': self._send_webhook_notification
        }
    
    def register_alert(self, alert: Alert):
        """Register a new alert"""
        self.alerts[alert.id] = alert
        self.logger.info(f"Registered alert: {alert.name}")
    
    async def check_alert_condition(self, alert_id: str, current_value: float) -> bool:
        """Check if alert condition is met"""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        if not alert.enabled:
            return False
        
        # Simple threshold check (can be extended for complex conditions)
        condition_met = current_value > alert.threshold
        
        if condition_met:
            # Check if alert should be triggered (duration check)
            if alert_id not in self.active_alerts:
                self.active_alerts[alert_id] = datetime.utcnow()
                return False
            
            # Check if duration threshold is met
            duration = (datetime.utcnow() - self.active_alerts[alert_id]).total_seconds()
            if duration >= alert.duration:
                return True
        else:
            # Clear active alert if condition is no longer met
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
        
        return False
    
    async def trigger_alert(self, alert_id: str, current_value: float, context: Dict[str, Any] = None):
        """Trigger an alert"""
        if alert_id not in self.alerts:
            return
        
        alert = self.alerts[alert_id]
        
        alert_data = {
            'alert_id': alert_id,
            'name': alert.name,
            'description': alert.description,
            'severity': alert.severity.value,
            'component': alert.component.value,
            'current_value': current_value,
            'threshold': alert.threshold,
            'timestamp': datetime.utcnow().isoformat(),
            'context': context or {}
        }
        
        # Store alert in Redis
        await self.redis.lpush('active_alerts', json.dumps(alert_data))
        await self.redis.ltrim('active_alerts', 0, 999)  # Keep last 1000 alerts
        
        # Send notifications
        await self._send_notifications(alert, alert_data)
        
        self.logger.warning(f"Alert triggered: {alert.name}", extra=alert_data)
    
    async def _send_notifications(self, alert: Alert, alert_data: Dict[str, Any]):
        """Send notifications for an alert"""
        # Determine notification channels based on severity
        channels = []
        
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.ERROR]:
            channels.extend(['slack', 'email'])
        elif alert.severity == AlertSeverity.WARNING:
            channels.append('slack')
        
        for channel in channels:
            if channel in self.notification_channels:
                try:
                    await self.notification_channels[channel](alert_data)
                except Exception as e:
                    self.logger.error(f"Failed to send {channel} notification: {e}")
    
    async def _send_slack_notification(self, alert_data: Dict[str, Any]):
        """Send Slack notification"""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return
        
        color = {
            'critical': '#FF0000',
            'error': '#FF6600',
            'warning': '#FFCC00',
            'info': '#0099CC'
        }.get(alert_data['severity'], '#808080')
        
        payload = {
            'attachments': [{
                'color': color,
                'title': f"🚨 {alert_data['name']}",
                'text': alert_data['description'],
                'fields': [
                    {
                        'title': 'Severity',
                        'value': alert_data['severity'].upper(),
                        'short': True
                    },
                    {
                        'title': 'Component',
                        'value': alert_data['component'],
                        'short': True
                    },
                    {
                        'title': 'Current Value',
                        'value': str(alert_data['current_value']),
                        'short': True
                    },
                    {
                        'title': 'Threshold',
                        'value': str(alert_data['threshold']),
                        'short': True
                    }
                ],
                'timestamp': alert_data['timestamp']
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=payload)
    
    async def _send_email_notification(self, alert_data: Dict[str, Any]):
        """Send email notification"""
        # Implementation depends on email service (SendGrid, SES, etc.)
        pass
    
    async def _send_webhook_notification(self, alert_data: Dict[str, Any]):
        """Send webhook notification"""
        webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        if not webhook_url:
            return
        
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=alert_data)

class HealthChecker:
    """Perform health checks on system components"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.logger = structlog.get_logger(__name__)
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a health check"""
        self.health_checks[health_check.name] = health_check
        self.health_status[health_check.name] = {
            'status': 'unknown',
            'last_check': None,
            'message': '',
            'response_time': 0
        }
    
    async def run_health_check(self, check_name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if check_name not in self.health_checks:
            return {'status': 'error', 'message': 'Health check not found'}
        
        health_check = self.health_checks[check_name]
        if not health_check.enabled:
            return {'status': 'disabled', 'message': 'Health check disabled'}
        
        start_time = time.time()
        
        try:
            # Run health check with timeout
            result = await asyncio.wait_for(
                health_check.check_function(),
                timeout=health_check.timeout
            )
            
            response_time = time.time() - start_time
            
            status = {
                'status': 'healthy' if result.get('healthy', False) else 'unhealthy',
                'last_check': datetime.utcnow(),
                'message': result.get('message', ''),
                'response_time': response_time,
                'details': result.get('details', {})
            }
            
            self.health_status[check_name] = status
            return status
        
        except asyncio.TimeoutError:
            status = {
                'status': 'timeout',
                'last_check': datetime.utcnow(),
                'message': f'Health check timed out after {health_check.timeout}s',
                'response_time': health_check.timeout
            }
            self.health_status[check_name] = status
            return status
        
        except Exception as e:
            status = {
                'status': 'error',
                'last_check': datetime.utcnow(),
                'message': str(e),
                'response_time': time.time() - start_time
            }
            self.health_status[check_name] = status
            return status
    
    async def run_all_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all registered health checks"""
        results = {}
        
        for check_name in self.health_checks:
            results[check_name] = await self.run_health_check(check_name)
        
        return results
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self.health_status:
            return {'status': 'unknown', 'message': 'No health checks configured'}
        
        statuses = [status['status'] for status in self.health_status.values()]
        
        if 'error' in statuses or 'timeout' in statuses:
            overall_status = 'unhealthy'
        elif 'unhealthy' in statuses:
            overall_status = 'degraded'
        elif all(status == 'healthy' for status in statuses):
            overall_status = 'healthy'
        else:
            overall_status = 'unknown'
        
        return {
            'status': overall_status,
            'checks': self.health_status,
            'timestamp': datetime.utcnow().isoformat()
        }

class LogAggregator:
    """Aggregate and analyze logs"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)
        
        # Log patterns for analysis
        self.error_patterns = [
            r'ERROR',
            r'CRITICAL',
            r'FATAL',
            r'Exception',
            r'Traceback',
            r'500 Internal Server Error',
            r'Connection refused',
            r'Timeout'
        ]
    
    async def ingest_log(self, log_entry: Dict[str, Any]):
        """Ingest a log entry"""
        # Add timestamp if not present
        if 'timestamp' not in log_entry:
            log_entry['timestamp'] = datetime.utcnow().isoformat()
        
        # Store in Redis
        await self.redis.lpush('logs', json.dumps(log_entry))
        await self.redis.ltrim('logs', 0, 99999)  # Keep last 100k logs
        
        # Analyze for errors
        await self._analyze_log_entry(log_entry)
    
    async def _analyze_log_entry(self, log_entry: Dict[str, Any]):
        """Analyze log entry for patterns"""
        message = log_entry.get('message', '')
        level = log_entry.get('level', '').upper()
        
        # Check for error patterns
        if level in ['ERROR', 'CRITICAL', 'FATAL']:
            await self._handle_error_log(log_entry)
        
        # Check for specific patterns
        for pattern in self.error_patterns:
            if pattern.lower() in message.lower():
                await self._handle_pattern_match(log_entry, pattern)
    
    async def _handle_error_log(self, log_entry: Dict[str, Any]):
        """Handle error log entry"""
        error_key = f"errors:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        await self.redis.incr(error_key)
        await self.redis.expire(error_key, 86400 * 7)  # Keep for 7 days
    
    async def _handle_pattern_match(self, log_entry: Dict[str, Any], pattern: str):
        """Handle pattern match in log"""
        pattern_key = f"pattern:{pattern}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        await self.redis.incr(pattern_key)
        await self.redis.expire(pattern_key, 86400 * 7)  # Keep for 7 days
    
    async def get_error_rate(self, time_window: timedelta = timedelta(hours=1)) -> float:
        """Get error rate for a time window"""
        now = datetime.utcnow()
        start_time = now - time_window
        
        total_logs = 0
        error_logs = 0
        
        # Count logs by hour
        current_time = start_time.replace(minute=0, second=0, microsecond=0)
        while current_time <= now:
            hour_key = current_time.strftime('%Y-%m-%d-%H')
            
            # Get total logs (approximate)
            total_key = f"logs:{hour_key}"
            hour_total = await self.redis.get(total_key) or 0
            total_logs += int(hour_total)
            
            # Get error logs
            error_key = f"errors:{hour_key}"
            hour_errors = await self.redis.get(error_key) or 0
            error_logs += int(hour_errors)
            
            current_time += timedelta(hours=1)
        
        if total_logs == 0:
            return 0.0
        
        return error_logs / total_logs

class TracingManager:
    """Manage distributed tracing"""
    
    def __init__(self, service_name: str = "mcp-system"):
        self.service_name = service_name
        
        # Configure OpenTelemetry
        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(__name__)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv('JAEGER_AGENT_HOST', 'localhost'),
            agent_port=int(os.getenv('JAEGER_AGENT_PORT', '6831')),
        )
        
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
    
    def start_span(self, name: str, attributes: Dict[str, Any] = None):
        """Start a new span"""
        span = self.tracer.start_span(name)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        return span
    
    def trace_function(self, name: str = None):
        """Decorator to trace function execution"""
        def decorator(func):
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            if asyncio.iscoroutinefunction(func):
                async def async_wrapper(*args, **kwargs):
                    with self.start_span(span_name) as span:
                        try:
                            result = await func(*args, **kwargs)
                            span.set_attribute("success", True)
                            return result
                        except Exception as e:
                            span.set_attribute("success", False)
                            span.set_attribute("error", str(e))
                            raise
                return async_wrapper
            else:
                def sync_wrapper(*args, **kwargs):
                    with self.start_span(span_name) as span:
                        try:
                            result = func(*args, **kwargs)
                            span.set_attribute("success", True)
                            return result
                        except Exception as e:
                            span.set_attribute("success", False)
                            span.set_attribute("error", str(e))
                            raise
                return sync_wrapper
        
        return decorator

# Health check implementations
async def database_health_check() -> Dict[str, Any]:
    """Check database health"""
    try:
        # Example PostgreSQL health check
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await conn.execute('SELECT 1')
        await conn.close()
        
        return {
            'healthy': True,
            'message': 'Database connection successful'
        }
    except Exception as e:
        return {
            'healthy': False,
            'message': f'Database connection failed: {e}'
        }

async def redis_health_check() -> Dict[str, Any]:
    """Check Redis health"""
    try:
        redis = await aioredis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        await redis.ping()
        await redis.close()
        
        return {
            'healthy': True,
            'message': 'Redis connection successful'
        }
    except Exception as e:
        return {
            'healthy': False,
            'message': f'Redis connection failed: {e}'
        }

async def external_api_health_check() -> Dict[str, Any]:
    """Check external API health"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.example.com/health', timeout=5) as response:
                if response.status == 200:
                    return {
                        'healthy': True,
                        'message': 'External API is healthy'
                    }
                else:
                    return {
                        'healthy': False,
                        'message': f'External API returned status {response.status}'
                    }
    except Exception as e:
        return {
            'healthy': False,
            'message': f'External API check failed: {e}'
        }

# Example monitoring setup
async def setup_monitoring():
    """Setup comprehensive monitoring"""
    
    # Initialize components
    metrics_collector = MetricsCollector()
    performance_monitor = PerformanceMonitor()
    
    # Redis for alerts and logs
    redis_client = await aioredis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
    
    alert_manager = AlertManager(redis_client)
    health_checker = HealthChecker()
    log_aggregator = LogAggregator(redis_client)
    tracing_manager = TracingManager()
    
    # Register alerts
    alerts = [
        Alert(
            id="high_response_time",
            name="High Response Time",
            description="API response time is above threshold",
            severity=AlertSeverity.WARNING,
            component=MonitoringComponent.API,
            condition="avg_response_time > threshold",
            threshold=2.0,
            duration=300
        ),
        Alert(
            id="high_error_rate",
            name="High Error Rate",
            description="Error rate is above threshold",
            severity=AlertSeverity.CRITICAL,
            component=MonitoringComponent.API,
            condition="error_rate > threshold",
            threshold=0.05,
            duration=180
        ),
        Alert(
            id="high_cpu_usage",
            name="High CPU Usage",
            description="System CPU usage is above threshold",
            severity=AlertSeverity.WARNING,
            component=MonitoringComponent.SYSTEM,
            condition="cpu_usage > threshold",
            threshold=80.0,
            duration=600
        )
    ]
    
    for alert in alerts:
        alert_manager.register_alert(alert)
    
    # Register health checks
    health_checks = [
        HealthCheck(
            name="database",
            component=MonitoringComponent.DATABASE,
            check_function=database_health_check,
            interval=30
        ),
        HealthCheck(
            name="redis",
            component=MonitoringComponent.CACHE,
            check_function=redis_health_check,
            interval=30
        ),
        HealthCheck(
            name="external_api",
            component=MonitoringComponent.EXTERNAL_SERVICE,
            check_function=external_api_health_check,
            interval=60
        )
    ]
    
    for health_check in health_checks:
        health_checker.register_health_check(health_check)
    
    return {
        'metrics': metrics_collector,
        'performance': performance_monitor,
        'alerts': alert_manager,
        'health': health_checker,
        'logs': log_aggregator,
        'tracing': tracing_manager
    }

if __name__ == "__main__":
    async def main():
        # Setup monitoring
        monitoring = await setup_monitoring()
        
        # Example: Record metrics
        monitoring['metrics'].record_http_request(
            method="GET",
            endpoint="/api/users",
            status_code=200,
            duration=0.5,
            request_size=1024,
            response_size=2048
        )
        
        # Example: Check health
        health_status = await monitoring['health'].run_all_health_checks()
        print(f"Health status: {health_status}")
        
        # Example: Update system metrics
        monitoring['metrics'].update_system_metrics()
        
        # Example: Record performance metric
        monitoring['performance'].record_metric('response_time', 1.5)
        
        # Example: Check for anomalies
        anomalies = monitoring['performance'].detect_anomalies('response_time')
        print(f"Anomalies detected: {len(anomalies)}")
    
    asyncio.run(main())

