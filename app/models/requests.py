# app/models/requests.py
"""API request models"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from fastapi import UploadFile

class GenerateRoleRequest(BaseModel):
    """Request to generate a role for a cluster"""
    cluster_id: str = Field(..., description="Cluster identifier")
    force_regenerate: bool = Field(False, description="Force regeneration if role exists")
    
class BatchGenerateRequest(BaseModel):
    """Request to generate roles for multiple clusters"""
    cluster_ids: Optional[List[str]] = Field(None, description="Specific cluster IDs to process")
    process_all: bool = Field(False, description="Process all available clusters")
    concurrent_limit: int = Field(5, ge=1, le=20, description="Number of concurrent LLM calls")

class ReviewRoleRequest(BaseModel):
    """Request to review/approve a generated role"""
    cluster_id: str
    approved: bool
    feedback: Optional[str] = None
    modified_name: Optional[str] = None
    modified_description: Optional[str] = None
    modified_rationale: Optional[str] = None

class FileUploadRequest(BaseModel):
    """File upload metadata"""
    file_type: str = Field(..., description="Type: cluster_summary, user_metadata, or entitlement_metadata")
    
    @validator('file_type')
    def validate_file_type(cls, v):
        allowed_types = ['cluster_summary', 'user_metadata', 'entitlement_metadata']
        if v not in allowed_types:
            raise ValueError(f"file_type must be one of {allowed_types}")
        return v
