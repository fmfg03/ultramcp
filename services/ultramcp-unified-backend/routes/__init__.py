"""
Consolidated routes package for UltraMCP Unified Backend
"""

from . import (
    health_routes,
    cod_routes,
    memory_routes,
    voyage_routes,
    ref_routes,
    docs_routes,
    actions_routes
)

__all__ = [
    "health_routes",
    "cod_routes", 
    "memory_routes",
    "voyage_routes",
    "ref_routes",
    "docs_routes",
    "actions_routes"
]