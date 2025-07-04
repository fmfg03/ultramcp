"""
Routes module for actions-mcp service
"""

from .actions import router as actions_router
from .health import router as health_router

__all__ = ["actions_router", "health_router"]