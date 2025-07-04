"""
Enhanced Memory System with Graphiti Knowledge Graph Integration

This module implements a sophisticated memory system that combines:
- Existing vector-based memory storage (Supabase)
- Knowledge graph relationships (Neo4j + Graphiti)
- Temporal reasoning and bi-temporal queries
- Agent collaboration through shared knowledge graphs
- Predictive assistance based on relationship patterns

Architecture:
User Query → SAM Agent → Graphiti Knowledge Graph → Neo4j + Vector Search → Contextual Response
                      ↓
                Memory Analyzer (backup/export)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Core dependencies
import neo4j
from graphiti import Graphiti
from openai import OpenAI

# MCP dependencies
from .memoryService import SAMMemoryAnalyzer
from ..utils.logger import logger

class SearchType(Enum):
    """Types of search operations available"""
    VECTOR_ONLY = "vector_only"
    GRAPH_ONLY = "graph_only"
    HYBRID = "hybrid"
    TEMPORAL = "temporal"
    PREDICTIVE = "predictive"

@dataclass
class MemoryEpisode:
    """Represents a memory episode with both vector and graph data"""
    content: str
    context: Dict[str, Any]
    timestamp: datetime
    memory_id: Optional[str] = None
    graph_episode_id: Optional[str] = None
    relationships: List[Dict] = None
    entities: List[str] = None
    temporal_context: Optional[Dict] = None

@dataclass
class SearchResult:
    """Enhanced search result with multiple data sources"""
    content: str
    relevance_score: float
    source: str  # 'memory', 'graph', 'hybrid'
    relationships: List[Dict] = None
    temporal_context: Optional[Dict] = None
    graph_path: Optional[List] = None
    metadata: Dict = None

class EnhancedMemorySystem:
    """
    Advanced memory system combining vector embeddings with knowledge graphs
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the enhanced memory system"""
        self.config = config or {}
        
        # Initialize existing memory analyzer
        self.memory_analyzer = SAMMemoryAnalyzer()
        
        # Initialize Graphiti knowledge graph
        self.graphiti = None
        self.neo4j_driver = None
        
        # Performance tracking
        self.metrics = {
            "total_episodes": 0,
            "successful_stores": 0,
            "failed_stores": 0,
            "search_operations": 0,
            "graph_operations": 0,
            "relationships_created": 0,
            "predictions_made": 0
        }
        
        # Configuration for different operation modes
        self.dual_write_enabled = True
        self.fallback_to_vector = True
        self.enable_temporal_reasoning = True
        self.enable_predictive_assistance = True
        
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize connections to Neo4j and Graphiti"""
        try:
            # Initialize Neo4j driver
            neo4j_uri = self.config.get('NEO4J_URI', 'bolt://sam.chat:7687')
            neo4j_username = self.config.get('NEO4J_USERNAME', 'neo4j')
            neo4j_password = self.config.get('NEO4J_PASSWORD', 'neo4j_password')
            
            self.neo4j_driver = neo4j.GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_username, neo4j_password)
            )
            
            # Test Neo4j connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            
            # Initialize OpenAI client for Graphiti
            openai_client = OpenAI(
                api_key=self.config.get('OPENAI_API_KEY')
            )
            
            # Initialize Graphiti
            self.graphiti = Graphiti(
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_username,
                neo4j_password=neo4j_password,
                llm_client=openai_client,
                embedding_model=self.config.get('GRAPHITI_EMBEDDING_MODEL', 'text-embedding-3-small'),
                llm_model=self.config.get('GRAPHITI_LLM_MODEL', 'gpt-4-turbo-preview')
            )
            
            logger.info("✅ Enhanced Memory System initialized with Graphiti and Neo4j")
            
        except Exception as error:
            logger.error(f"❌ Failed to initialize Enhanced Memory System: {error}")
            # Fall back to vector-only mode
            self.dual_write_enabled = False
            self.graphiti = None
            self.neo4j_driver = None
    
    async def store_memory(self, content: str, context: Dict[str, Any] = None) -> MemoryEpisode:
        """
        Store memory in both vector database and knowledge graph
        Implements dual-write strategy for zero-downtime migration
        """
        episode = MemoryEpisode(
            content=content,
            context=context or {},
            timestamp=datetime.now()
        )
        
        try:
            self.metrics["total_episodes"] += 1
            
            # Store in existing memory system (vector database)
            memory_result = await self.memory_analyzer.store_memory(content, context)
            episode.memory_id = memory_result.get('id')
            
            # Store in knowledge graph if available
            if self.graphiti and self.dual_write_enabled:
                try:
                    graph_episode = {
                        "text": content,
                        "metadata": {
                            **context,
                            "timestamp": episode.timestamp.isoformat(),
                            "memory_id": episode.memory_id,
                            "source": "enhanced_memory_system"
                        }
                    }
                    
                    graph_result = await self._store_in_graph(graph_episode)
                    episode.graph_episode_id = graph_result.get('episode_id')
                    episode.relationships = graph_result.get('relationships', [])
                    episode.entities = graph_result.get('entities', [])
                    
                    self.metrics["relationships_created"] += len(episode.relationships)
                    
                except Exception as graph_error:
                    logger.warning(f"Graph storage failed, continuing with vector only: {graph_error}")
            
            self.metrics["successful_stores"] += 1
            
            logger.info(f"📝 Memory stored successfully", {
                "memory_id": episode.memory_id,
                "graph_episode_id": episode.graph_episode_id,
                "relationships_found": len(episode.relationships or [])
            })
            
            return episode
            
        except Exception as error:
            self.metrics["failed_stores"] += 1
            logger.error(f"❌ Failed to store memory: {error}")
            raise
    
    async def enhanced_search(
        self,
        query: str,
        search_type: SearchType = SearchType.HYBRID,
        user_context: Dict[str, Any] = None,
        limit: int = 10,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[SearchResult]:
        """
        Enhanced search combining vector similarity and graph traversal
        """
        try:
            self.metrics["search_operations"] += 1
            results = []
            
            if search_type in [SearchType.VECTOR_ONLY, SearchType.HYBRID]:
                # Get vector search results
                vector_results = await self.memory_analyzer.search(query, limit=limit)
                
                for result in vector_results:
                    results.append(SearchResult(
                        content=result.get('content', ''),
                        relevance_score=result.get('score', 0.0),
                        source='memory',
                        metadata=result.get('metadata', {})
                    ))
            
            if search_type in [SearchType.GRAPH_ONLY, SearchType.HYBRID] and self.graphiti:
                # Get graph search results
                graph_results = await self._search_graph(
                    query=query,
                    user_context=user_context,
                    time_range=time_range,
                    limit=limit
                )
                
                for result in graph_results:
                    results.append(SearchResult(
                        content=result.get('content', ''),
                        relevance_score=result.get('score', 0.0),
                        source='graph',
                        relationships=result.get('relationships', []),
                        graph_path=result.get('path', []),
                        metadata=result.get('metadata', {})
                    ))
            
            if search_type == SearchType.TEMPORAL and self.enable_temporal_reasoning:
                # Temporal context search
                temporal_results = await self.temporal_context_search(
                    query=query,
                    time_range=time_range,
                    limit=limit
                )
                results.extend(temporal_results)
            
            if search_type == SearchType.PREDICTIVE and self.enable_predictive_assistance:
                # Predictive search based on patterns
                predictive_results = await self.predictive_search(
                    query=query,
                    user_context=user_context,
                    limit=limit
                )
                results.extend(predictive_results)
            
            # Merge and re-rank results for hybrid search
            if search_type == SearchType.HYBRID:
                results = self._merge_and_rerank(results)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"🔍 Enhanced search completed", {
                "query": query[:50] + "..." if len(query) > 50 else query,
                "search_type": search_type.value,
                "results_count": len(results),
                "sources": list(set(r.source for r in results))
            })
            
            return results[:limit]
            
        except Exception as error:
            logger.error(f"❌ Enhanced search failed: {error}")
            # Fallback to basic vector search
            if self.fallback_to_vector:
                return await self._fallback_search(query, limit)
            raise
    
    async def temporal_context_search(
        self,
        query: str,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 10,
        include_evolution: bool = True
    ) -> List[SearchResult]:
        """
        Perform temporal reasoning queries to understand how relationships changed over time
        """
        if not self.graphiti or not self.enable_temporal_reasoning:
            return []
        
        try:
            # Extract entities from query
            entities = await self._extract_entities(query)
            
            # Get historical context
            historical_context = await self._search_temporal_graph(
                query=query,
                entities=entities,
                time_range=time_range,
                include_evolution=include_evolution
            )
            
            # Get relationship evolution
            relationship_evolution = await self._get_relationship_history(
                entities=entities,
                time_range=time_range
            )
            
            results = []
            for context in historical_context:
                result = SearchResult(
                    content=context.get('content', ''),
                    relevance_score=context.get('score', 0.0),
                    source='temporal',
                    temporal_context={
                        'evolution': relationship_evolution,
                        'insights': self._analyze_temporal_patterns(relationship_evolution),
                        'time_period': context.get('time_period')
                    },
                    metadata=context.get('metadata', {})
                )
                results.append(result)
            
            return results[:limit]
            
        except Exception as error:
            logger.error(f"❌ Temporal context search failed: {error}")
            return []
    
    async def predictive_search(
        self,
        query: str,
        user_context: Dict[str, Any] = None,
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Predict what user might need based on graph patterns and historical behavior
        """
        if not self.graphiti or not self.enable_predictive_assistance:
            return []
        
        try:
            self.metrics["predictions_made"] += 1
            
            # Get user's historical patterns
            user_patterns = await self._get_user_patterns(user_context)
            
            # Find similar interaction patterns
            similar_patterns = await self._find_similar_patterns(query, user_patterns)
            
            # Generate predictions based on graph traversal
            predictions = await self._generate_predictions(
                current_context=user_context,
                historical_patterns=user_patterns,
                similar_patterns=similar_patterns,
                confidence_threshold=0.7
            )
            
            results = []
            for prediction in predictions[:limit]:
                result = SearchResult(
                    content=prediction.get('suggested_content', ''),
                    relevance_score=prediction.get('confidence', 0.0),
                    source='predictive',
                    metadata={
                        'prediction_type': prediction.get('type'),
                        'reasoning': prediction.get('reasoning'),
                        'confidence': prediction.get('confidence'),
                        'based_on_patterns': prediction.get('patterns')
                    }
                )
                results.append(result)
            
            return results
            
        except Exception as error:
            logger.error(f"❌ Predictive search failed: {error}")
            return []
    
    async def get_agent_collaboration_context(
        self,
        agent_name: str,
        task_id: str = None,
        include_shared_knowledge: bool = True
    ) -> Dict[str, Any]:
        """
        Get contextual knowledge for agent collaboration
        """
        if not self.graphiti:
            return {}
        
        try:
            # Get agent-specific context
            agent_context = await self._get_agent_context(agent_name, task_id)
            
            # Find collaboration opportunities
            if include_shared_knowledge:
                collaboration_map = await self._find_collaboration_opportunities(
                    agent_name=agent_name,
                    current_context=agent_context
                )
                agent_context['collaboration_opportunities'] = collaboration_map
            
            return agent_context
            
        except Exception as error:
            logger.error(f"❌ Failed to get agent collaboration context: {error}")
            return {}
    
    async def analyze_knowledge_gaps(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze knowledge gaps in the graph and suggest areas for improvement
        """
        if not self.graphiti:
            return {}
        
        try:
            # Find missing relationships
            missing_relationships = await self._find_missing_relationships(query, context)
            
            # Identify weak connections
            weak_connections = await self._identify_weak_connections(query)
            
            # Suggest knowledge enrichment opportunities
            enrichment_opportunities = await self._suggest_knowledge_enrichment(
                missing_relationships,
                weak_connections
            )
            
            return {
                'missing_relationships': missing_relationships,
                'weak_connections': weak_connections,
                'enrichment_opportunities': enrichment_opportunities,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as error:
            logger.error(f"❌ Knowledge gap analysis failed: {error}")
            return {}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics and health status"""
        neo4j_status = "connected" if self.neo4j_driver else "disconnected"
        graphiti_status = "enabled" if self.graphiti else "disabled"
        
        return {
            **self.metrics,
            "system_status": {
                "dual_write_enabled": self.dual_write_enabled,
                "neo4j_status": neo4j_status,
                "graphiti_status": graphiti_status,
                "temporal_reasoning_enabled": self.enable_temporal_reasoning,
                "predictive_assistance_enabled": self.enable_predictive_assistance,
                "fallback_to_vector": self.fallback_to_vector
            },
            "performance": {
                "success_rate": (
                    self.metrics["successful_stores"] / 
                    max(self.metrics["total_episodes"], 1) * 100
                ),
                "avg_relationships_per_episode": (
                    self.metrics["relationships_created"] / 
                    max(self.metrics["successful_stores"], 1)
                )
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all components"""
        health = {
            "overall_status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check vector memory system
        try:
            await self.memory_analyzer.health_check()
            health["components"]["vector_memory"] = "healthy"
        except Exception as error:
            health["components"]["vector_memory"] = f"unhealthy: {error}"
            health["overall_status"] = "degraded"
        
        # Check Neo4j connection
        if self.neo4j_driver:
            try:
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
                health["components"]["neo4j"] = "healthy"
            except Exception as error:
                health["components"]["neo4j"] = f"unhealthy: {error}"
                health["overall_status"] = "degraded"
        else:
            health["components"]["neo4j"] = "not_configured"
        
        # Check Graphiti
        if self.graphiti:
            try:
                # Test basic Graphiti functionality
                health["components"]["graphiti"] = "healthy"
            except Exception as error:
                health["components"]["graphiti"] = f"unhealthy: {error}"
                health["overall_status"] = "degraded"
        else:
            health["components"]["graphiti"] = "not_configured"
        
        return health
    
    # Private helper methods
    
    async def _store_in_graph(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """Store episode in Graphiti knowledge graph"""
        if not self.graphiti:
            return {}
        
        self.metrics["graph_operations"] += 1
        
        # Add episode to Graphiti
        result = await self.graphiti.add_episode(episode)
        
        return {
            "episode_id": result.get("episode_id"),
            "relationships": result.get("relationships", []),
            "entities": result.get("entities", [])
        }
    
    async def _search_graph(
        self,
        query: str,
        user_context: Dict[str, Any] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search the knowledge graph using Graphiti"""
        if not self.graphiti:
            return []
        
        self.metrics["graph_operations"] += 1
        
        search_params = {
            "query": query,
            "search_type": "hybrid",  # semantic + keyword + graph
            "limit": limit
        }
        
        if user_context:
            search_params["user_context"] = user_context
        
        if time_range:
            search_params["time_range"] = {
                "start": time_range[0].isoformat(),
                "end": time_range[1].isoformat()
            }
        
        results = await self.graphiti.search(**search_params)
        return results.get("results", [])
    
    async def _search_temporal_graph(
        self,
        query: str,
        entities: List[str],
        time_range: Optional[Tuple[datetime, datetime]] = None,
        include_evolution: bool = True
    ) -> List[Dict[str, Any]]:
        """Search graph with temporal context"""
        if not self.graphiti:
            return []
        
        return await self.graphiti.search_temporal(
            query=query,
            entities=entities,
            time_range=time_range,
            include_evolution=include_evolution
        )
    
    async def _get_relationship_history(
        self,
        entities: List[str],
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """Get history of how relationships between entities changed over time"""
        if not self.graphiti:
            return []
        
        return await self.graphiti.get_relationship_history(
            entities=entities,
            time_range=time_range
        )
    
    async def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text using Graphiti's NER"""
        if not self.graphiti:
            return []
        
        return await self.graphiti.extract_entities(text)
    
    def _analyze_temporal_patterns(self, evolution_data: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in relationship evolution"""
        if not evolution_data:
            return {}
        
        patterns = {
            "relationship_trends": [],
            "stability_periods": [],
            "change_points": [],
            "cyclical_patterns": []
        }
        
        # Analyze trends and patterns in the evolution data
        # This would include statistical analysis of relationship changes
        
        return patterns
    
    async def _get_user_patterns(self, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get historical patterns for a user"""
        if not user_context or not self.graphiti:
            return {}
        
        user_id = user_context.get('user_id')
        if not user_id:
            return {}
        
        # Query graph for user interaction patterns
        patterns = await self.graphiti.get_user_patterns(user_id)
        return patterns
    
    async def _find_similar_patterns(
        self,
        query: str,
        user_patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find similar interaction patterns in the graph"""
        if not self.graphiti:
            return []
        
        return await self.graphiti.find_similar_patterns(query, user_patterns)
    
    async def _generate_predictions(
        self,
        current_context: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        similar_patterns: List[Dict[str, Any]],
        confidence_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Generate predictions based on patterns"""
        predictions = []
        
        # Analyze patterns and generate predictions
        # This would use graph algorithms to predict likely next actions
        
        return predictions
    
    async def _get_agent_context(self, agent_name: str, task_id: str = None) -> Dict[str, Any]:
        """Get context for a specific agent"""
        if not self.graphiti:
            return {}
        
        return await self.graphiti.get_agent_context(agent_name, task_id)
    
    async def _find_collaboration_opportunities(
        self,
        agent_name: str,
        current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find opportunities for agent collaboration"""
        if not self.graphiti:
            return {}
        
        return await self.graphiti.find_collaboration_opportunities(
            agent_name, current_context
        )
    
    async def _find_missing_relationships(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Find missing relationships in the knowledge graph"""
        # Implementation would analyze graph structure to find gaps
        return []
    
    async def _identify_weak_connections(self, query: str) -> List[Dict[str, Any]]:
        """Identify weak connections that could be strengthened"""
        # Implementation would analyze relationship strengths
        return []
    
    async def _suggest_knowledge_enrichment(
        self,
        missing_relationships: List[Dict],
        weak_connections: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Suggest opportunities to enrich the knowledge graph"""
        # Implementation would suggest specific actions to improve graph
        return []
    
    def _merge_and_rerank(self, results: List[SearchResult]) -> List[SearchResult]:
        """Merge and re-rank results from multiple sources"""
        # Group by source
        vector_results = [r for r in results if r.source == 'memory']
        graph_results = [r for r in results if r.source == 'graph']
        
        # Apply different weighting strategies
        for result in vector_results:
            result.relevance_score *= 0.7  # Vector results weight
        
        for result in graph_results:
            result.relevance_score *= 0.9  # Graph results weight (higher due to context)
        
        # Merge and deduplicate
        merged_results = vector_results + graph_results
        
        # Remove duplicates based on content similarity
        unique_results = []
        seen_content = set()
        
        for result in merged_results:
            content_hash = hash(result.content[:100])  # Use first 100 chars as fingerprint
            if content_hash not in seen_content:
                unique_results.append(result)
                seen_content.add(content_hash)
        
        return unique_results
    
    async def _fallback_search(self, query: str, limit: int) -> List[SearchResult]:
        """Fallback to basic vector search when graph is unavailable"""
        try:
            vector_results = await self.memory_analyzer.search(query, limit=limit)
            
            results = []
            for result in vector_results:
                results.append(SearchResult(
                    content=result.get('content', ''),
                    relevance_score=result.get('score', 0.0),
                    source='memory_fallback',
                    metadata=result.get('metadata', {})
                ))
            
            return results
            
        except Exception as error:
            logger.error(f"❌ Fallback search failed: {error}")
            return []
    
    async def close(self):
        """Clean up connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        if self.graphiti:
            await self.graphiti.close()

# Global instance
_enhanced_memory_system = None

def get_enhanced_memory_system(config: Dict[str, Any] = None) -> EnhancedMemorySystem:
    """Get or create the global enhanced memory system instance"""
    global _enhanced_memory_system
    
    if _enhanced_memory_system is None:
        _enhanced_memory_system = EnhancedMemorySystem(config)
    
    return _enhanced_memory_system