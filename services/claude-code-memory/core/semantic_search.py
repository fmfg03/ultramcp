"""
Semantic search engine using Qdrant vector database
"""
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any, Tuple
import logging
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a semantic search result"""
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    file_path: str
    element_type: str
    element_name: str
    start_line: int
    end_line: int
    language: str
    context: Optional[str] = None

@dataclass
class IndexStats:
    """Statistics about the vector index"""
    total_points: int
    collections: List[str]
    vector_dimensions: int
    index_size_mb: float
    last_updated: datetime
    languages: Dict[str, int]
    element_types: Dict[str, int]

class SemanticSearchEngine:
    """Advanced semantic search using Qdrant and sentence transformers"""
    
    def __init__(self, 
                 qdrant_url: str = "http://sam.chat:6333",
                 collection_name: str = "code_memory",
                 model_name: str = "all-MiniLM-L6-v2"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.model_name = model_name
        
        # Initialize clients
        self.client = None
        self.encoder = None
        self.vector_size = 384  # Default for all-MiniLM-L6-v2
        
        # Connection status
        self.is_connected = False
        
    async def initialize(self):
        """Initialize the search engine"""
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(url=self.qdrant_url)
            
            # Test connection
            collections = await self._get_collections()
            self.is_connected = True
            logger.info(f"Connected to Qdrant at {self.qdrant_url}")
            
            # Initialize sentence transformer
            self.encoder = SentenceTransformer(self.model_name)
            self.vector_size = self.encoder.get_sentence_embedding_dimension()
            logger.info(f"Loaded sentence transformer: {self.model_name} (dim: {self.vector_size})")
            
            # Create collection if it doesn't exist
            await self.ensure_collection()
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic search engine: {e}")
            self.is_connected = False
            raise
    
    async def _get_collections(self) -> List[str]:
        """Get list of collections from Qdrant"""
        try:
            collections_response = self.client.get_collections()
            return [collection.name for collection in collections_response.collections]
        except Exception as e:
            logger.error(f"Error getting collections: {e}")
            return []
    
    async def ensure_collection(self):
        """Ensure the collection exists with proper configuration"""
        try:
            collections = await self._get_collections()
            
            if self.collection_name not in collections:
                # Create collection with vector configuration
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    def encode_text(self, text: str) -> np.ndarray:
        """Encode text to vector using sentence transformer"""
        if not self.encoder:
            raise RuntimeError("Encoder not initialized")
        
        try:
            # Clean and prepare text
            clean_text = self._clean_text(text)
            
            # Encode to vector
            vector = self.encoder.encode(clean_text, convert_to_numpy=True)
            return vector.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better embedding"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove very long lines that might be generated code
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            if len(line) <= 1000:  # Skip very long lines
                clean_lines.append(line)
        
        # Truncate if too long (sentence transformers have limits)
        clean_text = '\n'.join(clean_lines)
        if len(clean_text) > 8000:
            clean_text = clean_text[:8000] + "..."
        
        return clean_text
    
    async def index_code_element(self, 
                                element_id: str,
                                content: str,
                                metadata: Dict[str, Any]) -> bool:
        """Index a single code element"""
        try:
            if not self.is_connected:
                await self.initialize()
            
            # Encode content to vector
            vector = self.encode_text(content)
            
            # Create point for Qdrant
            point = PointStruct(
                id=element_id,
                vector=vector.tolist(),
                payload={
                    'content': content,
                    'indexed_at': datetime.utcnow().isoformat(),
                    **metadata
                }
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Indexed element: {element_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing element {element_id}: {e}")
            return False
    
    async def batch_index_elements(self, 
                                  elements: List[Tuple[str, str, Dict[str, Any]]], 
                                  batch_size: int = 100) -> Dict[str, int]:
        """Index multiple code elements in batches"""
        stats = {'success': 0, 'failed': 0}
        
        try:
            if not self.is_connected:
                await self.initialize()
            
            # Process in batches
            for i in range(0, len(elements), batch_size):
                batch = elements[i:i + batch_size]
                points = []
                
                for element_id, content, metadata in batch:
                    try:
                        # Encode content
                        vector = self.encode_text(content)
                        
                        # Create point
                        point = PointStruct(
                            id=element_id,
                            vector=vector.tolist(),
                            payload={
                                'content': content,
                                'indexed_at': datetime.utcnow().isoformat(),
                                **metadata
                            }
                        )
                        points.append(point)
                        
                    except Exception as e:
                        logger.error(f"Error preparing element {element_id}: {e}")
                        stats['failed'] += 1
                
                # Batch upsert
                if points:
                    try:
                        self.client.upsert(
                            collection_name=self.collection_name,
                            points=points
                        )
                        stats['success'] += len(points)
                        logger.info(f"Indexed batch of {len(points)} elements")
                        
                    except Exception as e:
                        logger.error(f"Error batch indexing: {e}")
                        stats['failed'] += len(points)
        
        except Exception as e:
            logger.error(f"Error in batch indexing: {e}")
        
        return stats
    
    async def search(self, 
                    query: str, 
                    limit: int = 10,
                    score_threshold: float = 0.7,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform semantic search"""
        try:
            if not self.is_connected:
                await self.initialize()
            
            # Encode query
            query_vector = self.encode_text(query)
            
            # Build filters
            qdrant_filter = None
            if filters:
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
                
                if conditions:
                    qdrant_filter = Filter(should=conditions) if len(conditions) > 1 else Filter(must=[conditions[0]])
            
            # Perform search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                query_filter=qdrant_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Convert to SearchResult objects
            results = []
            for hit in search_results:
                payload = hit.payload
                
                result = SearchResult(
                    id=str(hit.id),
                    score=hit.score,
                    content=payload.get('content', ''),
                    metadata=payload,
                    file_path=payload.get('file_path', ''),
                    element_type=payload.get('element_type', ''),
                    element_name=payload.get('element_name', ''),
                    start_line=payload.get('start_line', 0),
                    end_line=payload.get('end_line', 0),
                    language=payload.get('language', ''),
                    context=self._generate_context(payload)
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _generate_context(self, metadata: Dict[str, Any]) -> str:
        """Generate context string from metadata"""
        context_parts = []
        
        if metadata.get('parent_element'):
            context_parts.append(f"in {metadata['parent_element']}")
        
        if metadata.get('file_path'):
            context_parts.append(f"from {metadata['file_path']}")
        
        if metadata.get('language'):
            context_parts.append(f"({metadata['language']})")
        
        return " ".join(context_parts) if context_parts else ""
    
    async def search_by_element_type(self, 
                                   element_type: str, 
                                   query: str = "", 
                                   limit: int = 10) -> List[SearchResult]:
        """Search for specific element types"""
        filters = {'element_type': element_type}
        
        if query:
            return await self.search(query, limit=limit, filters=filters)
        else:
            # If no query, just filter by type
            try:
                search_results = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=Filter(
                        must=[FieldCondition(key='element_type', match=MatchValue(value=element_type))]
                    ),
                    limit=limit
                )
                
                results = []
                for point in search_results[0]:
                    payload = point.payload
                    result = SearchResult(
                        id=str(point.id),
                        score=1.0,  # No semantic scoring for filter-only
                        content=payload.get('content', ''),
                        metadata=payload,
                        file_path=payload.get('file_path', ''),
                        element_type=payload.get('element_type', ''),
                        element_name=payload.get('element_name', ''),
                        start_line=payload.get('start_line', 0),
                        end_line=payload.get('end_line', 0),
                        language=payload.get('language', ''),
                        context=self._generate_context(payload)
                    )
                    results.append(result)
                
                return results
                
            except Exception as e:
                logger.error(f"Error searching by element type: {e}")
                return []
    
    async def search_similar_code(self, 
                                code_snippet: str, 
                                language: Optional[str] = None,
                                limit: int = 5) -> List[SearchResult]:
        """Find similar code snippets"""
        filters = {}
        if language:
            filters['language'] = language
        
        return await self.search(
            query=code_snippet,
            limit=limit,
            score_threshold=0.8,  # Higher threshold for code similarity
            filters=filters
        )
    
    async def get_index_stats(self) -> IndexStats:
        """Get statistics about the index"""
        try:
            if not self.is_connected:
                await self.initialize()
            
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            
            # Get all points to analyze metadata
            all_points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000  # Adjust based on expected size
            )
            
            # Analyze metadata
            languages = {}
            element_types = {}
            
            for point in all_points:
                payload = point.payload
                
                lang = payload.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
                
                elem_type = payload.get('element_type', 'unknown')
                element_types[elem_type] = element_types.get(elem_type, 0) + 1
            
            return IndexStats(
                total_points=collection_info.points_count or 0,
                collections=[self.collection_name],
                vector_dimensions=self.vector_size,
                index_size_mb=0.0,  # Qdrant doesn't easily expose this
                last_updated=datetime.utcnow(),
                languages=languages,
                element_types=element_types
            )
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return IndexStats(
                total_points=0,
                collections=[],
                vector_dimensions=self.vector_size,
                index_size_mb=0.0,
                last_updated=datetime.utcnow(),
                languages={},
                element_types={}
            )
    
    async def delete_by_file(self, file_path: str) -> bool:
        """Delete all indexed elements from a specific file"""
        try:
            if not self.is_connected:
                await self.initialize()
            
            # Delete points with matching file_path
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key='file_path', match=MatchValue(value=file_path))]
                )
            )
            
            logger.info(f"Deleted indexed elements from file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    async def clear_index(self) -> bool:
        """Clear all indexed elements"""
        try:
            if not self.is_connected:
                await self.initialize()
            
            # Delete collection and recreate
            self.client.delete_collection(self.collection_name)
            await self.ensure_collection()
            
            logger.info("Cleared semantic search index")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return False
    
    def generate_element_id(self, file_path: str, element_name: str, start_line: int) -> str:
        """Generate unique ID for code element"""
        content = f"{file_path}:{element_name}:{start_line}"
        return hashlib.md5(content.encode()).hexdigest()