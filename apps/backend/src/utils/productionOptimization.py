"""
Production Optimization and Performance Tuning for Enhanced Agents

This module provides production-ready optimizations for the LangGraph + Graphiti + MCP
enterprise system, including:

- Connection pooling and resource management
- Caching strategies for frequent operations
- Batch processing optimizations
- Memory management and cleanup
- Performance profiling and tuning
- Auto-scaling and load balancing strategies
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import gc
import psutil
import threading
from collections import defaultdict, deque
from functools import wraps, lru_cache

from ..utils.logger import logger

class OptimizationLevel(Enum):
    """Production optimization levels"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_PERFORMANCE = "high_performance"

@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization tracking"""
    cpu_usage: float
    memory_usage: float
    response_time: float
    throughput: float
    cache_hit_rate: float
    error_rate: float
    timestamp: datetime

@dataclass
class OptimizationConfig:
    """Configuration for production optimizations"""
    level: OptimizationLevel
    max_concurrent_workflows: int = 50
    connection_pool_size: int = 20
    cache_ttl: int = 3600  # seconds
    batch_size: int = 10
    gc_threshold: int = 100  # operations before garbage collection
    memory_limit_mb: int = 2048
    auto_scaling_enabled: bool = True
    monitoring_interval: int = 60  # seconds

class ConnectionPool:
    """Production-grade connection pool for external services"""
    
    def __init__(self, max_connections: int = 20):
        self.max_connections = max_connections
        self.active_connections = {}
        self.connection_queue = asyncio.Queue(maxsize=max_connections)
        self.stats = {
            "total_created": 0,
            "total_reused": 0,
            "total_errors": 0,
            "active_count": 0
        }
        
        # Pre-populate the pool
        for _ in range(max_connections):
            self.connection_queue.put_nowait(None)
    
    async def get_connection(self, service_type: str, config: Dict = None):
        """Get a connection from the pool"""
        try:
            # Wait for available connection slot
            await self.connection_queue.get()
            
            connection_key = f"{service_type}_{hash(str(config))}"
            
            if connection_key in self.active_connections:
                # Reuse existing connection
                connection = self.active_connections[connection_key]
                self.stats["total_reused"] += 1
                logger.debug(f"♻️ Reusing connection for {service_type}")
                return connection
            else:
                # Create new connection
                connection = await self._create_connection(service_type, config)
                self.active_connections[connection_key] = connection
                self.stats["total_created"] += 1
                self.stats["active_count"] += 1
                logger.debug(f"🔗 Created new connection for {service_type}")
                return connection
                
        except Exception as error:
            self.stats["total_errors"] += 1
            logger.error(f"❌ Connection pool error: {error}")
            # Release the slot back to queue
            self.connection_queue.put_nowait(None)
            raise
    
    async def release_connection(self, connection, service_type: str):
        """Release a connection back to the pool"""
        try:
            # Put the slot back in the queue
            self.connection_queue.put_nowait(None)
            logger.debug(f"🔓 Released connection for {service_type}")
        except Exception as error:
            logger.error(f"❌ Error releasing connection: {error}")
    
    async def _create_connection(self, service_type: str, config: Dict = None):
        """Create a new connection based on service type"""
        if service_type == "graphiti":
            # Mock Graphiti connection
            return {"type": "graphiti", "status": "connected", "config": config}
        elif service_type == "neo4j":
            # Mock Neo4j connection
            return {"type": "neo4j", "status": "connected", "config": config}
        elif service_type == "openai":
            # Mock OpenAI connection
            return {"type": "openai", "status": "connected", "config": config}
        else:
            return {"type": "generic", "status": "connected", "config": config}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the connection pool"""
        return {
            "max_connections": self.max_connections,
            "active_connections": len(self.active_connections),
            "available_slots": self.connection_queue.qsize(),
            "stats": self.stats,
            "health_status": "healthy" if self.stats["total_errors"] < 10 else "degraded"
        }

class IntelligentCache:
    """Production-optimized caching system with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = {}
        self.access_times = {}
        self.expiry_times = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired": 0
        }
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with TTL and LRU tracking"""
        with self._lock:
            current_time = time.time()
            
            if key not in self.cache:
                self.stats["misses"] += 1
                return None
            
            # Check if expired
            if current_time > self.expiry_times.get(key, 0):
                self._remove_key(key)
                self.stats["expired"] += 1
                self.stats["misses"] += 1
                return None
            
            # Update access time for LRU
            self.access_times[key] = current_time
            self.stats["hits"] += 1
            
            logger.debug(f"💾 Cache hit for key: {key}")
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache with TTL"""
        with self._lock:
            current_time = time.time()
            ttl = ttl or self.default_ttl
            
            # Evict if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            self.cache[key] = value
            self.access_times[key] = current_time
            self.expiry_times[key] = current_time + ttl
            
            logger.debug(f"💾 Cache set for key: {key}, TTL: {ttl}s")
    
    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache key"""
        with self._lock:
            if key in self.cache:
                self._remove_key(key)
                logger.debug(f"🗑️ Cache invalidated for key: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
            self.expiry_times.clear()
            logger.info("🧹 Cache cleared")
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self.cache:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        self._remove_key(lru_key)
        self.stats["evictions"] += 1
        logger.debug(f"🗑️ LRU evicted key: {lru_key}")
    
    def _remove_key(self, key: str) -> None:
        """Remove a key from all cache structures"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.expiry_times.pop(key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / max(total_requests, 1)) * 100
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "current_size": len(self.cache),
            "max_size": self.max_size
        }

class BatchProcessor:
    """Batch processing for efficient bulk operations"""
    
    def __init__(self, batch_size: int = 10, max_wait_time: float = 1.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.batches = defaultdict(list)
        self.batch_timers = {}
        self.processors = {}
        self.stats = defaultdict(int)
    
    async def add_to_batch(
        self,
        batch_type: str,
        item: Any,
        processor_func: callable = None
    ) -> Any:
        """Add item to batch for processing"""
        if processor_func:
            self.processors[batch_type] = processor_func
        
        self.batches[batch_type].append(item)
        self.stats[f"{batch_type}_items"] += 1
        
        # Set timer for batch if not already set
        if batch_type not in self.batch_timers:
            self.batch_timers[batch_type] = asyncio.create_task(
                self._wait_and_process(batch_type)
            )
        
        # Process immediately if batch is full
        if len(self.batches[batch_type]) >= self.batch_size:
            await self._process_batch(batch_type)
        
        logger.debug(f"📦 Added item to {batch_type} batch, size: {len(self.batches[batch_type])}")
    
    async def _wait_and_process(self, batch_type: str):
        """Wait for max time then process batch"""
        try:
            await asyncio.sleep(self.max_wait_time)
            if self.batches[batch_type]:  # Check if batch still has items
                await self._process_batch(batch_type)
        except asyncio.CancelledError:
            pass  # Timer was cancelled because batch was processed early
    
    async def _process_batch(self, batch_type: str):
        """Process a complete batch"""
        if not self.batches[batch_type]:
            return
        
        batch_items = self.batches[batch_type].copy()
        self.batches[batch_type].clear()
        
        # Cancel the timer
        if batch_type in self.batch_timers:
            self.batch_timers[batch_type].cancel()
            del self.batch_timers[batch_type]
        
        # Process the batch
        if batch_type in self.processors:
            try:
                await self.processors[batch_type](batch_items)
                self.stats[f"{batch_type}_batches_processed"] += 1
                logger.info(f"⚡ Processed batch of {len(batch_items)} {batch_type} items")
            except Exception as error:
                self.stats[f"{batch_type}_batch_errors"] += 1
                logger.error(f"❌ Batch processing error for {batch_type}: {error}")
    
    async def flush_all(self):
        """Flush all pending batches"""
        for batch_type in list(self.batches.keys()):
            if self.batches[batch_type]:
                await self._process_batch(batch_type)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        return dict(self.stats)

class ResourceMonitor:
    """Monitor and manage system resources"""
    
    def __init__(self, memory_limit_mb: int = 2048):
        self.memory_limit_mb = memory_limit_mb
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.process = psutil.Process()
        self.stats_history = deque(maxlen=100)
        self.alerts = []
    
    async def check_resources(self) -> PerformanceMetrics:
        """Check current resource usage"""
        try:
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            
            # Memory usage
            memory_info = self.process.memory_info()
            memory_percent = (memory_info.rss / self.memory_limit_bytes) * 100
            
            metrics = PerformanceMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                response_time=0.0,  # Will be updated by callers
                throughput=0.0,  # Will be updated by callers
                cache_hit_rate=0.0,  # Will be updated by callers
                error_rate=0.0,  # Will be updated by callers
                timestamp=datetime.now()
            )
            
            self.stats_history.append(metrics)
            
            # Check for alerts
            await self._check_resource_alerts(metrics)
            
            return metrics
            
        except Exception as error:
            logger.error(f"❌ Resource monitoring error: {error}")
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, datetime.now())
    
    async def _check_resource_alerts(self, metrics: PerformanceMetrics):
        """Check for resource-based alerts"""
        alerts = []
        
        if metrics.memory_usage > 90:
            alerts.append({
                "type": "memory_critical",
                "message": f"Memory usage critical: {metrics.memory_usage:.1f}%",
                "severity": "critical"
            })
        elif metrics.memory_usage > 80:
            alerts.append({
                "type": "memory_warning",
                "message": f"Memory usage high: {metrics.memory_usage:.1f}%",
                "severity": "warning"
            })
        
        if metrics.cpu_usage > 90:
            alerts.append({
                "type": "cpu_critical",
                "message": f"CPU usage critical: {metrics.cpu_usage:.1f}%",
                "severity": "critical"
            })
        
        # Store alerts
        for alert in alerts:
            alert["timestamp"] = datetime.now()
            self.alerts.append(alert)
            logger.warning(f"🚨 Resource alert: {alert['message']}")
        
        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    async def trigger_gc_if_needed(self, operation_count: int, gc_threshold: int = 100):
        """Trigger garbage collection if needed"""
        if operation_count % gc_threshold == 0:
            collected = gc.collect()
            logger.info(f"🗑️ Garbage collection: {collected} objects collected")
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get resource statistics"""
        if not self.stats_history:
            return {"status": "no_data"}
        
        recent_metrics = list(self.stats_history)[-10:]  # Last 10 readings
        
        return {
            "current": {
                "cpu_usage": recent_metrics[-1].cpu_usage,
                "memory_usage": recent_metrics[-1].memory_usage,
                "timestamp": recent_metrics[-1].timestamp.isoformat()
            },
            "averages": {
                "cpu_usage": sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
                "memory_usage": sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            },
            "alerts": self.alerts[-5:],  # Last 5 alerts
            "memory_limit_mb": self.memory_limit_mb
        }

class ProductionOptimizer:
    """Main production optimization manager"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.connection_pool = ConnectionPool(config.connection_pool_size)
        self.cache = IntelligentCache(max_size=1000, default_ttl=config.cache_ttl)
        self.batch_processor = BatchProcessor(batch_size=config.batch_size)
        self.resource_monitor = ResourceMonitor(config.memory_limit_mb)
        
        self.operation_count = 0
        self.start_time = datetime.now()
        self.optimization_stats = {
            "total_operations": 0,
            "cache_operations": 0,
            "batch_operations": 0,
            "gc_triggers": 0
        }
        
        # Start background monitoring
        if config.level in [OptimizationLevel.PRODUCTION, OptimizationLevel.HIGH_PERFORMANCE]:
            asyncio.create_task(self._background_monitoring())
        
        logger.info(f"🚀 Production optimizer initialized with {config.level.value} level")
    
    async def _background_monitoring(self):
        """Background task for continuous monitoring"""
        while True:
            try:
                await asyncio.sleep(self.config.monitoring_interval)
                
                # Check resources
                metrics = await self.resource_monitor.check_resources()
                
                # Trigger optimizations if needed
                await self._auto_optimize(metrics)
                
            except Exception as error:
                logger.error(f"❌ Background monitoring error: {error}")
    
    async def _auto_optimize(self, metrics: PerformanceMetrics):
        """Automatic optimization based on metrics"""
        try:
            # Memory optimization
            if metrics.memory_usage > 80:
                await self.resource_monitor.trigger_gc_if_needed(1, 1)  # Force GC
                self.cache.clear()  # Clear cache to free memory
                logger.info("🧹 Auto-optimization: Cleared cache due to high memory usage")
            
            # Batch processing optimization
            if self.operation_count > 100:
                await self.batch_processor.flush_all()
                logger.info("⚡ Auto-optimization: Flushed all batches")
            
        except Exception as error:
            logger.error(f"❌ Auto-optimization error: {error}")
    
    # Decorator for performance optimization
    def optimize_performance(self, cache_key_func=None, batch_type=None):
        """Decorator to add performance optimizations to functions"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                self.operation_count += 1
                self.optimization_stats["total_operations"] += 1
                
                try:
                    # Try cache first if cache key function provided
                    if cache_key_func:
                        cache_key = cache_key_func(*args, **kwargs)
                        cached_result = self.cache.get(cache_key)
                        if cached_result is not None:
                            self.optimization_stats["cache_operations"] += 1
                            return cached_result
                    
                    # Execute function
                    if batch_type:
                        # Add to batch for processing
                        result = await self.batch_processor.add_to_batch(
                            batch_type, 
                            {"args": args, "kwargs": kwargs},
                            lambda items: func(*args, **kwargs)
                        )
                        self.optimization_stats["batch_operations"] += 1
                    else:
                        result = await func(*args, **kwargs)
                    
                    # Cache result if cache key function provided
                    if cache_key_func:
                        cache_key = cache_key_func(*args, **kwargs)
                        self.cache.set(cache_key, result)
                    
                    # Periodic cleanup
                    if self.operation_count % self.config.gc_threshold == 0:
                        await self.resource_monitor.trigger_gc_if_needed(
                            self.operation_count, 
                            self.config.gc_threshold
                        )
                        self.optimization_stats["gc_triggers"] += 1
                    
                    return result
                    
                except Exception as error:
                    logger.error(f"❌ Optimized function error: {error}")
                    raise
                finally:
                    # Update performance metrics
                    duration = time.time() - start_time
                    logger.debug(f"⚡ Operation completed in {duration:.3f}s")
            
            return wrapper
        return decorator
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report"""
        try:
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            return {
                "config": {
                    "level": self.config.level.value,
                    "max_concurrent_workflows": self.config.max_concurrent_workflows,
                    "connection_pool_size": self.config.connection_pool_size,
                    "cache_ttl": self.config.cache_ttl,
                    "batch_size": self.config.batch_size
                },
                "connection_pool": await self.connection_pool.health_check(),
                "cache": self.cache.get_stats(),
                "batch_processor": self.batch_processor.get_stats(),
                "resource_monitor": self.resource_monitor.get_resource_stats(),
                "optimization_stats": {
                    **self.optimization_stats,
                    "uptime_seconds": uptime,
                    "operations_per_second": self.optimization_stats["total_operations"] / max(uptime, 1)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as error:
            logger.error(f"❌ Optimization report error: {error}")
            return {"error": str(error)}
    
    async def cleanup(self):
        """Clean up optimization resources"""
        try:
            await self.batch_processor.flush_all()
            self.cache.clear()
            logger.info("🧹 Production optimizer cleaned up successfully")
        except Exception as error:
            logger.error(f"❌ Cleanup error: {error}")

# Global optimizer instance
_production_optimizer = None

def get_production_optimizer(config: OptimizationConfig = None) -> ProductionOptimizer:
    """Get or create the global production optimizer instance"""
    global _production_optimizer
    
    if _production_optimizer is None:
        if config is None:
            config = OptimizationConfig(
                level=OptimizationLevel.PRODUCTION,
                max_concurrent_workflows=50,
                connection_pool_size=20,
                cache_ttl=3600,
                batch_size=10,
                memory_limit_mb=2048
            )
        _production_optimizer = ProductionOptimizer(config)
    
    return _production_optimizer

# Utility functions for common optimizations

@lru_cache(maxsize=128)
def cached_config_lookup(config_key: str) -> Any:
    """Cached configuration lookup"""
    # Mock configuration lookup
    configs = {
        "default_llm_model": "gpt-4-turbo-preview",
        "max_context_length": 8192,
        "default_temperature": 0.1
    }
    return configs.get(config_key, None)

def performance_profile(func):
    """Simple performance profiling decorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        
        if duration > 1.0:  # Log slow operations
            logger.warning(f"🐌 Slow operation: {func.__name__} took {duration:.3f}s")
        
        return result
    return wrapper