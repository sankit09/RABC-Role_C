# app/api/v1/api.py
"""API router aggregation"""

from fastapi import APIRouter
from app.api.v1.endpoints import roles, clusters, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])