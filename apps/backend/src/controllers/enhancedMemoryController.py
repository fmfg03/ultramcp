"""
Enhanced Memory Controller - REST API for Graphiti Knowledge Graph Integration

Provides comprehensive API endpoints for:
- Hybrid memory storage (vector + graph)
- Temporal reasoning queries
- Agent collaboration features
- Predictive assistance
- Knowledge gap analysis
- System monitoring and health checks
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..services.enhancedMemoryService import (
    EnhancedMemorySystem,
    SearchType,
    MemoryEpisode,
    SearchResult,
    get_enhanced_memory_system
)
from ..utils.logger import logger

# Request/Response Models

class StoreMemoryRequest(BaseModel):
    """Request model for storing memory"""
    content: str = Field(..., description="Content to store in memory")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context metadata")
    agent_name: Optional[str] = Field(None, description="Name of the agent storing the memory")
    task_id: Optional[str] = Field(None, description="Associated task ID")

class SearchMemoryRequest(BaseModel):
    """Request model for searching memory"""
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(SearchType.HYBRID, description="Type of search to perform")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context for personalization")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    start_time: Optional[datetime] = Field(None, description="Start time for temporal queries")
    end_time: Optional[datetime] = Field(None, description="End time for temporal queries")

class TemporalSearchRequest(BaseModel):
    """Request model for temporal reasoning queries"""
    query: str = Field(..., description="Search query")
    start_time: Optional[datetime] = Field(None, description="Start of time range")
    end_time: Optional[datetime] = Field(None, description="End of time range")
    include_evolution: bool = Field(True, description="Include relationship evolution analysis")
    limit: int = Field(10, ge=1, le=50)

class AgentCollaborationRequest(BaseModel):
    """Request model for agent collaboration context"""
    agent_name: str = Field(..., description="Name of the requesting agent")
    task_id: Optional[str] = Field(None, description="Current task ID")
    include_shared_knowledge: bool = Field(True, description="Include shared knowledge analysis")

class KnowledgeGapRequest(BaseModel):
    """Request model for knowledge gap analysis"""
    query: str = Field(..., description="Query to analyze for knowledge gaps")
    context: Optional[Dict[str, Any]] = Field(None, description="Analysis context")

# Response Models

class StoreMemoryResponse(BaseModel):
    """Response model for memory storage"""
    success: bool
    memory_id: Optional[str]
    graph_episode_id: Optional[str]
    relationships_found: int
    entities_found: int
    message: str

class SearchMemoryResponse(BaseModel):
    """Response model for memory search"""
    success: bool
    results: List[Dict[str, Any]]
    total_results: int
    search_type: str
    sources_used: List[str]
    query_time_ms: int

class TemporalSearchResponse(BaseModel):
    """Response model for temporal search"""
    success: bool
    results: List[Dict[str, Any]]
    temporal_insights: Dict[str, Any]
    relationship_evolution: List[Dict[str, Any]]
    patterns_detected: List[str]

class AgentCollaborationResponse(BaseModel):
    """Response model for agent collaboration"""
    success: bool
    agent_context: Dict[str, Any]
    collaboration_opportunities: List[Dict[str, Any]]
    shared_knowledge: Dict[str, Any]

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    overall_status: str
    components: Dict[str, str]
    metrics: Dict[str, Any]
    timestamp: str

class EnhancedMemoryController:
    """
    Controller for Enhanced Memory System with Graphiti integration
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the enhanced memory controller"""
        self.enhanced_memory = get_enhanced_memory_system(config)
        self.request_count = 0
        self.error_count = 0
    
    async def store_memory(self, request: StoreMemoryRequest) -> StoreMemoryResponse:
        """
        Store content in both vector database and knowledge graph
        POST /api/memory/enhanced/store
        """
        try:
            self.request_count += 1
            start_time = datetime.now()
            
            # Prepare context with additional metadata
            context = request.context or {}
            context.update({
                "agent_name": request.agent_name,
                "task_id": request.task_id,
                "stored_at": start_time.isoformat(),
                "api_version": "enhanced_v1"
            })
            
            # Store memory in enhanced system
            episode = await self.enhanced_memory.store_memory(
                content=request.content,
                context=context
            )
            
            response = StoreMemoryResponse(
                success=True,
                memory_id=episode.memory_id,
                graph_episode_id=episode.graph_episode_id,
                relationships_found=len(episode.relationships or []),
                entities_found=len(episode.entities or []),
                message="Memory stored successfully in enhanced system"
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info("✅ Enhanced memory stored", {
                "memory_id": episode.memory_id,
                "graph_episode_id": episode.graph_episode_id,
                "relationships": len(episode.relationships or []),
                "processing_time_ms": processing_time
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Failed to store enhanced memory: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def search_memory(self, request: SearchMemoryRequest) -> SearchMemoryResponse:
        """
        Search memory using hybrid vector + graph approach
        POST /api/memory/enhanced/search
        """
        try:
            self.request_count += 1
            start_time = datetime.now()
            
            # Prepare time range if provided
            time_range = None
            if request.start_time and request.end_time:
                time_range = (request.start_time, request.end_time)
            
            # Perform enhanced search
            results = await self.enhanced_memory.enhanced_search(
                query=request.query,
                search_type=request.search_type,
                user_context=request.user_context,
                limit=request.limit,
                time_range=time_range
            )
            
            # Convert results to response format
            formatted_results = []
            sources_used = set()
            
            for result in results:
                sources_used.add(result.source)
                formatted_result = {
                    "content": result.content,
                    "relevance_score": result.relevance_score,
                    "source": result.source,
                    "metadata": result.metadata or {}
                }
                
                if result.relationships:
                    formatted_result["relationships"] = result.relationships
                
                if result.temporal_context:
                    formatted_result["temporal_context"] = result.temporal_context
                
                if result.graph_path:
                    formatted_result["graph_path"] = result.graph_path
                
                formatted_results.append(formatted_result)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            response = SearchMemoryResponse(
                success=True,
                results=formatted_results,
                total_results=len(formatted_results),
                search_type=request.search_type.value,
                sources_used=list(sources_used),
                query_time_ms=int(processing_time)
            )
            
            logger.info("🔍 Enhanced memory search completed", {
                "query": request.query[:50] + "..." if len(request.query) > 50 else request.query,
                "search_type": request.search_type.value,
                "results_count": len(formatted_results),
                "sources": list(sources_used),
                "processing_time_ms": processing_time
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Enhanced memory search failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def temporal_search(self, request: TemporalSearchRequest) -> TemporalSearchResponse:
        """
        Perform temporal reasoning queries
        POST /api/memory/enhanced/temporal
        """
        try:
            self.request_count += 1
            
            # Prepare time range
            time_range = None
            if request.start_time and request.end_time:
                time_range = (request.start_time, request.end_time)
            
            # Perform temporal search
            results = await self.enhanced_memory.temporal_context_search(
                query=request.query,
                time_range=time_range,
                limit=request.limit,
                include_evolution=request.include_evolution
            )
            
            # Extract temporal insights and patterns
            temporal_insights = {}
            relationship_evolution = []
            patterns_detected = []
            
            for result in results:
                if result.temporal_context:
                    temporal_insights.update(result.temporal_context.get('insights', {}))
                    if result.temporal_context.get('evolution'):
                        relationship_evolution.extend(result.temporal_context['evolution'])
            
            # Analyze patterns across results
            if temporal_insights:
                patterns_detected = list(temporal_insights.keys())
            
            response = TemporalSearchResponse(
                success=True,
                results=[{
                    "content": r.content,
                    "relevance_score": r.relevance_score,
                    "temporal_context": r.temporal_context,
                    "metadata": r.metadata
                } for r in results],
                temporal_insights=temporal_insights,
                relationship_evolution=relationship_evolution,
                patterns_detected=patterns_detected
            )
            
            logger.info("⏰ Temporal search completed", {
                "query": request.query[:50],
                "results_count": len(results),
                "patterns_detected": len(patterns_detected)
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Temporal search failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def get_agent_collaboration(self, request: AgentCollaborationRequest) -> AgentCollaborationResponse:
        """
        Get agent collaboration context and opportunities
        POST /api/memory/enhanced/collaboration
        """
        try:
            self.request_count += 1
            
            # Get agent collaboration context
            context = await self.enhanced_memory.get_agent_collaboration_context(
                agent_name=request.agent_name,
                task_id=request.task_id,
                include_shared_knowledge=request.include_shared_knowledge
            )
            
            response = AgentCollaborationResponse(
                success=True,
                agent_context=context,
                collaboration_opportunities=context.get('collaboration_opportunities', []),
                shared_knowledge=context.get('shared_knowledge', {})
            )
            
            logger.info("🤝 Agent collaboration context retrieved", {
                "agent_name": request.agent_name,
                "task_id": request.task_id,
                "opportunities_found": len(response.collaboration_opportunities)
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Agent collaboration context failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def analyze_knowledge_gaps(self, request: KnowledgeGapRequest) -> Dict[str, Any]:
        """
        Analyze knowledge gaps in the system
        POST /api/memory/enhanced/gaps
        """
        try:
            self.request_count += 1
            
            # Perform knowledge gap analysis
            gap_analysis = await self.enhanced_memory.analyze_knowledge_gaps(
                query=request.query,
                context=request.context
            )
            
            response = {
                "success": True,
                "analysis": gap_analysis,
                "recommendations": self._generate_gap_recommendations(gap_analysis),
                "priority_areas": self._identify_priority_areas(gap_analysis)
            }
            
            logger.info("🔍 Knowledge gap analysis completed", {
                "query": request.query[:50],
                "gaps_found": len(gap_analysis.get('missing_relationships', [])),
                "weak_connections": len(gap_analysis.get('weak_connections', []))
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Knowledge gap analysis failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive system metrics
        GET /api/memory/enhanced/metrics
        """
        try:
            # Get enhanced memory system metrics
            system_metrics = self.enhanced_memory.get_system_metrics()
            
            # Add controller-level metrics
            controller_metrics = {
                "controller_requests": self.request_count,
                "controller_errors": self.error_count,
                "error_rate": (self.error_count / max(self.request_count, 1)) * 100
            }
            
            response = {
                "success": True,
                "system_metrics": system_metrics,
                "controller_metrics": controller_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Failed to get system metrics: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def health_check(self) -> HealthCheckResponse:
        """
        Comprehensive health check
        GET /api/memory/enhanced/health
        """
        try:
            # Perform health check
            health_data = await self.enhanced_memory.health_check()
            
            # Get system metrics for additional context
            metrics = self.enhanced_memory.get_system_metrics()
            
            response = HealthCheckResponse(
                overall_status=health_data["overall_status"],
                components=health_data["components"],
                metrics=metrics,
                timestamp=health_data["timestamp"]
            )
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Health check failed: {error}")
            
            return HealthCheckResponse(
                overall_status="unhealthy",
                components={"enhanced_memory": f"error: {error}"},
                metrics={},
                timestamp=datetime.now().isoformat()
            )
    
    async def predict_next_actions(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Predict next actions based on graph patterns
        POST /api/memory/enhanced/predict
        """
        try:
            self.request_count += 1
            
            # Perform predictive search
            predictions = await self.enhanced_memory.predictive_search(
                query=query,
                user_context=user_context,
                limit=5
            )
            
            response = {
                "success": True,
                "predictions": [{
                    "suggested_action": p.content,
                    "confidence": p.relevance_score,
                    "reasoning": p.metadata.get('reasoning', ''),
                    "prediction_type": p.metadata.get('prediction_type', ''),
                    "based_on_patterns": p.metadata.get('based_on_patterns', [])
                } for p in predictions],
                "total_predictions": len(predictions)
            }
            
            logger.info("🔮 Predictive analysis completed", {
                "query": query[:50],
                "predictions_count": len(predictions),
                "avg_confidence": sum(p.relevance_score for p in predictions) / len(predictions) if predictions else 0
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Predictive analysis failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    # Private helper methods
    
    def _generate_gap_recommendations(self, gap_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on gap analysis"""
        recommendations = []
        
        missing_relationships = gap_analysis.get('missing_relationships', [])
        weak_connections = gap_analysis.get('weak_connections', [])
        
        # Recommendations for missing relationships
        for missing in missing_relationships[:5]:  # Top 5
            recommendations.append({
                "type": "missing_relationship",
                "priority": "high",
                "action": f"Establish relationship between {missing.get('entities', [])}",
                "expected_impact": "Improved contextual understanding"
            })
        
        # Recommendations for weak connections
        for weak in weak_connections[:3]:  # Top 3
            recommendations.append({
                "type": "weak_connection",
                "priority": "medium",
                "action": f"Strengthen connection in {weak.get('domain', 'unknown area')}",
                "expected_impact": "Better knowledge recall"
            })
        
        return recommendations
    
    def _identify_priority_areas(self, gap_analysis: Dict[str, Any]) -> List[str]:
        """Identify priority areas for knowledge improvement"""
        priority_areas = []
        
        # Analyze gap analysis to identify domains with most issues
        missing_count = len(gap_analysis.get('missing_relationships', []))
        weak_count = len(gap_analysis.get('weak_connections', []))
        
        if missing_count > 5:
            priority_areas.append("relationship_discovery")
        
        if weak_count > 3:
            priority_areas.append("connection_strengthening")
        
        if gap_analysis.get('enrichment_opportunities'):
            priority_areas.append("knowledge_enrichment")
        
        return priority_areas

# Global controller instance
_enhanced_memory_controller = None

def get_enhanced_memory_controller(config: Dict[str, Any] = None) -> EnhancedMemoryController:
    """Get or create the global enhanced memory controller instance"""
    global _enhanced_memory_controller
    
    if _enhanced_memory_controller is None:
        _enhanced_memory_controller = EnhancedMemoryController(config)
    
    return _enhanced_memory_controller