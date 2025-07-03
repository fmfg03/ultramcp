#!/usr/bin/env python3
"""
Enhanced UltraMCP Claude Code Memory Service with VoyageAI Integration
Hybrid semantic search with privacy-first fallback
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from contextlib import asynccontextmanager

# Internal imports
from core.enhanced_semantic_search import (
    EnhancedSemanticSearchEngine, 
    EnhancedSearchRequest, 
    EnhancedSearchResult,
    SearchMode, 
    PrivacyLevel, 
    DomainType
)
from core.memory_orchestrator import UnifiedMemoryOrchestrator
from core.code_parser import TreeSitterCodeParser
from core.pattern_analyzer import CodePatternAnalyzer

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
enhanced_search_engine: Optional[EnhancedSemanticSearchEngine] = None
memory_orchestrator: Optional[UnifiedMemoryOrchestrator] = None

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    score_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    privacy_level: PrivacyLevel = Field(PrivacyLevel.PUBLIC, description="Privacy level for processing")
    domain: Optional[DomainType] = Field(None, description="Domain specialization")
    search_mode: SearchMode = Field(SearchMode.AUTO, description="Search processing mode")
    enable_reranking: bool = Field(True, description="Enable result reranking")
    project_name: Optional[str] = Field(None, description="Project context")

class ProjectIndexRequest(BaseModel):
    project_path: str = Field(..., description="Path to project directory")
    project_name: str = Field(..., description="Unique project name")
    include_patterns: List[str] = Field(["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h"], description="File patterns to include")
    exclude_patterns: List[str] = Field(["node_modules", ".git", "__pycache__", "*.pyc"], description="Patterns to exclude")
    domain: Optional[DomainType] = Field(None, description="Project domain for specialized processing")
    privacy_level: PrivacyLevel = Field(PrivacyLevel.INTERNAL, description="Privacy level for project content")

class MemoryAnalysisRequest(BaseModel):
    file_path: str = Field(..., description="Path to file for analysis")
    project_name: str = Field(..., description="Project context")
    analysis_type: str = Field("comprehensive", description="Type of analysis: quick, comprehensive, security")
    include_patterns: bool = Field(True, description="Include pattern analysis")
    include_quality: bool = Field(True, description="Include quality assessment")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global enhanced_search_engine, memory_orchestrator
    
    try:
        logger.info("🧠 Initializing Enhanced Claude Code Memory Service...")
        
        # Initialize enhanced search engine
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        voyage_url = os.getenv("VOYAGE_SERVICE_URL", "http://localhost:8010")
        
        enhanced_search_engine = EnhancedSemanticSearchEngine(
            qdrant_url=qdrant_url,
            collection_name="enhanced_code_memory",
            voyage_service_url=voyage_url
        )
        await enhanced_search_engine.initialize()
        
        # Initialize memory orchestrator
        memory_orchestrator = UnifiedMemoryOrchestrator()
        await memory_orchestrator.initialize()
        
        logger.info("✅ Enhanced Claude Code Memory Service initialized successfully")
        
        # Start background tasks
        asyncio.create_task(background_health_check())
        asyncio.create_task(periodic_optimization())
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced service: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Enhanced Claude Code Memory Service...")
        
        if memory_orchestrator:
            await memory_orchestrator.cleanup()

# FastAPI app with lifespan
app = FastAPI(
    title="UltraMCP Enhanced Claude Code Memory Service",
    description="Hybrid semantic search with VoyageAI integration and privacy-first fallback",
    version="2.0.0",
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check with service dependencies"""
    try:
        status = {
            "status": "healthy",
            "service": "enhanced-claude-code-memory",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
        
        if enhanced_search_engine:
            # Check Qdrant connection
            status["qdrant_connected"] = enhanced_search_engine.is_connected
            status["voyage_available"] = enhanced_search_engine.voyage_available
            
            # Get service stats
            stats = await enhanced_search_engine.get_enhanced_stats()
            status["search_stats"] = stats["search_stats"]
            status["service_health"] = stats["service_health"]
        
        return status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Enhanced search endpoints
@app.post("/memory/search/enhanced", response_model=Dict[str, Any])
async def enhanced_search(request: SearchRequest):
    """Enhanced semantic search with VoyageAI integration"""
    try:
        if not enhanced_search_engine:
            raise HTTPException(status_code=503, detail="Search engine not initialized")
        
        # Create enhanced search request
        search_request = EnhancedSearchRequest(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filters=request.filters,
            privacy_level=request.privacy_level,
            domain=request.domain,
            search_mode=request.search_mode,
            enable_reranking=request.enable_reranking,
            context={"project_name": request.project_name} if request.project_name else None
        )
        
        # Perform enhanced search
        results = await enhanced_search_engine.enhanced_search(search_request)
        
        # Format response
        return {
            "results": [asdict(result) for result in results],
            "query": request.query,
            "total_results": len(results),
            "search_mode": request.search_mode.value,
            "privacy_level": request.privacy_level.value,
            "domain": request.domain.value if request.domain else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Enhanced search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search/code", response_model=Dict[str, Any])
async def code_search(
    query: str = Field(..., description="Code search query"),
    project_name: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = Field(10, ge=1, le=50),
    privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL
):
    """Code-optimized search with VoyageAI code embeddings"""
    try:
        if not enhanced_search_engine:
            raise HTTPException(status_code=503, detail="Search engine not initialized")
        
        # Build filters
        filters = {}
        if project_name:
            filters["project_name"] = project_name
        if language:
            filters["language"] = language
        
        # Perform code search
        results = await enhanced_search_engine.code_search(
            query=query,
            limit=limit,
            filters=filters,
            privacy_level=privacy_level
        )
        
        return {
            "results": [asdict(result) for result in results],
            "query": query,
            "total_results": len(results),
            "search_type": "code_optimized",
            "model_used": results[0].model_used if results else "none",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Code search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search/privacy-first", response_model=Dict[str, Any])
async def privacy_first_search(
    query: str = Field(..., description="Search query"),
    project_name: Optional[str] = None,
    limit: int = Field(10, ge=1, le=50)
):
    """Privacy-first search using only local models"""
    try:
        if not enhanced_search_engine:
            raise HTTPException(status_code=503, detail="Search engine not initialized")
        
        filters = {}
        if project_name:
            filters["project_name"] = project_name
        
        # Perform privacy-first search
        results = await enhanced_search_engine.privacy_first_search(
            query=query,
            limit=limit,
            filters=filters
        )
        
        return {
            "results": [asdict(result) for result in results],
            "query": query,
            "total_results": len(results),
            "search_type": "privacy_first",
            "privacy_compliant": True,
            "local_processing": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Privacy-first search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search/domain", response_model=Dict[str, Any])
async def domain_search(
    query: str = Field(..., description="Search query"),
    domain: DomainType = Field(..., description="Domain specialization"),
    project_name: Optional[str] = None,
    limit: int = Field(10, ge=1, le=50),
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
):
    """Domain-specialized search (finance, healthcare, legal, etc.)"""
    try:
        if not enhanced_search_engine:
            raise HTTPException(status_code=503, detail="Search engine not initialized")
        
        filters = {}
        if project_name:
            filters["project_name"] = project_name
        
        # Perform domain search
        results = await enhanced_search_engine.domain_search(
            query=query,
            domain=domain,
            limit=limit,
            filters=filters,
            privacy_level=privacy_level
        )
        
        return {
            "results": [asdict(result) for result in results],
            "query": query,
            "domain": domain.value,
            "total_results": len(results),
            "search_type": f"domain_{domain.value}",
            "model_used": results[0].model_used if results else "none",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Domain search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Project management endpoints
@app.post("/memory/projects/index", response_model=Dict[str, Any])
async def index_project(request: ProjectIndexRequest, background_tasks: BackgroundTasks):
    """Index a project with enhanced semantic processing"""
    try:
        if not memory_orchestrator:
            raise HTTPException(status_code=503, detail="Memory orchestrator not initialized")
        
        # Validate project path
        project_path = Path(request.project_path)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project path not found: {request.project_path}")
        
        # Start background indexing
        background_tasks.add_task(
            enhanced_project_indexing,
            request.project_path,
            request.project_name,
            request.include_patterns,
            request.exclude_patterns,
            request.domain,
            request.privacy_level
        )
        
        return {
            "status": "indexing_started",
            "project_name": request.project_name,
            "project_path": request.project_path,
            "domain": request.domain.value if request.domain else None,
            "privacy_level": request.privacy_level.value,
            "estimated_time": "2-10 minutes depending on project size",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Project indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/projects", response_model=Dict[str, Any])
async def list_projects():
    """List all indexed projects"""
    try:
        if not memory_orchestrator:
            raise HTTPException(status_code=503, detail="Memory orchestrator not initialized")
        
        projects = await memory_orchestrator.list_projects()
        
        return {
            "projects": projects,
            "total_projects": len(projects),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/analyze", response_model=Dict[str, Any])
async def analyze_code(request: MemoryAnalysisRequest):
    """Analyze code with enhanced pattern detection"""
    try:
        if not memory_orchestrator:
            raise HTTPException(status_code=503, detail="Memory orchestrator not initialized")
        
        # Perform enhanced analysis
        analysis_result = await memory_orchestrator.analyze_file(
            file_path=request.file_path,
            project_name=request.project_name,
            analysis_type=request.analysis_type,
            include_patterns=request.include_patterns,
            include_quality=request.include_quality
        )
        
        return {
            "analysis": analysis_result,
            "file_path": request.file_path,
            "project_name": request.project_name,
            "analysis_type": request.analysis_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics and monitoring endpoints
@app.get("/memory/stats/enhanced", response_model=Dict[str, Any])
async def get_enhanced_stats():
    """Get comprehensive service statistics"""
    try:
        stats = {}
        
        if enhanced_search_engine:
            enhanced_stats = await enhanced_search_engine.get_enhanced_stats()
            stats.update(enhanced_stats)
        
        if memory_orchestrator:
            memory_stats = await memory_orchestrator.get_stats()
            stats["memory_stats"] = memory_stats
        
        stats["service_info"] = {
            "name": "enhanced-claude-code-memory",
            "version": "2.0.0",
            "features": [
                "voyage_ai_integration",
                "hybrid_search",
                "privacy_first_fallback",
                "domain_specialization",
                "intelligent_reranking"
            ]
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get enhanced stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/models", response_model=Dict[str, Any])
async def list_available_models():
    """List available embedding and reranking models"""
    return {
        "embedding_models": {
            "voyage_models": [
                "voyage-code-2",
                "voyage-large-2", 
                "voyage-finance-2",
                "voyage-healthcare-2",
                "voyage-law-2"
            ],
            "local_models": [
                "sentence-transformer",
                "codebert-base"
            ]
        },
        "reranking_models": {
            "voyage_models": [
                "rerank-lite-1",
                "rerank-2"
            ],
            "local_models": [
                "similarity-rerank"
            ]
        },
        "privacy_levels": [level.value for level in PrivacyLevel],
        "domains": [domain.value for domain in DomainType],
        "search_modes": [mode.value for mode in SearchMode]
    }

# Background tasks
async def enhanced_project_indexing(
    project_path: str,
    project_name: str,
    include_patterns: List[str],
    exclude_patterns: List[str],
    domain: Optional[DomainType],
    privacy_level: PrivacyLevel
):
    """Enhanced background project indexing"""
    try:
        logger.info(f"Starting enhanced indexing for project: {project_name}")
        
        if memory_orchestrator:
            await memory_orchestrator.index_project(
                project_path=project_path,
                project_name=project_name,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                enhanced_mode=True,
                domain=domain.value if domain else None,
                privacy_level=privacy_level.value
            )
        
        logger.info(f"Completed enhanced indexing for project: {project_name}")
        
    except Exception as e:
        logger.error(f"Enhanced indexing failed for {project_name}: {e}")

async def background_health_check():
    """Background health monitoring"""
    while True:
        try:
            if enhanced_search_engine:
                # Check VoyageAI service availability
                async with enhanced_search_engine.voyage_client as client:
                    voyage_health = await client.health_check()
                    enhanced_search_engine.voyage_available = voyage_health
            
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.warning(f"Health check error: {e}")
            await asyncio.sleep(60)

async def periodic_optimization():
    """Periodic optimization and cleanup"""
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            
            if enhanced_search_engine:
                # Clear old cache entries
                current_time = datetime.utcnow().timestamp()
                cache = enhanced_search_engine.voyage_client.cache if hasattr(enhanced_search_engine.voyage_client, 'cache') else None
                
                if cache:
                    # Simple cache cleanup
                    expired_keys = [
                        key for key, (_, timestamp) in cache.cache.items()
                        if current_time - timestamp > cache.ttl_seconds
                    ]
                    
                    for key in expired_keys:
                        cache.cache.pop(key, None)
                    
                    logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
            
        except Exception as e:
            logger.warning(f"Optimization task error: {e}")

if __name__ == "__main__":
    port = int(os.getenv("MEMORY_SERVICE_PORT", 8009))
    uvicorn.run(
        "enhanced_memory_service:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )