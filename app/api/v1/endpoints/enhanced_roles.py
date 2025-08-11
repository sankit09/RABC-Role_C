# app/api/v1/endpoints/enhanced_roles.py
"""Enhanced role generation endpoints for multiple role options"""

from fastapi import APIRouter, HTTPException
import logging
from typing import List
from app.models.enhanced_models import (
    GenerateMultipleRolesRequest,
    MultipleRolesResponse,
    SelectRoleRequest,
    RoleOptionResponse
)
from app.services.enhanced_role_generator import EnhancedRoleGeneratorService
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
enhanced_role_service = EnhancedRoleGeneratorService()

@router.post("/generate-multiple", response_model=MultipleRolesResponse)
async def generate_multiple_role_options(request: GenerateMultipleRolesRequest):
    """Generate 3 role options for a single cluster"""
    try:
        role_set = await enhanced_role_service.generate_multiple_options(
            cluster_id=request.cluster_id,
            force_regenerate=request.force_regenerate
        )
        
        return MultipleRolesResponse(
            cluster_id=role_set.cluster_id,
            role_options=[
                RoleOptionResponse(
                    option_number=opt.option_number,
                    role_name=opt.role_name,
                    style=opt.style.value,
                    description=opt.description,
                    rationale=opt.rationale
                )
                for opt in role_set.role_options
            ],
            recommended_option=role_set.recommended_option,
            recommendation_reason=role_set.recommendation_reason,
            risk_level=role_set.risk_level,
            entitlement_count=len(role_set.entitlements),
            user_count=role_set.user_summary.get("total_users", 0),
            generated_at=role_set.generated_at
        )
    except Exception as e:
        logger.error(f"Multiple role generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/select")
async def select_role_option(request: SelectRoleRequest):
    """Select a specific role option for a cluster"""
    try:
        updated_role = enhanced_role_service.select_option(
            cluster_id=request.cluster_id,
            selected_option=request.selected_option,
            feedback=request.feedback
        )
        
        return {
            "success": True,
            "cluster_id": request.cluster_id,
            "selected_option": request.selected_option,
            "message": f"Successfully selected option {request.selected_option}"
        }
    except Exception as e:
        logger.error(f"Role selection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison/{cluster_id}")
async def get_role_comparison(cluster_id: str):
    """Get side-by-side comparison of all role options for a cluster"""
    try:
        role_set = enhanced_role_service.get_role_set(cluster_id)
        if not role_set:
            raise HTTPException(status_code=404, detail=f"No roles found for cluster {cluster_id}")
        
        comparison = {
            "cluster_id": cluster_id,
            "comparison_table": []
        }
        
        # Create comparison table
        for opt in role_set.role_options:
            comparison["comparison_table"].append({
                "option": opt.option_number,
                "role_name": opt.role_name,
                "style": opt.style.value,
                "word_count": len(opt.role_name.split()),
                "focuses_on": opt.style.value.replace("_focused", "").replace("_", " ").title(),
                "is_recommended": opt.option_number == role_set.recommended_option,
                "is_selected": opt.option_number == role_set.selected_option
            })
        
        comparison["recommendation_reason"] = role_set.recommendation_reason
        comparison["risk_level"] = role_set.risk_level
        
        return comparison
        
    except Exception as e:
        logger.error(f"Failed to get role comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add these endpoints to your existing API router in app/api/v1/api.py:
# api_router.include_router(enhanced_roles.router, prefix="/roles", tags=["enhanced_roles"])