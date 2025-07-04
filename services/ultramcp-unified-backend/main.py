#!/usr/bin/env python3
"""
UltraMCP Unified Backend with FastAPI MCP Integration
Consolidates core services with native MCP protocol support
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import consolidado de rutas
from .routes import (
    cod_routes,
    memory_routes,
    voyage_routes, 
    ref_routes,
    docs_routes,
    health_routes,
    actions_routes
)

# MCP Integration
from .mcp_integration import UltraMCPToolRegistry
from .core.shared_dependencies import get_database, get_redis, get_qdrant

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global shared resources
shared_resources = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with shared resource initialization"""
    global shared_resources
    
    try:
        logger.info("🚀 Initializing UltraMCP Unified Backend...")
        
        # Initialize shared resources
        shared_resources["database"] = await get_database()
        shared_resources["redis"] = await get_redis()
        shared_resources["qdrant"] = await get_qdrant()
        
        # Initialize MCP tool registry
        mcp_registry = UltraMCPToolRegistry(app)
        await mcp_registry.initialize()
        shared_resources["mcp_registry"] = mcp_registry
        
        logger.info("✅ UltraMCP Unified Backend initialized successfully")
        logger.info("🔗 MCP Tools registered and available")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize unified backend: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down UltraMCP Unified Backend...")
        
        # Cleanup shared resources
        for resource_name, resource in shared_resources.items():
            try:
                if hasattr(resource, 'close'):
                    await resource.close()
                logger.info(f"✅ Cleaned up {resource_name}")
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up {resource_name}: {e}")

# FastAPI application with lifespan
app = FastAPI(
    title="UltraMCP Unified Backend",
    description="Consolidated AI orchestration platform with native MCP protocol support",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include consolidated routes
app.include_router(health_routes.router, prefix="/health", tags=["Health"])
app.include_router(cod_routes.router, prefix="/cod", tags=["Chain of Debate"])
app.include_router(memory_routes.router, prefix="/memory", tags=["Code Memory"])
app.include_router(voyage_routes.router, prefix="/voyage", tags=["VoyageAI"])
app.include_router(ref_routes.router, prefix="/ref", tags=["Ref Tools"])
app.include_router(docs_routes.router, prefix="/docs", tags=["Unified Docs"])
app.include_router(actions_routes.router, prefix="/actions", tags=["External Actions"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "UltraMCP Unified Backend",
        "version": "2.0.0",
        "description": "Consolidated AI orchestration platform with native MCP protocol support",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "fastapi_mcp_integration",
            "chain_of_debate",
            "claude_code_memory", 
            "voyage_ai_embeddings",
            "ref_tools_documentation",
            "unified_documentation_intelligence",
            "external_actions_execution",
            "native_mcp_protocol",
            "shared_resource_optimization"
        ],
        "mcp_tools": "Available at /mcp/tools",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

# Global health endpoint
@app.get("/health", tags=["Health"])
async def global_health():
    """Global health check for unified backend"""
    return {
        "status": "healthy",
        "service": "ultramcp-unified-backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "components": {
            "database": "connected" if shared_resources.get("database") else "disconnected",
            "redis": "connected" if shared_resources.get("redis") else "disconnected", 
            "qdrant": "connected" if shared_resources.get("qdrant") else "disconnected",
            "mcp_registry": "active" if shared_resources.get("mcp_registry") else "inactive"
        },
        "routes": {
            "cod": "/cod/*",
            "memory": "/memory/*", 
            "voyage": "/voyage/*",
            "ref": "/ref/*",
            "docs": "/docs/*",
            "actions": "/actions/*"
        }
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "service": "ultramcp-unified-backend",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "service": "ultramcp-unified-backend", 
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("UNIFIED_BACKEND_PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )