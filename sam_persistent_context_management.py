#!/usr/bin/env python3
"""
SAM Persistent Context Management System
Sistema avanzado de gestión de contexto persistente y estado para SAM
"""

import asyncio
import json
import time
import uuid
import logging
import pickle
import hashlib
import gzip
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
import redis
import pymongo
from contextlib import asynccontextmanager
import weakref
import os
from pathlib import Path
import aiofiles
import msgpack
from collections import OrderedDict, defaultdict

class ContextType(Enum):
    """Tipos de contexto"""
    CONVERSATION = "conversation"
    TASK_STATE = "task_state"
    AGENT_MEMORY = "agent_memory"
    SESSION_DATA = "session_data"
    WORKFLOW_STATE = "workflow_state"
    CACHE_DATA = "cache_data"
    TEMPORARY = "temporary"

class StorageBackend(Enum):
    """Backends de almacenamiento"""
    SQLITE = "sqlite"
    REDIS = "redis"
    MONGODB = "mongodb"
    FILE_SYSTEM = "file_system"
    MEMORY = "memory"
    HYBRID = "hybrid"

class CompressionType(Enum):
    """Tipos de compresión"""
    NONE = "none"
    GZIP = "gzip"
    MSGPACK = "msgpack"
    PICKLE = "pickle"

@dataclass
class ContextMetadata:
    """Metadatos del contexto"""
    context_id: str
    context_type: ContextType
    agent_id: str
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    size_bytes: int = 0
    compression: CompressionType = CompressionType.NONE
    storage_backend: StorageBackend = StorageBackend.SQLITE
    access_count: int = 0
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # 1-10, donde 10 es máxima prioridad
    checksum: Optional[str] = None

@dataclass
class ContextData:
    """Datos del contexto"""
    metadata: ContextMetadata
    content: Any
    
    def calculate_checksum(self) -> str:
        """Calcular checksum del contenido"""
        content_str = json.dumps(self.content, sort_keys=True) if isinstance(self.content, dict) else str(self.content)
        return hashlib.sha256(content_str.encode()).hexdigest()

class ContextCache:
    """Cache en memoria para contextos frecuentemente accedidos"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, Tuple[ContextData, float]] = OrderedDict()
        self.access_stats: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
    
    def get(self, context_id: str) -> Optional[ContextData]:
        """Obtener contexto del cache"""
        with self._lock:
            if context_id in self.cache:
                context_data, timestamp = self.cache[context_id]
                
                # Verificar TTL
                if time.time() - timestamp > self.ttl:
                    del self.cache[context_id]
                    return None
                
                # Mover al final (LRU)
                self.cache.move_to_end(context_id)
                self.access_stats[context_id] += 1
                
                return context_data
            
            return None
    
    def put(self, context_id: str, context_data: ContextData):
        """Almacenar contexto en cache"""
        with self._lock:
            # Verificar límite de tamaño
            if len(self.cache) >= self.max_size and context_id not in self.cache:
                # Remover el menos recientemente usado
                oldest_id, _ = self.cache.popitem(last=False)
                self.access_stats.pop(oldest_id, None)
            
            self.cache[context_id] = (context_data, time.time())
            self.cache.move_to_end(context_id)
    
    def remove(self, context_id: str):
        """Remover contexto del cache"""
        with self._lock:
            self.cache.pop(context_id, None)
            self.access_stats.pop(context_id, None)
    
    def clear(self):
        """Limpiar cache completo"""
        with self._lock:
            self.cache.clear()
            self.access_stats.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        with self._lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_rate": sum(self.access_stats.values()) / max(len(self.access_stats), 1),
                "most_accessed": sorted(self.access_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            }

class SQLiteContextStorage:
    """Almacenamiento de contexto en SQLite"""
    
    def __init__(self, db_path: str = "/tmp/sam_context.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contexts (
                    context_id TEXT PRIMARY KEY,
                    context_type TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    task_id TEXT,
                    session_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    size_bytes INTEGER DEFAULT 0,
                    compression TEXT DEFAULT 'none',
                    storage_backend TEXT DEFAULT 'sqlite',
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    priority INTEGER DEFAULT 1,
                    checksum TEXT,
                    content BLOB NOT NULL
                )
            """)
            
            # Índices para optimización
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON contexts(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_id ON contexts(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON contexts(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_type ON contexts(context_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON contexts(expires_at)")
    
    async def store(self, context_data: ContextData) -> bool:
        """Almacenar contexto"""
        try:
            # Serializar contenido
            content_bytes = self._serialize_content(context_data.content, context_data.metadata.compression)
            
            # Actualizar metadatos
            context_data.metadata.size_bytes = len(content_bytes)
            context_data.metadata.updated_at = datetime.now().isoformat()
            context_data.metadata.checksum = context_data.calculate_checksum()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO contexts 
                    (context_id, context_type, agent_id, task_id, session_id,
                     created_at, updated_at, expires_at, size_bytes, compression,
                     storage_backend, access_count, last_accessed, tags, priority,
                     checksum, content)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    context_data.metadata.context_id,
                    context_data.metadata.context_type.value,
                    context_data.metadata.agent_id,
                    context_data.metadata.task_id,
                    context_data.metadata.session_id,
                    context_data.metadata.created_at,
                    context_data.metadata.updated_at,
                    context_data.metadata.expires_at,
                    context_data.metadata.size_bytes,
                    context_data.metadata.compression.value,
                    context_data.metadata.storage_backend.value,
                    context_data.metadata.access_count,
                    context_data.metadata.last_accessed,
                    json.dumps(context_data.metadata.tags),
                    context_data.metadata.priority,
                    context_data.metadata.checksum,
                    content_bytes
                ))
            
            return True
            
        except Exception as e:
            logging.error(f"Error storing context {context_data.metadata.context_id}: {e}")
            return False
    
    async def retrieve(self, context_id: str) -> Optional[ContextData]:
        """Recuperar contexto"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT context_type, agent_id, task_id, session_id, created_at,
                           updated_at, expires_at, size_bytes, compression, storage_backend,
                           access_count, last_accessed, tags, priority, checksum, content
                    FROM contexts WHERE context_id = ?
                """, (context_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Verificar expiración
                if row[6]:  # expires_at
                    expires_at = datetime.fromisoformat(row[6])
                    if datetime.now() > expires_at:
                        await self.delete(context_id)
                        return None
                
                # Crear metadatos
                metadata = ContextMetadata(
                    context_id=context_id,
                    context_type=ContextType(row[0]),
                    agent_id=row[1],
                    task_id=row[2],
                    session_id=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                    expires_at=row[6],
                    size_bytes=row[7],
                    compression=CompressionType(row[8]),
                    storage_backend=StorageBackend(row[9]),
                    access_count=row[10],
                    last_accessed=row[11],
                    tags=json.loads(row[12]),
                    priority=row[13],
                    checksum=row[14]
                )
                
                # Deserializar contenido
                content = self._deserialize_content(row[15], metadata.compression)
                
                # Actualizar estadísticas de acceso
                metadata.access_count += 1
                metadata.last_accessed = datetime.now().isoformat()
                
                conn.execute("""
                    UPDATE contexts SET access_count = ?, last_accessed = ?
                    WHERE context_id = ?
                """, (metadata.access_count, metadata.last_accessed, context_id))
                
                return ContextData(metadata=metadata, content=content)
                
        except Exception as e:
            logging.error(f"Error retrieving context {context_id}: {e}")
            return None
    
    async def delete(self, context_id: str) -> bool:
        """Eliminar contexto"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM contexts WHERE context_id = ?", (context_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting context {context_id}: {e}")
            return False
    
    async def list_contexts(self, 
                           agent_id: Optional[str] = None,
                           task_id: Optional[str] = None,
                           context_type: Optional[ContextType] = None,
                           limit: int = 100) -> List[ContextMetadata]:
        """Listar contextos con filtros"""
        try:
            query = "SELECT * FROM contexts WHERE 1=1"
            params = []
            
            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)
            
            if task_id:
                query += " AND task_id = ?"
                params.append(task_id)
            
            if context_type:
                query += " AND context_type = ?"
                params.append(context_type.value)
            
            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                
                contexts = []
                for row in cursor.fetchall():
                    metadata = ContextMetadata(
                        context_id=row[0],
                        context_type=ContextType(row[1]),
                        agent_id=row[2],
                        task_id=row[3],
                        session_id=row[4],
                        created_at=row[5],
                        updated_at=row[6],
                        expires_at=row[7],
                        size_bytes=row[8],
                        compression=CompressionType(row[9]),
                        storage_backend=StorageBackend(row[10]),
                        access_count=row[11],
                        last_accessed=row[12],
                        tags=json.loads(row[13]),
                        priority=row[14],
                        checksum=row[15]
                    )
                    contexts.append(metadata)
                
                return contexts
                
        except Exception as e:
            logging.error(f"Error listing contexts: {e}")
            return []
    
    def _serialize_content(self, content: Any, compression: CompressionType) -> bytes:
        """Serializar contenido con compresión"""
        if compression == CompressionType.PICKLE:
            data = pickle.dumps(content)
        elif compression == CompressionType.MSGPACK:
            data = msgpack.packb(content)
        else:  # JSON por defecto
            data = json.dumps(content).encode('utf-8')
        
        if compression == CompressionType.GZIP:
            data = gzip.compress(data)
        
        return data
    
    def _deserialize_content(self, data: bytes, compression: CompressionType) -> Any:
        """Deserializar contenido con descompresión"""
        if compression == CompressionType.GZIP:
            data = gzip.decompress(data)
        
        if compression == CompressionType.PICKLE:
            return pickle.loads(data)
        elif compression == CompressionType.MSGPACK:
            return msgpack.unpackb(data)
        else:  # JSON por defecto
            return json.loads(data.decode('utf-8'))

class RedisContextStorage:
    """Almacenamiento de contexto en Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        self.metadata_prefix = "ctx:meta:"
        self.content_prefix = "ctx:data:"
    
    async def store(self, context_data: ContextData) -> bool:
        """Almacenar contexto en Redis"""
        try:
            # Serializar contenido
            content_bytes = self._serialize_content(context_data.content, context_data.metadata.compression)
            
            # Actualizar metadatos
            context_data.metadata.size_bytes = len(content_bytes)
            context_data.metadata.updated_at = datetime.now().isoformat()
            context_data.metadata.checksum = context_data.calculate_checksum()
            
            # Almacenar metadatos
            metadata_key = f"{self.metadata_prefix}{context_data.metadata.context_id}"
            metadata_json = json.dumps(asdict(context_data.metadata))
            
            # Almacenar contenido
            content_key = f"{self.content_prefix}{context_data.metadata.context_id}"
            
            # Usar pipeline para atomicidad
            pipe = self.redis_client.pipeline()
            pipe.set(metadata_key, metadata_json)
            pipe.set(content_key, content_bytes)
            
            # Configurar TTL si está especificado
            if context_data.metadata.expires_at:
                expires_at = datetime.fromisoformat(context_data.metadata.expires_at)
                ttl = int((expires_at - datetime.now()).total_seconds())
                if ttl > 0:
                    pipe.expire(metadata_key, ttl)
                    pipe.expire(content_key, ttl)
            
            pipe.execute()
            return True
            
        except Exception as e:
            logging.error(f"Error storing context in Redis {context_data.metadata.context_id}: {e}")
            return False
    
    async def retrieve(self, context_id: str) -> Optional[ContextData]:
        """Recuperar contexto de Redis"""
        try:
            metadata_key = f"{self.metadata_prefix}{context_id}"
            content_key = f"{self.content_prefix}{context_id}"
            
            # Obtener metadatos y contenido
            pipe = self.redis_client.pipeline()
            pipe.get(metadata_key)
            pipe.get(content_key)
            results = pipe.execute()
            
            metadata_json, content_bytes = results
            
            if not metadata_json or not content_bytes:
                return None
            
            # Deserializar metadatos
            metadata_dict = json.loads(metadata_json)
            metadata = ContextMetadata(**metadata_dict)
            
            # Deserializar contenido
            content = self._deserialize_content(content_bytes, metadata.compression)
            
            # Actualizar estadísticas de acceso
            metadata.access_count += 1
            metadata.last_accessed = datetime.now().isoformat()
            
            # Actualizar metadatos en Redis
            updated_metadata_json = json.dumps(asdict(metadata))
            self.redis_client.set(metadata_key, updated_metadata_json)
            
            return ContextData(metadata=metadata, content=content)
            
        except Exception as e:
            logging.error(f"Error retrieving context from Redis {context_id}: {e}")
            return None
    
    async def delete(self, context_id: str) -> bool:
        """Eliminar contexto de Redis"""
        try:
            metadata_key = f"{self.metadata_prefix}{context_id}"
            content_key = f"{self.content_prefix}{context_id}"
            
            pipe = self.redis_client.pipeline()
            pipe.delete(metadata_key)
            pipe.delete(content_key)
            results = pipe.execute()
            
            return any(results)
            
        except Exception as e:
            logging.error(f"Error deleting context from Redis {context_id}: {e}")
            return False
    
    def _serialize_content(self, content: Any, compression: CompressionType) -> bytes:
        """Serializar contenido"""
        if compression == CompressionType.MSGPACK:
            return msgpack.packb(content)
        else:
            data = json.dumps(content).encode('utf-8')
            if compression == CompressionType.GZIP:
                data = gzip.compress(data)
            return data
    
    def _deserialize_content(self, data: bytes, compression: CompressionType) -> Any:
        """Deserializar contenido"""
        if compression == CompressionType.GZIP:
            data = gzip.decompress(data)
        
        if compression == CompressionType.MSGPACK:
            return msgpack.unpackb(data)
        else:
            return json.loads(data.decode('utf-8'))

class MongoDBContextStorage:
    """Almacenamiento de contexto en MongoDB"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", database: str = "sam_context"):
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client[database]
        self.collection = self.db.contexts
        
        # Crear índices
        self.collection.create_index("context_id", unique=True)
        self.collection.create_index("agent_id")
        self.collection.create_index("task_id")
        self.collection.create_index("context_type")
        self.collection.create_index("expires_at")
    
    async def store(self, context_data: ContextData) -> bool:
        """Almacenar contexto en MongoDB"""
        try:
            # Preparar documento
            doc = asdict(context_data.metadata)
            doc['content'] = context_data.content
            doc['updated_at'] = datetime.now().isoformat()
            doc['checksum'] = context_data.calculate_checksum()
            
            # Upsert documento
            result = self.collection.replace_one(
                {"context_id": context_data.metadata.context_id},
                doc,
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            logging.error(f"Error storing context in MongoDB {context_data.metadata.context_id}: {e}")
            return False
    
    async def retrieve(self, context_id: str) -> Optional[ContextData]:
        """Recuperar contexto de MongoDB"""
        try:
            doc = self.collection.find_one({"context_id": context_id})
            
            if not doc:
                return None
            
            # Verificar expiración
            if doc.get('expires_at'):
                expires_at = datetime.fromisoformat(doc['expires_at'])
                if datetime.now() > expires_at:
                    await self.delete(context_id)
                    return None
            
            # Extraer contenido
            content = doc.pop('content')
            
            # Crear metadatos
            metadata = ContextMetadata(**doc)
            
            # Actualizar estadísticas de acceso
            metadata.access_count += 1
            metadata.last_accessed = datetime.now().isoformat()
            
            self.collection.update_one(
                {"context_id": context_id},
                {"$set": {"access_count": metadata.access_count, "last_accessed": metadata.last_accessed}}
            )
            
            return ContextData(metadata=metadata, content=content)
            
        except Exception as e:
            logging.error(f"Error retrieving context from MongoDB {context_id}: {e}")
            return None
    
    async def delete(self, context_id: str) -> bool:
        """Eliminar contexto de MongoDB"""
        try:
            result = self.collection.delete_one({"context_id": context_id})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting context from MongoDB {context_id}: {e}")
            return False

class ContextManager:
    """Gestor principal de contexto persistente"""
    
    def __init__(self, 
                 primary_storage: StorageBackend = StorageBackend.SQLITE,
                 cache_enabled: bool = True,
                 cache_size: int = 1000,
                 cache_ttl: int = 3600):
        
        self.primary_storage = primary_storage
        self.storage_backends: Dict[StorageBackend, Any] = {}
        
        # Inicializar backends de almacenamiento
        self._init_storage_backends()
        
        # Cache en memoria
        self.cache = ContextCache(cache_size, cache_ttl) if cache_enabled else None
        
        # Configuración de compresión automática
        self.auto_compression_threshold = 1024  # bytes
        self.default_compression = CompressionType.GZIP
        
        # Configuración de TTL por tipo de contexto
        self.default_ttl = {
            ContextType.CONVERSATION: 86400 * 7,  # 7 días
            ContextType.TASK_STATE: 86400 * 3,    # 3 días
            ContextType.AGENT_MEMORY: 86400 * 30, # 30 días
            ContextType.SESSION_DATA: 86400,      # 1 día
            ContextType.WORKFLOW_STATE: 86400 * 7, # 7 días
            ContextType.CACHE_DATA: 3600,         # 1 hora
            ContextType.TEMPORARY: 1800           # 30 minutos
        }
        
        self.logger = logging.getLogger(__name__)
        
        # Iniciar tareas de mantenimiento
        asyncio.create_task(self._maintenance_loop())
    
    def _init_storage_backends(self):
        """Inicializar backends de almacenamiento"""
        try:
            # SQLite (siempre disponible)
            self.storage_backends[StorageBackend.SQLITE] = SQLiteContextStorage()
            
            # Redis (opcional)
            try:
                self.storage_backends[StorageBackend.REDIS] = RedisContextStorage()
            except Exception as e:
                self.logger.warning(f"Redis not available: {e}")
            
            # MongoDB (opcional)
            try:
                self.storage_backends[StorageBackend.MONGODB] = MongoDBContextStorage()
            except Exception as e:
                self.logger.warning(f"MongoDB not available: {e}")
                
        except Exception as e:
            self.logger.error(f"Error initializing storage backends: {e}")
    
    async def store_context(self,
                           context_id: str,
                           content: Any,
                           context_type: ContextType,
                           agent_id: str,
                           task_id: Optional[str] = None,
                           session_id: Optional[str] = None,
                           ttl: Optional[int] = None,
                           tags: Optional[List[str]] = None,
                           priority: int = 1,
                           compression: Optional[CompressionType] = None) -> bool:
        """Almacenar contexto"""
        try:
            # Determinar TTL
            if ttl is None:
                ttl = self.default_ttl.get(context_type, 86400)
            
            expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat() if ttl > 0 else None
            
            # Determinar compresión
            if compression is None:
                content_size = len(json.dumps(content).encode('utf-8'))
                compression = self.default_compression if content_size > self.auto_compression_threshold else CompressionType.NONE
            
            # Crear metadatos
            metadata = ContextMetadata(
                context_id=context_id,
                context_type=context_type,
                agent_id=agent_id,
                task_id=task_id,
                session_id=session_id,
                expires_at=expires_at,
                compression=compression,
                storage_backend=self.primary_storage,
                tags=tags or [],
                priority=priority
            )
            
            # Crear datos de contexto
            context_data = ContextData(metadata=metadata, content=content)
            
            # Almacenar en backend primario
            storage = self.storage_backends.get(self.primary_storage)
            if not storage:
                raise Exception(f"Primary storage backend {self.primary_storage.value} not available")
            
            success = await storage.store(context_data)
            
            if success:
                # Actualizar cache
                if self.cache:
                    self.cache.put(context_id, context_data)
                
                self.logger.info(f"Context {context_id} stored successfully")
                return True
            else:
                self.logger.error(f"Failed to store context {context_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error storing context {context_id}: {e}")
            return False
    
    async def retrieve_context(self, context_id: str) -> Optional[ContextData]:
        """Recuperar contexto"""
        try:
            # Verificar cache primero
            if self.cache:
                cached_data = self.cache.get(context_id)
                if cached_data:
                    self.logger.debug(f"Context {context_id} retrieved from cache")
                    return cached_data
            
            # Buscar en backend primario
            storage = self.storage_backends.get(self.primary_storage)
            if storage:
                context_data = await storage.retrieve(context_id)
                
                if context_data:
                    # Actualizar cache
                    if self.cache:
                        self.cache.put(context_id, context_data)
                    
                    self.logger.debug(f"Context {context_id} retrieved from {self.primary_storage.value}")
                    return context_data
            
            # Buscar en backends alternativos
            for backend_type, storage in self.storage_backends.items():
                if backend_type != self.primary_storage:
                    context_data = await storage.retrieve(context_id)
                    if context_data:
                        # Migrar al backend primario
                        await self.storage_backends[self.primary_storage].store(context_data)
                        
                        # Actualizar cache
                        if self.cache:
                            self.cache.put(context_id, context_data)
                        
                        self.logger.info(f"Context {context_id} migrated from {backend_type.value} to {self.primary_storage.value}")
                        return context_data
            
            self.logger.debug(f"Context {context_id} not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving context {context_id}: {e}")
            return None
    
    async def update_context(self, 
                           context_id: str, 
                           content: Any, 
                           merge: bool = False) -> bool:
        """Actualizar contexto existente"""
        try:
            # Recuperar contexto existente
            existing_context = await self.retrieve_context(context_id)
            if not existing_context:
                return False
            
            # Actualizar contenido
            if merge and isinstance(existing_context.content, dict) and isinstance(content, dict):
                existing_context.content.update(content)
            else:
                existing_context.content = content
            
            # Actualizar metadatos
            existing_context.metadata.updated_at = datetime.now().isoformat()
            existing_context.metadata.checksum = existing_context.calculate_checksum()
            
            # Almacenar contexto actualizado
            storage = self.storage_backends.get(self.primary_storage)
            success = await storage.store(existing_context)
            
            if success:
                # Actualizar cache
                if self.cache:
                    self.cache.put(context_id, existing_context)
                
                self.logger.info(f"Context {context_id} updated successfully")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating context {context_id}: {e}")
            return False
    
    async def delete_context(self, context_id: str) -> bool:
        """Eliminar contexto"""
        try:
            success = False
            
            # Eliminar de todos los backends
            for storage in self.storage_backends.values():
                if await storage.delete(context_id):
                    success = True
            
            # Eliminar del cache
            if self.cache:
                self.cache.remove(context_id)
            
            if success:
                self.logger.info(f"Context {context_id} deleted successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting context {context_id}: {e}")
            return False
    
    async def list_contexts(self,
                           agent_id: Optional[str] = None,
                           task_id: Optional[str] = None,
                           context_type: Optional[ContextType] = None,
                           limit: int = 100) -> List[ContextMetadata]:
        """Listar contextos con filtros"""
        try:
            storage = self.storage_backends.get(self.primary_storage)
            if storage and hasattr(storage, 'list_contexts'):
                return await storage.list_contexts(agent_id, task_id, context_type, limit)
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error listing contexts: {e}")
            return []
    
    async def cleanup_expired_contexts(self) -> int:
        """Limpiar contextos expirados"""
        try:
            cleaned_count = 0
            
            # Obtener todos los contextos
            all_contexts = await self.list_contexts(limit=10000)
            
            for metadata in all_contexts:
                if metadata.expires_at:
                    expires_at = datetime.fromisoformat(metadata.expires_at)
                    if datetime.now() > expires_at:
                        if await self.delete_context(metadata.context_id):
                            cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} expired contexts")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired contexts: {e}")
            return 0
    
    async def _maintenance_loop(self):
        """Loop de mantenimiento en background"""
        while True:
            try:
                # Limpiar contextos expirados cada hora
                await self.cleanup_expired_contexts()
                
                # Limpiar cache si está habilitado
                if self.cache:
                    # Limpiar entradas expiradas del cache
                    pass  # El cache se limpia automáticamente en get()
                
                await asyncio.sleep(3600)  # 1 hora
                
            except Exception as e:
                self.logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(3600)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del gestor de contexto"""
        stats = {
            "primary_storage": self.primary_storage.value,
            "available_backends": list(self.storage_backends.keys()),
            "cache_enabled": self.cache is not None
        }
        
        if self.cache:
            stats["cache_stats"] = self.cache.get_stats()
        
        return stats

# Instancia global del gestor de contexto
context_manager = ContextManager()

# Funciones de conveniencia para tipos específicos de contexto
async def store_conversation_context(agent_id: str, 
                                   conversation_data: Dict[str, Any],
                                   session_id: Optional[str] = None) -> str:
    """Almacenar contexto de conversación"""
    context_id = f"conv_{agent_id}_{int(time.time())}"
    
    await context_manager.store_context(
        context_id=context_id,
        content=conversation_data,
        context_type=ContextType.CONVERSATION,
        agent_id=agent_id,
        session_id=session_id,
        tags=["conversation", "dialogue"]
    )
    
    return context_id

async def store_task_state(agent_id: str,
                          task_id: str,
                          state_data: Dict[str, Any]) -> str:
    """Almacenar estado de tarea"""
    context_id = f"task_{task_id}_{agent_id}"
    
    await context_manager.store_context(
        context_id=context_id,
        content=state_data,
        context_type=ContextType.TASK_STATE,
        agent_id=agent_id,
        task_id=task_id,
        tags=["task", "state"]
    )
    
    return context_id

async def store_agent_memory(agent_id: str,
                           memory_data: Dict[str, Any],
                           memory_type: str = "general") -> str:
    """Almacenar memoria del agente"""
    context_id = f"memory_{agent_id}_{memory_type}_{int(time.time())}"
    
    await context_manager.store_context(
        context_id=context_id,
        content=memory_data,
        context_type=ContextType.AGENT_MEMORY,
        agent_id=agent_id,
        ttl=86400 * 30,  # 30 días
        tags=["memory", memory_type],
        priority=5
    )
    
    return context_id

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejemplo de uso
    async def demo():
        # Almacenar contexto de conversación
        conv_id = await store_conversation_context(
            agent_id="sam_001",
            conversation_data={
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"}
                ],
                "context": "greeting",
                "timestamp": datetime.now().isoformat()
            },
            session_id="session_123"
        )
        
        print(f"Stored conversation context: {conv_id}")
        
        # Recuperar contexto
        context_data = await context_manager.retrieve_context(conv_id)
        if context_data:
            print(f"Retrieved context: {context_data.content}")
        
        # Almacenar estado de tarea
        task_state_id = await store_task_state(
            agent_id="sam_001",
            task_id="task_456",
            state_data={
                "current_step": "analysis",
                "progress": 0.3,
                "intermediate_results": {"key": "value"},
                "next_actions": ["validate", "process"]
            }
        )
        
        print(f"Stored task state: {task_state_id}")
        
        # Mostrar estadísticas
        stats = context_manager.get_stats()
        print(f"Context manager stats: {json.dumps(stats, indent=2)}")
    
    # Ejecutar demo
    asyncio.run(demo())

