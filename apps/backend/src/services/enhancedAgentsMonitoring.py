"""
Enhanced Agents Monitoring and Observability System

This module provides comprehensive monitoring and observability for LangGraph workflows,
agent performance, and system health across the enhanced SAM and Manus agents.

Features:
- Real-time LangGraph workflow monitoring
- Agent performance analytics
- System health dashboards
- Error tracking and alerting
- Resource utilization monitoring
- Collaboration pattern analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import time
from collections import defaultdict, deque

from ..utils.logger import logger

class MonitoringLevel(Enum):
    """Monitoring intensity levels"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"
    DEBUG = "debug"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class WorkflowMetrics:
    """Metrics for LangGraph workflow execution"""
    workflow_id: str
    agent_type: str
    agent_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    node_executions: List[Dict] = None
    decision_points: List[Dict] = None
    context_retrievals: int = 0
    tool_executions: int = 0
    collaboration_events: int = 0
    memory_operations: int = 0
    error_count: int = 0
    success: bool = True

@dataclass
class NodeMetrics:
    """Metrics for individual LangGraph nodes"""
    node_name: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    input_size: int = 0
    output_size: int = 0
    success: bool = True
    error_message: Optional[str] = None
    context_sources: List[str] = None
    resources_used: Dict[str, Any] = None

@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for enhanced agents"""
    agent_id: str
    agent_type: str
    uptime: float
    total_conversations: int
    successful_conversations: int
    failed_conversations: int
    avg_response_time: float
    total_tool_executions: int
    collaboration_events: int
    knowledge_graph_updates: int
    memory_operations: int
    resource_utilization: Dict[str, float]
    health_status: str

@dataclass
class SystemAlert:
    """System alert for monitoring issues"""
    alert_id: str
    severity: AlertSeverity
    component: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class EnhancedAgentsMonitor:
    """
    Comprehensive monitoring system for enhanced agents and LangGraph workflows
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the monitoring system"""
        self.config = config or {}
        self.monitoring_level = MonitoringLevel(
            self.config.get('monitoring_level', 'detailed')
        )
        
        # Storage for metrics and monitoring data
        self.workflow_metrics = {}
        self.node_metrics = {}
        self.agent_metrics = {}
        self.system_alerts = []
        self.performance_history = defaultdict(lambda: deque(maxlen=1000))
        
        # Real-time monitoring
        self.active_workflows = {}
        self.resource_monitors = {}
        self.alert_handlers = []
        
        # Aggregated statistics
        self.stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "avg_workflow_duration": 0.0,
            "total_node_executions": 0,
            "total_context_retrievals": 0,
            "total_tool_executions": 0,
            "total_collaboration_events": 0,
            "system_uptime": datetime.now(),
            "last_updated": datetime.now()
        }
        
        logger.info(f"📊 Enhanced Agents Monitor initialized with {self.monitoring_level.value} level")
    
    # Workflow Monitoring
    
    async def start_workflow_monitoring(
        self,
        workflow_id: str,
        agent_type: str,
        agent_id: str,
        user_id: str
    ) -> WorkflowMetrics:
        """Start monitoring a LangGraph workflow"""
        
        workflow_metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            agent_type=agent_type,
            agent_id=agent_id,
            user_id=user_id,
            start_time=datetime.now(),
            node_executions=[],
            decision_points=[]
        )
        
        self.workflow_metrics[workflow_id] = workflow_metrics
        self.active_workflows[workflow_id] = workflow_metrics
        self.stats["total_workflows"] += 1
        
        logger.info(f"🔍 Started monitoring workflow", {
            "workflow_id": workflow_id,
            "agent_type": agent_type,
            "agent_id": agent_id,
            "user_id": user_id
        })
        
        return workflow_metrics
    
    async def end_workflow_monitoring(
        self,
        workflow_id: str,
        success: bool = True,
        error_message: str = None
    ) -> Optional[WorkflowMetrics]:
        """End monitoring for a workflow"""
        
        if workflow_id not in self.workflow_metrics:
            logger.warning(f"Workflow {workflow_id} not found in monitoring")
            return None
        
        workflow_metrics = self.workflow_metrics[workflow_id]
        workflow_metrics.end_time = datetime.now()
        workflow_metrics.total_duration = (
            workflow_metrics.end_time - workflow_metrics.start_time
        ).total_seconds()
        workflow_metrics.success = success
        
        # Update statistics
        if success:
            self.stats["successful_workflows"] += 1
        else:
            self.stats["failed_workflows"] += 1
            
        # Update average duration
        total_completed = self.stats["successful_workflows"] + self.stats["failed_workflows"]
        if total_completed > 0:
            current_avg = self.stats["avg_workflow_duration"]
            self.stats["avg_workflow_duration"] = (
                (current_avg * (total_completed - 1) + workflow_metrics.total_duration) / total_completed
            )
        
        # Remove from active workflows
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]
        
        # Store in performance history
        self.performance_history[workflow_metrics.agent_type].append({
            "timestamp": workflow_metrics.end_time,
            "duration": workflow_metrics.total_duration,
            "success": success,
            "node_count": len(workflow_metrics.node_executions),
            "tool_executions": workflow_metrics.tool_executions,
            "collaboration_events": workflow_metrics.collaboration_events
        })
        
        logger.info(f"✅ Completed workflow monitoring", {
            "workflow_id": workflow_id,
            "duration": workflow_metrics.total_duration,
            "success": success,
            "nodes_executed": len(workflow_metrics.node_executions)
        })
        
        return workflow_metrics
    
    async def monitor_node_execution(
        self,
        workflow_id: str,
        node_name: str,
        input_data: Dict = None,
        output_data: Dict = None,
        duration: float = None,
        success: bool = True,
        error_message: str = None,
        context_sources: List[str] = None
    ):
        """Monitor individual node execution within a workflow"""
        
        execution_id = f"{workflow_id}_{node_name}_{int(time.time())}"
        
        node_metrics = NodeMetrics(
            node_name=node_name,
            execution_id=execution_id,
            start_time=datetime.now(),
            duration=duration,
            input_size=len(json.dumps(input_data)) if input_data else 0,
            output_size=len(json.dumps(output_data)) if output_data else 0,
            success=success,
            error_message=error_message,
            context_sources=context_sources or []
        )
        
        if duration:
            node_metrics.end_time = node_metrics.start_time + timedelta(seconds=duration)
        
        self.node_metrics[execution_id] = node_metrics
        
        # Update workflow metrics
        if workflow_id in self.workflow_metrics:
            workflow_metrics = self.workflow_metrics[workflow_id]
            workflow_metrics.node_executions.append(asdict(node_metrics))
            
            if not success:
                workflow_metrics.error_count += 1
            
            # Update counters based on node type
            if 'context' in node_name.lower():
                workflow_metrics.context_retrievals += 1
                self.stats["total_context_retrievals"] += 1
            elif 'tool' in node_name.lower():
                workflow_metrics.tool_executions += 1
                self.stats["total_tool_executions"] += 1
            elif 'collaboration' in node_name.lower():
                workflow_metrics.collaboration_events += 1
                self.stats["total_collaboration_events"] += 1
            elif 'memory' in node_name.lower():
                workflow_metrics.memory_operations += 1
        
        self.stats["total_node_executions"] += 1
        
        if self.monitoring_level in [MonitoringLevel.DETAILED, MonitoringLevel.COMPREHENSIVE]:
            logger.info(f"🔧 Node execution monitored", {
                "workflow_id": workflow_id,
                "node_name": node_name,
                "duration": duration,
                "success": success,
                "input_size": node_metrics.input_size,
                "output_size": node_metrics.output_size
            })
    
    async def monitor_decision_point(
        self,
        workflow_id: str,
        decision_node: str,
        decision_made: str,
        confidence: float,
        reasoning: str,
        context_used: List[str] = None
    ):
        """Monitor agent decision points in workflows"""
        
        decision_data = {
            "timestamp": datetime.now().isoformat(),
            "decision_node": decision_node,
            "decision_made": decision_made,
            "confidence": confidence,
            "reasoning": reasoning,
            "context_used": context_used or []
        }
        
        if workflow_id in self.workflow_metrics:
            self.workflow_metrics[workflow_id].decision_points.append(decision_data)
        
        if self.monitoring_level in [MonitoringLevel.COMPREHENSIVE, MonitoringLevel.DEBUG]:
            logger.info(f"🧠 Decision point monitored", {
                "workflow_id": workflow_id,
                "decision_node": decision_node,
                "decision_made": decision_made,
                "confidence": confidence
            })
    
    # Agent Performance Monitoring
    
    async def update_agent_metrics(
        self,
        agent_id: str,
        agent_type: str,
        metrics_update: Dict[str, Any]
    ):
        """Update performance metrics for an agent"""
        
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentPerformanceMetrics(
                agent_id=agent_id,
                agent_type=agent_type,
                uptime=0.0,
                total_conversations=0,
                successful_conversations=0,
                failed_conversations=0,
                avg_response_time=0.0,
                total_tool_executions=0,
                collaboration_events=0,
                knowledge_graph_updates=0,
                memory_operations=0,
                resource_utilization={},
                health_status="healthy"
            )
        
        agent_metrics = self.agent_metrics[agent_id]
        
        # Update metrics
        for key, value in metrics_update.items():
            if hasattr(agent_metrics, key):
                if key == "avg_response_time":
                    # Calculate running average
                    current_avg = agent_metrics.avg_response_time
                    total_conversations = agent_metrics.total_conversations
                    if total_conversations > 0:
                        agent_metrics.avg_response_time = (
                            (current_avg * total_conversations + value) / (total_conversations + 1)
                        )
                    else:
                        agent_metrics.avg_response_time = value
                else:
                    setattr(agent_metrics, key, value)
        
        if self.monitoring_level in [MonitoringLevel.DETAILED, MonitoringLevel.COMPREHENSIVE]:
            logger.info(f"📈 Agent metrics updated", {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "metrics_count": len(metrics_update)
            })
    
    # System Health Monitoring
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        
        health_status = {
            "overall_status": "healthy",
            "components": {},
            "metrics": {},
            "alerts": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check active workflows
            active_count = len(self.active_workflows)
            if active_count > 50:  # Threshold for concern
                await self._create_alert(
                    AlertSeverity.WARNING,
                    "workflow_overload",
                    f"High number of active workflows: {active_count}",
                    {"active_workflows": active_count}
                )
            
            health_status["components"]["workflows"] = {
                "status": "healthy" if active_count < 50 else "warning",
                "active_workflows": active_count,
                "total_processed": self.stats["total_workflows"]
            }
            
            # Check agent health
            healthy_agents = 0
            total_agents = len(self.agent_metrics)
            
            for agent_id, agent_metrics in self.agent_metrics.items():
                if agent_metrics.health_status == "healthy":
                    healthy_agents += 1
            
            health_status["components"]["agents"] = {
                "status": "healthy" if healthy_agents == total_agents else "degraded",
                "healthy_agents": healthy_agents,
                "total_agents": total_agents
            }
            
            # Check error rates
            total_workflows = self.stats["total_workflows"]
            failed_workflows = self.stats["failed_workflows"]
            error_rate = (failed_workflows / max(total_workflows, 1)) * 100
            
            if error_rate > 10:  # 10% error rate threshold
                await self._create_alert(
                    AlertSeverity.ERROR,
                    "high_error_rate",
                    f"High workflow error rate: {error_rate:.2f}%",
                    {"error_rate": error_rate, "failed_workflows": failed_workflows}
                )
                health_status["overall_status"] = "degraded"
            
            health_status["components"]["error_tracking"] = {
                "status": "healthy" if error_rate < 5 else "warning" if error_rate < 10 else "error",
                "error_rate": error_rate,
                "failed_workflows": failed_workflows
            }
            
            # Add performance metrics
            health_status["metrics"] = {
                "total_workflows": self.stats["total_workflows"],
                "successful_workflows": self.stats["successful_workflows"],
                "failed_workflows": self.stats["failed_workflows"],
                "avg_workflow_duration": self.stats["avg_workflow_duration"],
                "total_node_executions": self.stats["total_node_executions"],
                "active_workflows": len(self.active_workflows),
                "total_agents": len(self.agent_metrics)
            }
            
            # Include recent alerts
            recent_alerts = [
                asdict(alert) for alert in self.system_alerts[-10:]
                if not alert.resolved
            ]
            health_status["alerts"] = recent_alerts
            
        except Exception as error:
            logger.error(f"❌ System health check failed: {error}")
            health_status["overall_status"] = "error"
            health_status["error"] = str(error)
        
        return health_status
    
    async def _create_alert(
        self,
        severity: AlertSeverity,
        component: str,
        message: str,
        details: Dict[str, Any] = None
    ):
        """Create a system alert"""
        
        alert = SystemAlert(
            alert_id=f"alert_{uuid.uuid4().hex[:8]}",
            severity=severity,
            component=component,
            message=message,
            details=details or {},
            timestamp=datetime.now()
        )
        
        self.system_alerts.append(alert)
        
        # Keep only recent alerts (last 1000)
        if len(self.system_alerts) > 1000:
            self.system_alerts = self.system_alerts[-1000:]
        
        logger.warning(f"🚨 System alert created", {
            "alert_id": alert.alert_id,
            "severity": severity.value,
            "component": component,
            "message": message
        })
        
        # Trigger alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as error:
                logger.error(f"Alert handler failed: {error}")
    
    # Analytics and Reporting
    
    async def get_performance_analytics(
        self,
        agent_type: str = None,
        time_range: int = 3600  # seconds
    ) -> Dict[str, Any]:
        """Get performance analytics for agents and workflows"""
        
        cutoff_time = datetime.now() - timedelta(seconds=time_range)
        analytics = {
            "time_range": time_range,
            "agent_performance": {},
            "workflow_patterns": {},
            "resource_utilization": {},
            "collaboration_analysis": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Analyze agent performance
            for agent_id, agent_metrics in self.agent_metrics.items():
                if agent_type is None or agent_metrics.agent_type == agent_type:
                    analytics["agent_performance"][agent_id] = {
                        "agent_type": agent_metrics.agent_type,
                        "total_conversations": agent_metrics.total_conversations,
                        "success_rate": (
                            agent_metrics.successful_conversations / 
                            max(agent_metrics.total_conversations, 1) * 100
                        ),
                        "avg_response_time": agent_metrics.avg_response_time,
                        "tool_executions": agent_metrics.total_tool_executions,
                        "collaboration_events": agent_metrics.collaboration_events,
                        "health_status": agent_metrics.health_status
                    }
            
            # Analyze workflow patterns
            recent_workflows = [
                wf for wf in self.workflow_metrics.values()
                if wf.end_time and wf.end_time >= cutoff_time
            ]
            
            if recent_workflows:
                analytics["workflow_patterns"] = {
                    "total_workflows": len(recent_workflows),
                    "avg_duration": sum(wf.total_duration for wf in recent_workflows) / len(recent_workflows),
                    "success_rate": sum(1 for wf in recent_workflows if wf.success) / len(recent_workflows) * 100,
                    "avg_nodes_per_workflow": sum(len(wf.node_executions) for wf in recent_workflows) / len(recent_workflows),
                    "most_common_nodes": self._analyze_node_usage(recent_workflows),
                    "collaboration_frequency": sum(wf.collaboration_events for wf in recent_workflows)
                }
            
            # Analyze collaboration patterns
            collaboration_data = {}
            for wf in recent_workflows:
                if wf.collaboration_events > 0:
                    key = f"{wf.agent_type}_collaboration"
                    if key not in collaboration_data:
                        collaboration_data[key] = {"count": 0, "avg_duration": 0}
                    collaboration_data[key]["count"] += wf.collaboration_events
                    collaboration_data[key]["avg_duration"] += wf.total_duration
            
            for key, data in collaboration_data.items():
                if data["count"] > 0:
                    data["avg_duration"] /= data["count"]
            
            analytics["collaboration_analysis"] = collaboration_data
            
        except Exception as error:
            logger.error(f"❌ Performance analytics failed: {error}")
            analytics["error"] = str(error)
        
        return analytics
    
    def _analyze_node_usage(self, workflows: List[WorkflowMetrics]) -> Dict[str, int]:
        """Analyze node usage patterns across workflows"""
        node_counts = defaultdict(int)
        
        for workflow in workflows:
            for node_execution in workflow.node_executions:
                node_name = node_execution.get("node_name", "unknown")
                node_counts[node_name] += 1
        
        # Return top 10 most used nodes
        return dict(sorted(node_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # Public Interface
    
    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        
        dashboard = {
            "system_overview": await self.check_system_health(),
            "performance_analytics": await self.get_performance_analytics(),
            "active_workflows": len(self.active_workflows),
            "total_agents": len(self.agent_metrics),
            "recent_alerts": [
                asdict(alert) for alert in self.system_alerts[-5:]
                if not alert.resolved
            ],
            "system_stats": self.stats.copy(),
            "timestamp": datetime.now().isoformat()
        }
        
        dashboard["system_stats"]["uptime"] = (
            datetime.now() - self.stats["system_uptime"]
        ).total_seconds()
        
        return dashboard
    
    def add_alert_handler(self, handler_func):
        """Add custom alert handler function"""
        self.alert_handlers.append(handler_func)
    
    async def cleanup(self):
        """Clean up monitoring resources"""
        try:
            # Clear monitoring data
            self.workflow_metrics.clear()
            self.node_metrics.clear()
            self.active_workflows.clear()
            
            logger.info("🧹 Enhanced Agents Monitor cleaned up successfully")
            
        except Exception as error:
            logger.error(f"❌ Error cleaning up monitor: {error}")

# Global monitor instance
_enhanced_agents_monitor = None

def get_enhanced_agents_monitor(config: Dict[str, Any] = None) -> EnhancedAgentsMonitor:
    """Get or create the global enhanced agents monitor instance"""
    global _enhanced_agents_monitor
    
    if _enhanced_agents_monitor is None:
        _enhanced_agents_monitor = EnhancedAgentsMonitor(config)
    
    return _enhanced_agents_monitor