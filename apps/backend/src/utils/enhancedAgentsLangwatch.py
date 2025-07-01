"""
Enhanced Agents LangWatch Integration

This module provides comprehensive LangWatch integration for the Enhanced Agents system,
including specialized tracking for LangGraph workflows, Graphiti knowledge graphs,
and multi-agent collaboration patterns.

Features:
- LangGraph workflow step tracking
- Graphiti knowledge graph operation monitoring
- Multi-agent collaboration tracing
- Performance metrics and analytics
- Enterprise-grade observability
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

from ..utils.logger import logger

# LangWatch integration
try:
    import langwatch
    from langwatch.types import ChatMessage, LLMSpan
    LANGWATCH_AVAILABLE = True
    logger.info("✅ Enhanced Agents LangWatch integration available")
except ImportError:
    LANGWATCH_AVAILABLE = False
    logger.warning("⚠️ LangWatch not available - install with: pip install langwatch")

class EnhancedAgentTraceType(Enum):
    """Types of traces for enhanced agents"""
    SAM_CONVERSATION = "sam_conversation"
    MANUS_TASK_EXECUTION = "manus_task_execution"
    MULTI_AGENT_COLLABORATION = "multi_agent_collaboration"
    KNOWLEDGE_GRAPH_OPERATION = "knowledge_graph_operation"
    LANGGRAPH_WORKFLOW = "langgraph_workflow"

class LangGraphNodeType(Enum):
    """Types of LangGraph nodes for tracking"""
    CONTEXT_RETRIEVAL = "context_retrieval"
    ENHANCED_AGENT = "enhanced_agent"
    TOOL_EXECUTION = "tool_execution"
    MEMORY_STORAGE = "memory_storage"
    COLLABORATION = "collaboration"
    DECISION_ANALYSIS = "decision_analysis"
    TASK_ANALYSIS = "task_analysis"
    TASK_PLANNING = "task_planning"
    RESOURCE_ALLOCATION = "resource_allocation"
    TASK_EXECUTION = "task_execution"
    PROGRESS_MONITORING = "progress_monitoring"
    RESULT_VALIDATION = "result_validation"
    COMPLETION_HANDLING = "completion_handling"

@dataclass
class EnhancedAgentTrace:
    """Enhanced agent trace data"""
    trace_id: str
    agent_type: str
    agent_id: str
    user_id: str
    trace_type: EnhancedAgentTraceType
    start_time: datetime
    metadata: Dict[str, Any]
    tags: List[str]
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class LangGraphNodeTrace:
    """LangGraph node execution trace"""
    node_id: str
    node_type: LangGraphNodeType
    trace_id: str
    start_time: datetime
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    context_sources: List[str] = None
    tools_used: List[str] = None

class EnhancedAgentsLangwatchTracker:
    """
    Comprehensive LangWatch tracker for Enhanced Agents system
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the enhanced agents LangWatch tracker"""
        self.config = config or {}
        self.active_traces = {}
        self.node_traces = {}
        self.collaboration_traces = {}
        self.performance_metrics = {}
        
        # Initialize LangWatch if available
        if LANGWATCH_AVAILABLE and self.config.get('LANGWATCH_API_KEY'):
            try:
                langwatch.login(api_key=self.config.get('LANGWATCH_API_KEY'))
                self.langwatch_enabled = True
                logger.info("🔍 Enhanced Agents LangWatch tracker initialized")
            except Exception as error:
                self.langwatch_enabled = False
                logger.warning(f"⚠️ LangWatch initialization failed: {error}")
        else:
            self.langwatch_enabled = False
            logger.info("⚠️ LangWatch not configured for Enhanced Agents")
    
    async def start_agent_trace(
        self,
        agent_type: str,
        agent_id: str,
        user_id: str,
        trace_type: EnhancedAgentTraceType,
        input_data: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> str:
        """Start tracking an enhanced agent interaction"""
        
        trace_id = f"enhanced_{agent_type}_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        trace = EnhancedAgentTrace(
            trace_id=trace_id,
            agent_type=agent_type,
            agent_id=agent_id,
            user_id=user_id,
            trace_type=trace_type,
            start_time=datetime.now(),
            metadata=metadata or {},
            tags=[
                "enhanced_agents",
                f"agent_{agent_type}",
                trace_type.value,
                "langgraph_integration",
                "graphiti_integration",
                "mcp_enterprise"
            ]
        )
        
        self.active_traces[trace_id] = trace
        
        if self.langwatch_enabled:
            try:
                langwatch.get_current_trace().trace_id = trace_id
                langwatch.get_current_trace().user_id = user_id
                langwatch.get_current_trace().metadata = {
                    "agent_type": agent_type,
                    "agent_id": agent_id,
                    "trace_type": trace_type.value,
                    "enhanced_agents_system": True,
                    "langgraph_enabled": True,
                    "graphiti_enabled": True,
                    **trace.metadata
                }
                langwatch.get_current_trace().tags = trace.tags
                langwatch.get_current_trace().input = input_data
                
                logger.debug(f"🔍 Started LangWatch trace: {trace_id}")
                
            except Exception as error:
                logger.warning(f"⚠️ Error starting LangWatch trace: {error}")
        
        return trace_id
    
    async def track_langgraph_node(
        self,
        trace_id: str,
        node_type: LangGraphNodeType,
        node_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any] = None,
        duration: float = None,
        success: bool = True,
        error_message: str = None,
        context_sources: List[str] = None,
        tools_used: List[str] = None
    ):
        """Track individual LangGraph node execution"""
        
        node_id = f"{trace_id}_{node_name}_{int(datetime.now().timestamp())}"
        
        node_trace = LangGraphNodeTrace(
            node_id=node_id,
            node_type=node_type,
            trace_id=trace_id,
            start_time=datetime.now(),
            input_data=input_data,
            output_data=output_data,
            duration=duration,
            success=success,
            error_message=error_message,
            context_sources=context_sources or [],
            tools_used=tools_used or []
        )
        
        if duration:
            node_trace.end_time = node_trace.start_time + timedelta(seconds=duration)
        
        self.node_traces[node_id] = node_trace
        
        if self.langwatch_enabled:
            try:
                span_data = {
                    "name": f"LangGraph Node: {node_name}",
                    "type": "langgraph_node",
                    "input": json.dumps(input_data) if input_data else None,
                    "output": json.dumps(output_data) if output_data else None,
                    "metadata": {
                        "node_type": node_type.value,
                        "node_name": node_name,
                        "success": success,
                        "context_sources": context_sources or [],
                        "tools_used": tools_used or [],
                        "langgraph_integration": True
                    },
                    "metrics": {
                        "duration": duration or 0,
                        "context_sources_count": len(context_sources or []),
                        "tools_used_count": len(tools_used or []),
                        "success": 1 if success else 0
                    },
                    "tags": [
                        "langgraph_node",
                        node_type.value,
                        node_name,
                        "success" if success else "error"
                    ]
                }
                
                if error_message:
                    span_data["error"] = error_message
                
                # Create span in LangWatch
                langwatch.span(**span_data)
                
                logger.debug(f"🔧 Tracked LangGraph node: {node_name} ({node_type.value})")
                
            except Exception as error:
                logger.warning(f"⚠️ Error tracking LangGraph node: {error}")
    
    async def track_graphiti_operation(
        self,
        trace_id: str,
        operation_type: str,
        operation_data: Dict[str, Any],
        result: Dict[str, Any] = None,
        duration: float = None,
        success: bool = True
    ):
        """Track Graphiti knowledge graph operations"""
        
        if self.langwatch_enabled:
            try:
                langwatch.span(
                    name=f"Graphiti: {operation_type}",
                    type="knowledge_graph",
                    input=json.dumps(operation_data),
                    output=json.dumps(result) if result else None,
                    metadata={
                        "operation_type": operation_type,
                        "knowledge_graph": "graphiti",
                        "success": success,
                        "temporal_reasoning": True
                    },
                    metrics={
                        "duration": duration or 0,
                        "success": 1 if success else 0,
                        "entities_affected": result.get("entities_affected", 0) if result else 0,
                        "relationships_created": result.get("relationships_created", 0) if result else 0
                    },
                    tags=[
                        "graphiti",
                        "knowledge_graph",
                        operation_type,
                        "temporal_reasoning",
                        "success" if success else "error"
                    ]
                )
                
                logger.debug(f"📊 Tracked Graphiti operation: {operation_type}")
                
            except Exception as error:
                logger.warning(f"⚠️ Error tracking Graphiti operation: {error}")
    
    async def track_collaboration_event(
        self,
        primary_trace_id: str,
        collaboration_type: str,
        agents_involved: List[str],
        collaboration_data: Dict[str, Any],
        result: Dict[str, Any] = None,
        duration: float = None,
        success: bool = True
    ):
        """Track multi-agent collaboration events"""
        
        collaboration_id = f"collab_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        self.collaboration_traces[collaboration_id] = {
            "collaboration_id": collaboration_id,
            "primary_trace_id": primary_trace_id,
            "collaboration_type": collaboration_type,
            "agents_involved": agents_involved,
            "start_time": datetime.now(),
            "duration": duration,
            "success": success,
            "collaboration_data": collaboration_data,
            "result": result
        }
        
        if self.langwatch_enabled:
            try:
                langwatch.span(
                    name=f"Multi-Agent Collaboration: {collaboration_type}",
                    type="collaboration",
                    input=json.dumps(collaboration_data),
                    output=json.dumps(result) if result else None,
                    metadata={
                        "collaboration_id": collaboration_id,
                        "collaboration_type": collaboration_type,
                        "agents_involved": agents_involved,
                        "agents_count": len(agents_involved),
                        "success": success,
                        "multi_agent_system": True,
                        "knowledge_sharing": True
                    },
                    metrics={
                        "duration": duration or 0,
                        "agents_count": len(agents_involved),
                        "success": 1 if success else 0,
                        "knowledge_items_shared": result.get("knowledge_items_shared", 0) if result else 0,
                        "collaboration_efficiency": result.get("efficiency_score", 0) if result else 0
                    },
                    tags=[
                        "multi_agent_collaboration",
                        collaboration_type,
                        f"agents_{len(agents_involved)}",
                        "knowledge_sharing",
                        "success" if success else "error"
                    ]
                )
                
                logger.info(f"🤝 Tracked collaboration: {collaboration_type} with {len(agents_involved)} agents")
                
            except Exception as error:
                logger.warning(f"⚠️ Error tracking collaboration: {error}")
    
    async def end_agent_trace(
        self,
        trace_id: str,
        output_data: Any,
        success: bool = True,
        error_message: str = None,
        final_metrics: Dict[str, Any] = None
    ):
        """End tracking for an enhanced agent interaction"""
        
        if trace_id not in self.active_traces:
            logger.warning(f"Trace not found: {trace_id}")
            return
        
        trace = self.active_traces[trace_id]
        trace.end_time = datetime.now()
        trace.duration = (trace.end_time - trace.start_time).total_seconds()
        trace.success = success
        trace.error_message = error_message
        
        if self.langwatch_enabled:
            try:
                # Update trace with final data
                langwatch.get_current_trace().output = output_data
                langwatch.get_current_trace().metadata.update({
                    "duration": trace.duration,
                    "success": success,
                    "end_time": trace.end_time.isoformat(),
                    **(final_metrics or {})
                })
                
                # Add final metrics
                if final_metrics:
                    for metric_name, metric_value in final_metrics.items():
                        langwatch.get_current_trace().metrics[metric_name] = metric_value
                
                # Add success/error tag
                if success:
                    langwatch.get_current_trace().tags.append("success")
                else:
                    langwatch.get_current_trace().tags.append("error")
                    if error_message:
                        langwatch.get_current_trace().error = error_message
                
                logger.info(f"✅ Completed LangWatch trace: {trace_id} (duration: {trace.duration:.2f}s)")
                
            except Exception as error:
                logger.warning(f"⚠️ Error completing LangWatch trace: {error}")
        
        # Store performance metrics
        self.performance_metrics[trace_id] = {
            "agent_type": trace.agent_type,
            "trace_type": trace.trace_type.value,
            "duration": trace.duration,
            "success": success,
            "timestamp": trace.end_time,
            "final_metrics": final_metrics or {}
        }
        
        # Clean up active trace
        del self.active_traces[trace_id]
    
    async def get_performance_summary(
        self,
        agent_type: str = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance summary from tracked data"""
        
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        # Filter metrics by time window and agent type
        relevant_metrics = [
            metrics for metrics in self.performance_metrics.values()
            if metrics["timestamp"] >= cutoff_time and 
            (agent_type is None or metrics["agent_type"] == agent_type)
        ]
        
        if not relevant_metrics:
            return {
                "total_traces": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "agent_types": {},
                "trace_types": {}
            }
        
        # Calculate summary statistics
        total_traces = len(relevant_metrics)
        successful_traces = sum(1 for m in relevant_metrics if m["success"])
        success_rate = successful_traces / total_traces * 100
        avg_duration = sum(m["duration"] for m in relevant_metrics) / total_traces
        
        # Group by agent type
        agent_types = {}
        for metrics in relevant_metrics:
            agent_type_key = metrics["agent_type"]
            if agent_type_key not in agent_types:
                agent_types[agent_type_key] = {
                    "count": 0,
                    "success_count": 0,
                    "total_duration": 0
                }
            agent_types[agent_type_key]["count"] += 1
            if metrics["success"]:
                agent_types[agent_type_key]["success_count"] += 1
            agent_types[agent_type_key]["total_duration"] += metrics["duration"]
        
        # Calculate agent type averages
        for agent_type_key, data in agent_types.items():
            data["success_rate"] = data["success_count"] / data["count"] * 100
            data["avg_duration"] = data["total_duration"] / data["count"]
        
        # Group by trace type
        trace_types = {}
        for metrics in relevant_metrics:
            trace_type_key = metrics["trace_type"]
            if trace_type_key not in trace_types:
                trace_types[trace_type_key] = {"count": 0, "avg_duration": 0}
            trace_types[trace_type_key]["count"] += 1
        
        return {
            "time_window_hours": time_window_hours,
            "total_traces": total_traces,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "agent_types": agent_types,
            "trace_types": trace_types,
            "active_traces": len(self.active_traces),
            "collaboration_events": len(self.collaboration_traces),
            "langwatch_enabled": self.langwatch_enabled,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_old_data(self, max_age_hours: int = 168):  # 7 days
        """Clean up old tracking data"""
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Clean up performance metrics
        old_trace_ids = [
            trace_id for trace_id, metrics in self.performance_metrics.items()
            if metrics["timestamp"] < cutoff_time
        ]
        
        for trace_id in old_trace_ids:
            del self.performance_metrics[trace_id]
        
        # Clean up node traces
        old_node_ids = [
            node_id for node_id, node_trace in self.node_traces.items()
            if node_trace.start_time < cutoff_time
        ]
        
        for node_id in old_node_ids:
            del self.node_traces[node_id]
        
        # Clean up collaboration traces
        old_collab_ids = [
            collab_id for collab_id, collab_data in self.collaboration_traces.items()
            if collab_data["start_time"] < cutoff_time
        ]
        
        for collab_id in old_collab_ids:
            del self.collaboration_traces[collab_id]
        
        logger.info(f"🧹 Cleaned up old tracking data: {len(old_trace_ids)} traces, {len(old_node_ids)} nodes, {len(old_collab_ids)} collaborations")
    
    def is_enabled(self) -> bool:
        """Check if LangWatch tracking is enabled"""
        return self.langwatch_enabled

# Global tracker instance
_enhanced_agents_langwatch_tracker = None

def get_enhanced_agents_langwatch_tracker(config: Dict[str, Any] = None) -> EnhancedAgentsLangwatchTracker:
    """Get or create the global enhanced agents LangWatch tracker"""
    global _enhanced_agents_langwatch_tracker
    
    if _enhanced_agents_langwatch_tracker is None:
        _enhanced_agents_langwatch_tracker = EnhancedAgentsLangwatchTracker(config)
    
    return _enhanced_agents_langwatch_tracker

# Convenience decorators and functions

def track_enhanced_agent_method(
    trace_type: EnhancedAgentTraceType,
    node_type: LangGraphNodeType = None
):
    """Decorator to automatically track enhanced agent methods"""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            tracker = get_enhanced_agents_langwatch_tracker(getattr(self, 'config', {}))
            
            if not tracker.is_enabled():
                return await func(self, *args, **kwargs)
            
            # Extract common parameters
            user_id = kwargs.get('user_id') or (args[1] if len(args) > 1 else 'unknown')
            input_data = {
                'method': func.__name__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            
            # Start trace
            trace_id = await tracker.start_agent_trace(
                agent_type=getattr(self, 'agent_id', 'unknown'),
                agent_id=getattr(self, 'agent_id', 'unknown'),
                user_id=user_id,
                trace_type=trace_type,
                input_data=input_data,
                metadata={'method': func.__name__}
            )
            
            try:
                start_time = datetime.now()
                result = await func(self, *args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                # Track as LangGraph node if specified
                if node_type:
                    await tracker.track_langgraph_node(
                        trace_id=trace_id,
                        node_type=node_type,
                        node_name=func.__name__,
                        input_data=input_data,
                        output_data={'result_type': type(result).__name__},
                        duration=duration,
                        success=True
                    )
                
                # End trace
                await tracker.end_agent_trace(
                    trace_id=trace_id,
                    output_data=result,
                    success=True,
                    final_metrics={
                        'method_duration': duration,
                        'result_type': type(result).__name__
                    }
                )
                
                return result
                
            except Exception as error:
                # Track error
                if node_type:
                    await tracker.track_langgraph_node(
                        trace_id=trace_id,
                        node_type=node_type,
                        node_name=func.__name__,
                        input_data=input_data,
                        success=False,
                        error_message=str(error)
                    )
                
                await tracker.end_agent_trace(
                    trace_id=trace_id,
                    output_data=None,
                    success=False,
                    error_message=str(error)
                )
                
                raise
        
        return wrapper
    return decorator