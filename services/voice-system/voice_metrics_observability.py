#!/usr/bin/env python3
"""
Voice System Metrics and Observability Dashboard
Comprehensive monitoring system for MCP Voice Agents with Langwatch integration
"""

import asyncio
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

# Langwatch integration
try:
    import langwatch
    LANGWATCH_AVAILABLE = True
except ImportError:
    LANGWATCH_AVAILABLE = False

@dataclass
class VoiceMetric:
    """Voice interaction metric"""
    timestamp: datetime
    trace_id: str
    user_id: str
    agent_type: str
    language: str
    stt_duration: float
    llm_duration: float
    tts_duration: float
    total_duration: float
    transcript_length: int
    response_length: int
    audio_size: int
    success: bool
    error: Optional[str] = None

@dataclass
class PerformanceStats:
    """Performance statistics"""
    avg_duration: float
    p95_duration: float
    p99_duration: float
    success_rate: float
    total_calls: int
    error_count: int
    throughput_per_minute: float

class VoiceMetricsCollector:
    """Collects and analyzes voice system metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.retention_hours = retention_hours
        self.agent_stats = defaultdict(list)
        self.language_stats = defaultdict(list)
        self.hourly_stats = defaultdict(list)
        
        # Real-time monitoring
        self.active_calls = {}
        self.alerts = []
        
        print("📊 Voice Metrics Collector initialized")
    
    def record_metric(self, metric: VoiceMetric):
        """Record a new voice interaction metric"""
        self.metrics.append(metric)
        
        # Update agent-specific stats
        self.agent_stats[metric.agent_type].append(metric)
        
        # Update language-specific stats
        self.language_stats[metric.language].append(metric)
        
        # Update hourly stats
        hour_key = metric.timestamp.strftime("%Y-%m-%d-%H")
        self.hourly_stats[hour_key].append(metric)
        
        # Check for alerts
        self._check_alerts(metric)
        
        # Clean old data
        self._cleanup_old_data()
    
    def _check_alerts(self, metric: VoiceMetric):
        """Check for performance alerts"""
        alerts = []
        
        # High latency alert
        if metric.total_duration > 10:  # > 10 seconds
            alerts.append({
                "type": "high_latency",
                "severity": "warning",
                "message": f"High latency detected: {metric.total_duration:.2f}s",
                "trace_id": metric.trace_id,
                "timestamp": metric.timestamp.isoformat()
            })
        
        # Error alert
        if not metric.success:
            alerts.append({
                "type": "error",
                "severity": "error",
                "message": f"Voice call failed: {metric.error}",
                "trace_id": metric.trace_id,
                "timestamp": metric.timestamp.isoformat()
            })
        
        # STT performance alert
        if metric.stt_duration > 5:  # > 5 seconds for STT
            alerts.append({
                "type": "stt_slow",
                "severity": "warning",
                "message": f"Slow STT processing: {metric.stt_duration:.2f}s",
                "trace_id": metric.trace_id,
                "timestamp": metric.timestamp.isoformat()
            })
        
        # LLM performance alert
        if metric.llm_duration > 5:  # > 5 seconds for LLM
            alerts.append({
                "type": "llm_slow",
                "severity": "warning",
                "message": f"Slow LLM processing: {metric.llm_duration:.2f}s",
                "trace_id": metric.trace_id,
                "timestamp": metric.timestamp.isoformat()
            })
        
        self.alerts.extend(alerts)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def _cleanup_old_data(self):
        """Remove old data beyond retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Clean metrics
        while self.metrics and self.metrics[0].timestamp < cutoff_time:
            self.metrics.popleft()
        
        # Clean agent stats
        for agent_type in self.agent_stats:
            self.agent_stats[agent_type] = [
                m for m in self.agent_stats[agent_type] 
                if m.timestamp >= cutoff_time
            ]
        
        # Clean language stats
        for language in self.language_stats:
            self.language_stats[language] = [
                m for m in self.language_stats[language]
                if m.timestamp >= cutoff_time
            ]
        
        # Clean hourly stats
        for hour_key in list(self.hourly_stats.keys()):
            hour_time = datetime.strptime(hour_key, "%Y-%m-%d-%H")
            if hour_time < cutoff_time:
                del self.hourly_stats[hour_key]
    
    def get_performance_stats(self, time_window_minutes: int = 60) -> PerformanceStats:
        """Get performance statistics for a time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return PerformanceStats(0, 0, 0, 0, 0, 0, 0)
        
        durations = [m.total_duration for m in recent_metrics]
        successful_calls = [m for m in recent_metrics if m.success]
        
        return PerformanceStats(
            avg_duration=statistics.mean(durations),
            p95_duration=statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
            p99_duration=statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
            success_rate=len(successful_calls) / len(recent_metrics) * 100,
            total_calls=len(recent_metrics),
            error_count=len(recent_metrics) - len(successful_calls),
            throughput_per_minute=len(recent_metrics) / time_window_minutes
        )
    
    def get_agent_performance(self, agent_type: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance stats for specific agent type"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        agent_metrics = [
            m for m in self.agent_stats[agent_type] 
            if m.timestamp >= cutoff_time
        ]
        
        if not agent_metrics:
            return {"agent_type": agent_type, "metrics": "no_data"}
        
        durations = [m.total_duration for m in agent_metrics]
        stt_durations = [m.stt_duration for m in agent_metrics]
        llm_durations = [m.llm_duration for m in agent_metrics]
        tts_durations = [m.tts_duration for m in agent_metrics]
        
        return {
            "agent_type": agent_type,
            "total_calls": len(agent_metrics),
            "success_rate": len([m for m in agent_metrics if m.success]) / len(agent_metrics) * 100,
            "avg_total_duration": statistics.mean(durations),
            "avg_stt_duration": statistics.mean(stt_durations),
            "avg_llm_duration": statistics.mean(llm_durations),
            "avg_tts_duration": statistics.mean(tts_durations),
            "p95_duration": statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
            "languages": list(set(m.language for m in agent_metrics)),
            "avg_transcript_length": statistics.mean([m.transcript_length for m in agent_metrics]),
            "avg_response_length": statistics.mean([m.response_length for m in agent_metrics])
        }
    
    def get_language_performance(self, language: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance stats for specific language"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        language_metrics = [
            m for m in self.language_stats[language]
            if m.timestamp >= cutoff_time
        ]
        
        if not language_metrics:
            return {"language": language, "metrics": "no_data"}
        
        durations = [m.total_duration for m in language_metrics]
        
        return {
            "language": language,
            "total_calls": len(language_metrics),
            "success_rate": len([m for m in language_metrics if m.success]) / len(language_metrics) * 100,
            "avg_duration": statistics.mean(durations),
            "agent_types": list(set(m.agent_type for m in language_metrics)),
            "avg_transcript_length": statistics.mean([m.transcript_length for m in language_metrics]),
            "avg_response_length": statistics.mean([m.response_length for m in language_metrics])
        }
    
    def get_hourly_trends(self, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """Get hourly performance trends"""
        trends = []
        
        for i in range(hours):
            hour_time = datetime.now() - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y-%m-%d-%H")
            hour_metrics = self.hourly_stats.get(hour_key, [])
            
            if hour_metrics:
                durations = [m.total_duration for m in hour_metrics]
                trends.append({
                    "hour": hour_key,
                    "timestamp": hour_time.isoformat(),
                    "total_calls": len(hour_metrics),
                    "success_rate": len([m for m in hour_metrics if m.success]) / len(hour_metrics) * 100,
                    "avg_duration": statistics.mean(durations),
                    "throughput": len(hour_metrics)
                })
            else:
                trends.append({
                    "hour": hour_key,
                    "timestamp": hour_time.isoformat(),
                    "total_calls": 0,
                    "success_rate": 0,
                    "avg_duration": 0,
                    "throughput": 0
                })
        
        return {"hourly_trends": list(reversed(trends))}
    
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        if severity:
            return [alert for alert in self.alerts if alert["severity"] == severity]
        return self.alerts
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        overall_stats = self.get_performance_stats(60)
        
        # Agent performance
        agent_performance = {}
        for agent_type in ["customer_service", "sales", "rag_assistant"]:
            agent_performance[agent_type] = self.get_agent_performance(agent_type, 60)
        
        # Language performance
        language_performance = {}
        for language in ["es_mx", "en_us", "pt_br"]:
            language_performance[language] = self.get_language_performance(language, 60)
        
        # Recent alerts
        recent_alerts = self.get_alerts()[-10:]  # Last 10 alerts
        
        # Hourly trends
        trends = self.get_hourly_trends(24)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_performance": asdict(overall_stats),
            "agent_performance": agent_performance,
            "language_performance": language_performance,
            "recent_alerts": recent_alerts,
            "hourly_trends": trends["hourly_trends"],
            "system_status": {
                "langwatch_enabled": LANGWATCH_AVAILABLE and bool(os.getenv("LANGWATCH_API_KEY")),
                "active_calls": len(self.active_calls),
                "total_metrics_collected": len(self.metrics),
                "retention_hours": self.retention_hours
            }
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        dashboard_data = self.get_dashboard_data()
        
        if format == "json":
            return json.dumps(dashboard_data, indent=2, default=str)
        elif format == "csv":
            # Convert to CSV format
            csv_lines = ["timestamp,trace_id,user_id,agent_type,language,total_duration,success,error"]
            for metric in self.metrics:
                csv_lines.append(
                    f"{metric.timestamp},{metric.trace_id},{metric.user_id},"
                    f"{metric.agent_type},{metric.language},{metric.total_duration},"
                    f"{metric.success},{metric.error or ''}"
                )
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

class LangwatchIntegration:
    """Integration with Langwatch for advanced monitoring"""
    
    def __init__(self, metrics_collector: VoiceMetricsCollector):
        self.metrics_collector = metrics_collector
        self.langwatch_enabled = LANGWATCH_AVAILABLE and bool(os.getenv("LANGWATCH_API_KEY"))
        
        if self.langwatch_enabled:
            print("✅ Langwatch integration enabled")
        else:
            print("⚠️ Langwatch integration disabled")
    
    async def sync_metrics_to_langwatch(self):
        """Sync local metrics to Langwatch"""
        if not self.langwatch_enabled:
            return
        
        try:
            # Get recent metrics
            recent_metrics = [
                m for m in self.metrics_collector.metrics
                if m.timestamp >= datetime.now() - timedelta(minutes=5)
            ]
            
            for metric in recent_metrics:
                # Create custom event in Langwatch
                await self._create_langwatch_event(metric)
            
        except Exception as e:
            print(f"❌ Error syncing to Langwatch: {e}")
    
    async def _create_langwatch_event(self, metric: VoiceMetric):
        """Create a custom event in Langwatch"""
        if not self.langwatch_enabled:
            return
        
        try:
            # Create custom metrics event
            langwatch.track_event(
                event_type="voice_interaction_complete",
                properties={
                    "trace_id": metric.trace_id,
                    "user_id": metric.user_id,
                    "agent_type": metric.agent_type,
                    "language": metric.language,
                    "total_duration": metric.total_duration,
                    "stt_duration": metric.stt_duration,
                    "llm_duration": metric.llm_duration,
                    "tts_duration": metric.tts_duration,
                    "transcript_length": metric.transcript_length,
                    "response_length": metric.response_length,
                    "audio_size": metric.audio_size,
                    "success": metric.success,
                    "error": metric.error,
                    "timestamp": metric.timestamp.isoformat()
                }
            )
            
        except Exception as e:
            print(f"❌ Error creating Langwatch event: {e}")

# Global metrics collector instance
voice_metrics = VoiceMetricsCollector()
langwatch_integration = LangwatchIntegration(voice_metrics)

# Utility functions for easy integration
def record_voice_interaction(
    trace_id: str,
    user_id: str,
    agent_type: str,
    language: str,
    stt_duration: float,
    llm_duration: float,
    tts_duration: float,
    transcript_length: int,
    response_length: int,
    audio_size: int,
    success: bool,
    error: Optional[str] = None
):
    """Record a voice interaction metric"""
    metric = VoiceMetric(
        timestamp=datetime.now(),
        trace_id=trace_id,
        user_id=user_id,
        agent_type=agent_type,
        language=language,
        stt_duration=stt_duration,
        llm_duration=llm_duration,
        tts_duration=tts_duration,
        total_duration=stt_duration + llm_duration + tts_duration,
        transcript_length=transcript_length,
        response_length=response_length,
        audio_size=audio_size,
        success=success,
        error=error
    )
    
    voice_metrics.record_metric(metric)

def get_voice_dashboard() -> Dict[str, Any]:
    """Get voice system dashboard data"""
    return voice_metrics.get_dashboard_data()

def get_voice_alerts(severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get voice system alerts"""
    return voice_metrics.get_alerts(severity)

if __name__ == "__main__":
    # Example usage
    print("🎤 Voice Metrics and Observability System")
    print("=========================================")
    
    # Simulate some metrics
    import random
    
    for i in range(10):
        record_voice_interaction(
            trace_id=f"trace_{i}",
            user_id=f"user_{i % 3}",
            agent_type=random.choice(["customer_service", "sales", "rag_assistant"]),
            language=random.choice(["es_mx", "en_us"]),
            stt_duration=random.uniform(0.5, 3.0),
            llm_duration=random.uniform(1.0, 4.0),
            tts_duration=random.uniform(0.3, 1.5),
            transcript_length=random.randint(50, 200),
            response_length=random.randint(100, 300),
            audio_size=random.randint(50000, 200000),
            success=random.choice([True, True, True, False])  # 75% success rate
        )
    
    # Get dashboard data
    dashboard = get_voice_dashboard()
    print(json.dumps(dashboard, indent=2, default=str))

