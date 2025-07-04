#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - ContextObservatory
Enterprise-grade observability and monitoring for semantic coherence systems
"""

import asyncio
import json
import yaml
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import psutil
import threading
import time
from collections import defaultdict, deque
import numpy as np
from semantic_coherence_bus import get_semantic_bus, SemanticMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(str, Enum):
    """Types of metrics being tracked"""
    PERFORMANCE = "performance"
    COHERENCE = "coherence"
    USAGE = "usage"
    ERROR = "error"
    SYSTEM = "system"

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: str
    value: float
    metric_name: str
    metric_type: MetricType
    service: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Alert:
    """System alert with details"""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: str
    source_service: str
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    resolved: bool = False
    resolution_time: Optional[str] = None

class HealthCheckRequest(BaseModel):
    """Request for health check"""
    services: List[str] = Field(default_factory=list)
    include_details: bool = True
    timeout_seconds: int = 30

class MetricsRequest(BaseModel):
    """Request for metrics data"""
    metric_names: List[str] = Field(default_factory=list)
    time_range_minutes: int = 60
    aggregation: str = "avg"  # avg, min, max, sum
    service_filter: Optional[str] = None

class AlertsRequest(BaseModel):
    """Request for alerts"""
    severity_filter: Optional[AlertSeverity] = None
    time_range_hours: int = 24
    resolved_filter: Optional[bool] = None
    service_filter: Optional[str] = None

class DashboardRequest(BaseModel):
    """Request for dashboard data"""
    dashboard_type: str = "overview"  # overview, performance, coherence, errors
    refresh_interval_seconds: int = 30
    include_predictions: bool = False

class ContextObservatory:
    """
    Enterprise-grade observability platform for ContextBuilderAgent ecosystem
    Provides monitoring, alerting, metrics collection, and real-time dashboards
    """
    
    def __init__(self):
        self.app = FastAPI(title="ContextObservatory", version="2.0.0")
        self.semantic_bus = None
        
        # Data storage
        self.metrics_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.alerts_store: List[Alert] = []
        self.health_cache: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: List[WebSocket] = []
        
        # Configuration
        self.service_endpoints = {
            "orchestrator": "http://localhost:8025",
            "drift_detector": "http://localhost:8020",
            "contradiction_resolver": "http://localhost:8021",
            "belief_reviser": "http://localhost:8022",
            "utility_predictor": "http://localhost:8023",
            "memory_tuner": "http://localhost:8026",
            "prompt_assembler": "http://localhost:8027"
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            "response_time": {"warning": 5000, "error": 10000, "critical": 20000},  # milliseconds
            "coherence_score": {"warning": 0.6, "error": 0.4, "critical": 0.2},
            "error_rate": {"warning": 0.05, "error": 0.1, "critical": 0.2},  # percentage
            "memory_usage": {"warning": 80, "error": 90, "critical": 95},  # percentage
            "cpu_usage": {"warning": 80, "error": 90, "critical": 95}  # percentage
        }
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests_monitored": 0,
            "alerts_generated": 0,
            "services_monitored": len(self.service_endpoints),
            "uptime_start": datetime.utcnow().isoformat() + "Z",
            "last_health_check": None
        }
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Setup routes and initialize
        self._setup_routes()
        
        # Add startup event handler
        @self.app.on_event("startup")
        async def startup_event():
            await self._initialize_system()
        
        # Add shutdown event handler
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self._cleanup_system()
    
    def _setup_routes(self):
        """Setup FastAPI routes for observatory"""
        
        @self.app.get("/health_check")
        async def comprehensive_health_check(request: HealthCheckRequest = HealthCheckRequest()):
            """Comprehensive health check across all services"""
            try:
                result = await self._perform_health_check(
                    request.services or list(self.service_endpoints.keys()),
                    request.include_details,
                    request.timeout_seconds
                )
                return result
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def get_metrics(request: MetricsRequest = MetricsRequest()):
            """Get aggregated metrics data"""
            try:
                result = await self._get_metrics_data(
                    request.metric_names,
                    request.time_range_minutes,
                    request.aggregation,
                    request.service_filter
                )
                return result
            except Exception as e:
                logger.error(f"Metrics retrieval failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/alerts")
        async def get_alerts(request: AlertsRequest = AlertsRequest()):
            """Get system alerts"""
            try:
                result = await self._get_alerts(
                    request.severity_filter,
                    request.time_range_hours,
                    request.resolved_filter,
                    request.service_filter
                )
                return result
            except Exception as e:
                logger.error(f"Alerts retrieval failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/dashboard/{dashboard_type}")
        async def get_dashboard_data(dashboard_type: str, request: DashboardRequest = DashboardRequest()):
            """Get dashboard data"""
            try:
                request.dashboard_type = dashboard_type
                result = await self._generate_dashboard_data(request)
                return result
            except Exception as e:
                logger.error(f"Dashboard generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/realtime")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time monitoring"""
            await self._handle_websocket_connection(websocket)
        
        @self.app.post("/start_monitoring")
        async def start_monitoring():
            """Start background monitoring"""
            try:
                await self._start_background_monitoring()
                return {"status": "monitoring_started", "timestamp": datetime.utcnow().isoformat() + "Z"}
            except Exception as e:
                logger.error(f"Failed to start monitoring: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stop_monitoring")
        async def stop_monitoring():
            """Stop background monitoring"""
            try:
                await self._stop_background_monitoring()
                return {"status": "monitoring_stopped", "timestamp": datetime.utcnow().isoformat() + "Z"}
            except Exception as e:
                logger.error(f"Failed to stop monitoring: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/system_overview")
        async def get_system_overview():
            """Get comprehensive system overview"""
            try:
                result = await self._generate_system_overview()
                return result
            except Exception as e:
                logger.error(f"System overview generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/alert/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolve a specific alert"""
            try:
                result = await self._resolve_alert(alert_id)
                return result
            except Exception as e:
                logger.error(f"Alert resolution failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/performance_trends")
        async def get_performance_trends():
            """Get performance trends and predictions"""
            try:
                result = await self._analyze_performance_trends()
                return result
            except Exception as e:
                logger.error(f"Performance trend analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/coherence_analytics")
        async def get_coherence_analytics():
            """Get semantic coherence analytics"""
            try:
                result = await self._analyze_semantic_coherence()
                return result
            except Exception as e:
                logger.error(f"Coherence analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Observatory health check"""
            try:
                return {
                    "status": "healthy",
                    "service": "ContextObservatory",
                    "version": "2.0.0",
                    "monitoring_active": self.monitoring_active,
                    "services_monitored": len(self.service_endpoints),
                    "alerts_count": len([a for a in self.alerts_store if not a.resolved]),
                    "websocket_connections": len(self.websocket_connections),
                    "performance_metrics": self.performance_metrics,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
    
    async def _initialize_system(self):
        """Initialize the ContextObservatory system"""
        try:
            # Initialize semantic bus connection
            self.semantic_bus = await get_semantic_bus()
            
            # Start background monitoring
            await self._start_background_monitoring()
            
            # Create initial system metrics
            await self._initialize_metrics()
            
            logger.info("ContextObservatory initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ContextObservatory: {e}")
    
    async def _cleanup_system(self):
        """Cleanup system resources"""
        try:
            await self._stop_background_monitoring()
            for websocket in self.websocket_connections:
                await websocket.close()
            logger.info("ContextObservatory cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def _perform_health_check(self, services: List[str], include_details: bool, 
                                   timeout_seconds: int) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        
        health_results = {
            "overall_status": "healthy",
            "services": {},
            "summary": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        async def check_service(service_name: str, endpoint: str):
            try:
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{endpoint}/health", timeout=timeout_seconds) as response:
                        response_time = (time.time() - start_time) * 1000  # milliseconds
                        
                        if response.status == 200:
                            data = await response.json()
                            status = "healthy"
                            
                            # Check response time thresholds
                            if response_time > self.alert_thresholds["response_time"]["critical"]:
                                status = "degraded"
                            elif response_time > self.alert_thresholds["response_time"]["warning"]:
                                status = "degraded"
                        else:
                            status = "unhealthy"
                            data = {"error": f"HTTP {response.status}"}
                        
                        service_health = {
                            "status": status,
                            "response_time_ms": response_time,
                            "endpoint": endpoint
                        }
                        
                        if include_details:
                            service_health["details"] = data
                        
                        health_results["services"][service_name] = service_health
                        health_results["summary"][status] += 1
                        
                        # Store metric
                        await self._store_metric(MetricPoint(
                            timestamp=datetime.utcnow().isoformat() + "Z",
                            value=response_time,
                            metric_name="response_time",
                            metric_type=MetricType.PERFORMANCE,
                            service=service_name
                        ))
                        
                        # Check for alerts
                        await self._check_response_time_alert(service_name, response_time)
                        
            except Exception as e:
                health_results["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "endpoint": endpoint
                }
                health_results["summary"]["unhealthy"] += 1
                
                # Generate alert for unhealthy service
                await self._generate_alert(
                    AlertSeverity.ERROR,
                    f"Service {service_name} Unhealthy",
                    f"Service {service_name} failed health check: {str(e)}",
                    service_name
                )
        
        # Check all requested services
        tasks = []
        for service_name in services:
            if service_name in self.service_endpoints:
                endpoint = self.service_endpoints[service_name]
                tasks.append(check_service(service_name, endpoint))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Determine overall status
        if health_results["summary"]["unhealthy"] > 0:
            health_results["overall_status"] = "unhealthy"
        elif health_results["summary"]["degraded"] > 0:
            health_results["overall_status"] = "degraded"
        
        # Update performance metrics
        self.performance_metrics["last_health_check"] = datetime.utcnow().isoformat() + "Z"
        self.health_cache = health_results
        
        return health_results
    
    async def _get_metrics_data(self, metric_names: List[str], time_range_minutes: int,
                               aggregation: str, service_filter: Optional[str]) -> Dict[str, Any]:
        """Get aggregated metrics data"""
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_range_minutes)
        result = {
            "metrics": {},
            "time_range_minutes": time_range_minutes,
            "aggregation": aggregation,
            "service_filter": service_filter,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # If no specific metrics requested, return all
        if not metric_names:
            metric_names = list(self.metrics_store.keys())
        
        for metric_name in metric_names:
            if metric_name in self.metrics_store:
                # Filter by time range and service
                filtered_points = []
                for point in self.metrics_store[metric_name]:
                    point_time = datetime.fromisoformat(point.timestamp.replace('Z', '+00:00'))
                    if point_time >= cutoff_time:
                        if not service_filter or point.service == service_filter:
                            filtered_points.append(point)
                
                if filtered_points:
                    values = [point.value for point in filtered_points]
                    
                    # Apply aggregation
                    if aggregation == "avg":
                        aggregated_value = np.mean(values)
                    elif aggregation == "min":
                        aggregated_value = np.min(values)
                    elif aggregation == "max":
                        aggregated_value = np.max(values)
                    elif aggregation == "sum":
                        aggregated_value = np.sum(values)
                    else:
                        aggregated_value = np.mean(values)  # Default to average
                    
                    result["metrics"][metric_name] = {
                        "aggregated_value": float(aggregated_value),
                        "data_points": len(filtered_points),
                        "raw_values": values[-10:],  # Last 10 values for trend
                        "latest_timestamp": filtered_points[-1].timestamp if filtered_points else None
                    }
        
        return result
    
    async def _get_alerts(self, severity_filter: Optional[AlertSeverity], time_range_hours: int,
                         resolved_filter: Optional[bool], service_filter: Optional[str]) -> Dict[str, Any]:
        """Get filtered alerts"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        filtered_alerts = []
        
        for alert in self.alerts_store:
            alert_time = datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00'))
            
            # Apply filters
            if alert_time < cutoff_time:
                continue
            if severity_filter and alert.severity != severity_filter:
                continue
            if resolved_filter is not None and alert.resolved != resolved_filter:
                continue
            if service_filter and alert.source_service != service_filter:
                continue
            
            filtered_alerts.append(asdict(alert))
        
        # Sort by timestamp (most recent first)
        filtered_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "alerts": filtered_alerts,
            "total_count": len(filtered_alerts),
            "filters_applied": {
                "severity": severity_filter,
                "time_range_hours": time_range_hours,
                "resolved": resolved_filter,
                "service": service_filter
            },
            "summary": {
                "critical": len([a for a in filtered_alerts if a["severity"] == "critical"]),
                "error": len([a for a in filtered_alerts if a["severity"] == "error"]),
                "warning": len([a for a in filtered_alerts if a["severity"] == "warning"]),
                "info": len([a for a in filtered_alerts if a["severity"] == "info"])
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    async def _generate_dashboard_data(self, request: DashboardRequest) -> Dict[str, Any]:
        """Generate dashboard data based on type"""
        
        dashboard_data = {
            "dashboard_type": request.dashboard_type,
            "refresh_interval": request.refresh_interval_seconds,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if request.dashboard_type == "overview":
            # System overview dashboard
            dashboard_data.update({
                "system_health": await self._get_system_health_summary(),
                "active_alerts": len([a for a in self.alerts_store if not a.resolved]),
                "services_status": await self._get_services_status_summary(),
                "key_metrics": await self._get_key_metrics_summary(),
                "recent_events": await self._get_recent_events()
            })
        
        elif request.dashboard_type == "performance":
            # Performance dashboard
            dashboard_data.update({
                "response_times": await self._get_response_time_metrics(),
                "throughput": await self._get_throughput_metrics(),
                "resource_usage": await self._get_resource_usage_metrics(),
                "error_rates": await self._get_error_rate_metrics()
            })
        
        elif request.dashboard_type == "coherence":
            # Semantic coherence dashboard
            dashboard_data.update({
                "coherence_scores": await self._get_coherence_metrics(),
                "mutation_success_rates": await self._get_mutation_metrics(),
                "validation_results": await self._get_validation_metrics(),
                "learning_progress": await self._get_learning_metrics()
            })
        
        elif request.dashboard_type == "errors":
            # Error tracking dashboard
            dashboard_data.update({
                "error_distribution": await self._get_error_distribution(),
                "failure_patterns": await self._get_failure_patterns(),
                "recovery_metrics": await self._get_recovery_metrics(),
                "incident_timeline": await self._get_incident_timeline()
            })
        
        if request.include_predictions:
            dashboard_data["predictions"] = await self._generate_predictions()
        
        return dashboard_data
    
    async def _handle_websocket_connection(self, websocket: WebSocket):
        """Handle WebSocket connection for real-time monitoring"""
        
        await websocket.accept()
        self.websocket_connections.append(websocket)
        
        try:
            while True:
                # Send real-time updates every 5 seconds
                update_data = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "system_status": await self._get_system_health_summary(),
                    "latest_metrics": await self._get_latest_metrics(),
                    "active_alerts_count": len([a for a in self.alerts_store if not a.resolved]),
                    "services_health": {
                        name: result.get("status", "unknown") 
                        for name, result in self.health_cache.get("services", {}).items()
                    }
                }
                
                await websocket.send_json(update_data)
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except WebSocketDisconnect:
            self.websocket_connections.remove(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)
    
    async def _start_background_monitoring(self):
        """Start background monitoring thread"""
        
        if not self.monitoring_active:
            self.monitoring_active = True
            
            def monitoring_loop():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                while self.monitoring_active:
                    try:
                        # Collect system metrics
                        loop.run_until_complete(self._collect_system_metrics())
                        
                        # Perform periodic health checks
                        loop.run_until_complete(self._periodic_health_check())
                        
                        # Check alert conditions
                        loop.run_until_complete(self._check_alert_conditions())
                        
                        # Clean old data
                        loop.run_until_complete(self._cleanup_old_data())
                        
                        time.sleep(30)  # Monitor every 30 seconds
                        
                    except Exception as e:
                        logger.error(f"Monitoring loop error: {e}")
                        time.sleep(30)
                
                loop.close()
            
            self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            logger.info("Background monitoring started")
    
    async def _stop_background_monitoring(self):
        """Stop background monitoring"""
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("Background monitoring stopped")
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            await self._store_metric(MetricPoint(
                timestamp=datetime.utcnow().isoformat() + "Z",
                value=cpu_percent,
                metric_name="cpu_usage",
                metric_type=MetricType.SYSTEM,
                service="system"
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            await self._store_metric(MetricPoint(
                timestamp=datetime.utcnow().isoformat() + "Z",
                value=memory.percent,
                metric_name="memory_usage",
                metric_type=MetricType.SYSTEM,
                service="system"
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self._store_metric(MetricPoint(
                timestamp=datetime.utcnow().isoformat() + "Z",
                value=disk_percent,
                metric_name="disk_usage",
                metric_type=MetricType.SYSTEM,
                service="system"
            ))
            
            # Check for resource alerts
            await self._check_resource_alerts(cpu_percent, memory.percent, disk_percent)
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
    
    async def _store_metric(self, metric: MetricPoint):
        """Store metric in local storage"""
        
        try:
            self.metrics_store[metric.metric_name].append(metric)
            self.performance_metrics["total_requests_monitored"] += 1
            
            # Publish to semantic bus for system-wide visibility
            if self.semantic_bus:
                metric_message = SemanticMessage(
                    message_id=f"metric_{int(datetime.utcnow().timestamp())}",
                    message_type="METRIC_UPDATE",
                    content={
                        "metric": asdict(metric),
                        "source": "ContextObservatory"
                    },
                    source="ContextObservatory",
                    timestamp=datetime.utcnow().isoformat() + "Z"
                )
                await self.semantic_bus.publish_semantic_message(metric_message)
        
        except Exception as e:
            logger.error(f"Metric storage failed: {e}")
    
    async def _generate_alert(self, severity: AlertSeverity, title: str, description: str,
                             source_service: str, metric_name: Optional[str] = None,
                             current_value: Optional[float] = None, threshold: Optional[float] = None):
        """Generate and store an alert"""
        
        try:
            alert = Alert(
                alert_id=f"alert_{int(datetime.utcnow().timestamp())}_{len(self.alerts_store)}",
                severity=severity,
                title=title,
                description=description,
                timestamp=datetime.utcnow().isoformat() + "Z",
                source_service=source_service,
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold,
                resolved=False
            )
            
            self.alerts_store.append(alert)
            self.performance_metrics["alerts_generated"] += 1
            
            # Send to WebSocket clients
            alert_data = {
                "type": "new_alert",
                "alert": asdict(alert),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            for websocket in self.websocket_connections[:]:  # Copy list to avoid modification during iteration
                try:
                    await websocket.send_json(alert_data)
                except Exception:
                    self.websocket_connections.remove(websocket)
            
            logger.warning(f"Alert generated: {title} - {description}")
            
        except Exception as e:
            logger.error(f"Alert generation failed: {e}")
    
    async def _check_response_time_alert(self, service_name: str, response_time: float):
        """Check if response time exceeds thresholds"""
        
        thresholds = self.alert_thresholds["response_time"]
        
        if response_time > thresholds["critical"]:
            await self._generate_alert(
                AlertSeverity.CRITICAL,
                f"{service_name} Critical Response Time",
                f"Response time {response_time:.2f}ms exceeds critical threshold {thresholds['critical']}ms",
                service_name,
                "response_time",
                response_time,
                thresholds["critical"]
            )
        elif response_time > thresholds["error"]:
            await self._generate_alert(
                AlertSeverity.ERROR,
                f"{service_name} High Response Time",
                f"Response time {response_time:.2f}ms exceeds error threshold {thresholds['error']}ms",
                service_name,
                "response_time",
                response_time,
                thresholds["error"]
            )
        elif response_time > thresholds["warning"]:
            await self._generate_alert(
                AlertSeverity.WARNING,
                f"{service_name} Elevated Response Time",
                f"Response time {response_time:.2f}ms exceeds warning threshold {thresholds['warning']}ms",
                service_name,
                "response_time",
                response_time,
                thresholds["warning"]
            )
    
    async def _check_resource_alerts(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Check system resource usage alerts"""
        
        # CPU alerts
        cpu_thresholds = self.alert_thresholds["cpu_usage"]
        if cpu_percent > cpu_thresholds["critical"]:
            await self._generate_alert(
                AlertSeverity.CRITICAL,
                "Critical CPU Usage",
                f"CPU usage {cpu_percent:.1f}% exceeds critical threshold {cpu_thresholds['critical']}%",
                "system",
                "cpu_usage",
                cpu_percent,
                cpu_thresholds["critical"]
            )
        
        # Memory alerts
        memory_thresholds = self.alert_thresholds["memory_usage"]
        if memory_percent > memory_thresholds["critical"]:
            await self._generate_alert(
                AlertSeverity.CRITICAL,
                "Critical Memory Usage",
                f"Memory usage {memory_percent:.1f}% exceeds critical threshold {memory_thresholds['critical']}%",
                "system",
                "memory_usage",
                memory_percent,
                memory_thresholds["critical"]
            )
    
    async def _initialize_metrics(self):
        """Initialize baseline metrics"""
        
        try:
            # System startup metrics
            await self._store_metric(MetricPoint(
                timestamp=datetime.utcnow().isoformat() + "Z",
                value=1.0,
                metric_name="system_startup",
                metric_type=MetricType.SYSTEM,
                service="observatory"
            ))
            
            logger.info("Baseline metrics initialized")
            
        except Exception as e:
            logger.error(f"Metrics initialization failed: {e}")
    
    async def _periodic_health_check(self):
        """Perform periodic health checks"""
        
        try:
            # Check all services
            await self._perform_health_check(
                list(self.service_endpoints.keys()),
                False,  # Don't include details for periodic checks
                10      # Shorter timeout for periodic checks
            )
            
        except Exception as e:
            logger.error(f"Periodic health check failed: {e}")
    
    async def _check_alert_conditions(self):
        """Check various alert conditions"""
        
        try:
            # Check for services that haven't reported metrics recently
            now = datetime.utcnow()
            for service_name in self.service_endpoints.keys():
                # Look for recent metrics from this service
                recent_metrics = False
                for metric_queue in self.metrics_store.values():
                    for metric in reversed(metric_queue):  # Check most recent first
                        if metric.service == service_name:
                            metric_time = datetime.fromisoformat(metric.timestamp.replace('Z', '+00:00'))
                            if (now - metric_time).total_seconds() < 300:  # 5 minutes
                                recent_metrics = True
                                break
                    if recent_metrics:
                        break
                
                if not recent_metrics:
                    await self._generate_alert(
                        AlertSeverity.WARNING,
                        f"{service_name} No Recent Metrics",
                        f"No metrics received from {service_name} in the last 5 minutes",
                        service_name
                    )
            
        except Exception as e:
            logger.error(f"Alert condition checking failed: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old metrics and resolved alerts"""
        
        try:
            # Clean old resolved alerts (keep for 7 days)
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            self.alerts_store = [
                alert for alert in self.alerts_store
                if not alert.resolved or 
                datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')) > cutoff_time
            ]
            
            # Metrics are automatically cleaned by deque maxlen
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
    
    # Additional helper methods for dashboard data
    async def _get_system_health_summary(self) -> str:
        """Get overall system health summary"""
        if self.health_cache:
            return self.health_cache.get("overall_status", "unknown")
        return "unknown"
    
    async def _get_services_status_summary(self) -> Dict[str, str]:
        """Get summary of service statuses"""
        if self.health_cache and "services" in self.health_cache:
            return {
                name: details.get("status", "unknown")
                for name, details in self.health_cache["services"].items()
            }
        return {}
    
    async def _get_key_metrics_summary(self) -> Dict[str, float]:
        """Get summary of key metrics"""
        summary = {}
        
        key_metrics = ["response_time", "cpu_usage", "memory_usage"]
        for metric_name in key_metrics:
            if metric_name in self.metrics_store and self.metrics_store[metric_name]:
                latest_metric = self.metrics_store[metric_name][-1]
                summary[metric_name] = latest_metric.value
        
        return summary
    
    async def _get_recent_events(self) -> List[Dict[str, Any]]:
        """Get recent system events"""
        recent_alerts = [
            asdict(alert) for alert in self.alerts_store[-5:]  # Last 5 alerts
        ]
        return recent_alerts
    
    async def _get_latest_metrics(self) -> Dict[str, float]:
        """Get latest metric values"""
        latest = {}
        for metric_name, metric_queue in self.metrics_store.items():
            if metric_queue:
                latest[metric_name] = metric_queue[-1].value
        return latest
    
    async def _resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        """Resolve a specific alert"""
        
        for alert in self.alerts_store:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_time = datetime.utcnow().isoformat() + "Z"
                
                return {
                    "success": True,
                    "alert_id": alert_id,
                    "resolution_time": alert.resolution_time,
                    "message": "Alert resolved successfully"
                }
        
        return {
            "success": False,
            "error": f"Alert {alert_id} not found"
        }
    
    # Placeholder methods for complex analytics (to be implemented)
    async def _generate_system_overview(self): return {"status": "not_implemented"}
    async def _analyze_performance_trends(self): return {"status": "not_implemented"}
    async def _analyze_semantic_coherence(self): return {"status": "not_implemented"}
    async def _get_response_time_metrics(self): return {"status": "not_implemented"}
    async def _get_throughput_metrics(self): return {"status": "not_implemented"}
    async def _get_resource_usage_metrics(self): return {"status": "not_implemented"}
    async def _get_error_rate_metrics(self): return {"status": "not_implemented"}
    async def _get_coherence_metrics(self): return {"status": "not_implemented"}
    async def _get_mutation_metrics(self): return {"status": "not_implemented"}
    async def _get_validation_metrics(self): return {"status": "not_implemented"}
    async def _get_learning_metrics(self): return {"status": "not_implemented"}
    async def _get_error_distribution(self): return {"status": "not_implemented"}
    async def _get_failure_patterns(self): return {"status": "not_implemented"}
    async def _get_recovery_metrics(self): return {"status": "not_implemented"}
    async def _get_incident_timeline(self): return {"status": "not_implemented"}
    async def _generate_predictions(self): return {"status": "not_implemented"}

# Global instance
context_observatory = ContextObservatory()

# FastAPI app instance for uvicorn
app = context_observatory.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8028)