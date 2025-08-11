# app/core/prompt_manager_enhanced.py
"""Enhanced prompt template management for generating multiple role options"""

from typing import List, Dict
from app.models.domain import ClusterData, Entitlement

class EnhancedPromptManager:
    """Manages enhanced prompt templates for multiple role generation"""
    
    @staticmethod
    def create_multi_role_generation_prompt(cluster_data: ClusterData) -> str:
        """Create a detailed prompt for generating 3 role options"""
        
        # Format entitlements
        entitlements_text = "\n".join([
            f"   - {e.id}: {e.name} - {e.description}"
            for e in cluster_data.core_entitlements
        ])
        
        # Format user information
        job_titles = ", ".join(cluster_data.user_summary.top_job_titles[:5]) if cluster_data.user_summary.top_job_titles else "Not specified"
        departments = ", ".join(cluster_data.user_summary.top_departments[:3]) if cluster_data.user_summary.top_departments else "Not specified"
        
        prompt = f"""
You are analyzing a cluster of users with similar access patterns to create RBAC roles.

CLUSTER INFORMATION:
- Cluster ID: {cluster_data.cluster_id}
- Total Users: {cluster_data.user_summary.total_users}
- Common Job Titles: {job_titles}
- Primary Departments: {departments}

ENTITLEMENTS IN THIS CLUSTER:
{entitlements_text}

Generate THREE different role options for this cluster, each with a different naming approach:

1. **Business-Focused Role**: Name emphasizes business function and responsibilities
   - Use business terminology
   - Focus on what the person does in the organization
   - Example style: "Financial Report Analyst", "Healthcare Claims Processor"

2. **Technical-Focused Role**: Name emphasizes systems and technical access
   - Use technical/system terminology
   - Focus on the systems and data being accessed
   - Example style: "ERP System Read User", "Medical Database Operator"

3. **Hierarchical-Focused Role**: Name emphasizes seniority and organizational level
   - Include level indicators (Senior, Lead, Junior, etc.)
   - Focus on organizational hierarchy and scope
   - Example style: "Senior Finance Specialist", "Lead Data Administrator"

For EACH of the three role options, provide:
- role_name: The role name following the specific style
- description: A 2-3 sentence description of the role's purpose and responsibilities
- rationale: A 2-3 sentence business and security justification
- style: The naming style used (business_focused, technical_focused, or hierarchical_focused)

Also provide:
- recommended_option: Which option (1, 2, or 3) you recommend as most appropriate
- risk_level: Overall risk assessment (LOW, MEDIUM, HIGH, or CRITICAL)
- recommendation_reason: Why you recommend that specific option

Respond in JSON format with this structure:
{{
  "role_options": [
    {{
      "option_number": 1,
      "role_name": "...",
      "style": "business_focused",
      "description": "...",
      "rationale": "..."
    }},
    {{
      "option_number": 2,
      "role_name": "...",
      "style": "technical_focused",
      "description": "...",
      "rationale": "..."
    }},
    {{
      "option_number": 3,
      "role_name": "...",
      "style": "hierarchical_focused",
      "description": "...",
      "rationale": "..."
    }}
  ],
  "recommended_option": 1,
  "recommendation_reason": "...",
  "risk_level": "..."
}}

Consider these factors:
- Follow the principle of least privilege
- Ensure each role name is clear and professional
- Make each option distinctly different while accurately representing the same access
- Consider regulatory compliance (HIPAA, SOX, GDPR, etc.)
- Think about how each naming style would resonate with different stakeholders
"""
        return prompt