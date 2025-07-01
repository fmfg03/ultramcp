"""
Intelligent Caching System for LangGraph Nodes
Implements memoization and smart caching to optimize resource usage
"""

import hashlib
import json
import time
import pickle
import os
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
import weakref

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    timestamp: float
    access_count: int
    last_access: float
    input_hash: str
    node_name: str
    ttl: Optional[float] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def is_stale(self, max_age: float = 3600) -> bool:
        """Check if cache entry is stale (default 1 hour)"""
        return time.time() - self.timestamp > max_age
    
    def touch(self):
        """Update access information"""
        self.access_count += 1
        self.last_access = time.time()

class IntelligentCache:
    """
    Intelligent caching system with multiple eviction strategies
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 max_memory_mb: int = 100,
                 default_ttl: float = 3600,
                 persistence_path: Optional[str] = None):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.persistence_path = persistence_path
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0
        }
        
        # Load persisted cache if available
        self._load_cache()
        
        # Cleanup thread
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def _generate_key(self, node_name: str, inputs: Dict[str, Any], 
                     context: Optional[Dict] = None) -> str:
        """Generate cache key from inputs"""
        # Create deterministic hash from inputs
        cache_data = {
            'node': node_name,
            'inputs': self._normalize_inputs(inputs),
            'context': context or {}
        }
        
        # Sort keys for consistent hashing
        cache_str = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def _normalize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize inputs for consistent caching"""
        normalized = {}
        
        for key, value in inputs.items():
            if isinstance(value, (str, int, float, bool)):
                normalized[key] = value
            elif isinstance(value, (list, tuple)):
                normalized[key] = [self._normalize_value(v) for v in value]
            elif isinstance(value, dict):
                normalized[key] = self._normalize_inputs(value)
            else:
                # Convert complex objects to string representation
                normalized[key] = str(value)
        
        return normalized
    
    def _normalize_value(self, value: Any) -> Any:
        """Normalize individual values"""
        if isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, dict):
            return self._normalize_inputs(value)
        else:
            return str(value)
    
    def _calculate_size(self, obj: Any) -> int:
        """Calculate approximate size of object in bytes"""
        try:
            return len(pickle.dumps(obj))
        except:
            # Fallback to string representation
            return len(str(obj).encode('utf-8'))
    
    def get(self, node_name: str, inputs: Dict[str, Any], 
            context: Optional[Dict] = None) -> Optional[Any]:
        """Get cached result if available"""
        key = self._generate_key(node_name, inputs, context)
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._stats['misses'] += 1
                self._stats['evictions'] += 1
                return None
            
            # Update access info
            entry.touch()
            self._stats['hits'] += 1
            
            return entry.value
    
    def set(self, node_name: str, inputs: Dict[str, Any], 
            value: Any, ttl: Optional[float] = None,
            context: Optional[Dict] = None):
        """Cache a result"""
        key = self._generate_key(node_name, inputs, context)
        size_bytes = self._calculate_size(value)
        
        with self._lock:
            # Check memory limits
            if size_bytes > self.max_memory_bytes:
                # Object too large to cache
                return
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                access_count=1,
                last_access=time.time(),
                input_hash=key,
                node_name=node_name,
                ttl=ttl or self.default_ttl,
                size_bytes=size_bytes
            )
            
            # Evict if necessary
            self._evict_if_needed(size_bytes)
            
            # Store entry
            self._cache[key] = entry
            self._stats['size_bytes'] += size_bytes
    
    def _evict_if_needed(self, new_size: int):
        """Evict entries if cache limits exceeded"""
        # Check size limit
        while len(self._cache) >= self.max_size:
            self._evict_lru()
        
        # Check memory limit
        while self._stats['size_bytes'] + new_size > self.max_memory_bytes:
            self._evict_lru()
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].last_access)
        
        entry = self._cache.pop(lru_key)
        self._stats['size_bytes'] -= entry.size_bytes
        self._stats['evictions'] += 1
    
    def _periodic_cleanup(self):
        """Periodic cleanup of expired entries"""
        while True:
            time.sleep(300)  # Run every 5 minutes
            
            with self._lock:
                expired_keys = [
                    key for key, entry in self._cache.items()
                    if entry.is_expired()
                ]
                
                for key in expired_keys:
                    entry = self._cache.pop(key)
                    self._stats['size_bytes'] -= entry.size_bytes
                    self._stats['evictions'] += 1
    
    def _load_cache(self):
        """Load cache from persistence"""
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return
        
        try:
            with open(self.persistence_path, 'rb') as f:
                data = pickle.load(f)
                self._cache = data.get('cache', {})
                self._stats = data.get('stats', self._stats)
        except Exception as e:
            print(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save cache to persistence"""
        if not self.persistence_path:
            return
        
        try:
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            with open(self.persistence_path, 'wb') as f:
                pickle.dump({
                    'cache': self._cache,
                    'stats': self._stats
                }, f)
        except Exception as e:
            print(f"Failed to save cache: {e}")
    
    def clear(self, node_name: Optional[str] = None):
        """Clear cache entries"""
        with self._lock:
            if node_name:
                # Clear specific node cache
                keys_to_remove = [
                    key for key, entry in self._cache.items()
                    if entry.node_name == node_name
                ]
                for key in keys_to_remove:
                    entry = self._cache.pop(key)
                    self._stats['size_bytes'] -= entry.size_bytes
            else:
                # Clear all cache
                self._cache.clear()
                self._stats['size_bytes'] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            hit_rate = (self._stats['hits'] / 
                       (self._stats['hits'] + self._stats['misses'])
                       if self._stats['hits'] + self._stats['misses'] > 0 else 0)
            
            return {
                **self._stats,
                'hit_rate': hit_rate,
                'cache_size': len(self._cache),
                'memory_usage_mb': self._stats['size_bytes'] / (1024 * 1024)
            }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        with self._lock:
            entries_by_node = {}
            for entry in self._cache.values():
                node = entry.node_name
                if node not in entries_by_node:
                    entries_by_node[node] = {
                        'count': 0,
                        'size_bytes': 0,
                        'avg_access_count': 0,
                        'oldest_timestamp': float('inf'),
                        'newest_timestamp': 0
                    }
                
                info = entries_by_node[node]
                info['count'] += 1
                info['size_bytes'] += entry.size_bytes
                info['avg_access_count'] += entry.access_count
                info['oldest_timestamp'] = min(info['oldest_timestamp'], entry.timestamp)
                info['newest_timestamp'] = max(info['newest_timestamp'], entry.timestamp)
            
            # Calculate averages
            for info in entries_by_node.values():
                if info['count'] > 0:
                    info['avg_access_count'] /= info['count']
            
            return {
                'total_entries': len(self._cache),
                'entries_by_node': entries_by_node,
                'stats': self.get_stats()
            }

# Global cache instance
_global_cache = IntelligentCache(
    max_size=1000,
    max_memory_mb=100,
    default_ttl=3600,
    persistence_path='cache/langgraph_cache.pkl'
)

def cached_node(ttl: Optional[float] = None, 
                cache_key_fn: Optional[Callable] = None,
                skip_cache_fn: Optional[Callable] = None):
    """
    Decorator for caching LangGraph node results
    
    Args:
        ttl: Time to live for cache entries
        cache_key_fn: Custom function to generate cache key
        skip_cache_fn: Function to determine if caching should be skipped
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(state: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
            node_name = func.__name__
            
            # Check if caching should be skipped
            if skip_cache_fn and skip_cache_fn(state):
                return func(state, *args, **kwargs)
            
            # Generate cache key
            if cache_key_fn:
                cache_inputs = cache_key_fn(state)
            else:
                # Use relevant state fields for caching
                cache_inputs = {
                    k: v for k, v in state.items()
                    if k not in ['_metadata', '_internal', 'session_id']
                }
            
            # Try to get from cache
            cached_result = _global_cache.get(node_name, cache_inputs)
            if cached_result is not None:
                print(f"🎯 Cache HIT for {node_name}")
                return cached_result
            
            print(f"⚡ Cache MISS for {node_name} - executing...")
            
            # Execute function
            result = func(state, *args, **kwargs)
            
            # Cache result
            _global_cache.set(node_name, cache_inputs, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def smart_cache_key(state: Dict[str, Any]) -> Dict[str, Any]:
    """Smart cache key generation for common patterns"""
    key_fields = {}
    
    # Include task/query if present
    if 'task' in state:
        key_fields['task'] = state['task']
    if 'query' in state:
        key_fields['query'] = state['query']
    if 'question' in state:
        key_fields['question'] = state['question']
    
    # Include input data
    if 'input' in state:
        key_fields['input'] = state['input']
    
    # Include configuration that affects output
    if 'model' in state:
        key_fields['model'] = state['model']
    if 'temperature' in state:
        key_fields['temperature'] = state['temperature']
    if 'max_tokens' in state:
        key_fields['max_tokens'] = state['max_tokens']
    
    return key_fields

def should_skip_cache(state: Dict[str, Any]) -> bool:
    """Determine if caching should be skipped"""
    # Skip for real-time or time-sensitive queries
    if state.get('real_time', False):
        return True
    
    # Skip for user-specific or session-specific data
    if 'user_id' in state or 'session_id' in state:
        return True
    
    # Skip for random or non-deterministic operations
    if state.get('random', False) or state.get('non_deterministic', False):
        return True
    
    return False

# Utility functions for cache management
def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics"""
    return _global_cache.get_stats()

def get_cache_info() -> Dict[str, Any]:
    """Get detailed cache information"""
    return _global_cache.get_cache_info()

def clear_cache(node_name: Optional[str] = None):
    """Clear cache entries"""
    _global_cache.clear(node_name)

def save_cache():
    """Save cache to persistence"""
    _global_cache._save_cache()

# Example usage in LangGraph nodes
if __name__ == "__main__":
    # Example cached node
    @cached_node(ttl=1800, cache_key_fn=smart_cache_key, skip_cache_fn=should_skip_cache)
    def reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Example reasoning node with caching"""
        import time
        
        # Simulate expensive computation
        time.sleep(2)
        
        task = state.get('task', '')
        result = f"Analyzed task: {task}"
        
        return {
            **state,
            'reasoning_result': result,
            'reasoning_confidence': 0.85
        }
    
    # Test caching
    test_state = {'task': 'Create a landing page'}
    
    print("First call (should miss cache):")
    start = time.time()
    result1 = reasoning_node(test_state)
    print(f"Time: {time.time() - start:.2f}s")
    
    print("\nSecond call (should hit cache):")
    start = time.time()
    result2 = reasoning_node(test_state)
    print(f"Time: {time.time() - start:.2f}s")
    
    print(f"\nCache stats: {get_cache_stats()}")

