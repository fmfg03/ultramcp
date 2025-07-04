"""
Enhanced Semantic Search with VoyageAI Integration
Hybrid architecture with privacy-first fallback
"""
import numpy as np
import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import time

from .semantic_search import SemanticSearchEngine, SearchResult, IndexStats
from .qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)

class SearchMode(Enum):
    """Search processing modes"""
    HYBRID = "hybrid"           # VoyageAI + local fallback
    VOYAGE_ONLY = "voyage_only" # VoyageAI only
    LOCAL_ONLY = "local_only"   # Local models only
    AUTO = "auto"               # Intelligent selection

class PrivacyLevel(Enum):
    """Privacy levels for content processing"""
    PUBLIC = "public"           # External APIs allowed
    INTERNAL = "internal"       # Local processing preferred
    CONFIDENTIAL = "confidential"  # Local processing only
    RESTRICTED = "restricted"   # Local processing only

class DomainType(Enum):
    """Domain types for specialized embeddings"""
    CODE = "code"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    GENERAL = "general"

@dataclass
class EnhancedSearchRequest:
    """Enhanced search request with privacy and domain context"""
    query: str
    limit: int = 10
    score_threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    domain: Optional[DomainType] = None
    search_mode: SearchMode = SearchMode.AUTO
    enable_reranking: bool = True
    context: Optional[Dict[str, Any]] = None

@dataclass
class EnhancedSearchResult(SearchResult):
    """Enhanced search result with additional metadata"""
    rerank_score: Optional[float] = None
    model_used: str = "unknown"
    privacy_compliant: bool = True
    processing_time: float = 0.0
    cost: float = 0.0

@dataclass
class SearchStats:
    """Enhanced search statistics"""
    total_searches: int
    voyage_searches: int
    local_searches: int
    cache_hits: int
    average_latency: float
    total_cost: float
    privacy_compliance_rate: float

class VoyageAIIntegration:
    """Integration client for VoyageAI service"""
    
    def __init__(self, service_url: str = "http://sam.chat:8010"):
        self.service_url = service_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def embed_texts(self, 
                         texts: List[str], 
                         privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC,
                         domain: Optional[DomainType] = None) -> Dict[str, Any]:
        """Generate embeddings using VoyageAI hybrid service"""
        try:
            # Select model based on domain
            if domain == DomainType.CODE:
                model = "VOYAGE_CODE_2"
            elif domain == DomainType.FINANCE:
                model = "VOYAGE_FINANCE"
            elif domain == DomainType.HEALTHCARE:
                model = "VOYAGE_HEALTHCARE"
            elif domain == DomainType.LEGAL:
                model = "VOYAGE_LAW"
            else:
                model = "VOYAGE_LARGE_2"
            
            payload = {
                "texts": texts,
                "model": model,
                "privacy_level": privacy_level.value,
                "input_type": "query",
                "domain": domain.value if domain else None
            }
            
            async with self.session.post(
                f"{self.service_url}/embed",
                json=payload
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except Exception as e:
            logger.error(f"VoyageAI embedding error: {e}")
            raise
    
    async def rerank_documents(self, 
                              query: str, 
                              documents: List[str],
                              privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC,
                              top_k: int = 20) -> Dict[str, Any]:
        """Rerank documents using VoyageAI hybrid service"""
        try:
            payload = {
                "query": query,
                "documents": documents,
                "model": "RERANK_LITE",
                "privacy_level": privacy_level.value,
                "top_k": top_k
            }
            
            async with self.session.post(
                f"{self.service_url}/rerank",
                json=payload
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except Exception as e:
            logger.error(f"VoyageAI reranking error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if VoyageAI service is available"""
        try:
            async with self.session.get(f"{self.service_url}/health") as response:
                return response.status == 200
        except:
            return False

class EnhancedSemanticSearchEngine(SemanticSearchEngine):
    """Enhanced semantic search with VoyageAI integration"""
    
    def __init__(self, 
                 qdrant_url: str = "http://sam.chat:6333",
                 collection_name: str = "enhanced_code_memory",
                 voyage_service_url: str = "http://sam.chat:8010"):
        super().__init__(qdrant_url, collection_name)
        self.voyage_service_url = voyage_service_url
        self.voyage_client = VoyageAIIntegration(voyage_service_url)
        
        # Search statistics
        self.stats = SearchStats(
            total_searches=0,
            voyage_searches=0,
            local_searches=0,
            cache_hits=0,
            average_latency=0.0,
            total_cost=0.0,
            privacy_compliance_rate=1.0
        )
        
        # Service availability
        self.voyage_available = False
        
    async def initialize(self):
        """Initialize enhanced search engine"""
        await super().initialize()
        
        # Check VoyageAI service availability
        try:
            async with self.voyage_client as client:
                self.voyage_available = await client.health_check()
            logger.info(f"VoyageAI service available: {self.voyage_available}")
        except Exception as e:
            logger.warning(f"VoyageAI service not available: {e}")
            self.voyage_available = False
    
    def _should_use_voyage(self, request: EnhancedSearchRequest) -> bool:
        """Determine if VoyageAI should be used"""
        if not self.voyage_available:
            return False
        
        if request.search_mode == SearchMode.LOCAL_ONLY:
            return False
        
        if request.search_mode == SearchMode.VOYAGE_ONLY:
            return True
        
        if request.privacy_level in [PrivacyLevel.CONFIDENTIAL, PrivacyLevel.RESTRICTED]:
            return False
        
        if request.search_mode == SearchMode.AUTO:
            # Use VoyageAI for public content and specialized domains
            return (
                request.privacy_level == PrivacyLevel.PUBLIC and
                request.domain in [DomainType.CODE, DomainType.FINANCE, DomainType.HEALTHCARE]
            )
        
        return request.search_mode == SearchMode.HYBRID
    
    async def enhanced_search(self, request: EnhancedSearchRequest) -> List[EnhancedSearchResult]:
        """Perform enhanced semantic search with optional reranking"""
        start_time = time.time()
        self.stats.total_searches += 1
        
        try:
            use_voyage = self._should_use_voyage(request)
            
            # Stage 1: Vector search
            if use_voyage:
                results = await self._voyage_search(request)
                self.stats.voyage_searches += 1
            else:
                results = await self._local_search(request)
                self.stats.local_searches += 1
            
            # Stage 2: Reranking (if enabled and we have results)
            if request.enable_reranking and results and len(results) > 1:
                results = await self._rerank_results(request, results, use_voyage)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(processing_time, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            # Fallback to basic search
            basic_results = await self.search(
                request.query, 
                request.limit, 
                request.score_threshold, 
                request.filters
            )
            
            # Convert to enhanced results
            enhanced_results = []
            for result in basic_results:
                enhanced_result = EnhancedSearchResult(
                    id=result.id,
                    score=result.score,
                    content=result.content,
                    metadata=result.metadata,
                    file_path=result.file_path,
                    element_type=result.element_type,
                    element_name=result.element_name,
                    start_line=result.start_line,
                    end_line=result.end_line,
                    language=result.language,
                    context=result.context,
                    model_used="local-fallback",
                    privacy_compliant=True,
                    processing_time=time.time() - start_time
                )
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
    
    async def _voyage_search(self, request: EnhancedSearchRequest) -> List[EnhancedSearchResult]:
        """Search using VoyageAI embeddings"""
        try:
            # Generate query embedding using VoyageAI
            async with self.voyage_client as client:
                embedding_result = await client.embed_texts(
                    [request.query],
                    privacy_level=request.privacy_level,
                    domain=request.domain
                )
            
            query_vector = np.array(embedding_result["embeddings"][0])
            
            # Search in Qdrant
            search_results = await self._vector_search(
                query_vector, 
                request.limit * 2,  # Get more candidates for reranking
                request.score_threshold,
                request.filters
            )
            
            # Convert to enhanced results
            enhanced_results = []
            for result in search_results:
                enhanced_result = EnhancedSearchResult(
                    id=result.id,
                    score=result.score,
                    content=result.content,
                    metadata=result.metadata,
                    file_path=result.file_path,
                    element_type=result.element_type,
                    element_name=result.element_name,
                    start_line=result.start_line,
                    end_line=result.end_line,
                    language=result.language,
                    context=result.context,
                    model_used=embedding_result["model_used"],
                    privacy_compliant=embedding_result["privacy_compliant"],
                    cost=embedding_result.get("cost", 0.0)
                )
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"VoyageAI search failed, falling back to local: {e}")
            return await self._local_search(request)
    
    async def _local_search(self, request: EnhancedSearchRequest) -> List[EnhancedSearchResult]:
        """Search using local embeddings"""
        # Use parent class search method
        search_results = await self.search(
            request.query,
            request.limit,
            request.score_threshold,
            request.filters
        )
        
        # Convert to enhanced results
        enhanced_results = []
        for result in search_results:
            enhanced_result = EnhancedSearchResult(
                id=result.id,
                score=result.score,
                content=result.content,
                metadata=result.metadata,
                file_path=result.file_path,
                element_type=result.element_type,
                element_name=result.element_name,
                start_line=result.start_line,
                end_line=result.end_line,
                language=result.language,
                context=result.context,
                model_used="local-sentence-transformer",
                privacy_compliant=True,
                cost=0.0
            )
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    async def _vector_search(self, 
                            query_vector: np.ndarray, 
                            limit: int,
                            score_threshold: float,
                            filters: Optional[Dict[str, Any]]) -> List[SearchResult]:
        """Perform vector search in Qdrant"""
        # Use existing search logic from parent class
        # This is a simplified version - in practice, you'd extract the vector search logic
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        # Build filters
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    for v in value:
                        conditions.append(FieldCondition(key=key, match=MatchValue(value=v)))
                else:
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            
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
        
        return results
    
    async def _rerank_results(self, 
                             request: EnhancedSearchRequest, 
                             results: List[EnhancedSearchResult],
                             use_voyage: bool) -> List[EnhancedSearchResult]:
        """Rerank search results for better relevance"""
        if len(results) <= 1:
            return results
        
        try:
            documents = [result.content for result in results]
            
            if use_voyage and self.voyage_available:
                # Use VoyageAI reranking
                async with self.voyage_client as client:
                    rerank_result = await client.rerank_documents(
                        query=request.query,
                        documents=documents,
                        privacy_level=request.privacy_level,
                        top_k=request.limit
                    )
                
                # Map reranked results back to original results
                reranked_results = []
                for rerank_item in rerank_result["reranked_documents"]:
                    original_index = rerank_item["index"]
                    if original_index < len(results):
                        result = results[original_index]
                        result.rerank_score = rerank_item["relevance_score"]
                        result.cost += rerank_result.get("cost", 0.0)
                        reranked_results.append(result)
                
                return reranked_results
            
            else:
                # Simple local reranking based on query similarity
                query_terms = set(request.query.lower().split())
                
                for result in results:
                    content_terms = set(result.content.lower().split())
                    # Simple Jaccard similarity
                    intersection = len(query_terms & content_terms)
                    union = len(query_terms | content_terms)
                    result.rerank_score = intersection / union if union > 0 else 0.0
                
                # Sort by rerank score
                results.sort(key=lambda x: x.rerank_score or 0.0, reverse=True)
                return results[:request.limit]
        
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results[:request.limit]
    
    def _update_stats(self, processing_time: float, results: List[EnhancedSearchResult]):
        """Update search statistics"""
        # Update average latency
        total_time = self.stats.average_latency * (self.stats.total_searches - 1) + processing_time
        self.stats.average_latency = total_time / self.stats.total_searches
        
        # Update total cost
        for result in results:
            self.stats.total_cost += result.cost
        
        # Update privacy compliance rate
        privacy_compliant_searches = sum(1 for r in results if r.privacy_compliant)
        total_result_count = len(results) if results else 1
        current_compliance = privacy_compliant_searches / total_result_count
        
        # Running average of compliance rate
        self.stats.privacy_compliance_rate = (
            (self.stats.privacy_compliance_rate * (self.stats.total_searches - 1) + current_compliance) 
            / self.stats.total_searches
        )
    
    async def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced search statistics"""
        base_stats = await self.get_index_stats()
        
        return {
            "index_stats": asdict(base_stats),
            "search_stats": asdict(self.stats),
            "voyage_availability": self.voyage_available,
            "service_health": {
                "qdrant_connected": self.is_connected,
                "voyage_connected": self.voyage_available
            }
        }
    
    # Convenience methods for different search modes
    async def privacy_first_search(self, query: str, **kwargs) -> List[EnhancedSearchResult]:
        """Search with maximum privacy (local only)"""
        request = EnhancedSearchRequest(
            query=query,
            privacy_level=PrivacyLevel.CONFIDENTIAL,
            search_mode=SearchMode.LOCAL_ONLY,
            **kwargs
        )
        return await self.enhanced_search(request)
    
    async def code_search(self, query: str, **kwargs) -> List[EnhancedSearchResult]:
        """Search optimized for code content"""
        request = EnhancedSearchRequest(
            query=query,
            domain=DomainType.CODE,
            search_mode=SearchMode.HYBRID,
            **kwargs
        )
        return await self.enhanced_search(request)
    
    async def domain_search(self, query: str, domain: DomainType, **kwargs) -> List[EnhancedSearchResult]:
        """Search optimized for specific domain"""
        request = EnhancedSearchRequest(
            query=query,
            domain=domain,
            search_mode=SearchMode.HYBRID,
            **kwargs
        )
        return await self.enhanced_search(request)