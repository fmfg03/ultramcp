# Performance Optimization and Caching for MCP System
# Enterprise-grade performance optimization with intelligent caching

import asyncio
import time
import json
import hashlib
import pickle
import zlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import aioredis
import aiocache
from aiocache import Cache, cached
from aiocache.serializers import PickleSerializer, JsonSerializer
import asyncpg
import aiohttp
from functools import wraps, lru_cache
import threading
import queue
import weakref
import gc
import psutil
import numpy as np
from collections import defaultdict, OrderedDict
import heapq
import bisect

T = TypeVar('T')

class CacheStrategy(Enum):
    """Cache strategies"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    ADAPTIVE = "adaptive"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"

class CacheLevel(Enum):
    """Cache levels"""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DATABASE = "l3_database"

class OptimizationTarget(Enum):
    """Optimization targets"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    CPU = "cpu"
    COST = "cost"

@dataclass
class CacheConfig:
    """Cache configuration"""
    strategy: CacheStrategy = CacheStrategy.LRU
    max_size: int = 1000
    ttl: int = 3600  # seconds
    serializer: str = "pickle"
    compression: bool = False
    namespace: str = "default"
    
@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    throughput: float = 0.0
    cache_hit_rate: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    error_rate: float = 0.0

class IntelligentCache(Generic[T]):
    """Intelligent multi-level cache with adaptive strategies"""
    
    def __init__(self, config: CacheConfig, redis_client: Optional[aioredis.Redis] = None):
        self.config = config
        self.redis = redis_client
        
        # L1 Cache (Memory)
        self.l1_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.l1_access_count: Dict[str, int] = defaultdict(int)
        self.l1_access_time: Dict[str, float] = {}
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'l1_hits': 0,
            'l2_hits': 0,
            'l3_hits': 0
        }
        
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[T]:
        """Get value from cache"""
        async with self._lock:
            # Try L1 cache first
            l1_result = await self._get_l1(key)
            if l1_result is not None:
                self.stats['hits'] += 1
                self.stats['l1_hits'] += 1
                return l1_result
            
            # Try L2 cache (Redis)
            if self.redis:
                l2_result = await self._get_l2(key)
                if l2_result is not None:
                    # Promote to L1
                    await self._set_l1(key, l2_result)
                    self.stats['hits'] += 1
                    self.stats['l2_hits'] += 1
                    return l2_result
            
            self.stats['misses'] += 1
            return None
    
    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        async with self._lock:
            ttl = ttl or self.config.ttl
            
            # Set in L1
            await self._set_l1(key, value, ttl)
            
            # Set in L2 (Redis)
            if self.redis:
                await self._set_l2(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        async with self._lock:
            # Delete from L1
            if key in self.l1_cache:
                del self.l1_cache[key]
                del self.l1_access_count[key]
                del self.l1_access_time[key]
            
            # Delete from L2
            if self.redis:
                await self.redis.delete(f"{self.config.namespace}:{key}")
    
    async def _get_l1(self, key: str) -> Optional[T]:
        """Get from L1 cache"""
        if key not in self.l1_cache:
            return None
        
        entry = self.l1_cache[key]
        
        # Check TTL
        if entry['expires_at'] and time.time() > entry['expires_at']:
            await self._evict_l1(key)
            return None
        
        # Update access statistics
        self.l1_access_count[key] += 1
        self.l1_access_time[key] = time.time()
        
        # Move to end for LRU
        if self.config.strategy == CacheStrategy.LRU:
            self.l1_cache.move_to_end(key)
        
        return entry['value']
    
    async def _set_l1(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set in L1 cache"""
        expires_at = time.time() + ttl if ttl else None
        
        entry = {
            'value': value,
            'created_at': time.time(),
            'expires_at': expires_at,
            'size': self._estimate_size(value)
        }
        
        self.l1_cache[key] = entry
        self.l1_access_count[key] = 1
        self.l1_access_time[key] = time.time()
        
        # Check if eviction is needed
        if len(self.l1_cache) > self.config.max_size:
            await self._evict_l1_by_strategy()
    
    async def _get_l2(self, key: str) -> Optional[T]:
        """Get from L2 cache (Redis)"""
        try:
            data = await self.redis.get(f"{self.config.namespace}:{key}")
            if data is None:
                return None
            
            if self.config.compression:
                data = zlib.decompress(data)
            
            if self.config.serializer == "json":
                return json.loads(data)
            else:
                return pickle.loads(data)
        
        except Exception as e:
            self.logger.error(f"L2 cache get error: {e}")
            return None
    
    async def _set_l2(self, key: str, value: T, ttl: int) -> None:
        """Set in L2 cache (Redis)"""
        try:
            if self.config.serializer == "json":
                data = json.dumps(value).encode()
            else:
                data = pickle.dumps(value)
            
            if self.config.compression:
                data = zlib.compress(data)
            
            await self.redis.setex(f"{self.config.namespace}:{key}", ttl, data)
        
        except Exception as e:
            self.logger.error(f"L2 cache set error: {e}")
    
    async def _evict_l1_by_strategy(self) -> None:
        """Evict from L1 cache based on strategy"""
        if self.config.strategy == CacheStrategy.LRU:
            # Remove least recently used
            key = next(iter(self.l1_cache))
            await self._evict_l1(key)
        
        elif self.config.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            key = min(self.l1_access_count, key=self.l1_access_count.get)
            await self._evict_l1(key)
        
        elif self.config.strategy == CacheStrategy.TTL:
            # Remove expired items first
            now = time.time()
            expired_keys = [
                key for key, entry in self.l1_cache.items()
                if entry['expires_at'] and now > entry['expires_at']
            ]
            
            if expired_keys:
                await self._evict_l1(expired_keys[0])
            else:
                # Fallback to LRU
                key = next(iter(self.l1_cache))
                await self._evict_l1(key)
        
        elif self.config.strategy == CacheStrategy.ADAPTIVE:
            # Adaptive eviction based on access patterns
            await self._adaptive_eviction()
    
    async def _evict_l1(self, key: str) -> None:
        """Evict specific key from L1"""
        if key in self.l1_cache:
            del self.l1_cache[key]
            del self.l1_access_count[key]
            del self.l1_access_time[key]
            self.stats['evictions'] += 1
    
    async def _adaptive_eviction(self) -> None:
        """Adaptive eviction strategy"""
        # Score each item based on multiple factors
        scores = {}
        now = time.time()
        
        for key, entry in self.l1_cache.items():
            access_count = self.l1_access_count[key]
            last_access = self.l1_access_time[key]
            age = now - entry['created_at']
            size = entry['size']
            
            # Calculate composite score (lower is better for eviction)
            frequency_score = access_count / max(age, 1)  # Access frequency
            recency_score = 1 / max(now - last_access, 1)  # Recency
            size_penalty = size / 1024  # Size penalty
            
            scores[key] = frequency_score + recency_score - size_penalty
        
        # Evict item with lowest score
        key_to_evict = min(scores, key=scores.get)
        await self._evict_l1(key_to_evict)
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value"""
        try:
            return len(pickle.dumps(value))
        except:
            return 1024  # Default estimate
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': hit_rate,
            'l1_size': len(self.l1_cache),
            'total_requests': total_requests
        }

class LLMCacheManager:
    """Specialized cache manager for LLM requests"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.cache = IntelligentCache(
            CacheConfig(
                strategy=CacheStrategy.ADAPTIVE,
                max_size=10000,
                ttl=86400,  # 24 hours
                namespace="llm_cache",
                compression=True
            ),
            redis_client
        )
        self.logger = logging.getLogger(__name__)
    
    def _generate_cache_key(self, provider: str, model: str, messages: List[Dict], **kwargs) -> str:
        """Generate cache key for LLM request"""
        # Create deterministic hash of request parameters
        request_data = {
            'provider': provider,
            'model': model,
            'messages': messages,
            'kwargs': sorted(kwargs.items())
        }
        
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(request_str.encode()).hexdigest()
    
    async def get_cached_response(self, provider: str, model: str, messages: List[Dict], **kwargs) -> Optional[Dict]:
        """Get cached LLM response"""
        cache_key = self._generate_cache_key(provider, model, messages, **kwargs)
        return await self.cache.get(cache_key)
    
    async def cache_response(self, provider: str, model: str, messages: List[Dict], response: Dict, **kwargs) -> None:
        """Cache LLM response"""
        cache_key = self._generate_cache_key(provider, model, messages, **kwargs)
        
        # Add metadata
        cached_response = {
            'response': response,
            'cached_at': datetime.utcnow().isoformat(),
            'provider': provider,
            'model': model
        }
        
        await self.cache.set(cache_key, cached_response)
    
    async def invalidate_model_cache(self, provider: str, model: str) -> None:
        """Invalidate all cache entries for a specific model"""
        pattern = f"llm_cache:*"
        
        if self.redis:
            keys = await self.redis.keys(pattern)
            for key in keys:
                try:
                    data = await self.redis.get(key)
                    if data:
                        cached_data = pickle.loads(data)
                        if (cached_data.get('provider') == provider and 
                            cached_data.get('model') == model):
                            await self.redis.delete(key)
                except Exception as e:
                    self.logger.error(f"Error invalidating cache key {key}: {e}")

class DatabaseQueryOptimizer:
    """Optimize database queries with caching and connection pooling"""
    
    def __init__(self, database_url: str, redis_client: aioredis.Redis):
        self.database_url = database_url
        self.redis = redis_client
        self.pool: Optional[asyncpg.Pool] = None
        
        # Query cache
        self.query_cache = IntelligentCache(
            CacheConfig(
                strategy=CacheStrategy.LRU,
                max_size=5000,
                ttl=1800,  # 30 minutes
                namespace="query_cache"
            ),
            redis_client
        )
        
        # Query statistics
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'cache_hits': 0
        })
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self, min_size: int = 10, max_size: int = 20) -> None:
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60
        )
    
    async def execute_query(self, query: str, *args, cache_ttl: Optional[int] = None, use_cache: bool = True) -> List[Dict]:
        """Execute query with caching"""
        # Generate cache key
        cache_key = self._generate_query_cache_key(query, args)
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        
        # Try cache first
        if use_cache:
            cached_result = await self.query_cache.get(cache_key)
            if cached_result is not None:
                self.query_stats[query_hash]['cache_hits'] += 1
                return cached_result
        
        # Execute query
        start_time = time.time()
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                result = [dict(row) for row in rows]
            
            execution_time = time.time() - start_time
            
            # Update statistics
            stats = self.query_stats[query_hash]
            stats['count'] += 1
            stats['total_time'] += execution_time
            stats['avg_time'] = stats['total_time'] / stats['count']
            
            # Cache result
            if use_cache and cache_ttl is not None:
                await self.query_cache.set(cache_key, result, cache_ttl)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    def _generate_query_cache_key(self, query: str, args: tuple) -> str:
        """Generate cache key for query"""
        key_data = {
            'query': query.strip(),
            'args': args
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    async def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """Get queries that exceed time threshold"""
        slow_queries = []
        
        for query_hash, stats in self.query_stats.items():
            if stats['avg_time'] > threshold:
                slow_queries.append({
                    'query_hash': query_hash,
                    'avg_time': stats['avg_time'],
                    'count': stats['count'],
                    'total_time': stats['total_time'],
                    'cache_hit_rate': stats['cache_hits'] / stats['count'] if stats['count'] > 0 else 0
                })
        
        return sorted(slow_queries, key=lambda x: x['avg_time'], reverse=True)
    
    async def optimize_query(self, query: str) -> str:
        """Suggest query optimizations"""
        optimizations = []
        
        # Basic optimization suggestions
        if 'SELECT *' in query.upper():
            optimizations.append("Consider selecting specific columns instead of SELECT *")
        
        if 'ORDER BY' in query.upper() and 'LIMIT' not in query.upper():
            optimizations.append("Consider adding LIMIT when using ORDER BY")
        
        if query.upper().count('JOIN') > 3:
            optimizations.append("Consider breaking down complex joins")
        
        if 'WHERE' not in query.upper() and 'SELECT' in query.upper():
            optimizations.append("Consider adding WHERE clause to filter results")
        
        return "; ".join(optimizations) if optimizations else "No obvious optimizations found"

class MemoryOptimizer:
    """Optimize memory usage and detect memory leaks"""
    
    def __init__(self):
        self.memory_snapshots: List[Dict[str, Any]] = []
        self.object_tracking: Dict[type, int] = defaultdict(int)
        self.logger = logging.getLogger(__name__)
    
    def take_memory_snapshot(self) -> Dict[str, Any]:
        """Take a memory snapshot"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        snapshot = {
            'timestamp': datetime.utcnow(),
            'rss': memory_info.rss,  # Resident Set Size
            'vms': memory_info.vms,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available,
            'gc_counts': gc.get_count(),
            'object_count': len(gc.get_objects())
        }
        
        self.memory_snapshots.append(snapshot)
        
        # Keep only last 100 snapshots
        if len(self.memory_snapshots) > 100:
            self.memory_snapshots.pop(0)
        
        return snapshot
    
    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks"""
        if len(self.memory_snapshots) < 10:
            return []
        
        leaks = []
        
        # Check for consistent memory growth
        recent_snapshots = self.memory_snapshots[-10:]
        memory_trend = [s['rss'] for s in recent_snapshots]
        
        # Calculate trend
        x = np.arange(len(memory_trend))
        slope = np.polyfit(x, memory_trend, 1)[0]
        
        if slope > 1024 * 1024:  # Growing by more than 1MB per snapshot
            leaks.append({
                'type': 'memory_growth',
                'severity': 'high' if slope > 10 * 1024 * 1024 else 'medium',
                'growth_rate': slope,
                'description': f'Memory growing at {slope / (1024*1024):.2f} MB per measurement'
            })
        
        # Check object count growth
        object_trend = [s['object_count'] for s in recent_snapshots]
        object_slope = np.polyfit(x, object_trend, 1)[0]
        
        if object_slope > 1000:  # Growing by more than 1000 objects
            leaks.append({
                'type': 'object_growth',
                'severity': 'medium',
                'growth_rate': object_slope,
                'description': f'Object count growing by {object_slope:.0f} objects per measurement'
            })
        
        return leaks
    
    def optimize_garbage_collection(self) -> Dict[str, Any]:
        """Optimize garbage collection"""
        # Force garbage collection
        collected = gc.collect()
        
        # Get GC statistics
        gc_stats = {
            'collected_objects': collected,
            'gc_counts': gc.get_count(),
            'gc_thresholds': gc.get_threshold()
        }
        
        # Suggest optimizations
        suggestions = []
        
        if gc_stats['gc_counts'][0] > 1000:
            suggestions.append("Consider increasing GC threshold for generation 0")
        
        if collected > 1000:
            suggestions.append("High number of collected objects - check for circular references")
        
        gc_stats['suggestions'] = suggestions
        
        return gc_stats
    
    def get_memory_usage_by_type(self) -> Dict[str, int]:
        """Get memory usage breakdown by object type"""
        type_counts = defaultdict(int)
        
        for obj in gc.get_objects():
            type_counts[type(obj).__name__] += 1
        
        # Sort by count
        return dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:20])

class PerformanceProfiler:
    """Profile application performance"""
    
    def __init__(self):
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'call_count': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0
        })
        self.logger = logging.getLogger(__name__)
    
    def profile_function(self, name: str = None):
        """Decorator to profile function performance"""
        def decorator(func):
            func_name = name or f"{func.__module__}.{func.__name__}"
            
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    finally:
                        execution_time = time.time() - start_time
                        self._update_stats(func_name, execution_time)
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        execution_time = time.time() - start_time
                        self._update_stats(func_name, execution_time)
                return sync_wrapper
        
        return decorator
    
    def _update_stats(self, func_name: str, execution_time: float):
        """Update function statistics"""
        stats = self.function_stats[func_name]
        stats['call_count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['call_count']
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report"""
        # Sort by total time
        sorted_stats = sorted(
            self.function_stats.items(),
            key=lambda x: x[1]['total_time'],
            reverse=True
        )
        
        report = {
            'top_functions_by_total_time': sorted_stats[:10],
            'top_functions_by_avg_time': sorted(
                self.function_stats.items(),
                key=lambda x: x[1]['avg_time'],
                reverse=True
            )[:10],
            'most_called_functions': sorted(
                self.function_stats.items(),
                key=lambda x: x[1]['call_count'],
                reverse=True
            )[:10]
        }
        
        return report
    
    def get_bottlenecks(self, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        for func_name, stats in self.function_stats.items():
            if stats['avg_time'] > threshold:
                bottlenecks.append({
                    'function': func_name,
                    'avg_time': stats['avg_time'],
                    'total_time': stats['total_time'],
                    'call_count': stats['call_count'],
                    'severity': 'high' if stats['avg_time'] > threshold * 5 else 'medium'
                })
        
        return sorted(bottlenecks, key=lambda x: x['total_time'], reverse=True)

class AdaptiveOptimizer:
    """Adaptive optimization based on runtime metrics"""
    
    def __init__(self):
        self.optimization_history: List[Dict[str, Any]] = []
        self.current_config: Dict[str, Any] = {}
        self.baseline_metrics: Optional[PerformanceMetrics] = None
        self.logger = logging.getLogger(__name__)
    
    async def optimize_cache_strategy(self, cache: IntelligentCache, metrics: PerformanceMetrics) -> CacheStrategy:
        """Optimize cache strategy based on metrics"""
        current_strategy = cache.config.strategy
        
        # Analyze current performance
        hit_rate = metrics.cache_hit_rate
        memory_usage = metrics.memory_usage
        
        # Decision logic
        if hit_rate < 0.5 and memory_usage < 0.7:
            # Low hit rate, plenty of memory - try LRU with larger size
            recommended_strategy = CacheStrategy.LRU
        elif hit_rate < 0.5 and memory_usage > 0.8:
            # Low hit rate, high memory - try LFU
            recommended_strategy = CacheStrategy.LFU
        elif hit_rate > 0.8:
            # Good hit rate - try adaptive for even better performance
            recommended_strategy = CacheStrategy.ADAPTIVE
        else:
            # Keep current strategy
            recommended_strategy = current_strategy
        
        # Record optimization attempt
        optimization = {
            'timestamp': datetime.utcnow(),
            'component': 'cache',
            'from_strategy': current_strategy.value,
            'to_strategy': recommended_strategy.value,
            'metrics': metrics,
            'reason': self._get_optimization_reason(hit_rate, memory_usage)
        }
        
        self.optimization_history.append(optimization)
        
        return recommended_strategy
    
    def _get_optimization_reason(self, hit_rate: float, memory_usage: float) -> str:
        """Get reason for optimization"""
        if hit_rate < 0.5 and memory_usage < 0.7:
            return "Low hit rate with available memory - increasing cache size"
        elif hit_rate < 0.5 and memory_usage > 0.8:
            return "Low hit rate with high memory usage - switching to frequency-based eviction"
        elif hit_rate > 0.8:
            return "Good hit rate - trying adaptive strategy for optimization"
        else:
            return "Maintaining current strategy"
    
    async def auto_tune_parameters(self, component: str, current_metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Auto-tune parameters based on metrics"""
        recommendations = {}
        
        if component == "database":
            # Database connection pool tuning
            if current_metrics.latency_p95 > 1.0:  # High latency
                recommendations['pool_size'] = 'increase'
                recommendations['connection_timeout'] = 'increase'
            
            if current_metrics.throughput < 100:  # Low throughput
                recommendations['max_connections'] = 'increase'
        
        elif component == "cache":
            # Cache tuning
            if current_metrics.cache_hit_rate < 0.6:
                recommendations['cache_size'] = 'increase'
                recommendations['ttl'] = 'increase'
            
            if current_metrics.memory_usage > 0.9:
                recommendations['eviction_policy'] = 'more_aggressive'
        
        elif component == "api":
            # API tuning
            if current_metrics.error_rate > 0.05:
                recommendations['timeout'] = 'increase'
                recommendations['retry_policy'] = 'more_conservative'
            
            if current_metrics.latency_p99 > 5.0:
                recommendations['worker_count'] = 'increase'
        
        return recommendations

# Example usage and integration
async def setup_performance_optimization():
    """Setup comprehensive performance optimization"""
    
    # Redis client for caching
    redis_client = await aioredis.from_url('redis://localhost:6379')
    
    # Initialize components
    llm_cache = LLMCacheManager(redis_client)
    db_optimizer = DatabaseQueryOptimizer('postgresql://user:pass@localhost/db', redis_client)
    memory_optimizer = MemoryOptimizer()
    profiler = PerformanceProfiler()
    adaptive_optimizer = AdaptiveOptimizer()
    
    # Initialize database pool
    await db_optimizer.initialize()
    
    return {
        'llm_cache': llm_cache,
        'db_optimizer': db_optimizer,
        'memory_optimizer': memory_optimizer,
        'profiler': profiler,
        'adaptive_optimizer': adaptive_optimizer
    }

# Decorators for easy integration
def cached_llm_request(cache_manager: LLMCacheManager):
    """Decorator for caching LLM requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(provider: str, model: str, messages: List[Dict], **kwargs):
            # Try cache first
            cached_response = await cache_manager.get_cached_response(provider, model, messages, **kwargs)
            if cached_response:
                return cached_response['response']
            
            # Execute function
            response = await func(provider, model, messages, **kwargs)
            
            # Cache response
            await cache_manager.cache_response(provider, model, messages, response, **kwargs)
            
            return response
        return wrapper
    return decorator

def optimized_db_query(db_optimizer: DatabaseQueryOptimizer, cache_ttl: int = 1800):
    """Decorator for optimized database queries"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need to be customized based on the specific function
            # For now, just profile the execution
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow queries
            if execution_time > 1.0:
                logging.warning(f"Slow query detected: {func.__name__} took {execution_time:.2f}s")
            
            return result
        return wrapper
    return decorator

if __name__ == "__main__":
    async def main():
        # Setup optimization
        optimization = await setup_performance_optimization()
        
        # Example: Cache LLM request
        @cached_llm_request(optimization['llm_cache'])
        async def call_llm(provider: str, model: str, messages: List[Dict], **kwargs):
            # Simulate LLM call
            await asyncio.sleep(1)
            return {"response": "Hello, world!", "tokens": 10}
        
        # Example: Profile function
        @optimization['profiler'].profile_function("example_function")
        async def example_function():
            await asyncio.sleep(0.1)
            return "result"
        
        # Test caching
        start_time = time.time()
        result1 = await call_llm("openai", "gpt-4", [{"role": "user", "content": "Hello"}])
        first_call_time = time.time() - start_time
        
        start_time = time.time()
        result2 = await call_llm("openai", "gpt-4", [{"role": "user", "content": "Hello"}])
        second_call_time = time.time() - start_time
        
        print(f"First call: {first_call_time:.3f}s")
        print(f"Second call (cached): {second_call_time:.3f}s")
        print(f"Cache speedup: {first_call_time / second_call_time:.1f}x")
        
        # Test profiling
        for _ in range(5):
            await example_function()
        
        report = optimization['profiler'].get_performance_report()
        print(f"Performance report: {report}")
        
        # Memory optimization
        snapshot = optimization['memory_optimizer'].take_memory_snapshot()
        print(f"Memory snapshot: {snapshot}")
    
    asyncio.run(main())

