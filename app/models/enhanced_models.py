# app/models/enhanced_models.py
"""Enhanced models for multiple role options"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class RoleStyle(str, Enum):
    """Role naming style"""
    BUSINESS_FOCUSED = "business_focused"
    TECHNICAL_FOCUSED = "technical_focused"
    HIERARCHICAL_FOCUSED = "hierarchical_focused"

@dataclass
class RoleOption:
    """Single role option"""
    option_number: int
    role_name: str
    style: RoleStyle
    description: str
    rationale: str
    
    def to_dict(self) -> Dict:
        return {
            "option_number": self.option_number,
            "role_name": self.role_name,
            "style": self.style.value,
            "description": self.description,
            "rationale": self.rationale
        }

@dataclass
class GeneratedRoleSet:
    """Set of generated role options for a cluster"""
    cluster_id: str
    role_options: List[RoleOption]
    recommended_option: int
    recommendation_reason: str
    risk_level: str
    entitlements: List
    user_summary: Dict
    generated_at: datetime = field(default_factory=datetime.now)
    selected_option: Optional[int] = None
    reviewed: bool = False
    approved: bool = False
    feedback: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "cluster_id": self.cluster_id,
            "role_options": [opt.to_dict() for opt in self.role_options],
            "recommended_option": self.recommended_option,
            "recommendation_reason": self.recommendation_reason,
            "risk_level": self.risk_level,
            "entitlement_count": len(self.entitlements),
            "user_count": self.user_summary.get("total_users", 0),
            "generated_at": self.generated_at.isoformat(),
            "selected_option": self.selected_option,
            "reviewed": self.reviewed,
            "approved": self.approved,
            "feedback": self.feedback
        }

# API Request/Response Models
class GenerateMultipleRolesRequest(BaseModel):
    """Request to generate multiple role options"""
    cluster_id: str = Field(..., description="Cluster identifier")
    force_regenerate: bool = Field(False, description="Force regeneration if roles exist")

class RoleOptionResponse(BaseModel):
    """Single role option response"""
    option_number: int
    role_name: str
    style: str
    description: str
    rationale: str

class MultipleRolesResponse(BaseModel):
    """Multiple role options response"""
    cluster_id: str
    role_options: List[RoleOptionResponse]
    recommended_option: int
    recommendation_reason: str
    risk_level: str
    entitlement_count: int
    user_count: int
    generated_at: datetime

class SelectRoleRequest(BaseModel):
    """Request to select a specific role option"""
    cluster_id: str
    selected_option: int = Field(..., ge=1, le=3)
    feedback: Optional[str] = None