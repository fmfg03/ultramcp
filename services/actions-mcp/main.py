#!/usr/bin/env python3
"""
UltraMCP Actions Service - External Action Execution Platform
Handles escalation to humans, email notifications, workflow triggers, and external integrations
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

# Import routes
from .routes import (
    execute_routes,
    status_routes,
    config_routes,
    escalation_routes,
    notification_routes
)

# Core components
from .core.action_registry import ActionRegistry
from .core.execution_engine import ExecutionEngine
from .core.security_manager import SecurityManager
from .core.audit_logger import AuditLogger

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
    """Application lifespan manager with action service initialization"""
    global shared_resources
    
    try:
        logger.info("🚀 Initializing UltraMCP Actions Service...")
        
        # Initialize core components
        shared_resources["security_manager"] = SecurityManager()
        shared_resources["audit_logger"] = AuditLogger()
        shared_resources["action_registry"] = ActionRegistry()
        shared_resources["execution_engine"] = ExecutionEngine(
            security_manager=shared_resources["security_manager"],
            audit_logger=shared_resources["audit_logger"]
        )
        
        # Initialize action registry
        await shared_resources["action_registry"].initialize()
        
        # Initialize execution engine
        await shared_resources["execution_engine"].initialize()
        
        logger.info("✅ UltraMCP Actions Service initialized successfully")
        logger.info(f"🔧 {len(shared_resources['action_registry'].get_all_actions())} actions registered")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize actions service: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down UltraMCP Actions Service...")
        
        # Cleanup shared resources
        for resource_name, resource in shared_resources.items():
            try:
                if hasattr(resource, 'cleanup'):
                    await resource.cleanup()
                logger.info(f"✅ Cleaned up {resource_name}")
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up {resource_name}: {e}")

# FastAPI application with lifespan
app = FastAPI(
    title="UltraMCP Actions Service",
    description="External action execution platform for automation, escalation, and integration",
    version="1.0.0",
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

# Include routes
app.include_router(execute_routes.router, prefix="/execute", tags=["Action Execution"])
app.include_router(status_routes.router, prefix="/status", tags=["Action Status"])
app.include_router(config_routes.router, prefix="/config", tags=["Configuration"])
app.include_router(escalation_routes.router, prefix="/escalation", tags=["Human Escalation"])
app.include_router(notification_routes.router, prefix="/notifications", tags=["Notifications"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "UltraMCP Actions Service",
        "version": "1.0.0",
        "description": "External action execution platform for automation, escalation, and integration",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": [
            "human_escalation",
            "email_notifications",
            "slack_integration",
            "workflow_triggers",
            "ticket_creation",
            "external_system_integration",
            "audit_logging",
            "security_controls"
        ],
        "available_actions": len(shared_resources.get("action_registry", {}).get_all_actions() if shared_resources.get("action_registry") else []),
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

# Global health endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check for actions service"""
    try:
        registry_healthy = shared_resources.get("action_registry") is not None
        engine_healthy = shared_resources.get("execution_engine") is not None
        security_healthy = shared_resources.get("security_manager") is not None
        
        overall_status = "healthy" if all([registry_healthy, engine_healthy, security_healthy]) else "degraded"
        
        return {
            "status": overall_status,
            "service": "ultramcp-actions-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "components": {
                "action_registry": "healthy" if registry_healthy else "unhealthy",
                "execution_engine": "healthy" if engine_healthy else "unhealthy",
                "security_manager": "healthy" if security_healthy else "unhealthy",
                "audit_logger": "healthy" if shared_resources.get("audit_logger") else "unhealthy"
            },
            "metrics": {
                "registered_actions": len(shared_resources.get("action_registry", {}).get_all_actions() if shared_resources.get("action_registry") else []),
                "active_executions": 0,  # TODO: Implement active execution tracking
                "total_executions": 0    # TODO: Implement execution counter
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "ultramcp-actions-service",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler with audit logging"""
    # Log to audit system
    if shared_resources.get("audit_logger"):
        await shared_resources["audit_logger"].log_error(
            action="http_error",
            error=exc.detail,
            status_code=exc.status_code,
            path=str(request.url)
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "service": "ultramcp-actions-service",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler with audit logging"""
    logger.error(f"Unhandled exception: {exc}")
    
    # Log to audit system
    if shared_resources.get("audit_logger"):
        await shared_resources["audit_logger"].log_error(
            action="internal_error",
            error=str(exc),
            status_code=500,
            path=str(request.url)
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "service": "ultramcp-actions-service",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("ACTIONS_SERVICE_PORT", 8004))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )