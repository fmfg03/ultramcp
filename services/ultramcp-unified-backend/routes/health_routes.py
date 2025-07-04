"""
Health check routes for unified backend
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any

from ..core.shared_dependencies import (
    check_shared_resources_health,
    get_db_dependency,
    get_redis_dependency, 
    get_qdrant_dependency
)

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "ultramcp-unified-backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with all components"""
    try:
        # Check shared resources
        resource_health = await check_shared_resources_health()
        
        # Overall status
        all_healthy = all(status == "healthy" for status in resource_health.values())
        overall_status = "healthy" if all_healthy else "degraded"
        
        return {
            "status": overall_status,
            "service": "ultramcp-unified-backend",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "components": resource_health,
            "features": {
                "fastapi_mcp_integration": True,
                "shared_resources": True,
                "unified_orchestration": True,
                "privacy_aware_routing": True
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "ultramcp-unified-backend", 
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/components")
async def component_health():
    """Health check for individual components"""
    return await check_shared_resources_health()

@router.get("/metrics")
async def health_metrics():
    """Basic metrics endpoint"""
    return {
        "service": "ultramcp-unified-backend",
        "version": "2.0.0",
        "uptime": "calculated_at_runtime",
        "requests_handled": "counter_placeholder",
        "memory_usage": "memory_placeholder",
        "active_connections": "connections_placeholder",
        "timestamp": datetime.utcnow().isoformat()
    }