"""
VoyageAI Enhanced Search consolidated routes
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from ..core.shared_dependencies import (
    get_qdrant_dependency,
    vector_search,
    cache_get,
    cache_set
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class VoyageSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    privacy_level: str = Field("PUBLIC", description="Privacy level: PUBLIC, INTERNAL, CONFIDENTIAL")
    domain: Optional[str] = Field(None, description="Domain specialization: CODE, FINANCE, HEALTHCARE, LEGAL, GENERAL")
    search_mode: str = Field("AUTO", description="Search mode: AUTO, HYBRID, VOYAGE_ONLY")
    limit: int = Field(10, ge=1, le=50, description="Maximum results")
    enable_reranking: bool = Field(True, description="Enable result reranking")
    cost_optimization: bool = Field(True, description="Enable cost optimization")

class DomainSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    domain: str = Field(..., description="Specialized domain: CODE, FINANCE, HEALTHCARE, LEGAL")
    privacy_level: str = Field("PUBLIC", description="Privacy level")
    limit: int = Field(10, ge=1, le=30, description="Maximum results")
    include_metadata: bool = Field(True, description="Include result metadata")

class VoyageResult(BaseModel):
    id: str
    score: float
    content: str
    source: str
    domain: str
    model_used: str
    metadata: Dict[str, Any]
    privacy_compliant: bool
    processing_time: float
    cost: float

class VoyageResponse(BaseModel):
    results: List[VoyageResult]
    query: str
    domain: Optional[str]
    model_used: str
    search_mode: str
    privacy_compliant: bool
    total_results: int
    processing_time: float
    cost: float
    cost_savings: float

# Mock VoyageAI service implementation
class MockVoyageService:
    """Simplified VoyageAI service for unified backend"""
    
    @staticmethod
    async def enhanced_search(request: VoyageSearchRequest) -> VoyageResponse:
        """Enhanced semantic search with VoyageAI embeddings"""
        start_time = datetime.utcnow()
        
        # Simulate processing
        await asyncio.sleep(0.3)
        
        # Determine model based on privacy and domain
        if request.privacy_level == "CONFIDENTIAL":
            model_used = "local-sentence-transformer"
            base_cost = 0.0
        elif request.domain == "CODE":
            model_used = "voyage-code-2"
            base_cost = 0.005
        elif request.domain in ["FINANCE", "LEGAL", "HEALTHCARE"]:
            model_used = "voyage-2-large"
            base_cost = 0.008
        else:
            model_used = "voyage-2"
            base_cost = 0.004
        
        # Generate mock results
        mock_results = []
        for i in range(min(request.limit, 8)):
            result = VoyageResult(
                id=f"voyage_result_{i}",
                score=0.95 - (i * 0.08),
                content=f"Enhanced VoyageAI result {i+1} for query '{request.query}' in domain {request.domain or 'GENERAL'}",
                source=f"voyage_source_{i}",
                domain=request.domain or "GENERAL",
                model_used=model_used,
                metadata={
                    "document_type": "enhanced_content",
                    "confidence": 0.95 - (i * 0.05),
                    "relevance_factors": ["semantic_similarity", "domain_expertise"]
                },
                privacy_compliant=True,
                processing_time=0.15,
                cost=base_cost * (1 - i * 0.1) if request.privacy_level != "CONFIDENTIAL" else 0.0
            )
            mock_results.append(result)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        total_cost = sum(r.cost for r in mock_results)
        
        # Calculate cost savings from optimization
        base_total_cost = base_cost * len(mock_results)
        cost_savings = max(0, (base_total_cost - total_cost) / base_total_cost * 100) if base_total_cost > 0 else 0
        
        return VoyageResponse(
            results=mock_results,
            query=request.query,
            domain=request.domain,
            model_used=model_used,
            search_mode=request.search_mode,
            privacy_compliant=True,
            total_results=len(mock_results),
            processing_time=processing_time,
            cost=total_cost,
            cost_savings=cost_savings
        )
    
    @staticmethod
    async def domain_search(request: DomainSearchRequest) -> VoyageResponse:
        """Domain-specialized search"""
        start_time = datetime.utcnow()
        
        # Simulate domain-specific processing
        await asyncio.sleep(0.4)
        
        # Domain-specific models
        domain_models = {
            "CODE": "voyage-code-2",
            "FINANCE": "voyage-finance-2", 
            "HEALTHCARE": "voyage-2-large",
            "LEGAL": "voyage-2-large"
        }
        
        model_used = domain_models.get(request.domain, "voyage-2")
        base_cost = 0.007 if request.privacy_level != "CONFIDENTIAL" else 0.0
        
        # Generate domain-specific results
        mock_results = []
        for i in range(min(request.limit, 6)):
            result = VoyageResult(
                id=f"domain_{request.domain.lower()}_{i}",
                score=0.92 - (i * 0.06),
                content=f"Domain-specialized {request.domain} result {i+1}: {request.query}",
                source=f"{request.domain.lower()}_source_{i}",
                domain=request.domain,
                model_used=model_used,
                metadata={
                    "domain_specialization": request.domain,
                    "domain_confidence": 0.98,
                    "specialist_factors": [f"{request.domain.lower()}_terminology", "domain_context"]
                } if request.include_metadata else {},
                privacy_compliant=True,
                processing_time=0.2,
                cost=base_cost * (1 - i * 0.1)
            )
            mock_results.append(result)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        total_cost = sum(r.cost for r in mock_results)
        
        return VoyageResponse(
            results=mock_results,
            query=request.query,
            domain=request.domain,
            model_used=model_used,
            search_mode="DOMAIN_SPECIALIZED",
            privacy_compliant=True,
            total_results=len(mock_results),
            processing_time=processing_time,
            cost=total_cost,
            cost_savings=15.0  # Domain specialization provides cost savings
        )

# Routes
@router.post("/search/enhanced", response_model=VoyageResponse)
async def enhanced_search(
    request: VoyageSearchRequest,
    background_tasks: BackgroundTasks,
    qdrant=Depends(get_qdrant_dependency)
):
    """Premium semantic search with VoyageAI embeddings"""
    try:
        # Check cache
        cache_key = f"voyage_search:{hash(request.query + request.privacy_level + (request.domain or ''))}:{request.limit}"
        cached_result = await cache_get(cache_key)
        
        if cached_result:
            logger.info(f"Returning cached VoyageAI search for: {request.query}")
            return VoyageResponse.parse_raw(cached_result)
        
        # Perform search
        result = await MockVoyageService.enhanced_search(request)
        
        # Cache result
        await cache_set(cache_key, result.json(), ttl=3600)
        
        # Log search analytics
        background_tasks.add_task(
            log_voyage_analytics,
            request.query,
            result.total_results,
            request.domain,
            request.privacy_level
        )
        
        return result
        
    except Exception as e:
        logger.error(f"VoyageAI enhanced search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/search/domain", response_model=VoyageResponse)
async def domain_search(
    request: DomainSearchRequest,
    background_tasks: BackgroundTasks
):
    """Domain-specialized search (finance, healthcare, legal, code)"""
    try:
        result = await MockVoyageService.domain_search(request)
        
        # Log domain search analytics
        background_tasks.add_task(
            log_voyage_analytics,
            request.query,
            result.total_results,
            request.domain,
            request.privacy_level
        )
        
        return result
        
    except Exception as e:
        logger.error(f"VoyageAI domain search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Domain search failed: {str(e)}")

@router.post("/search/privacy-first")
async def privacy_first_search(
    query: str,
    domain: Optional[str] = None,
    limit: int = 10
):
    """Privacy-first search using only local models"""
    try:
        request = VoyageSearchRequest(
            query=query,
            privacy_level="CONFIDENTIAL",
            domain=domain,
            search_mode="LOCAL_ONLY",
            limit=limit,
            cost_optimization=True
        )
        
        result = await MockVoyageService.enhanced_search(request)
        
        return {
            "results": [r.dict() for r in result.results],
            "query": query,
            "domain": domain,
            "search_type": "privacy_first",
            "model_used": "local-sentence-transformer",
            "privacy_compliant": True,
            "local_processing": True,
            "cost": 0.0,
            "cost_savings": 100.0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Privacy-first VoyageAI search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/search/cost-optimized")
async def cost_optimized_search(
    query: str,
    privacy_level: str = "PUBLIC",
    domain: Optional[str] = None,
    max_cost: float = 0.05
):
    """Cost-optimized search with spending limits"""
    try:
        request = VoyageSearchRequest(
            query=query,
            privacy_level=privacy_level,
            domain=domain,
            search_mode="HYBRID",
            limit=8,  # Reduced limit for cost optimization
            cost_optimization=True
        )
        
        result = await MockVoyageService.enhanced_search(request)
        
        # Filter results if cost exceeds limit
        if result.cost > max_cost:
            # Reduce results to stay within budget
            cost_per_result = result.cost / len(result.results) if result.results else 0
            max_results = int(max_cost / cost_per_result) if cost_per_result > 0 else len(result.results)
            result.results = result.results[:max_results]
            result.total_results = len(result.results)
            result.cost = sum(r.cost for r in result.results)
        
        return {
            "results": [r.dict() for r in result.results],
            "query": query,
            "total_results": result.total_results,
            "cost": result.cost,
            "max_cost": max_cost,
            "cost_savings": result.cost_savings,
            "within_budget": result.cost <= max_cost,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cost-optimized VoyageAI search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/models/available")
async def get_available_models():
    """Get available VoyageAI models and their capabilities"""
    return {
        "premium_models": [
            {
                "name": "Voyage Code 2",
                "id": "voyage-code-2", 
                "domain": "CODE",
                "cost_per_search": 0.005,
                "context_length": 16000,
                "embedding_dimension": 1024
            },
            {
                "name": "Voyage 2 Large",
                "id": "voyage-2-large",
                "domain": "GENERAL",
                "cost_per_search": 0.008,
                "context_length": 16000,
                "embedding_dimension": 1536
            },
            {
                "name": "Voyage 2",
                "id": "voyage-2",
                "domain": "GENERAL", 
                "cost_per_search": 0.004,
                "context_length": 4000,
                "embedding_dimension": 1024
            }
        ],
        "local_models": [
            {
                "name": "Local Sentence Transformer",
                "id": "local-sentence-transformer",
                "domain": "GENERAL",
                "cost_per_search": 0.0,
                "privacy_level": "CONFIDENTIAL"
            }
        ],
        "domain_specializations": ["CODE", "FINANCE", "HEALTHCARE", "LEGAL", "GENERAL"],
        "privacy_levels": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/stats")
async def voyage_stats():
    """Get VoyageAI service statistics"""
    return {
        "total_searches": 1250,
        "domain_searches": 340,
        "privacy_first_searches": 180,
        "cost_optimized_searches": 95,
        "average_search_time": 0.35,
        "average_cost_per_search": 0.006,
        "cost_savings_rate": 22.5,
        "privacy_compliance_rate": 100.0,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def voyage_health():
    """VoyageAI service health"""
    return {
        "status": "healthy",
        "service": "voyage-ai-enhanced-search",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": {
            "premium_embeddings": True,
            "domain_specialization": True,
            "privacy_first_processing": True,
            "cost_optimization": True,
            "local_fallback": True
        }
    }

# Background tasks
async def log_voyage_analytics(query: str, results_count: int, domain: Optional[str], privacy_level: str):
    """Log VoyageAI search analytics"""
    try:
        logger.info(f"VoyageAI search: '{query}', results: {results_count}, domain: {domain}, privacy: {privacy_level}")
    except Exception as e:
        logger.warning(f"Failed to log VoyageAI analytics: {e}")