"""
Shared dependencies and resources for unified backend
Provides singleton access to databases and shared services
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
import aioredis
import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

# Global shared instances
_database_pool: Optional[asyncpg.Pool] = None
_redis_client: Optional[aioredis.Redis] = None
_qdrant_client: Optional[QdrantClient] = None
_shared_cache: Dict[str, Any] = {}

class SharedResourceManager:
    """Manages shared resources across all consolidated services"""
    
    def __init__(self):
        self.initialized = False
        self.resources = {}
    
    async def initialize(self):
        """Initialize all shared resources"""
        if self.initialized:
            return
        
        try:
            # Initialize database connection pool
            self.resources["database"] = await self._init_database()
            
            # Initialize Redis connection
            self.resources["redis"] = await self._init_redis()
            
            # Initialize Qdrant client
            self.resources["qdrant"] = await self._init_qdrant()
            
            self.initialized = True
            logger.info("✅ All shared resources initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize shared resources: {e}")
            raise
    
    async def _init_database(self) -> asyncpg.Pool:
        """Initialize PostgreSQL connection pool"""
        try:
            database_url = os.getenv(
                "DATABASE_URL",
                f"postgresql://{os.getenv('POSTGRES_USER', 'ultramcp')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'ultramcp_secure')}@"
                f"{os.getenv('POSTGRES_HOST', 'sam.chat')}:"
                f"{os.getenv('POSTGRES_PORT', '5432')}/"
                f"{os.getenv('POSTGRES_DB', 'ultramcp')}"
            )
            
            pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Test connection
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            logger.info("✅ Database pool initialized")
            return pool
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    async def _init_redis(self) -> aioredis.Redis:
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://sam.chat:6379")
            redis_password = os.getenv("REDIS_PASSWORD")
            
            if redis_password:
                redis_url = f"redis://:{redis_password}@{redis_url.split('@')[-1] if '@' in redis_url else redis_url.replace('redis://', '')}"
            
            redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            
            # Test connection
            await redis_client.ping()
            
            logger.info("✅ Redis client initialized")
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            raise
    
    async def _init_qdrant(self) -> QdrantClient:
        """Initialize Qdrant vector database client"""
        try:
            qdrant_url = os.getenv("QDRANT_URL", "http://sam.chat:6333")
            
            client = QdrantClient(url=qdrant_url)
            
            # Test connection
            collections = client.get_collections()
            
            logger.info("✅ Qdrant client initialized")
            return client
            
        except Exception as e:
            logger.error(f"❌ Qdrant initialization failed: {e}")
            raise
    
    def get_resource(self, name: str):
        """Get shared resource by name"""
        if not self.initialized:
            raise RuntimeError("Shared resources not initialized")
        return self.resources.get(name)
    
    async def cleanup(self):
        """Cleanup all shared resources"""
        try:
            if "database" in self.resources:
                await self.resources["database"].close()
                logger.info("✅ Database pool closed")
            
            if "redis" in self.resources:
                await self.resources["redis"].close()
                logger.info("✅ Redis client closed")
            
            if "qdrant" in self.resources:
                # Qdrant client doesn't need explicit closing
                logger.info("✅ Qdrant client cleaned up")
            
            self.resources.clear()
            self.initialized = False
            
        except Exception as e:
            logger.warning(f"⚠️ Error during cleanup: {e}")

# Global shared resource manager instance
_resource_manager = SharedResourceManager()

# Dependency injection functions
async def get_database() -> asyncpg.Pool:
    """Dependency injection for database pool"""
    global _database_pool
    
    if _database_pool is None:
        await _resource_manager.initialize()
        _database_pool = _resource_manager.get_resource("database")
    
    return _database_pool

async def get_redis() -> aioredis.Redis:
    """Dependency injection for Redis client"""
    global _redis_client
    
    if _redis_client is None:
        await _resource_manager.initialize()
        _redis_client = _resource_manager.get_resource("redis")
    
    return _redis_client

async def get_qdrant() -> QdrantClient:
    """Dependency injection for Qdrant client"""
    global _qdrant_client
    
    if _qdrant_client is None:
        await _resource_manager.initialize()
        _qdrant_client = _resource_manager.get_resource("qdrant")
    
    return _qdrant_client

def get_shared_cache() -> Dict[str, Any]:
    """Get shared in-memory cache"""
    return _shared_cache

# FastAPI dependencies
async def get_db_dependency():
    """FastAPI dependency for database"""
    return await get_database()

async def get_redis_dependency():
    """FastAPI dependency for Redis"""
    return await get_redis()

async def get_qdrant_dependency():
    """FastAPI dependency for Qdrant"""
    return await get_qdrant()

# Utility functions
async def execute_db_query(query: str, *args, fetch_one: bool = False, fetch_all: bool = False):
    """Execute database query with shared pool"""
    db_pool = await get_database()
    
    async with db_pool.acquire() as conn:
        if fetch_one:
            return await conn.fetchrow(query, *args)
        elif fetch_all:
            return await conn.fetch(query, *args)
        else:
            return await conn.execute(query, *args)

async def cache_get(key: str, default=None):
    """Get value from Redis cache"""
    try:
        redis_client = await get_redis()
        value = await redis_client.get(key)
        return value if value is not None else default
    except Exception as e:
        logger.warning(f"Cache get error for key {key}: {e}")
        return default

async def cache_set(key: str, value: Any, ttl: int = 3600):
    """Set value in Redis cache"""
    try:
        redis_client = await get_redis()
        await redis_client.setex(key, ttl, str(value))
    except Exception as e:
        logger.warning(f"Cache set error for key {key}: {e}")

async def vector_search(collection_name: str, query_vector: list, limit: int = 10):
    """Perform vector search in Qdrant"""
    try:
        qdrant_client = await get_qdrant()
        
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        return search_results
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []

# Health check functions
async def check_shared_resources_health() -> Dict[str, str]:
    """Check health of all shared resources"""
    health_status = {}
    
    try:
        # Check database
        db_pool = await get_database()
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Redis
        redis_client = await get_redis()
        await redis_client.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Qdrant
        qdrant_client = await get_qdrant()
        collections = qdrant_client.get_collections()
        health_status["qdrant"] = "healthy"
    except Exception as e:
        health_status["qdrant"] = f"unhealthy: {str(e)}"
    
    return health_status