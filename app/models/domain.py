# app/models/domain.py
"""Domain models for RBAC Role Mining"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class Entitlement:
    """Single entitlement with metadata"""
    id: str
    name: str
    description: str
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

@dataclass
class UserSummary:
    """Summary statistics for users in a cluster"""
    total_users: int
    top_job_titles: List[str] = field(default_factory=list)
    top_departments: List[str] = field(default_factory=list)
    job_title_distribution: Dict[str, int] = field(default_factory=dict)
    department_distribution: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "total_users": self.total_users,
            "top_job_titles": self.top_job_titles[:5],  # Top 5
            "top_departments": self.top_departments[:3],  # Top 3
            "job_title_distribution": self.job_title_distribution,
            "department_distribution": self.department_distribution
        }

@dataclass
class ClusterData:
    """Complete data for a single cluster"""
    cluster_id: str
    core_entitlements: List[Entitlement]
    user_summary: UserSummary
    entitlement_count: int = 0
    
    def __post_init__(self):
        self.entitlement_count = len(self.core_entitlements)
    
    def to_dict(self) -> Dict:
        return {
            "cluster_id": self.cluster_id,
            "entitlement_count": self.entitlement_count,
            "core_entitlements": [e.to_dict() for e in self.core_entitlements],
            "user_summary": self.user_summary.to_dict()
        }

@dataclass
class GeneratedRole:
    """Generated role definition"""
    cluster_id: str
    role_name: str
    description: str
    rationale: str
    risk_level: RiskLevel
    entitlements: List[Entitlement]
    user_summary: UserSummary
    generated_at: datetime = field(default_factory=datetime.now)
    reviewed: bool = False
    approved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "cluster_id": self.cluster_id,
            "role_name": self.role_name,
            "description": self.description,
            "rationale": self.rationale,
            "risk_level": self.risk_level,
            "entitlements": [e.to_dict() for e in self.entitlements],
            "user_summary": self.user_summary.to_dict(),
            "generated_at": self.generated_at.isoformat(),
            "reviewed": self.reviewed,
            "approved": self.approved
        }