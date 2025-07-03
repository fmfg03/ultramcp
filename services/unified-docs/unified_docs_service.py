#!/usr/bin/env python3
"""
Unified Documentation Intelligence Service
Combines Context7, Ref Tools, and VoyageAI for complete documentation ecosystem
"""

import asyncio
import logging
import os
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentationType(Enum):
    """Types of documentation"""
    CODE_SNIPPETS = "code_snippets"      # Context7 - library code examples
    FULL_DOCS = "full_docs"              # Ref Tools - complete documentation
    SEMANTIC_CODE = "semantic_code"      # Claude Memory - semantic code search
    HYBRID = "hybrid"                    # All sources combined

class IntelligenceLevel(Enum):
    """Level of intelligence to apply"""
    BASIC = "basic"                      # Simple search
    ENHANCED = "enhanced"                # With VoyageAI embeddings
    COGNITIVE = "cognitive"              # With reranking and analysis
    SUPREME = "supreme"                  # Full AI orchestration

@dataclass
class UnifiedSearchRequest:
    """Unified documentation search request"""
    query: str
    documentation_type: DocumentationType = DocumentationType.HYBRID
    intelligence_level: IntelligenceLevel = IntelligenceLevel.ENHANCED
    privacy_level: str = "INTERNAL"
    include_code: bool = True
    include_examples: bool = True
    max_results_per_source: int = 5
    project_context: Optional[str] = None
    organization: Optional[str] = None

@dataclass 
class DocumentationSource:
    """Documentation source metadata"""
    name: str
    type: str
    url: str
    relevance_score: float
    intelligence_used: str
    privacy_compliant: bool
    processing_time: float

@dataclass
class UnifiedResult:
    """Unified documentation result"""
    title: str
    content: str
    source: DocumentationSource
    code_examples: List[str]
    related_links: List[str]
    confidence_score: float
    last_updated: Optional[str] = None

@dataclass
class UnifiedResponse:
    """Complete unified documentation response"""
    results: List[UnifiedResult]
    query: str
    sources_used: List[str]
    total_results: int
    search_time: float
    intelligence_level: str
    privacy_compliant: bool
    cost_analysis: Dict[str, Any]

class UnifiedDocumentationOrchestrator:
    """Orchestrates multiple documentation intelligence services"""
    
    def __init__(self):
        self.session = None
        
        # Service endpoints
        self.context7_url = os.getenv("CONTEXT7_SERVICE_URL", "http://localhost:8003")
        self.ref_tools_url = os.getenv("REF_TOOLS_SERVICE_URL", "http://localhost:8011")
        self.voyage_url = os.getenv("VOYAGE_SERVICE_URL", "http://localhost:8010")
        self.memory_url = os.getenv("MEMORY_SERVICE_URL", "http://localhost:8009")
        
        # Service availability
        self.services_available = {
            "context7": False,
            "ref_tools": False,
            "voyage_ai": False,
            "claude_memory": False
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self._check_service_availability()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _check_service_availability(self):
        """Check which services are available"""
        services = {
            "context7": f"{self.context7_url}/health",
            "ref_tools": f"{self.ref_tools_url}/health", 
            "voyage_ai": f"{self.voyage_url}/health",
            "claude_memory": f"{self.memory_url}/health"
        }
        
        for service, url in services.items():
            try:
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    self.services_available[service] = response.status == 200
                    logger.info(f"Service {service}: {'✅ Available' if self.services_available[service] else '❌ Unavailable'}")
            except Exception as e:
                logger.warning(f"Service {service} check failed: {e}")
                self.services_available[service] = False
    
    async def unified_search(self, request: UnifiedSearchRequest) -> UnifiedResponse:
        """Perform unified documentation search across all sources"""
        start_time = datetime.now()
        all_results = []
        sources_used = []
        cost_analysis = {"total_cost": 0.0, "breakdown": {}}
        
        # Determine which sources to search based on documentation type
        sources_to_search = self._select_sources(request)
        
        # Execute searches in parallel for performance
        search_tasks = []
        
        if "context7" in sources_to_search and self.services_available["context7"]:
            search_tasks.append(self._search_context7(request))
            sources_used.append("context7")
        
        if "ref_tools" in sources_to_search and self.services_available["ref_tools"]:
            search_tasks.append(self._search_ref_tools(request))
            sources_used.append("ref_tools")
        
        if "claude_memory" in sources_to_search and self.services_available["claude_memory"]:
            search_tasks.append(self._search_claude_memory(request))
            sources_used.append("claude_memory")
        
        # Execute searches concurrently
        if search_tasks:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for i, result in enumerate(search_results):
                if isinstance(result, Exception):
                    logger.error(f"Search task {i} failed: {result}")
                else:
                    all_results.extend(result["results"])
                    cost_analysis["breakdown"][sources_used[i]] = result.get("cost", 0.0)
                    cost_analysis["total_cost"] += result.get("cost", 0.0)
        
        # Apply intelligence enhancement if requested
        if request.intelligence_level in [IntelligenceLevel.ENHANCED, IntelligenceLevel.COGNITIVE, IntelligenceLevel.SUPREME]:
            all_results = await self._enhance_with_voyage_ai(all_results, request)
        
        # Apply cognitive analysis for highest intelligence levels
        if request.intelligence_level in [IntelligenceLevel.COGNITIVE, IntelligenceLevel.SUPREME]:
            all_results = await self._apply_cognitive_analysis(all_results, request)
        
        # Sort and limit results
        all_results.sort(key=lambda x: x.confidence_score, reverse=True)
        final_results = all_results[:request.max_results_per_source * len(sources_used)]
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        return UnifiedResponse(
            results=final_results,
            query=request.query,
            sources_used=sources_used,
            total_results=len(final_results),
            search_time=search_time,
            intelligence_level=request.intelligence_level.value,
            privacy_compliant=self._check_privacy_compliance(final_results, request.privacy_level),
            cost_analysis=cost_analysis
        )
    
    def _select_sources(self, request: UnifiedSearchRequest) -> List[str]:
        """Select appropriate sources based on documentation type"""
        if request.documentation_type == DocumentationType.CODE_SNIPPETS:
            return ["context7", "claude_memory"]
        elif request.documentation_type == DocumentationType.FULL_DOCS:
            return ["ref_tools", "claude_memory"]
        elif request.documentation_type == DocumentationType.SEMANTIC_CODE:
            return ["claude_memory", "context7"]
        else:  # HYBRID
            return ["context7", "ref_tools", "claude_memory"]
    
    async def _search_context7(self, request: UnifiedSearchRequest) -> Dict[str, Any]:
        """Search Context7 for code snippets and library documentation"""
        try:
            # Detect library from query
            library = self._extract_library_from_query(request.query)
            
            if library:
                # Two-step Context7 approach: resolve library ID then get docs
                library_docs = await self._get_context7_library_docs(library)
                search_results = await self._search_context7_docs(library_docs, request.query)
            else:
                # Direct search if no specific library detected
                search_results = await self._search_context7_direct(request.query)
            
            # Convert to unified format
            unified_results = []
            for result in search_results:
                unified_result = UnifiedResult(
                    title=result.get("title", f"Context7: {library or 'Code'}"),
                    content=result.get("content", ""),
                    source=DocumentationSource(
                        name="Context7",
                        type="code_snippets",
                        url=result.get("url", ""),
                        relevance_score=result.get("score", 0.8),
                        intelligence_used="context7",
                        privacy_compliant=True,
                        processing_time=result.get("time", 0.0)
                    ),
                    code_examples=result.get("code_examples", []),
                    related_links=result.get("related_links", []),
                    confidence_score=result.get("score", 0.8)
                )
                unified_results.append(unified_result)
            
            return {"results": unified_results, "cost": 0.0}
            
        except Exception as e:
            logger.error(f"Context7 search failed: {e}")
            return {"results": [], "cost": 0.0}
    
    async def _search_ref_tools(self, request: UnifiedSearchRequest) -> Dict[str, Any]:
        """Search Ref Tools for full documentation"""
        try:
            # Map privacy levels
            privacy_mapping = {
                "PUBLIC": "PUBLIC",
                "INTERNAL": "INTERNAL", 
                "CONFIDENTIAL": "CONFIDENTIAL",
                "RESTRICTED": "RESTRICTED"
            }
            
            search_payload = {
                "query": request.query,
                "source_type": "AUTO",
                "privacy_level": privacy_mapping.get(request.privacy_level, "INTERNAL"),
                "include_code_examples": request.include_code,
                "max_results": request.max_results_per_source,
                "organization": request.organization,
                "project_context": request.project_context
            }
            
            async with self.session.post(
                f"{self.ref_tools_url}/ref/search",
                json=search_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Convert to unified format
                    unified_results = []
                    for result in data.get("results", []):
                        unified_result = UnifiedResult(
                            title=result.get("title", "Ref Tools Documentation"),
                            content=result.get("content", ""),
                            source=DocumentationSource(
                                name="Ref Tools",
                                type="full_docs",
                                url=result.get("url", ""),
                                relevance_score=result.get("relevance_score", 0.7),
                                intelligence_used="ref_tools",
                                privacy_compliant=result.get("privacy_compliant", True),
                                processing_time=data.get("search_time", 0.0)
                            ),
                            code_examples=result.get("code_examples", []),
                            related_links=[result.get("url", "")],
                            confidence_score=result.get("relevance_score", 0.7),
                            last_updated=result.get("last_updated")
                        )
                        unified_results.append(unified_result)
                    
                    return {"results": unified_results, "cost": 0.0}
                else:
                    logger.warning(f"Ref Tools search returned status {response.status}")
                    return {"results": [], "cost": 0.0}
                    
        except Exception as e:
            logger.error(f"Ref Tools search failed: {e}")
            return {"results": [], "cost": 0.0}
    
    async def _search_claude_memory(self, request: UnifiedSearchRequest) -> Dict[str, Any]:
        """Search Claude Code Memory for semantic code intelligence"""
        try:
            # Use enhanced search if VoyageAI intelligence is requested
            if request.intelligence_level in [IntelligenceLevel.ENHANCED, IntelligenceLevel.COGNITIVE, IntelligenceLevel.SUPREME]:
                endpoint = "/memory/search/enhanced"
                search_payload = {
                    "query": request.query,
                    "limit": request.max_results_per_source,
                    "privacy_level": request.privacy_level,
                    "search_mode": "HYBRID" if request.intelligence_level != IntelligenceLevel.BASIC else "LOCAL_ONLY",
                    "enable_reranking": request.intelligence_level in [IntelligenceLevel.COGNITIVE, IntelligenceLevel.SUPREME],
                    "project_name": request.project_context
                }
            else:
                endpoint = "/memory/search/privacy-first"
                search_payload = {
                    "query": request.query,
                    "limit": request.max_results_per_source,
                    "project_name": request.project_context
                }
            
            async with self.session.post(
                f"{self.memory_url}{endpoint}",
                json=search_payload if endpoint == "/memory/search/enhanced" else None,
                params=search_payload if endpoint != "/memory/search/enhanced" else None
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Convert to unified format
                    unified_results = []
                    for result in data.get("results", []):
                        unified_result = UnifiedResult(
                            title=result.get("element_name", "Code Memory Result"),
                            content=result.get("content", ""),
                            source=DocumentationSource(
                                name="Claude Code Memory",
                                type="semantic_code",
                                url=f"file://{result.get('file_path', '')}#{result.get('start_line', 0)}",
                                relevance_score=result.get("score", 0.8),
                                intelligence_used=result.get("model_used", "local"),
                                privacy_compliant=result.get("privacy_compliant", True),
                                processing_time=result.get("processing_time", 0.0)
                            ),
                            code_examples=[result.get("content", "")] if result.get("element_type") in ["function", "class", "method"] else [],
                            related_links=[f"file://{result.get('file_path', '')}"],
                            confidence_score=result.get("score", 0.8)
                        )
                        unified_results.append(unified_result)
                    
                    total_cost = sum(result.get("cost", 0.0) for result in data.get("results", []))
                    return {"results": unified_results, "cost": total_cost}
                else:
                    logger.warning(f"Claude Memory search returned status {response.status}")
                    return {"results": [], "cost": 0.0}
                    
        except Exception as e:
            logger.error(f"Claude Memory search failed: {e}")
            return {"results": [], "cost": 0.0}
    
    async def _enhance_with_voyage_ai(self, results: List[UnifiedResult], request: UnifiedSearchRequest) -> List[UnifiedResult]:
        """Enhance results with VoyageAI intelligence"""
        if not self.services_available["voyage_ai"] or not results:
            return results
        
        try:
            # Extract content for reranking
            documents = [result.content for result in results]
            
            rerank_payload = {
                "query": request.query,
                "documents": documents,
                "model": "RERANK_LITE",
                "privacy_level": request.privacy_level,
                "top_k": len(results)
            }
            
            async with self.session.post(
                f"{self.voyage_url}/rerank",
                json=rerank_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Apply reranking scores
                    reranked_docs = data.get("reranked_documents", [])
                    for rerank_item in reranked_docs:
                        original_index = rerank_item.get("index", 0)
                        if original_index < len(results):
                            results[original_index].confidence_score = rerank_item.get("relevance_score", results[original_index].confidence_score)
                            results[original_index].source.intelligence_used += "+voyage_rerank"
                    
                    # Sort by new confidence scores
                    results.sort(key=lambda x: x.confidence_score, reverse=True)
                    
        except Exception as e:
            logger.warning(f"VoyageAI enhancement failed: {e}")
        
        return results
    
    async def _apply_cognitive_analysis(self, results: List[UnifiedResult], request: UnifiedSearchRequest) -> List[UnifiedResult]:
        """Apply cognitive analysis for highest intelligence levels"""
        # Placeholder for advanced cognitive analysis
        # This could include:
        # - Cross-reference analysis between sources
        # - Confidence scoring based on source agreement
        # - Content quality assessment
        # - Relevance boosting based on project context
        
        for result in results:
            if request.intelligence_level == IntelligenceLevel.SUPREME:
                # Boost confidence for sources that agree
                similar_sources = [r for r in results if r != result and self._content_similarity(r.content, result.content) > 0.7]
                if similar_sources:
                    result.confidence_score = min(result.confidence_score * 1.2, 1.0)
                    result.source.intelligence_used += "+cognitive"
        
        return results
    
    def _content_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple content similarity"""
        if not content1 or not content2:
            return 0.0
        
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _check_privacy_compliance(self, results: List[UnifiedResult], privacy_level: str) -> bool:
        """Check if all results comply with privacy requirements"""
        return all(result.source.privacy_compliant for result in results)
    
    def _extract_library_from_query(self, query: str) -> Optional[str]:
        """Extract library name from query for Context7"""
        # Simple library detection - in practice, this could be more sophisticated
        common_libraries = ["react", "fastapi", "express", "django", "flask", "numpy", "pandas", "tensorflow"]
        query_lower = query.lower()
        
        for library in common_libraries:
            if library in query_lower:
                return library
        
        return None
    
    async def _get_context7_library_docs(self, library: str) -> Dict[str, Any]:
        """Get Context7 library documentation"""
        try:
            async with self.session.get(f"{self.context7_url}/docs/{library}") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.warning(f"Context7 library docs failed: {e}")
        
        return {}
    
    async def _search_context7_docs(self, library_docs: Dict, query: str) -> List[Dict]:
        """Search within Context7 library documentation"""
        # Simplified implementation - search within retrieved docs
        results = []
        
        content = library_docs.get("content", "")
        if query.lower() in content.lower():
            results.append({
                "title": f"Context7: {library_docs.get('library', 'Documentation')}",
                "content": content[:1000],
                "url": library_docs.get("url", ""),
                "score": 0.8,
                "code_examples": library_docs.get("examples", [])
            })
        
        return results
    
    async def _search_context7_direct(self, query: str) -> List[Dict]:
        """Direct Context7 search"""
        try:
            async with self.session.get(f"{self.context7_url}/search", params={"q": query}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
        except Exception as e:
            logger.warning(f"Context7 direct search failed: {e}")
        
        return []

# Global orchestrator instance
unified_orchestrator: Optional[UnifiedDocumentationOrchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global unified_orchestrator
    
    try:
        logger.info("🔗 Initializing Unified Documentation Intelligence Service...")
        
        unified_orchestrator = UnifiedDocumentationOrchestrator()
        
        logger.info("✅ Unified Documentation Intelligence Service initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize unified service: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Unified Documentation Intelligence Service...")

# FastAPI application
app = FastAPI(
    title="UltraMCP Unified Documentation Intelligence",
    description="Complete documentation ecosystem combining Context7, Ref Tools, and VoyageAI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class UnifiedSearchRequestModel(BaseModel):
    query: str = Field(..., description="Documentation search query")
    documentation_type: DocumentationType = Field(DocumentationType.HYBRID, description="Type of documentation to search")
    intelligence_level: IntelligenceLevel = Field(IntelligenceLevel.ENHANCED, description="Level of AI intelligence to apply")
    privacy_level: str = Field("INTERNAL", description="Privacy level for search")
    include_code: bool = Field(True, description="Include code examples")
    include_examples: bool = Field(True, description="Include usage examples")
    max_results_per_source: int = Field(5, ge=1, le=20, description="Maximum results per source")
    project_context: Optional[str] = Field(None, description="Project context")
    organization: Optional[str] = Field(None, description="Organization context")

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check with service availability"""
    return {
        "status": "healthy",
        "service": "unified-documentation-intelligence",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services_available": unified_orchestrator.services_available if unified_orchestrator else {}
    }

@app.post("/docs/unified-search", response_model=Dict[str, Any])
async def unified_documentation_search(request: UnifiedSearchRequestModel):
    """Unified documentation search across all intelligence sources"""
    try:
        if not unified_orchestrator:
            raise HTTPException(status_code=503, detail="Unified orchestrator not initialized")
        
        search_request = UnifiedSearchRequest(
            query=request.query,
            documentation_type=request.documentation_type,
            intelligence_level=request.intelligence_level,
            privacy_level=request.privacy_level,
            include_code=request.include_code,
            include_examples=request.include_examples,
            max_results_per_source=request.max_results_per_source,
            project_context=request.project_context,
            organization=request.organization
        )
        
        async with unified_orchestrator as orchestrator:
            response = await orchestrator.unified_search(search_request)
        
        return asdict(response)
        
    except Exception as e:
        logger.error(f"Unified documentation search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/docs/sources")
async def list_documentation_sources():
    """List all available documentation sources and their status"""
    try:
        if not unified_orchestrator:
            raise HTTPException(status_code=503, detail="Unified orchestrator not initialized")
        
        return {
            "services": unified_orchestrator.services_available,
            "documentation_types": [doc_type.value for doc_type in DocumentationType],
            "intelligence_levels": [level.value for level in IntelligenceLevel],
            "capabilities": {
                "context7": "Code snippets and library documentation",
                "ref_tools": "Complete internal/external documentation", 
                "claude_memory": "Semantic code search with AST parsing",
                "voyage_ai": "Enhanced embeddings and reranking"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("UNIFIED_DOCS_PORT", 8012))
    uvicorn.run(
        "unified_docs_service:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )