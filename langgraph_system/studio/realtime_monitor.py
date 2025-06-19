"""
Dashboard de Monitoreo en Tiempo Real para LangGraph Studio
Proporciona visualización de métricas, sesiones y rendimiento del sistema MCP
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import statistics
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """Métricas del sistema en tiempo real"""
    timestamp: str
    active_sessions: int
    total_requests: int
    avg_response_time: float
    success_rate: float
    error_rate: float
    memory_usage: float
    cpu_usage: float
    
@dataclass
class ModelMetrics:
    """Métricas específicas por modelo"""
    model_name: str
    total_calls: int
    avg_response_time: float
    avg_tokens_per_second: float
    success_rate: float
    avg_quality_score: float
    total_tokens: int
    
@dataclass
class ContradictionMetrics:
    """Métricas de contradicción explícita"""
    total_contradictions: int
    avg_effectiveness: float
    success_rate_after_contradiction: float
    most_effective_intensity: str
    contradiction_triggers: Dict[str, int]

class RealtimeMonitor:
    """Monitor en tiempo real para el sistema MCP"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.session_metrics = {}
        self.model_metrics = defaultdict(lambda: {
            "calls": 0,
            "response_times": [],
            "tokens": [],
            "scores": [],
            "successes": 0
        })
        self.contradiction_data = {
            "total": 0,
            "effectiveness_scores": [],
            "success_after": 0,
            "triggers": defaultdict(int),
            "intensities": defaultdict(int)
        }
        self.alerts = []
        self.is_monitoring = False
        
    def start_monitoring(self):
        """Inicia el monitoreo en tiempo real"""
        self.is_monitoring = True
        logger.info("🔍 Real-time monitoring started")
        
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.is_monitoring = False
        logger.info("⏹️ Real-time monitoring stopped")
        
    def record_session_start(self, session_id: str, metadata: Dict[str, Any]):
        """Registra inicio de sesión"""
        self.session_metrics[session_id] = {
            "start_time": datetime.now(),
            "metadata": metadata,
            "requests": 0,
            "errors": 0,
            "total_tokens": 0,
            "models_used": set(),
            "contradiction_applied": False,
            "final_score": None,
            "status": "active"
        }
        
    def record_session_end(self, session_id: str, final_score: float, success: bool):
        """Registra fin de sesión"""
        if session_id in self.session_metrics:
            session = self.session_metrics[session_id]
            session["end_time"] = datetime.now()
            session["final_score"] = final_score
            session["success"] = success
            session["status"] = "completed"
            session["duration"] = (session["end_time"] - session["start_time"]).total_seconds()
            
    def record_model_call(self, model_name: str, response_time: float, 
                         tokens: int, quality_score: float, success: bool):
        """Registra llamada a modelo"""
        metrics = self.model_metrics[model_name]
        metrics["calls"] += 1
        metrics["response_times"].append(response_time)
        metrics["tokens"].append(tokens)
        metrics["scores"].append(quality_score)
        if success:
            metrics["successes"] += 1
            
    def record_contradiction(self, session_id: str, trigger: str, intensity: str, 
                           effectiveness: float, success_after: bool):
        """Registra aplicación de contradicción"""
        self.contradiction_data["total"] += 1
        self.contradiction_data["effectiveness_scores"].append(effectiveness)
        self.contradiction_data["triggers"][trigger] += 1
        self.contradiction_data["intensities"][intensity] += 1
        
        if success_after:
            self.contradiction_data["success_after"] += 1
            
        if session_id in self.session_metrics:
            self.session_metrics[session_id]["contradiction_applied"] = True
            
    def get_system_metrics(self) -> SystemMetrics:
        """Obtiene métricas actuales del sistema"""
        now = datetime.now()
        
        # Calcular métricas de sesiones activas
        active_sessions = len([s for s in self.session_metrics.values() 
                              if s["status"] == "active"])
        
        total_requests = sum(s["requests"] for s in self.session_metrics.values())
        
        # Calcular tiempos de respuesta promedio
        all_response_times = []
        for model_data in self.model_metrics.values():
            all_response_times.extend(model_data["response_times"])
        
        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        
        # Calcular tasas de éxito y error
        total_calls = sum(m["calls"] for m in self.model_metrics.values())
        total_successes = sum(m["successes"] for m in self.model_metrics.values())
        
        success_rate = (total_successes / total_calls) if total_calls > 0 else 1.0
        error_rate = 1.0 - success_rate
        
        # Métricas de sistema (simuladas por ahora)
        memory_usage = 0.0  # TODO: Implementar monitoreo real
        cpu_usage = 0.0     # TODO: Implementar monitoreo real
        
        metrics = SystemMetrics(
            timestamp=now.isoformat(),
            active_sessions=active_sessions,
            total_requests=total_requests,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            error_rate=error_rate,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage
        )
        
        # Agregar a historial
        self.metrics_history.append(metrics)
        
        # Verificar alertas
        self._check_alerts(metrics)
        
        return metrics
        
    def get_model_metrics(self) -> List[ModelMetrics]:
        """Obtiene métricas por modelo"""
        model_metrics_list = []
        
        for model_name, data in self.model_metrics.items():
            if data["calls"] > 0:
                avg_response_time = statistics.mean(data["response_times"])
                avg_tokens = statistics.mean(data["tokens"])
                avg_tokens_per_second = avg_tokens / (avg_response_time / 1000) if avg_response_time > 0 else 0
                success_rate = data["successes"] / data["calls"]
                avg_quality_score = statistics.mean(data["scores"])
                total_tokens = sum(data["tokens"])
                
                metrics = ModelMetrics(
                    model_name=model_name,
                    total_calls=data["calls"],
                    avg_response_time=avg_response_time,
                    avg_tokens_per_second=avg_tokens_per_second,
                    success_rate=success_rate,
                    avg_quality_score=avg_quality_score,
                    total_tokens=total_tokens
                )
                model_metrics_list.append(metrics)
                
        return model_metrics_list
        
    def get_contradiction_metrics(self) -> ContradictionMetrics:
        """Obtiene métricas de contradicción"""
        data = self.contradiction_data
        
        avg_effectiveness = (statistics.mean(data["effectiveness_scores"]) 
                           if data["effectiveness_scores"] else 0.0)
        
        success_rate_after = (data["success_after"] / data["total"] 
                            if data["total"] > 0 else 0.0)
        
        # Encontrar intensidad más efectiva
        most_effective_intensity = max(data["intensities"].items(), 
                                     key=lambda x: x[1])[0] if data["intensities"] else "none"
        
        return ContradictionMetrics(
            total_contradictions=data["total"],
            avg_effectiveness=avg_effectiveness,
            success_rate_after_contradiction=success_rate_after,
            most_effective_intensity=most_effective_intensity,
            contradiction_triggers=dict(data["triggers"])
        )
        
    def get_session_analytics(self, time_window: int = 3600) -> Dict[str, Any]:
        """Obtiene analytics de sesiones en ventana de tiempo"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        recent_sessions = [
            s for s in self.session_metrics.values()
            if s["start_time"] >= cutoff_time
        ]
        
        if not recent_sessions:
            return {"message": "No recent sessions"}
            
        # Calcular estadísticas
        total_sessions = len(recent_sessions)
        completed_sessions = [s for s in recent_sessions if s["status"] == "completed"]
        successful_sessions = [s for s in completed_sessions if s.get("success", False)]
        
        avg_duration = statistics.mean([s.get("duration", 0) for s in completed_sessions]) if completed_sessions else 0
        avg_score = statistics.mean([s.get("final_score", 0) for s in completed_sessions if s.get("final_score")]) if completed_sessions else 0
        
        # Modelos más usados
        model_usage = defaultdict(int)
        for session in recent_sessions:
            for model in session.get("models_used", []):
                model_usage[model] += 1
                
        # Patrones de contradicción
        contradiction_sessions = [s for s in recent_sessions if s.get("contradiction_applied", False)]
        contradiction_rate = len(contradiction_sessions) / total_sessions if total_sessions > 0 else 0
        
        return {
            "time_window_hours": time_window / 3600,
            "total_sessions": total_sessions,
            "completed_sessions": len(completed_sessions),
            "success_rate": len(successful_sessions) / len(completed_sessions) if completed_sessions else 0,
            "avg_duration_seconds": avg_duration,
            "avg_quality_score": avg_score,
            "contradiction_rate": contradiction_rate,
            "most_used_models": dict(sorted(model_usage.items(), key=lambda x: x[1], reverse=True)[:5]),
            "active_sessions": total_sessions - len(completed_sessions)
        }
        
    def _check_alerts(self, metrics: SystemMetrics):
        """Verifica condiciones de alerta"""
        alerts = []
        
        # Alerta por alta tasa de error
        if metrics.error_rate > 0.1:
            alerts.append({
                "type": "error_rate",
                "severity": "warning",
                "message": f"High error rate: {metrics.error_rate:.2%}",
                "timestamp": metrics.timestamp
            })
            
        # Alerta por tiempo de respuesta alto
        if metrics.avg_response_time > 30000:  # 30 segundos
            alerts.append({
                "type": "response_time",
                "severity": "warning", 
                "message": f"High response time: {metrics.avg_response_time:.0f}ms",
                "timestamp": metrics.timestamp
            })
            
        # Alerta por muchas sesiones activas
        if metrics.active_sessions > 10:
            alerts.append({
                "type": "high_load",
                "severity": "info",
                "message": f"High number of active sessions: {metrics.active_sessions}",
                "timestamp": metrics.timestamp
            })
            
        # Agregar nuevas alertas
        self.alerts.extend(alerts)
        
        # Mantener solo las últimas 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
            
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene alertas activas"""
        if severity:
            return [a for a in self.alerts if a["severity"] == severity]
        return self.alerts.copy()
        
    def clear_alerts(self):
        """Limpia todas las alertas"""
        self.alerts.clear()
        
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene tendencias de rendimiento"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filtrar métricas recientes
        recent_metrics = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if len(recent_metrics) < 2:
            return {"message": "Insufficient data for trends"}
            
        # Calcular tendencias
        response_times = [m.avg_response_time for m in recent_metrics]
        success_rates = [m.success_rate for m in recent_metrics]
        active_sessions = [m.active_sessions for m in recent_metrics]
        
        return {
            "time_window_hours": hours,
            "data_points": len(recent_metrics),
            "response_time_trend": {
                "current": response_times[-1],
                "avg": statistics.mean(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "trend": "improving" if response_times[-1] < response_times[0] else "degrading"
            },
            "success_rate_trend": {
                "current": success_rates[-1],
                "avg": statistics.mean(success_rates),
                "min": min(success_rates),
                "max": max(success_rates),
                "trend": "improving" if success_rates[-1] > success_rates[0] else "degrading"
            },
            "load_trend": {
                "current": active_sessions[-1],
                "avg": statistics.mean(active_sessions),
                "min": min(active_sessions),
                "max": max(active_sessions),
                "trend": "increasing" if active_sessions[-1] > active_sessions[0] else "decreasing"
            }
        }
        
    def export_metrics_report(self, format: str = "json") -> str:
        """Exporta reporte completo de métricas"""
        system_metrics = self.get_system_metrics()
        model_metrics = self.get_model_metrics()
        contradiction_metrics = self.get_contradiction_metrics()
        session_analytics = self.get_session_analytics()
        performance_trends = self.get_performance_trends()
        
        report = {
            "export_timestamp": datetime.now().isoformat(),
            "system_metrics": asdict(system_metrics),
            "model_metrics": [asdict(m) for m in model_metrics],
            "contradiction_metrics": asdict(contradiction_metrics),
            "session_analytics": session_analytics,
            "performance_trends": performance_trends,
            "alerts": self.get_alerts(),
            "metadata": {
                "total_sessions_tracked": len(self.session_metrics),
                "metrics_history_size": len(self.metrics_history),
                "monitoring_active": self.is_monitoring
            }
        }
        
        if format == "json":
            return json.dumps(report, indent=2)
        else:
            return json.dumps(report, indent=2)  # Por ahora solo JSON

# Instancia global del monitor
realtime_monitor = RealtimeMonitor()

def get_realtime_monitor() -> RealtimeMonitor:
    """Obtiene instancia del monitor en tiempo real"""
    return realtime_monitor

def start_monitoring():
    """Inicia monitoreo en tiempo real"""
    realtime_monitor.start_monitoring()

def stop_monitoring():
    """Detiene monitoreo en tiempo real"""
    realtime_monitor.stop_monitoring()

