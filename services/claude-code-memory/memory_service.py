#!/usr/bin/env python3

"""
UltraMCP Claude Code Memory Service
Advanced semantic code memory with Tree-sitter AST parsing and Qdrant vector search
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
from core.memory_orchestrator import UnifiedMemoryOrchestrator
from core.code_parser import TreeSitterCodeParser
from core.semantic_search import SemanticCodeSearch
from core.pattern_analyzer import CodePatternAnalyzer
from utils.health_monitor import HealthMonitor
from utils.metrics_collector import MetricsCollector

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
memory_orchestrator: Optional[UnifiedMemoryOrchestrator] = None
health_monitor: Optional[HealthMonitor] = None
metrics_collector: Optional[MetricsCollector] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global memory_orchestrator, health_monitor, metrics_collector
    
    try:
        logger.info("🧠 Initializing Claude Code Memory Service...")
        
        # Initialize core components
        memory_orchestrator = UnifiedMemoryOrchestrator()
        await memory_orchestrator.initialize()
        
        health_monitor = HealthMonitor()
        await health_monitor.start()
        
        metrics_collector = MetricsCollector()
        await metrics_collector.start()
        
        logger.info("✅ Claude Code Memory Service initialized successfully")
        
        # Start background tasks
        asyncio.create_task(background_indexing_task())
        asyncio.create_task(memory_cleanup_task())
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize service: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Claude Code Memory Service...")
        
        if memory_orchestrator:
            await memory_orchestrator.cleanup()
        if health_monitor:
            await health_monitor.stop()
        if metrics_collector:
            await metrics_collector.stop()

# FastAPI app with lifespan
app = FastAPI(
    title="UltraMCP Claude Code Memory Service",
    description="Advanced semantic code memory with Tree-sitter AST parsing and Qdrant vector search",
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

# Data models
class CodeEntityType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    VARIABLE = "variable"
    INTERFACE = "interface"
    TYPE = "type"
    CONSTANT = "constant"
    IMPORT = "import"

class SearchMode(str, Enum):
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    HYBRID = "hybrid"
    PATTERN = "pattern"

class IndexingMode(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    FAST = "fast"
    DEEP = "deep"

@dataclass
class CodeEntity:
    """Represents a parsed code entity"""
    id: str
    type: CodeEntityType
    name: str
    signature: str
    docstring: Optional[str]
    file_path: str
    start_line: int
    end_line: int
    language: str
    complexity: float
    dependencies: List[str]
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    """Search result with similarity and context"""
    entity: CodeEntity
    similarity_score: float
    context: str
    explanation: str
    related_entities: List[str]

# Request/Response models
class IndexProjectRequest(BaseModel):
    project_path: str = Field(..., description="Path to project directory")
    project_name: str = Field(..., description="Unique project identifier")
    include_patterns: List[str] = Field(default=["**/*.py", "**/*.js", "**/*.ts"], description="File patterns to include")
    exclude_patterns: List[str] = Field(default=["**/node_modules/**", "**/.git/**", "**/__pycache__/**"], description="File patterns to exclude")
    indexing_mode: IndexingMode = Field(default=IndexingMode.FULL, description="Indexing strategy")
    force_reindex: bool = Field(default=False, description="Force complete reindexing")

class SearchCodeRequest(BaseModel):
    query: str = Field(..., description="Search query")
    project_name: Optional[str] = Field(None, description="Specific project to search in")
    entity_types: List[CodeEntityType] = Field(default=[], description="Filter by entity types")
    languages: List[str] = Field(default=[], description="Filter by programming languages")
    search_mode: SearchMode = Field(default=SearchMode.HYBRID, description="Search strategy")
    max_results: int = Field(default=10, description="Maximum number of results")
    min_similarity: float = Field(default=0.5, description="Minimum similarity threshold")

class SimilarCodeRequest(BaseModel):
    code_snippet: str = Field(..., description="Code snippet to find similar implementations")
    language: Optional[str] = Field(None, description="Programming language of the snippet")
    entity_type: Optional[CodeEntityType] = Field(None, description="Type of code entity")
    project_name: Optional[str] = Field(None, description="Project to search in")
    max_results: int = Field(default=5, description="Maximum number of results")

class CodePatternRequest(BaseModel):
    pattern_type: str = Field(..., description="Type of pattern to analyze")
    project_name: str = Field(..., description="Project to analyze")
    scope: str = Field(default="all", description="Analysis scope (file, module, project)")

class MemoryEnhancedChatRequest(BaseModel):
    prompt: str = Field(..., description="Chat prompt")
    project_context: Optional[str] = Field(None, description="Project context for code awareness")
    include_patterns: bool = Field(default=True, description="Include similar code patterns")
    include_documentation: bool = Field(default=True, description="Include relevant documentation")
    max_context_items: int = Field(default=5, description="Maximum context items to include")

# Dependency injection
async def get_memory_orchestrator() -> UnifiedMemoryOrchestrator:
    """Get memory orchestrator instance"""
    if memory_orchestrator is None:
        raise HTTPException(status_code=503, detail="Memory orchestrator not initialized")
    return memory_orchestrator

async def get_health_monitor() -> HealthMonitor:
    """Get health monitor instance"""
    if health_monitor is None:
        raise HTTPException(status_code=503, detail="Health monitor not available")
    return health_monitor

async def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector instance"""
    if metrics_collector is None:
        raise HTTPException(status_code=503, detail="Metrics collector not available")
    return metrics_collector

# API Routes

@app.get("/health")
async def health_check(monitor: HealthMonitor = Depends(get_health_monitor)):
    """Service health check"""
    try:
        health_data = await monitor.get_health_status()
        return {
            "status": "healthy" if health_data["overall_health"] else "unhealthy",
            "service": "claude-code-memory",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": health_data,
            "uptime": health_data.get("uptime", 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/api/projects/index")
async def index_project(
    request: IndexProjectRequest,
    background_tasks: BackgroundTasks,
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """Index a project for semantic code search"""
    try:
        logger.info(f"🔍 Starting indexing for project: {request.project_name}")
        
        # Validate project path
        project_path = Path(request.project_path)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project path not found: {request.project_path}")
        
        # Start indexing task
        task_id = await orchestrator.start_indexing_task(
            project_path=request.project_path,
            project_name=request.project_name,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns,
            indexing_mode=request.indexing_mode,
            force_reindex=request.force_reindex
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "project_name": request.project_name,
            "status": "indexing_started",
            "message": f"Started indexing project {request.project_name}",
            "estimated_time": "5-30 minutes depending on project size"
        }
        
    except Exception as e:
        logger.error(f"Error starting project indexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_name}/status")
async def get_project_status(
    project_name: str,
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """Get indexing status for a project"""
    try:
        status = await orchestrator.get_project_status(project_name)
        return {
            "success": True,
            "project_name": project_name,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/code")
async def search_code(
    request: SearchCodeRequest,
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """Search for code using semantic or structural search"""
    try:
        logger.info(f"🔍 Searching code: {request.query[:50]}...")
        
        results = await orchestrator.search_code(
            query=request.query,
            project_name=request.project_name,
            entity_types=request.entity_types,
            languages=request.languages,
            search_mode=request.search_mode,
            max_results=request.max_results,
            min_similarity=request.min_similarity
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": [asdict(result) for result in results],
            "total_results": len(results),
            "search_mode": request.search_mode.value,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/similar")
async def find_similar_code(
    request: SimilarCodeRequest,
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """Find similar code implementations"""
    try:
        logger.info(f"🔍 Finding similar code for {len(request.code_snippet)} characters...")
        
        results = await orchestrator.find_similar_code(
            code_snippet=request.code_snippet,
            language=request.language,
            entity_type=request.entity_type,
            project_name=request.project_name,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "code_snippet_length": len(request.code_snippet),
            "language": request.language,
            "results": [asdict(result) for result in results],
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error finding similar code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/patterns/analyze")
async def analyze_patterns(
    request: CodePatternRequest,
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """Analyze code patterns in a project"""
    try:
        logger.info(f"📊 Analyzing {request.pattern_type} patterns in {request.project_name}")
        
        patterns = await orchestrator.analyze_code_patterns(
            pattern_type=request.pattern_type,
            project_name=request.project_name,
            scope=request.scope
        )
        
        return {
            "success": True,
            "project_name": request.project_name,
            "pattern_type": request.pattern_type,
            "scope": request.scope,
            "patterns": patterns,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/memory-enhanced")
async def memory_enhanced_chat(
    request: MemoryEnhancedChatRequest,
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """Chat with memory-enhanced context"""
    try:
        logger.info(f"💬 Memory-enhanced chat: {request.prompt[:50]}...")
        
        enhanced_response = await orchestrator.memory_enhanced_chat(
            prompt=request.prompt,
            project_context=request.project_context,
            include_patterns=request.include_patterns,
            include_documentation=request.include_documentation,
            max_context_items=request.max_context_items
        )
        
        return {
            "success": True,
            "original_prompt": request.prompt,
            "enhanced_response": enhanced_response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in memory-enhanced chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def list_projects(
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """List all indexed projects"""
    try:
        projects = await orchestrator.list_projects()
        return {
            "success": True,
            "projects": projects,
            "total_projects": len(projects),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_service_stats(
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator),
    metrics: MetricsCollector = Depends(get_metrics_collector)
):
    """Get service statistics"""
    try:
        memory_stats = await orchestrator.get_memory_stats()
        service_metrics = await metrics.get_metrics()
        
        return {
            "success": True,
            "memory_stats": memory_stats,
            "service_metrics": service_metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_name}")
async def delete_project(
    project_name: str,
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """Delete a project from memory"""
    try:
        await orchestrator.delete_project(project_name)
        return {
            "success": True,
            "project_name": project_name,
            "message": f"Project {project_name} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_name}/refresh")
async def refresh_project(
    project_name: str,
    background_tasks: BackgroundTasks,
    orchestrator: UnifiedMemoryOrchestrator = Depends(get_memory_orchestrator)
):
    """Refresh/update project index"""
    try:
        task_id = await orchestrator.refresh_project(project_name)
        return {
            "success": True,
            "project_name": project_name,
            "task_id": task_id,
            "message": f"Started refresh for project {project_name}"
        }
    except Exception as e:
        logger.error(f"Error refreshing project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def background_indexing_task():
    """Background task for continuous indexing"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            if memory_orchestrator:
                await memory_orchestrator.background_maintenance()
        except Exception as e:
            logger.error(f"Background indexing error: {e}")

async def memory_cleanup_task():
    """Background task for memory cleanup"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            if memory_orchestrator:
                await memory_orchestrator.cleanup_stale_data()
        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")

# Main entry point
if __name__ == "__main__":
    config = {
        "host": os.getenv("MEMORY_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("MEMORY_SERVICE_PORT", 8009)),
        "log_level": os.getenv("LOG_LEVEL", "info"),
        "reload": os.getenv("NODE_ENV") == "development",
    }
    
    logger.info(f"🚀 Starting Claude Code Memory Service on {config['host']}:{config['port']}")
    uvicorn.run("memory_service:app", **config)