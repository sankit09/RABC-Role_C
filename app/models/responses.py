# app/models/responses.py
"""API response models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    azure_openai_connected: bool = False

class RoleResponse(BaseModel):
    """Single role response"""
    cluster_id: str
    role_name: str
    description: str
    rationale: str
    risk_level: str
    entitlement_count: int
    user_count: int
    generated_at: datetime
    reviewed: bool
    approved: bool

class BatchGenerateResponse(BaseModel):
    """Batch generation response"""
    total_clusters: int
    successful: int
    failed: int
    roles: List[RoleResponse]
    errors: Dict[str, str] = Field(default_factory=dict)
    processing_time: float

class FileUploadResponse(BaseModel):
    """File upload response"""
    filename: str
    file_type: str
    rows_processed: int
    status: str = "success"
    message: Optional[str] = None

class ClusterSummaryResponse(BaseModel):
    """Cluster summary response"""
    cluster_id: str
    entitlement_count: int
    user_count: int
    top_job_titles: List[str]
    top_departments: List[str]
    has_generated_role: bool = False

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)