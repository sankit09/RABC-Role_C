# app/api/v1/endpoints/roles.py
"""Role generation and management endpoints"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import logging
from app.models.requests import GenerateRoleRequest, BatchGenerateRequest, ReviewRoleRequest
from app.models.responses import RoleResponse, BatchGenerateResponse, ErrorResponse
from app.services.role_generator import RoleGeneratorService
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
role_service = RoleGeneratorService()

@router.post("/generate", response_model=RoleResponse)
async def generate_role(request: GenerateRoleRequest):
    """Generate a role for a single cluster"""
    try:
        role = await role_service.generate_single_role(
            cluster_id=request.cluster_id,
            force_regenerate=request.force_regenerate
        )
        
        return RoleResponse(
            cluster_id=role.cluster_id,
            role_name=role.role_name,
            description=role.description,
            rationale=role.rationale,
            risk_level=role.risk_level.value,
            entitlement_count=len(role.entitlements),
            user_count=role.user_summary.total_users,
            generated_at=role.generated_at,
            reviewed=role.reviewed,
            approved=role.approved
        )
    except Exception as e:
        logger.error(f"Role generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/batch", response_model=BatchGenerateResponse)
async def generate_batch_roles(request: BatchGenerateRequest):
    """Generate roles for multiple clusters"""
    try:
        start_time = datetime.now()
        
        generated_roles = await role_service.generate_batch_roles(
            cluster_ids=request.cluster_ids,
            process_all=request.process_all,
            concurrent_limit=request.concurrent_limit
        )
        
        # Prepare response
        roles_response = []
        for role in generated_roles.values():
            roles_response.append(RoleResponse(
                cluster_id=role.cluster_id,
                role_name=role.role_name,
                description=role.description,
                rationale=role.rationale,
                risk_level=role.risk_level.value,
                entitlement_count=len(role.entitlements),
                user_count=role.user_summary.total_users,
                generated_at=role.generated_at,
                reviewed=role.reviewed,
                approved=role.approved
            ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        total_requested = len(request.cluster_ids) if request.cluster_ids else len(role_service.data_processor.get_all_cluster_ids())
        
        return BatchGenerateResponse(
            total_clusters=total_requested,
            successful=len(generated_roles),
            failed=total_requested - len(generated_roles),
            roles=roles_response,
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Batch generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/review/{cluster_id}", response_model=RoleResponse)
async def review_role(cluster_id: str, request: ReviewRoleRequest):
    """Review and approve/reject a generated role"""
    try:
        role = role_service.review_role(
            cluster_id=cluster_id,
            approved=request.approved,
            feedback=request.feedback
        )
        
        return RoleResponse(
            cluster_id=role.cluster_id,
            role_name=role.role_name,
            description=role.description,
            rationale=role.rationale,
            risk_level=role.risk_level.value,
            entitlement_count=len(role.entitlements),
            user_count=role.user_summary.total_users,
            generated_at=role.generated_at,
            reviewed=role.reviewed,
            approved=role.approved
        )
    except Exception as e:
        logger.error(f"Role review failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_roles(format: str = "json"):
    """Export all generated roles"""
    try:
        if format not in ['json', 'csv']:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        output_path = role_service.export_roles(output_format=format)
        return {"message": "Roles exported successfully", "file_path": output_path}
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
