"""
Cache management for Claude Code Memory
"""
import os
import json
import pickle
import hashlib
import time
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import threading
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cache entry"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int] = None
    tags: List[str] = None
    size_bytes: int = 0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl_seconds is None:
            return False
        
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return (datetime.utcnow() - self.created_at).total_seconds()

class CacheManager:
    """Advanced cache manager with multiple storage backends"""
    
    def __init__(self, 
                 cache_dir: str,
                 max_memory_size: int = 100 * 1024 * 1024,  # 100MB
                 max_disk_size: int = 1024 * 1024 * 1024,   # 1GB
                 default_ttl: int = 3600,  # 1 hour
                 cleanup_interval: int = 300):  # 5 minutes
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_size = max_memory_size
        self.max_disk_size = max_disk_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        # In-memory cache (LRU-like)
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.memory_size = 0
        self._lock = threading.RLock()
        
        # Initialize disk cache database
        self.db_path = self.cache_dir / "cache.db"
        self._init_database()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        
        logger.info(f"Cache manager initialized: {cache_dir}")
    
    def _init_database(self):
        """Initialize SQLite database for disk cache metadata"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    file_path TEXT,
                    created_at TEXT,
                    last_accessed TEXT,
                    access_count INTEGER,
                    ttl_seconds INTEGER,
                    tags TEXT,
                    size_bytes INTEGER
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tags ON cache_entries(tags)
            """)
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            yield conn
        finally:
            conn.close()
    
    def _generate_cache_key(self, *components: Any) -> str:
        """Generate a unique cache key from components"""
        key_string = ":".join(str(c) for c in components)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (bytes, bytearray)):
                return len(value)
            elif isinstance(value, (list, tuple, dict)):
                return len(pickle.dumps(value))
            else:
                return len(str(value).encode('utf-8'))
        except Exception:
            return 1024  # Default estimate
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cached data"""
        # Create subdirectories based on key prefix for better organization
        subdir = key[:2]
        cache_subdir = self.cache_dir / subdir
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / f"{key}.cache"
    
    def set(self, 
            key: str, 
            value: Any, 
            ttl: Optional[int] = None,
            tags: Optional[List[str]] = None,
            force_disk: bool = False) -> bool:
        """Store value in cache"""
        ttl = ttl or self.default_ttl
        tags = tags or []
        
        with self._lock:
            try:
                # Calculate size
                size_bytes = self._calculate_size(value)
                
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.utcnow(),
                    last_accessed=datetime.utcnow(),
                    access_count=0,
                    ttl_seconds=ttl,
                    tags=tags,
                    size_bytes=size_bytes
                )
                
                # Decide storage location
                if not force_disk and size_bytes < 1024 * 1024:  # < 1MB
                    # Try memory cache first
                    if self.memory_size + size_bytes <= self.max_memory_size:
                        self.memory_cache[key] = entry
                        self.memory_size += size_bytes
                        logger.debug(f"Cached to memory: {key} ({size_bytes} bytes)")
                        return True
                    else:
                        # Evict LRU items
                        self._evict_memory_cache(size_bytes)
                        if self.memory_size + size_bytes <= self.max_memory_size:
                            self.memory_cache[key] = entry
                            self.memory_size += size_bytes
                            logger.debug(f"Cached to memory after eviction: {key}")
                            return True
                
                # Fall back to disk cache
                return self._set_disk_cache(key, entry)
                
            except Exception as e:
                logger.error(f"Error setting cache key {key}: {e}")
                return False
    
    def _set_disk_cache(self, key: str, entry: CacheEntry) -> bool:
        """Store entry in disk cache"""
        try:
            # Check disk space
            if self._get_disk_cache_size() + entry.size_bytes > self.max_disk_size:
                self._evict_disk_cache(entry.size_bytes)
            
            # Save data to file
            file_path = self._get_file_path(key)
            
            if isinstance(entry.value, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(entry.value)
            elif isinstance(entry.value, bytes):
                with open(file_path, 'wb') as f:
                    f.write(entry.value)
            else:
                with open(file_path, 'wb') as f:
                    pickle.dump(entry.value, f)
            
            # Update database
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, file_path, created_at, last_accessed, access_count, ttl_seconds, tags, size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key,
                    str(file_path),
                    entry.created_at.isoformat(),
                    entry.last_accessed.isoformat(),
                    entry.access_count,
                    entry.ttl_seconds,
                    json.dumps(entry.tags),
                    entry.size_bytes
                ))
                conn.commit()
            
            logger.debug(f"Cached to disk: {key} ({entry.size_bytes} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting disk cache for {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve value from cache"""
        with self._lock:
            try:
                # Check memory cache first
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    
                    if entry.is_expired:
                        del self.memory_cache[key]
                        self.memory_size -= entry.size_bytes
                        return default
                    
                    # Update access info
                    entry.last_accessed = datetime.utcnow()
                    entry.access_count += 1
                    
                    return entry.value
                
                # Check disk cache
                return self._get_disk_cache(key, default)
                
            except Exception as e:
                logger.error(f"Error getting cache key {key}: {e}")
                return default
    
    def _get_disk_cache(self, key: str, default: Any = None) -> Any:
        """Retrieve value from disk cache"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT file_path, created_at, ttl_seconds, size_bytes 
                    FROM cache_entries WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                if not row:
                    return default
                
                file_path, created_at_str, ttl_seconds, size_bytes = row
                created_at = datetime.fromisoformat(created_at_str)
                
                # Check expiration
                if ttl_seconds and (datetime.utcnow() - created_at).total_seconds() > ttl_seconds:
                    self.delete(key)
                    return default
                
                # Load data from file
                file_path = Path(file_path)
                if not file_path.exists():
                    self.delete(key)
                    return default
                
                # Try to determine file type and load appropriately
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        value = f.read()
                except UnicodeDecodeError:
                    # Binary data or pickled object
                    with open(file_path, 'rb') as f:
                        data = f.read()
                        try:
                            value = pickle.loads(data)
                        except pickle.UnpicklingError:
                            value = data
                
                # Update access info
                conn.execute("""
                    UPDATE cache_entries 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE key = ?
                """, (datetime.utcnow().isoformat(), key))
                conn.commit()
                
                logger.debug(f"Retrieved from disk cache: {key}")
                return value
                
        except Exception as e:
            logger.error(f"Error getting disk cache for {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self._lock:
            try:
                deleted = False
                
                # Remove from memory cache
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    del self.memory_cache[key]
                    self.memory_size -= entry.size_bytes
                    deleted = True
                
                # Remove from disk cache
                with self._get_db_connection() as conn:
                    cursor = conn.execute("SELECT file_path FROM cache_entries WHERE key = ?", (key,))
                    row = cursor.fetchone()
                    
                    if row:
                        file_path = Path(row[0])
                        if file_path.exists():
                            file_path.unlink()
                        
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                        conn.commit()
                        deleted = True
                
                return deleted
                
            except Exception as e:
                logger.error(f"Error deleting cache key {key}: {e}")
                return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        with self._lock:
            # Check memory cache
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not entry.is_expired:
                    return True
                else:
                    # Clean up expired entry
                    del self.memory_cache[key]
                    self.memory_size -= entry.size_bytes
            
            # Check disk cache
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.execute("""
                        SELECT created_at, ttl_seconds FROM cache_entries WHERE key = ?
                    """, (key,))
                    
                    row = cursor.fetchone()
                    if row:
                        created_at_str, ttl_seconds = row
                        created_at = datetime.fromisoformat(created_at_str)
                        
                        if ttl_seconds and (datetime.utcnow() - created_at).total_seconds() > ttl_seconds:
                            self.delete(key)
                            return False
                        
                        return True
            
            except Exception as e:
                logger.error(f"Error checking cache key existence {key}: {e}")
            
            return False
    
    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear cache entries by tags"""
        cleared_count = 0
        
        with self._lock:
            try:
                # Clear from memory cache
                keys_to_delete = []
                for key, entry in self.memory_cache.items():
                    if any(tag in entry.tags for tag in tags):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    self.delete(key)
                    cleared_count += 1
                
                # Clear from disk cache
                with self._get_db_connection() as conn:
                    for tag in tags:
                        cursor = conn.execute("""
                            SELECT key FROM cache_entries WHERE tags LIKE ?
                        """, (f'%"{tag}"%',))
                        
                        keys = [row[0] for row in cursor.fetchall()]
                        for key in keys:
                            if self.delete(key):
                                cleared_count += 1
                
            except Exception as e:
                logger.error(f"Error clearing cache by tags {tags}: {e}")
        
        return cleared_count
    
    def clear_expired(self) -> int:
        """Clear all expired cache entries"""
        cleared_count = 0
        
        with self._lock:
            try:
                # Clear from memory cache
                keys_to_delete = []
                for key, entry in self.memory_cache.items():
                    if entry.is_expired:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    cleared_count += 1
                
                # Clear from disk cache
                with self._get_db_connection() as conn:
                    current_time = datetime.utcnow()
                    
                    cursor = conn.execute("""
                        SELECT key, created_at, ttl_seconds FROM cache_entries 
                        WHERE ttl_seconds IS NOT NULL
                    """)
                    
                    expired_keys = []
                    for key, created_at_str, ttl_seconds in cursor.fetchall():
                        created_at = datetime.fromisoformat(created_at_str)
                        if (current_time - created_at).total_seconds() > ttl_seconds:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        if self.delete(key):
                            cleared_count += 1
                
            except Exception as e:
                logger.error(f"Error clearing expired cache entries: {e}")
        
        return cleared_count
    
    def _evict_memory_cache(self, required_space: int):
        """Evict LRU items from memory cache to free space"""
        if not self.memory_cache:
            return
        
        # Sort by last accessed time (LRU first)
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        freed_space = 0
        for key, entry in sorted_entries:
            if freed_space >= required_space:
                break
            
            del self.memory_cache[key]
            self.memory_size -= entry.size_bytes
            freed_space += entry.size_bytes
            
            logger.debug(f"Evicted from memory cache: {key}")
    
    def _evict_disk_cache(self, required_space: int):
        """Evict LRU items from disk cache to free space"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT key, size_bytes FROM cache_entries 
                    ORDER BY last_accessed ASC
                """)
                
                freed_space = 0
                for key, size_bytes in cursor.fetchall():
                    if freed_space >= required_space:
                        break
                    
                    if self.delete(key):
                        freed_space += size_bytes
                        logger.debug(f"Evicted from disk cache: {key}")
        
        except Exception as e:
            logger.error(f"Error evicting disk cache: {e}")
    
    def _get_disk_cache_size(self) -> int:
        """Get total size of disk cache"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
                result = cursor.fetchone()
                return result[0] or 0
        except Exception:
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*), SUM(size_bytes), SUM(access_count) 
                    FROM cache_entries
                """)
                disk_count, disk_size, total_accesses = cursor.fetchone()
                
                disk_count = disk_count or 0
                disk_size = disk_size or 0
                total_accesses = total_accesses or 0
            
            return {
                'memory_cache': {
                    'entries': len(self.memory_cache),
                    'size_bytes': self.memory_size,
                    'max_size_bytes': self.max_memory_size,
                    'usage_percent': (self.memory_size / self.max_memory_size) * 100
                },
                'disk_cache': {
                    'entries': disk_count,
                    'size_bytes': disk_size,
                    'max_size_bytes': self.max_disk_size,
                    'usage_percent': (disk_size / self.max_disk_size) * 100
                },
                'total': {
                    'entries': len(self.memory_cache) + disk_count,
                    'accesses': total_accesses,
                    'size_bytes': self.memory_size + disk_size
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def _cleanup_worker(self):
        """Background cleanup worker"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                cleared = self.clear_expired()
                if cleared > 0:
                    logger.info(f"Cleaned up {cleared} expired cache entries")
            
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
    
    def shutdown(self):
        """Shutdown cache manager"""
        logger.info("Shutting down cache manager")
        
        # Note: Python threads are daemon threads and will be cleaned up automatically
        # We don't need to explicitly stop the cleanup thread
    
    # Context manager support
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

# Specialized cache managers
class ParseResultCache(CacheManager):
    """Cache manager specialized for parse results"""
    
    def __init__(self, cache_dir: str):
        super().__init__(
            cache_dir=cache_dir,
            default_ttl=24 * 3600,  # 24 hours for parse results
            max_memory_size=50 * 1024 * 1024,  # 50MB
            max_disk_size=500 * 1024 * 1024   # 500MB
        )
    
    def cache_parse_result(self, file_path: str, file_checksum: str, parse_result: Any) -> bool:
        """Cache a parse result with file-based key"""
        key = self._generate_cache_key("parse", file_path, file_checksum)
        return self.set(key, parse_result, tags=["parse_result", "file:" + file_path])
    
    def get_parse_result(self, file_path: str, file_checksum: str) -> Any:
        """Get cached parse result"""
        key = self._generate_cache_key("parse", file_path, file_checksum)
        return self.get(key)

class VectorCache(CacheManager):
    """Cache manager specialized for vectors"""
    
    def __init__(self, cache_dir: str):
        super().__init__(
            cache_dir=cache_dir,
            default_ttl=7 * 24 * 3600,  # 7 days for vectors
            max_memory_size=20 * 1024 * 1024,  # 20MB (vectors are large)
            max_disk_size=200 * 1024 * 1024   # 200MB
        )
    
    def cache_vector(self, content_hash: str, vector: List[float]) -> bool:
        """Cache a vector with content-based key"""
        key = self._generate_cache_key("vector", content_hash)
        return self.set(key, vector, tags=["vector"], force_disk=True)
    
    def get_vector(self, content_hash: str) -> Optional[List[float]]:
        """Get cached vector"""
        key = self._generate_cache_key("vector", content_hash)
        return self.get(key)