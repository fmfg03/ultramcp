#!/usr/bin/env python3
"""
Blockoli MCP Service
Code Intelligence Service with semantic search and analysis
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import the blockoli client
from blockoli_client import BlockoliCodeContext
from code_intelligent_cod import CodeIntelligentCoDOrchestrator, CodeIntelligentTask, CodeIntelligenceMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Blockoli MCP Service",
    description="Code Intelligence Service with semantic search and analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class IndexProjectRequest(BaseModel):
    project_path: str
    project_name: str
    file_patterns: Optional[List[str]] = None

class CodeSearchRequest(BaseModel):
    query: str
    project_name: str
    limit: int = 10
    threshold: float = 0.7

class CodeDebateRequest(BaseModel):
    topic: str
    project_name: str
    intelligence_mode: str = "basic"
    code_query: Optional[str] = None
    context_depth: str = "medium"

class ArchitectureAnalysisRequest(BaseModel):
    focus: str
    project_name: str
    context_depth: str = "deep"

class PatternAnalysisRequest(BaseModel):
    pattern: str
    project_name: str
    patterns_focus: Optional[List[str]] = None

# Global state
blockoli_client = None
cod_orchestrator = None
active_tasks = {}
indexed_projects = {}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global blockoli_client, cod_orchestrator
    
    logger.info("🔍 Starting Blockoli MCP Service...")
    
    # Initialize Blockoli client
    blockoli_endpoint = os.getenv("BLOCKOLI_ENDPOINT", "http://sam.chat:8080")
    blockoli_client = BlockoliCodeContext(blockoli_endpoint)
    
    # Initialize CoD orchestrator
    cod_orchestrator = CodeIntelligentCoDOrchestrator(blockoli_endpoint=blockoli_endpoint)
    
    logger.info("✅ Blockoli MCP Service initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Blockoli connection
        if blockoli_client:
            async with blockoli_client as client:
                health = await client.health_check()
                blockoli_healthy = health.get('healthy', False)
        else:
            blockoli_healthy = False
        
        return {
            "status": "healthy" if blockoli_healthy else "degraded",
            "service": "blockoli-mcp",
            "blockoli_connection": "healthy" if blockoli_healthy else "disconnected",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "blockoli-mcp",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/status")
async def get_service_status():
    """Get detailed service status"""
    return {
        "service": "blockoli-mcp",
        "status": "running",
        "indexed_projects": len(indexed_projects),
        "active_tasks": len(active_tasks),
        "features": [
            "project_indexing",
            "semantic_search",
            "code_debates",
            "architecture_analysis",
            "pattern_analysis"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/projects/index")
async def index_project(request: IndexProjectRequest, background_tasks: BackgroundTasks):
    """Index a project for semantic search"""
    try:
        project_path = Path(request.project_path)
        if not project_path.exists():
            raise HTTPException(status_code=400, detail="Project path does not exist")
        
        task_id = f"index_{request.project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background indexing
        background_tasks.add_task(
            run_project_indexing,
            task_id,
            str(project_path),
            request.project_name,
            request.file_patterns
        )
        
        active_tasks[task_id] = {
            "type": "indexing",
            "status": "running",
            "project_name": request.project_name,
            "project_path": str(project_path),
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "task_id": task_id,
            "status": "started",
            "project_name": request.project_name,
            "message": "Project indexing initiated"
        }
        
    except Exception as e:
        logger.error(f"Project indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/search/code")
async def search_code(request: CodeSearchRequest):
    """Search code semantically"""
    try:
        if request.project_name not in indexed_projects:
            raise HTTPException(status_code=400, detail="Project not indexed")
        
        async with blockoli_client as client:
            context = await client.get_code_context(
                request.query,
                request.project_name,
                limit=request.limit
            )
        
        return {
            "query": request.query,
            "project": request.project_name,
            "results": context,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Code search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/debate/code")
async def code_intelligent_debate(request: CodeDebateRequest, background_tasks: BackgroundTasks):
    """Start code-intelligent debate"""
    try:
        if request.project_name not in indexed_projects:
            raise HTTPException(status_code=400, detail="Project not indexed")
        
        task_id = f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background debate
        background_tasks.add_task(
            run_code_debate,
            task_id,
            request.topic,
            request.project_name,
            request.intelligence_mode,
            request.code_query,
            request.context_depth
        )
        
        active_tasks[task_id] = {
            "type": "debate",
            "status": "running",
            "topic": request.topic,
            "project_name": request.project_name,
            "intelligence_mode": request.intelligence_mode,
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "task_id": task_id,
            "status": "started",
            "topic": request.topic,
            "message": "Code-intelligent debate initiated"
        }
        
    except Exception as e:
        logger.error(f"Code debate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analysis/architecture")
async def analyze_architecture(request: ArchitectureAnalysisRequest, background_tasks: BackgroundTasks):
    """Perform architecture analysis"""
    try:
        if request.project_name not in indexed_projects:
            raise HTTPException(status_code=400, detail="Project not indexed")
        
        task_id = f"arch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background analysis
        background_tasks.add_task(
            run_architecture_analysis,
            task_id,
            request.focus,
            request.project_name,
            request.context_depth
        )
        
        active_tasks[task_id] = {
            "type": "architecture_analysis",
            "status": "running",
            "focus": request.focus,
            "project_name": request.project_name,
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "task_id": task_id,
            "status": "started",
            "focus": request.focus,
            "message": "Architecture analysis initiated"
        }
        
    except Exception as e:
        logger.error(f"Architecture analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analysis/patterns")
async def analyze_patterns(request: PatternAnalysisRequest, background_tasks: BackgroundTasks):
    """Perform pattern analysis"""
    try:
        if request.project_name not in indexed_projects:
            raise HTTPException(status_code=400, detail="Project not indexed")
        
        task_id = f"pattern_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background analysis
        background_tasks.add_task(
            run_pattern_analysis,
            task_id,
            request.pattern,
            request.project_name,
            request.patterns_focus
        )
        
        active_tasks[task_id] = {
            "type": "pattern_analysis",
            "status": "running",
            "pattern": request.pattern,
            "project_name": request.project_name,
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "task_id": task_id,
            "status": "started",
            "pattern": request.pattern,
            "message": "Pattern analysis initiated"
        }
        
    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/list")
async def list_projects():
    """List all indexed projects"""
    return {
        "projects": indexed_projects,
        "total_projects": len(indexed_projects),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get status of a running task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return active_tasks[task_id]

@app.get("/api/v1/tasks/list")
async def list_tasks():
    """List all tasks"""
    return {
        "active_tasks": active_tasks,
        "total_active": len(active_tasks)
    }

# Background task functions
async def run_project_indexing(task_id: str, project_path: str, project_name: str, file_patterns: Optional[List[str]]):
    """Run project indexing in background"""
    try:
        logger.info(f"Starting project indexing {task_id}")
        
        async with blockoli_client as client:
            # Create project
            await client.create_project(project_name)
            
            # Index codebase
            result = await client.index_codebase(project_name, project_path, file_patterns)
            
            # Generate embeddings
            await client.generate_embeddings(project_name)
        
        # Store project info
        indexed_projects[project_name] = {
            "project_path": project_path,
            "indexed_files": result.get("indexed_files", 0),
            "last_indexed": datetime.now().isoformat(),
            "task_id": task_id
        }
        
        # Update task status
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "completed",
                "result": result,
                "completed_at": datetime.now().isoformat()
            })
        
        logger.info(f"Project indexing {task_id} completed")
        
    except Exception as e:
        logger.error(f"Project indexing {task_id} failed: {e}")
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })

async def run_code_debate(task_id: str, topic: str, project_name: str, intelligence_mode: str, code_query: Optional[str], context_depth: str):
    """Run code-intelligent debate in background"""
    try:
        logger.info(f"Starting code debate {task_id}")
        
        # Create debate task
        debate_task = CodeIntelligentTask(
            task_id=task_id,
            topic=topic,
            project_name=project_name,
            code_query=code_query,
            intelligence_mode=CodeIntelligenceMode(intelligence_mode),
            context_depth=context_depth
        )
        
        # Run debate
        result = await cod_orchestrator.run_code_intelligent_debate(debate_task)
        
        # Update task status
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "completed",
                "result": result,
                "completed_at": datetime.now().isoformat()
            })
        
        logger.info(f"Code debate {task_id} completed")
        
    except Exception as e:
        logger.error(f"Code debate {task_id} failed: {e}")
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })

async def run_architecture_analysis(task_id: str, focus: str, project_name: str, context_depth: str):
    """Run architecture analysis in background"""
    try:
        logger.info(f"Starting architecture analysis {task_id}")
        
        # Create architecture analysis task
        debate_task = CodeIntelligentTask(
            task_id=task_id,
            topic=f"Architecture analysis: {focus}",
            project_name=project_name,
            intelligence_mode=CodeIntelligenceMode.ARCHITECTURE_FOCUSED,
            context_depth=context_depth
        )
        
        # Run analysis
        result = await cod_orchestrator.run_code_intelligent_debate(debate_task)
        
        # Update task status
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "completed",
                "result": result,
                "completed_at": datetime.now().isoformat()
            })
        
        logger.info(f"Architecture analysis {task_id} completed")
        
    except Exception as e:
        logger.error(f"Architecture analysis {task_id} failed: {e}")
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })

async def run_pattern_analysis(task_id: str, pattern: str, project_name: str, patterns_focus: Optional[List[str]]):
    """Run pattern analysis in background"""
    try:
        logger.info(f"Starting pattern analysis {task_id}")
        
        # Create pattern analysis task
        debate_task = CodeIntelligentTask(
            task_id=task_id,
            topic=f"Pattern analysis: {pattern}",
            project_name=project_name,
            intelligence_mode=CodeIntelligenceMode.PATTERN_ANALYSIS,
            patterns_focus=patterns_focus
        )
        
        # Run analysis
        result = await cod_orchestrator.run_code_intelligent_debate(debate_task)
        
        # Update task status
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "completed",
                "result": result,
                "completed_at": datetime.now().isoformat()
            })
        
        logger.info(f"Pattern analysis {task_id} completed")
        
    except Exception as e:
        logger.error(f"Pattern analysis {task_id} failed: {e}")
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })

if __name__ == "__main__":
    port = int(os.getenv("BLOCKOLI_SERVICE_PORT", 8003))
    
    logger.info(f"🔍 Starting Blockoli MCP Service on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )