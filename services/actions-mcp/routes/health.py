"""
Health check routes for actions-mcp service
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any
import psutil
import asyncio

from ..core.action_registry import ActionRegistry
from ..core.execution_engine import ExecutionEngine
from ..core.security_manager import SecurityManager
from ..core.audit_logger import AuditLogger

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "actions-mcp"
    }


@router.get("/detailed")
async def detailed_health_check(
    action_registry: ActionRegistry = Depends(),
    execution_engine: ExecutionEngine = Depends(),
    security_manager: SecurityManager = Depends(),
    audit_logger: AuditLogger = Depends()
):
    """Detailed health check with component status"""
    
    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Check component health
    registry_health = await check_registry_health(action_registry)
    engine_health = await check_engine_health(execution_engine)
    security_health = await check_security_health(security_manager)
    audit_health = await check_audit_health(audit_logger)
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "actions-mcp",
        "components": {
            "action_registry": registry_health,
            "execution_engine": engine_health,
            "security_manager": security_health,
            "audit_logger": audit_health
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": memory.available,
            "uptime": datetime.utcnow().isoformat()
        }
    }


async def check_registry_health(registry: ActionRegistry) -> Dict[str, Any]:
    """Check action registry health"""
    try:
        actions = registry.list_actions()
        return {
            "status": "healthy",
            "total_actions": len(actions),
            "active_actions": len([a for a in actions if a.get("enabled", True)])
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_engine_health(engine: ExecutionEngine) -> Dict[str, Any]:
    """Check execution engine health"""
    try:
        stats = engine.get_stats()
        return {
            "status": "healthy",
            "active_executions": stats.get("active_executions", 0),
            "total_executions": stats.get("total_executions", 0),
            "success_rate": stats.get("success_rate", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_security_health(security: SecurityManager) -> Dict[str, Any]:
    """Check security manager health"""
    try:
        return {
            "status": "healthy",
            "active_sessions": len(security.active_sessions),
            "security_policies": len(security.policies)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_audit_health(audit: AuditLogger) -> Dict[str, Any]:
    """Check audit logger health"""
    try:
        recent_events = await audit.get_recent_events(limit=1)
        return {
            "status": "healthy",
            "recent_events": len(recent_events),
            "logging_active": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }