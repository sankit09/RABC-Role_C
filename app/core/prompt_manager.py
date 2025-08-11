# app/core/prompt_manager.py
"""Prompt template management for role generation"""

from typing import List, Dict
from app.models.domain import ClusterData, Entitlement

class PromptManager:
    """Manages prompt templates for role generation"""
    
    @staticmethod
    def create_role_generation_prompt(cluster_data: ClusterData) -> str:
        """Create a detailed prompt for role generation"""
        
        # Format entitlements
        entitlements_text = "\n".join([
            f"   - {e.id}: {e.name} - {e.description}"
            for e in cluster_data.core_entitlements
        ])
        
        # Format user information
        job_titles = ", ".join(cluster_data.user_summary.top_job_titles[:5]) if cluster_data.user_summary.top_job_titles else "Not specified"
        departments = ", ".join(cluster_data.user_summary.top_departments[:3]) if cluster_data.user_summary.top_departments else "Not specified"
        
        prompt = f"""
You are analyzing a cluster of users with similar access patterns to create an RBAC role.

CLUSTER INFORMATION:
- Cluster ID: {cluster_data.cluster_id}
- Total Users: {cluster_data.user_summary.total_users}
- Common Job Titles: {job_titles}
- Primary Departments: {departments}

ENTITLEMENTS IN THIS CLUSTER:
{entitlements_text}

Based on this information, generate a role definition with the following:

1. **Role Name**: Create a concise, professional role name (3-5 words) that reflects the primary function and level of access.
   - Use standard naming conventions (e.g., "Senior Financial Analyst", "Healthcare Data Administrator")
   - Avoid generic names like "User Role" or "Access Group"

2. **Description**: Write a 2-3 sentence description that:
   - Explains the primary purpose of this role
   - Identifies the key responsibilities
   - Mentions the typical user profile

3. **Rationale**: Provide a 2-3 sentence business and security justification that:
   - Explains why this role grouping makes sense from a business perspective
   - Addresses the security principle of least privilege
   - Identifies any compliance or regulatory considerations

4. **Risk Level**: Assess the risk level (LOW, MEDIUM, HIGH, or CRITICAL) based on:
   - Sensitivity of data accessed
   - Potential for data modification
   - Scope of access across systems
   - Regulatory compliance implications

Respond in JSON format with keys: role_name, description, rationale, risk_level

Consider these factors:
- Follow the principle of least privilege
- Ensure the role is cohesive and logical
- Consider separation of duties where applicable
- Think about regulatory compliance (HIPAA, SOX, GDPR, etc.)
"""
        return prompt
    
    @staticmethod
    def create_review_prompt(role_data: Dict, feedback: str) -> str:
        """Create a prompt for role refinement based on feedback"""
        
        prompt = f"""
You previously generated this RBAC role:

Role Name: {role_data.get('role_name')}
Description: {role_data.get('description')}
Rationale: {role_data.get('rationale')}
Risk Level: {role_data.get('risk_level')}

The reviewer provided this feedback:
{feedback}

Please refine the role definition based on this feedback. Maintain the same JSON format with keys: role_name, description, rationale, risk_level
"""
        return prompt