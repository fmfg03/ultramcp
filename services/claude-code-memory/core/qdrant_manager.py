"""
Qdrant vector database management for Claude Code Memory
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import (
        Distance, VectorParams, PointStruct, Filter, FieldCondition, 
        MatchValue, SearchRequest, Record, UpdateResult, CollectionInfo
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Qdrant client not available. Install with: pip install qdrant-client")

logger = logging.getLogger(__name__)

@dataclass
class VectorPoint:
    """Represents a vector point in Qdrant"""
    id: str
    vector: List[float]
    payload: Dict[str, Any]

@dataclass
class CollectionStatus:
    """Status information for a Qdrant collection"""
    name: str
    points_count: int
    indexed_vectors_count: int
    vectors_config: Dict[str, Any]
    status: str
    optimizer_status: Dict[str, Any]

class QdrantManager:
    """Advanced Qdrant vector database manager"""
    
    def __init__(self, 
                 url: str = "http://sam.chat:6333",
                 api_key: Optional[str] = None,
                 timeout: int = 30):
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant client not available. Install with: pip install qdrant-client")
        
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.client: Optional[QdrantClient] = None
        self.is_connected = False
        
        # Default collection configurations
        self.default_vector_size = 384  # for all-MiniLM-L6-v2
        self.default_distance = Distance.COSINE
        
    async def connect(self) -> bool:
        """Establish connection to Qdrant"""
        try:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=self.timeout
            )
            
            # Test connection
            collections = await self.list_collections()
            self.is_connected = True
            logger.info(f"Connected to Qdrant at {self.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Qdrant"""
        if self.client:
            try:
                self.client.close()
                self.is_connected = False
                logger.info("Disconnected from Qdrant")
            except Exception as e:
                logger.error(f"Error disconnecting from Qdrant: {e}")
    
    async def list_collections(self) -> List[str]:
        """List all collections in Qdrant"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            collections_response = self.client.get_collections()
            return [collection.name for collection in collections_response.collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    async def create_collection(self, 
                               name: str, 
                               vector_size: int = None,
                               distance: Distance = None,
                               overwrite: bool = False) -> bool:
        """Create a new collection"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        vector_size = vector_size or self.default_vector_size
        distance = distance or self.default_distance
        
        try:
            # Check if collection exists
            existing_collections = await self.list_collections()
            
            if name in existing_collections:
                if overwrite:
                    await self.delete_collection(name)
                    logger.info(f"Deleted existing collection: {name}")
                else:
                    logger.info(f"Collection already exists: {name}")
                    return True
            
            # Create collection
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            logger.info(f"Created collection: {name} (size={vector_size}, distance={distance})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            return False
    
    async def delete_collection(self, name: str) -> bool:
        """Delete a collection"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            self.client.delete_collection(collection_name=name)
            logger.info(f"Deleted collection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {e}")
            return False
    
    async def get_collection_info(self, name: str) -> Optional[CollectionStatus]:
        """Get detailed information about a collection"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            collection_info = self.client.get_collection(collection_name=name)
            
            return CollectionStatus(
                name=name,
                points_count=collection_info.points_count or 0,
                indexed_vectors_count=collection_info.indexed_vectors_count or 0,
                vectors_config=collection_info.config.params.vectors.dict() if collection_info.config else {},
                status=collection_info.status.name if collection_info.status else "unknown",
                optimizer_status=collection_info.optimizer_status.dict() if collection_info.optimizer_status else {}
            )
            
        except Exception as e:
            logger.error(f"Error getting collection info for {name}: {e}")
            return None
    
    async def upsert_points(self, 
                           collection_name: str, 
                           points: List[VectorPoint],
                           batch_size: int = 100) -> Dict[str, int]:
        """Insert or update points in batches"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        stats = {"success": 0, "failed": 0}
        
        try:
            # Process in batches
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                
                # Convert to Qdrant PointStruct
                qdrant_points = []
                for point in batch:
                    try:
                        qdrant_point = PointStruct(
                            id=point.id,
                            vector=point.vector,
                            payload=point.payload
                        )
                        qdrant_points.append(qdrant_point)
                    except Exception as e:
                        logger.error(f"Error creating point {point.id}: {e}")
                        stats["failed"] += 1
                
                # Upsert batch
                if qdrant_points:
                    try:
                        operation_info = self.client.upsert(
                            collection_name=collection_name,
                            points=qdrant_points
                        )
                        stats["success"] += len(qdrant_points)
                        logger.debug(f"Upserted batch of {len(qdrant_points)} points")
                        
                    except Exception as e:
                        logger.error(f"Error upserting batch: {e}")
                        stats["failed"] += len(qdrant_points)
        
        except Exception as e:
            logger.error(f"Error in batch upsert: {e}")
            stats["failed"] += len(points)
        
        return stats
    
    async def search_vectors(self, 
                            collection_name: str,
                            query_vector: List[float],
                            limit: int = 10,
                            score_threshold: float = 0.0,
                            filter_conditions: Optional[Filter] = None) -> List[Record]:
        """Search for similar vectors"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=filter_conditions,
                limit=limit,
                score_threshold=score_threshold
            )
            
            logger.debug(f"Found {len(search_result)} similar vectors")
            return search_result
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []
    
    async def search_by_metadata(self, 
                                collection_name: str,
                                filters: Dict[str, Any],
                                limit: int = 100) -> List[Record]:
        """Search points by metadata filters"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            # Build filter conditions
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    # Multiple values (OR condition)
                    for v in value:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=v))
                        )
                else:
                    # Single value
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
            
            # Create filter
            if len(conditions) == 1:
                filter_obj = Filter(must=[conditions[0]])
            elif len(conditions) > 1:
                filter_obj = Filter(should=conditions)  # OR logic
            else:
                filter_obj = None
            
            # Perform search
            points, _ = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_obj,
                limit=limit
            )
            
            logger.debug(f"Found {len(points)} points matching metadata filters")
            return points
            
        except Exception as e:
            logger.error(f"Error searching by metadata: {e}")
            return []
    
    async def get_point(self, collection_name: str, point_id: str) -> Optional[Record]:
        """Get a specific point by ID"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id]
            )
            
            return points[0] if points else None
            
        except Exception as e:
            logger.error(f"Error getting point {point_id}: {e}")
            return None
    
    async def delete_points(self, 
                           collection_name: str, 
                           point_ids: List[str] = None,
                           filter_conditions: Optional[Filter] = None) -> bool:
        """Delete points by IDs or filter"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            if point_ids:
                # Delete by IDs
                operation_info = self.client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(
                        points=point_ids
                    )
                )
            elif filter_conditions:
                # Delete by filter
                operation_info = self.client.delete(
                    collection_name=collection_name,
                    points_selector=filter_conditions
                )
            else:
                logger.error("Either point_ids or filter_conditions must be provided")
                return False
            
            logger.info(f"Deleted points from collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting points: {e}")
            return False
    
    async def count_points(self, 
                          collection_name: str, 
                          filter_conditions: Optional[Filter] = None) -> int:
        """Count points in collection, optionally with filter"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            count_result = self.client.count(
                collection_name=collection_name,
                count_filter=filter_conditions
            )
            
            return count_result.count
            
        except Exception as e:
            logger.error(f"Error counting points: {e}")
            return 0
    
    async def create_index(self, 
                          collection_name: str, 
                          field_name: str, 
                          field_type: str = "keyword") -> bool:
        """Create an index on a payload field"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            # Note: Qdrant automatically indexes payload fields, 
            # but we can create explicit indexes for better performance
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD if field_type == "keyword" else models.PayloadSchemaType.INTEGER
            )
            
            logger.info(f"Created index on {field_name} in collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    async def get_cluster_info(self) -> Dict[str, Any]:
        """Get Qdrant cluster information"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            # Note: This would require cluster endpoints
            # For now, return basic info
            collections = await self.list_collections()
            
            cluster_info = {
                "connected": self.is_connected,
                "url": self.url,
                "collections_count": len(collections),
                "collections": collections,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return cluster_info
            
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {"error": str(e)}
    
    async def backup_collection(self, 
                               collection_name: str, 
                               backup_path: str) -> bool:
        """Create a backup of a collection"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            # Get all points from collection
            all_points, _ = self.client.scroll(
                collection_name=collection_name,
                limit=10000  # Adjust based on collection size
            )
            
            # Prepare backup data
            backup_data = {
                "collection_name": collection_name,
                "timestamp": datetime.utcnow().isoformat(),
                "points_count": len(all_points),
                "points": []
            }
            
            # Convert points to serializable format
            for point in all_points:
                backup_data["points"].append({
                    "id": str(point.id),
                    "vector": point.vector,
                    "payload": point.payload
                })
            
            # Save to file
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Backed up collection {collection_name} to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up collection: {e}")
            return False
    
    async def restore_collection(self, 
                                backup_path: str, 
                                target_collection: str = None) -> bool:
        """Restore a collection from backup"""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")
        
        try:
            # Load backup data
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            collection_name = target_collection or backup_data["collection_name"]
            
            # Create collection if it doesn't exist
            await self.create_collection(collection_name, overwrite=True)
            
            # Restore points
            points = []
            for point_data in backup_data["points"]:
                point = VectorPoint(
                    id=point_data["id"],
                    vector=point_data["vector"],
                    payload=point_data["payload"]
                )
                points.append(point)
            
            # Upsert points in batches
            stats = await self.upsert_points(collection_name, points)
            
            logger.info(f"Restored collection {collection_name} from {backup_path}")
            logger.info(f"Restore stats: {stats}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring collection: {e}")
            return False
    
    def generate_point_id(self, *components: str) -> str:
        """Generate a unique point ID from components"""
        content = ":".join(str(c) for c in components)
        return hashlib.md5(content.encode()).hexdigest()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Qdrant"""
        health_status = {
            "connected": False,
            "collections_accessible": False,
            "error": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Test connection
            if not self.is_connected:
                await self.connect()
            
            health_status["connected"] = self.is_connected
            
            # Test collections access
            collections = await self.list_collections()
            health_status["collections_accessible"] = True
            health_status["collections_count"] = len(collections)
            
        except Exception as e:
            health_status["error"] = str(e)
            logger.error(f"Qdrant health check failed: {e}")
        
        return health_status

# Context manager for automatic connection handling
class QdrantConnection:
    """Context manager for Qdrant connections"""
    
    def __init__(self, manager: QdrantManager):
        self.manager = manager
    
    async def __aenter__(self):
        await self.manager.connect()
        return self.manager
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.manager.disconnect()

# Utility functions
def create_filter_condition(field: str, value: Any) -> FieldCondition:
    """Create a simple filter condition"""
    return FieldCondition(key=field, match=MatchValue(value=value))

def create_range_filter(field: str, gte: float = None, lte: float = None) -> FieldCondition:
    """Create a range filter condition"""
    range_condition = {}
    if gte is not None:
        range_condition["gte"] = gte
    if lte is not None:
        range_condition["lte"] = lte
    
    return FieldCondition(key=field, range=range_condition)