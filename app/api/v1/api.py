# app/api/v1/api.py
"""API router aggregation"""

from fastapi import APIRouter
from app.api.v1.endpoints import roles, clusters, health

# Import the enhanced roles endpoint
try:
    from app.api.v1.endpoints import enhanced_roles
    has_enhanced = True
except ImportError:
    has_enhanced = False

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])

# Add enhanced roles if available
if has_enhanced:
    api_router.include_router(enhanced_roles.router, prefix="/roles", tags=["enhanced_roles"])