"""
Enhanced Memory Routes - REST API routes for Graphiti Knowledge Graph Integration

Provides comprehensive routing for:
- Hybrid memory storage and retrieval
- Temporal reasoning queries
- Agent collaboration features
- Predictive assistance
- Knowledge gap analysis
- System monitoring
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
import os
import json

from ..controllers.enhancedMemoryController import (
    EnhancedMemoryController,
    StoreMemoryRequest,
    SearchMemoryRequest,
    TemporalSearchRequest,
    AgentCollaborationRequest,
    KnowledgeGapRequest,
    StoreMemoryResponse,
    SearchMemoryResponse,
    TemporalSearchResponse,
    AgentCollaborationResponse,
    HealthCheckResponse,
    get_enhanced_memory_controller
)
from ..services.enhancedMemoryService import SearchType
from ..middleware.authMiddleware import AuthMiddleware
from ..utils.logger import logger

# Create router
router = APIRouter(prefix="/api/memory/enhanced", tags=["Enhanced Memory"])

# Auth middleware
auth_middleware = AuthMiddleware()

def get_controller() -> EnhancedMemoryController:
    """Dependency to get enhanced memory controller"""
    config = {
        'NEO4J_URI': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        'NEO4J_USERNAME': os.getenv('NEO4J_USERNAME', 'neo4j'),
        'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD', 'neo4j_password'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'GRAPHITI_EMBEDDING_MODEL': os.getenv('GRAPHITI_EMBEDDING_MODEL', 'text-embedding-3-small'),
        'GRAPHITI_LLM_MODEL': os.getenv('GRAPHITI_LLM_MODEL', 'gpt-4-turbo-preview')
    }
    return get_enhanced_memory_controller(config)

@router.post(
    "/store",
    response_model=StoreMemoryResponse,
    summary="Store content in enhanced memory system",
    description="Store content in both vector database and knowledge graph with relationship extraction"
)
async def store_memory(
    request: StoreMemoryRequest,
    controller: EnhancedMemoryController = Depends(get_controller),
    # current_user = Depends(auth_middleware.get_current_user)  # Uncomment when auth is ready
) -> StoreMemoryResponse:
    """
    Store content in the enhanced memory system with dual-write capability.
    
    Features:
    - Stores in both vector database and knowledge graph
    - Extracts entities and relationships automatically
    - Supports contextual metadata
    - Zero-downtime migration strategy
    """
    try:
        return await controller.store_memory(request)
    except Exception as error:
        logger.error(f"Store memory endpoint failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@router.post(
    "/search",
    response_model=SearchMemoryResponse,
    summary="Search memory with hybrid approach",
    description="Search using combination of vector similarity and graph traversal"
)
async def search_memory(
    request: SearchMemoryRequest,
    controller: EnhancedMemoryController = Depends(get_controller),
    # current_user = Depends(auth_middleware.get_current_user)
) -> SearchMemoryResponse:
    """
    Search memory using advanced hybrid approach.
    
    Search Types:
    - VECTOR_ONLY: Traditional vector similarity search
    - GRAPH_ONLY: Knowledge graph traversal search
    - HYBRID: Combined vector + graph search (recommended)
    - TEMPORAL: Time-aware search with relationship evolution
    - PREDICTIVE: Pattern-based predictive search
    """
    try:
        return await controller.search_memory(request)
    except Exception as error:
        logger.error(f"Search memory endpoint failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@router.post(
    "/temporal",
    response_model=TemporalSearchResponse,
    summary="Temporal reasoning queries",
    description="Perform time-aware searches with relationship evolution analysis"
)
async def temporal_search(
    request: TemporalSearchRequest,
    controller: EnhancedMemoryController = Depends(get_controller),
    # current_user = Depends(auth_middleware.get_current_user)
) -> TemporalSearchResponse:
    """
    Perform temporal reasoning queries to understand how knowledge evolved over time.
    
    Features:
    - Point-in-time queries
    - Relationship evolution tracking
    - Temporal pattern detection
    - Historical context analysis
    """
    try:
        return await controller.temporal_search(request)
    except Exception as error:
        logger.error(f"Temporal search endpoint failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@router.post(
    "/collaboration",
    response_model=AgentCollaborationResponse,
    summary="Agent collaboration context",
    description="Get contextual knowledge for agent collaboration and shared intelligence"
)
async def get_agent_collaboration(
    request: AgentCollaborationRequest,
    controller: EnhancedMemoryController = Depends(get_controller),
    # current_user = Depends(auth_middleware.get_current_user)
) -> AgentCollaborationResponse:
    """
    Get agent collaboration context and opportunities.
    
    Features:
    - Agent-specific knowledge context
    - Collaboration opportunity detection
    - Shared knowledge graph analysis
    - Cross-agent learning insights
    """
    try:
        return await controller.get_agent_collaboration(request)
    except Exception as error:
        logger.error(f"Agent collaboration endpoint failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@router.post(
    "/gaps",
    summary="Knowledge gap analysis",
    description="Analyze knowledge gaps and suggest improvements"
)
async def analyze_knowledge_gaps(
    request: KnowledgeGapRequest,
    controller: EnhancedMemoryController = Depends(get_controller),
    # current_user = Depends(auth_middleware.get_current_user)
) -> Dict[str, Any]:
    """
    Analyze knowledge gaps in the system and provide recommendations.
    
    Features:
    - Missing relationship detection
    - Weak connection identification
    - Knowledge enrichment suggestions
    - Priority area identification
    """
    try:
        return await controller.analyze_knowledge_gaps(request)
    except Exception as error:
        logger.error(f"Knowledge gap analysis endpoint failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@router.post(
    "/predict",
    summary="Predictive assistance",
    description="Predict next actions based on knowledge graph patterns"
)
async def predict_next_actions(
    query: str,
    user_context: Optional[Dict[str, Any]] = None,
    controller: EnhancedMemoryController = Depends(get_controller),
    # current_user = Depends(auth_middleware.get_current_user)
) -> Dict[str, Any]:
    """
    Predict what user might need next based on graph patterns and historical behavior.
    
    Features:
    - Pattern-based predictions
    - Historical behavior analysis
    - Confidence scoring
    - Actionable recommendations
    """
    try:
        return await controller.predict_next_actions(query, user_context)
    except Exception as error:
        logger.error(f"Predictive assistance endpoint failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@router.get(
    "/metrics",
    summary="System metrics",
    description="Get comprehensive system metrics and performance data"
)
async def get_system_metrics(
    controller: EnhancedMemoryController = Depends(get_controller),
    # current_user = Depends(auth_middleware.get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive system metrics and performance data.
    
    Includes:
    - Storage statistics
    - Search performance
    - Graph operations
    - Relationship metrics
    - Error rates
    """
    try:
        return await controller.get_system_metrics()
    except Exception as error:
        logger.error(f"System metrics endpoint failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Comprehensive health check for all system components"
)
async def health_check(
    controller: EnhancedMemoryController = Depends(get_controller)
) -> HealthCheckResponse:
    """
    Perform comprehensive health check of all system components.
    
    Checks:
    - Vector memory system
    - Neo4j connection
    - Graphiti functionality
    - System metrics
    """
    try:
        return await controller.health_check()
    except Exception as error:
        logger.error(f"Health check endpoint failed: {error}")
        return HealthCheckResponse(
            overall_status="error",
            components={"health_check": f"error: {error}"},
            metrics={},
            timestamp="error"
        )

# Advanced search endpoints

@router.get(
    "/search/types",
    summary="Available search types",
    description="Get available search types and their descriptions"
)
async def get_search_types() -> Dict[str, Any]:
    """Get available search types and their descriptions"""
    return {
        "search_types": {
            "VECTOR_ONLY": {
                "description": "Traditional vector similarity search using embeddings",
                "use_cases": ["Simple content retrieval", "Fast searches", "Fallback mode"],
                "performance": "Fast",
                "accuracy": "Good"
            },
            "GRAPH_ONLY": {
                "description": "Knowledge graph traversal search using relationships",
                "use_cases": ["Relationship exploration", "Context discovery", "Entity connections"],
                "performance": "Medium",
                "accuracy": "High contextual"
            },
            "HYBRID": {
                "description": "Combined vector + graph search with intelligent merging",
                "use_cases": ["Best overall results", "Complex queries", "Contextual search"],
                "performance": "Medium",
                "accuracy": "Highest"
            },
            "TEMPORAL": {
                "description": "Time-aware search with relationship evolution",
                "use_cases": ["Historical analysis", "Change tracking", "Temporal patterns"],
                "performance": "Slower",
                "accuracy": "High temporal"
            },
            "PREDICTIVE": {
                "description": "Pattern-based search with future predictions",
                "use_cases": ["Proactive assistance", "Pattern recognition", "Trend analysis"],
                "performance": "Slower",
                "accuracy": "Predictive"
            }
        },
        "recommendations": {
            "general_use": "HYBRID",
            "fast_retrieval": "VECTOR_ONLY",
            "relationship_exploration": "GRAPH_ONLY",
            "historical_analysis": "TEMPORAL",
            "proactive_assistance": "PREDICTIVE"
        }
    }

@router.post(
    "/search/explain",
    summary="Explain search results",
    description="Get detailed explanation of how search results were derived"
)
async def explain_search_results(
    query: str,
    search_type: SearchType = SearchType.HYBRID,
    controller: EnhancedMemoryController = Depends(get_controller),
    # current_user = Depends(auth_middleware.get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed explanation of how search results were derived.
    
    Provides insight into:
    - Search strategy used
    - Vector similarity scores
    - Graph traversal paths
    - Ranking algorithm details
    - Performance metrics
    """
    try:
        # Perform search with detailed logging
        search_request = SearchMemoryRequest(
            query=query,
            search_type=search_type,
            limit=5
        )
        
        results = await controller.search_memory(search_request)
        
        explanation = {
            "query": query,
            "search_type": search_type.value,
            "strategy": {
                "description": f"Used {search_type.value} search strategy",
                "components": [],
                "ranking_factors": []
            },
            "results_analysis": {
                "total_results": results.total_results,
                "sources_used": results.sources_used,
                "avg_relevance": sum(r["relevance_score"] for r in results.results) / len(results.results) if results.results else 0
            },
            "performance": {
                "query_time_ms": results.query_time_ms,
                "efficiency_rating": "High" if results.query_time_ms < 500 else "Medium" if results.query_time_ms < 1000 else "Low"
            }
        }
        
        # Add strategy-specific details
        if search_type in [SearchType.VECTOR_ONLY, SearchType.HYBRID]:
            explanation["strategy"]["components"].append("Vector similarity using embeddings")
            explanation["strategy"]["ranking_factors"].append("Cosine similarity score")
        
        if search_type in [SearchType.GRAPH_ONLY, SearchType.HYBRID]:
            explanation["strategy"]["components"].append("Knowledge graph traversal")
            explanation["strategy"]["ranking_factors"].append("Relationship strength")
        
        if search_type == SearchType.TEMPORAL:
            explanation["strategy"]["components"].append("Temporal reasoning")
            explanation["strategy"]["ranking_factors"].append("Temporal relevance")
        
        if search_type == SearchType.PREDICTIVE:
            explanation["strategy"]["components"].append("Pattern analysis")
            explanation["strategy"]["ranking_factors"].append("Prediction confidence")
        
        return explanation
        
    except Exception as error:
        logger.error(f"Search explanation endpoint failed: {error}")
        raise HTTPException(status_code=500, detail=str(error))

# Export the router
__all__ = ["router"]