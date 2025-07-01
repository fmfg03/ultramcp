"""
Enhanced Memory Monitoring Middleware - Advanced monitoring for Graphiti integration

Provides comprehensive observability for:
- Dual-write operations (vector + graph)
- Search performance across multiple sources
- Knowledge graph operations
- Temporal reasoning queries
- Agent collaboration metrics
- Predictive assistance analytics
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

from ..utils.logger import logger

# Langwatch integration (optional)
try:
    import langwatch
    LANGWATCH_AVAILABLE = True
except ImportError:
    LANGWATCH_AVAILABLE = False
    logger.debug("Langwatch not available for enhanced memory monitoring")

@dataclass
class OperationMetrics:
    """Metrics for individual operations"""
    operation_id: str
    operation_type: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    
    # Memory-specific metrics
    vector_latency_ms: Optional[float] = None
    graph_latency_ms: Optional[float] = None
    total_results: int = 0
    vector_results: int = 0
    graph_results: int = 0
    
    # Quality metrics
    relevance_scores: List[float] = None
    relationships_found: int = 0
    entities_extracted: int = 0
    
    # Resource usage
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

class EnhancedMemoryMonitoring:
    """
    Advanced monitoring system for enhanced memory operations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the monitoring system"""
        self.config = config or {}
        
        # Metrics storage
        self.active_operations: Dict[str, OperationMetrics] = {}
        self.completed_operations: deque = deque(maxlen=1000)  # Keep last 1000 operations
        
        # Aggregated metrics
        self.aggregated_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            
            # Performance metrics
            "avg_latency_ms": 0.0,
            "avg_vector_latency_ms": 0.0,
            "avg_graph_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "p99_latency_ms": 0.0,
            
            # Quality metrics
            "avg_relevance_score": 0.0,
            "avg_relationships_per_operation": 0.0,
            "avg_entities_per_operation": 0.0,
            "dual_write_success_rate": 0.0,
            
            # Search effectiveness
            "search_hit_rate": 0.0,
            "hybrid_search_improvement": 0.0,
            "temporal_query_success_rate": 0.0,
            "prediction_accuracy": 0.0
        }
        
        # Operation type tracking
        self.operation_type_metrics = defaultdict(lambda: {
            "count": 0,
            "avg_latency": 0.0,
            "success_rate": 0.0,
            "avg_quality": 0.0
        })
        
        # Time-based metrics (last hour)
        self.hourly_metrics = deque(maxlen=60)  # 60 minutes
        
        # Alerting thresholds
        self.thresholds = {
            "high_latency_ms": 5000,
            "low_success_rate": 0.85,
            "low_relevance_score": 0.3,
            "high_error_rate": 0.15
        }
        
        # Langwatch integration
        self.langwatch_enabled = LANGWATCH_AVAILABLE and self.config.get('LANGWATCH_API_KEY')
        
        # Start periodic metric aggregation
        self._start_metric_aggregation()
    
    def start_operation(
        self,
        operation_type: str,
        operation_data: Dict[str, Any] = None
    ) -> str:
        """Start tracking an operation"""
        operation_id = f"{operation_type}_{int(time.time() * 1000)}_{id(operation_data) % 1000}"
        
        metrics = OperationMetrics(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=time.time()
        )
        
        self.active_operations[operation_id] = metrics
        
        # Start Langwatch trace if available
        if self.langwatch_enabled:
            try:
                trace = langwatch.trace({
                    "id": operation_id,
                    "metadata": {
                        "provider": "enhanced_memory",
                        "operation_type": operation_type,
                        "data": operation_data
                    }
                })
                metrics.langwatch_trace = trace
            except Exception as error:
                logger.debug(f"Failed to start Langwatch trace: {error}")
        
        logger.debug(f"🔍 Started monitoring operation: {operation_id}")
        return operation_id
    
    def complete_operation(
        self,
        operation_id: str,
        success: bool = True,
        results: Dict[str, Any] = None,
        error_message: str = None
    ):
        """Complete tracking an operation"""
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found in active operations")
            return
        
        metrics = self.active_operations[operation_id]
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.success = success
        metrics.error_message = error_message
        
        # Extract result metrics
        if results:
            self._extract_result_metrics(metrics, results)
        
        # Complete Langwatch trace
        if hasattr(metrics, 'langwatch_trace') and metrics.langwatch_trace:
            try:
                metrics.langwatch_trace.end({
                    "output": results,
                    "metadata": {
                        "duration_ms": metrics.duration_ms,
                        "success": success,
                        "error": error_message
                    }
                })
            except Exception as error:
                logger.debug(f"Failed to end Langwatch trace: {error}")
        
        # Move to completed operations
        self.completed_operations.append(metrics)
        del self.active_operations[operation_id]
        
        # Update aggregated metrics
        self._update_aggregated_metrics(metrics)
        
        logger.debug(f"✅ Completed monitoring operation: {operation_id}", {
            "duration_ms": metrics.duration_ms,
            "success": success,
            "total_results": metrics.total_results
        })
    
    def track_vector_operation(self, operation_id: str, latency_ms: float, results_count: int):
        """Track vector database operation metrics"""
        if operation_id in self.active_operations:
            metrics = self.active_operations[operation_id]
            metrics.vector_latency_ms = latency_ms
            metrics.vector_results = results_count
    
    def track_graph_operation(
        self,
        operation_id: str,
        latency_ms: float,
        results_count: int,
        relationships_found: int = 0,
        entities_extracted: int = 0
    ):
        """Track knowledge graph operation metrics"""
        if operation_id in self.active_operations:
            metrics = self.active_operations[operation_id]
            metrics.graph_latency_ms = latency_ms
            metrics.graph_results = results_count
            metrics.relationships_found = relationships_found
            metrics.entities_extracted = entities_extracted
    
    def track_search_quality(self, operation_id: str, relevance_scores: List[float]):
        """Track search result quality metrics"""
        if operation_id in self.active_operations:
            metrics = self.active_operations[operation_id]
            metrics.relevance_scores = relevance_scores
            metrics.total_results = len(relevance_scores)
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for monitoring dashboard"""
        current_time = datetime.now()
        
        # Recent operations (last 5 minutes)
        recent_ops = [
            op for op in self.completed_operations 
            if current_time.timestamp() - op.end_time < 300
        ]
        
        # Active operations count
        active_count = len(self.active_operations)
        
        # Calculate real-time rates
        success_rate = (
            sum(1 for op in recent_ops if op.success) / len(recent_ops) * 100
            if recent_ops else 0
        )
        
        avg_latency = (
            statistics.mean([op.duration_ms for op in recent_ops if op.duration_ms])
            if recent_ops else 0
        )
        
        return {
            "current_status": {
                "active_operations": active_count,
                "recent_operations_5min": len(recent_ops),
                "success_rate_5min": success_rate,
                "avg_latency_5min": avg_latency
            },
            "performance": {
                **self.aggregated_metrics
            },
            "operation_types": dict(self.operation_type_metrics),
            "alerts": self._generate_alerts(),
            "timestamp": current_time.isoformat()
        }
    
    def get_detailed_analytics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get detailed analytics for the specified time range"""
        cutoff_time = datetime.now().timestamp() - (time_range_hours * 3600)
        
        # Filter operations within time range
        ops_in_range = [
            op for op in self.completed_operations 
            if op.end_time and op.end_time > cutoff_time
        ]
        
        if not ops_in_range:
            return {"message": "No operations in specified time range"}
        
        # Performance analytics
        latencies = [op.duration_ms for op in ops_in_range if op.duration_ms]
        vector_latencies = [op.vector_latency_ms for op in ops_in_range if op.vector_latency_ms]
        graph_latencies = [op.graph_latency_ms for op in ops_in_range if op.graph_latency_ms]
        
        # Quality analytics
        all_relevance_scores = []
        for op in ops_in_range:
            if op.relevance_scores:
                all_relevance_scores.extend(op.relevance_scores)
        
        # Operation type breakdown
        type_breakdown = defaultdict(list)
        for op in ops_in_range:
            type_breakdown[op.operation_type].append(op)
        
        analytics = {
            "time_range": f"{time_range_hours} hours",
            "total_operations": len(ops_in_range),
            "success_rate": sum(1 for op in ops_in_range if op.success) / len(ops_in_range) * 100,
            
            "performance": {
                "latency": {
                    "avg": statistics.mean(latencies) if latencies else 0,
                    "median": statistics.median(latencies) if latencies else 0,
                    "p95": self._percentile(latencies, 95) if latencies else 0,
                    "p99": self._percentile(latencies, 99) if latencies else 0,
                    "min": min(latencies) if latencies else 0,
                    "max": max(latencies) if latencies else 0
                },
                "vector_performance": {
                    "avg_latency": statistics.mean(vector_latencies) if vector_latencies else 0,
                    "operations_count": len(vector_latencies)
                },
                "graph_performance": {
                    "avg_latency": statistics.mean(graph_latencies) if graph_latencies else 0,
                    "operations_count": len(graph_latencies)
                }
            },
            
            "quality": {
                "relevance_scores": {
                    "avg": statistics.mean(all_relevance_scores) if all_relevance_scores else 0,
                    "median": statistics.median(all_relevance_scores) if all_relevance_scores else 0,
                    "distribution": self._score_distribution(all_relevance_scores)
                },
                "relationships": {
                    "avg_per_operation": statistics.mean([
                        op.relationships_found for op in ops_in_range 
                        if op.relationships_found is not None
                    ]) if ops_in_range else 0
                },
                "entities": {
                    "avg_per_operation": statistics.mean([
                        op.entities_extracted for op in ops_in_range 
                        if op.entities_extracted is not None
                    ]) if ops_in_range else 0
                }
            },
            
            "operation_types": {
                op_type: {
                    "count": len(ops),
                    "success_rate": sum(1 for op in ops if op.success) / len(ops) * 100,
                    "avg_latency": statistics.mean([
                        op.duration_ms for op in ops if op.duration_ms
                    ]) if ops else 0
                }
                for op_type, ops in type_breakdown.items()
            },
            
            "trends": self._calculate_trends(ops_in_range)
        }
        
        return analytics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status based on metrics"""
        recent_ops = [
            op for op in self.completed_operations 
            if datetime.now().timestamp() - op.end_time < 600  # Last 10 minutes
        ]
        
        if not recent_ops:
            return {
                "status": "unknown",
                "message": "No recent operations to analyze",
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate health indicators
        success_rate = sum(1 for op in recent_ops if op.success) / len(recent_ops)
        avg_latency = statistics.mean([op.duration_ms for op in recent_ops if op.duration_ms])
        avg_relevance = statistics.mean([
            score for op in recent_ops if op.relevance_scores
            for score in op.relevance_scores
        ]) if any(op.relevance_scores for op in recent_ops) else 0
        
        # Determine health status
        health_issues = []
        
        if success_rate < self.thresholds["low_success_rate"]:
            health_issues.append(f"Low success rate: {success_rate:.2%}")
        
        if avg_latency > self.thresholds["high_latency_ms"]:
            health_issues.append(f"High latency: {avg_latency:.1f}ms")
        
        if avg_relevance < self.thresholds["low_relevance_score"]:
            health_issues.append(f"Low relevance scores: {avg_relevance:.2f}")
        
        if len(health_issues) == 0:
            status = "healthy"
            message = "All systems operating normally"
        elif len(health_issues) <= 1:
            status = "warning"
            message = f"Minor issues detected: {'; '.join(health_issues)}"
        else:
            status = "unhealthy"
            message = f"Multiple issues detected: {'; '.join(health_issues)}"
        
        return {
            "status": status,
            "message": message,
            "indicators": {
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency,
                "avg_relevance_score": avg_relevance,
                "recent_operations": len(recent_ops)
            },
            "issues": health_issues,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_metrics(self):
        """Reset all metrics (for testing or maintenance)"""
        self.active_operations.clear()
        self.completed_operations.clear()
        
        self.aggregated_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_latency_ms": 0.0,
            "avg_vector_latency_ms": 0.0,
            "avg_graph_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "p99_latency_ms": 0.0,
            "avg_relevance_score": 0.0,
            "avg_relationships_per_operation": 0.0,
            "avg_entities_per_operation": 0.0,
            "dual_write_success_rate": 0.0,
            "search_hit_rate": 0.0,
            "hybrid_search_improvement": 0.0,
            "temporal_query_success_rate": 0.0,
            "prediction_accuracy": 0.0
        }
        
        self.operation_type_metrics.clear()
        self.hourly_metrics.clear()
        
        logger.info("Enhanced memory monitoring metrics reset")
    
    # Private helper methods
    
    def _extract_result_metrics(self, metrics: OperationMetrics, results: Dict[str, Any]):
        """Extract metrics from operation results"""
        # Extract total results
        metrics.total_results = results.get('total_results', 0)
        
        # Extract source-specific results
        if 'sources_used' in results:
            sources = results['sources_used']
            if 'memory' in sources or 'memory_fallback' in sources:
                metrics.vector_results = len([
                    r for r in results.get('results', [])
                    if r.get('source') in ['memory', 'memory_fallback']
                ])
            if 'graph' in sources:
                metrics.graph_results = len([
                    r for r in results.get('results', [])
                    if r.get('source') == 'graph'
                ])
        
        # Extract relevance scores
        if 'results' in results:
            metrics.relevance_scores = [
                r.get('relevance_score', 0) for r in results['results']
            ]
        
        # Extract relationship and entity counts
        if 'relationships_found' in results:
            metrics.relationships_found = results['relationships_found']
        if 'entities_found' in results:
            metrics.entities_extracted = results['entities_found']
    
    def _update_aggregated_metrics(self, metrics: OperationMetrics):
        """Update aggregated metrics with new operation data"""
        self.aggregated_metrics["total_operations"] += 1
        
        if metrics.success:
            self.aggregated_metrics["successful_operations"] += 1
        else:
            self.aggregated_metrics["failed_operations"] += 1
        
        # Update operation type metrics
        op_type = metrics.operation_type
        type_metrics = self.operation_type_metrics[op_type]
        type_metrics["count"] += 1
        
        if metrics.duration_ms:
            # Update latency metrics
            current_avg = self.aggregated_metrics["avg_latency_ms"]
            total_ops = self.aggregated_metrics["total_operations"]
            self.aggregated_metrics["avg_latency_ms"] = (
                (current_avg * (total_ops - 1) + metrics.duration_ms) / total_ops
            )
            
            # Update type-specific latency
            type_avg = type_metrics["avg_latency"]
            type_count = type_metrics["count"]
            type_metrics["avg_latency"] = (
                (type_avg * (type_count - 1) + metrics.duration_ms) / type_count
            )
        
        # Update success rate for operation type
        type_metrics["success_rate"] = (
            sum(1 for op in self.completed_operations 
                if op.operation_type == op_type and op.success) /
            max(type_metrics["count"], 1)
        )
        
        # Update relevance score metrics
        if metrics.relevance_scores:
            avg_relevance = statistics.mean(metrics.relevance_scores)
            current_avg = self.aggregated_metrics["avg_relevance_score"]
            total_ops = self.aggregated_metrics["total_operations"]
            self.aggregated_metrics["avg_relevance_score"] = (
                (current_avg * (total_ops - 1) + avg_relevance) / total_ops
            )
            
            type_metrics["avg_quality"] = avg_relevance
    
    def _generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate alerts based on current metrics"""
        alerts = []
        
        # High latency alert
        if self.aggregated_metrics["avg_latency_ms"] > self.thresholds["high_latency_ms"]:
            alerts.append({
                "type": "performance",
                "level": "warning",
                "message": f"High average latency: {self.aggregated_metrics['avg_latency_ms']:.1f}ms",
                "threshold": self.thresholds["high_latency_ms"],
                "timestamp": datetime.now().isoformat()
            })
        
        # Low success rate alert
        total_ops = self.aggregated_metrics["total_operations"]
        if total_ops > 0:
            success_rate = self.aggregated_metrics["successful_operations"] / total_ops
            if success_rate < self.thresholds["low_success_rate"]:
                alerts.append({
                    "type": "reliability",
                    "level": "critical",
                    "message": f"Low success rate: {success_rate:.2%}",
                    "threshold": self.thresholds["low_success_rate"],
                    "timestamp": datetime.now().isoformat()
                })
        
        # Low relevance score alert
        if self.aggregated_metrics["avg_relevance_score"] < self.thresholds["low_relevance_score"]:
            alerts.append({
                "type": "quality",
                "level": "warning",
                "message": f"Low relevance scores: {self.aggregated_metrics['avg_relevance_score']:.2f}",
                "threshold": self.thresholds["low_relevance_score"],
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate distribution of relevance scores"""
        if not scores:
            return {}
        
        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        for score in scores:
            if score < 0.2:
                distribution["0.0-0.2"] += 1
            elif score < 0.4:
                distribution["0.2-0.4"] += 1
            elif score < 0.6:
                distribution["0.4-0.6"] += 1
            elif score < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1
        
        return distribution
    
    def _calculate_trends(self, operations: List[OperationMetrics]) -> Dict[str, Any]:
        """Calculate trends in the operations data"""
        if len(operations) < 2:
            return {}
        
        # Sort by end time
        sorted_ops = sorted(operations, key=lambda x: x.end_time)
        
        # Calculate moving averages
        window_size = min(10, len(sorted_ops) // 2)
        if window_size < 2:
            return {}
        
        early_ops = sorted_ops[:window_size]
        late_ops = sorted_ops[-window_size:]
        
        early_latency = statistics.mean([op.duration_ms for op in early_ops if op.duration_ms])
        late_latency = statistics.mean([op.duration_ms for op in late_ops if op.duration_ms])
        
        early_success_rate = sum(1 for op in early_ops if op.success) / len(early_ops)
        late_success_rate = sum(1 for op in late_ops if op.success) / len(late_ops)
        
        return {
            "latency_trend": {
                "direction": "improving" if late_latency < early_latency else "degrading",
                "change_percent": ((late_latency - early_latency) / early_latency * 100) if early_latency else 0
            },
            "success_rate_trend": {
                "direction": "improving" if late_success_rate > early_success_rate else "degrading",
                "change_percent": ((late_success_rate - early_success_rate) * 100)
            }
        }
    
    def _start_metric_aggregation(self):
        """Start background task for metric aggregation"""
        async def aggregate_metrics():
            while True:
                try:
                    # Recalculate percentiles from recent operations
                    recent_ops = list(self.completed_operations)[-100:]  # Last 100 operations
                    
                    if recent_ops:
                        latencies = [op.duration_ms for op in recent_ops if op.duration_ms]
                        if latencies:
                            self.aggregated_metrics["p95_latency_ms"] = self._percentile(latencies, 95)
                            self.aggregated_metrics["p99_latency_ms"] = self._percentile(latencies, 99)
                    
                    # Store hourly metrics
                    current_metrics = self.aggregated_metrics.copy()
                    current_metrics["timestamp"] = datetime.now().isoformat()
                    self.hourly_metrics.append(current_metrics)
                    
                    await asyncio.sleep(60)  # Update every minute
                    
                except Exception as error:
                    logger.error(f"Error in metric aggregation: {error}")
                    await asyncio.sleep(60)
        
        # Start the background task
        asyncio.create_task(aggregate_metrics())

# Global monitoring instance
_enhanced_memory_monitoring = None

def get_enhanced_memory_monitoring(config: Dict[str, Any] = None) -> EnhancedMemoryMonitoring:
    """Get or create the global enhanced memory monitoring instance"""
    global _enhanced_memory_monitoring
    
    if _enhanced_memory_monitoring is None:
        _enhanced_memory_monitoring = EnhancedMemoryMonitoring(config)
    
    return _enhanced_memory_monitoring