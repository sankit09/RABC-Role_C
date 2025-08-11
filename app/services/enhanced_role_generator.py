# app/services/enhanced_role_generator.py
"""Enhanced role generation service for multiple options - FIXED"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
from app.models.enhanced_models import GeneratedRoleSet, RoleOption, RoleStyle
from app.core.llm_client import AzureOpenAIClient
from app.core.prompt_manager_enhanced import EnhancedPromptManager
from app.services.data_processor import DataProcessor
from app.config import settings

logger = logging.getLogger(__name__)

class EnhancedRoleGeneratorService:
    """Service for generating multiple RBAC role options"""
    
    def __init__(self):
        self.llm_client = None  # Lazy initialization
        self.prompt_manager = EnhancedPromptManager()
        self.data_processor = DataProcessor()
        self.generated_role_sets: Dict[str, GeneratedRoleSet] = {}
    
    def _get_llm_client(self) -> AzureOpenAIClient:
        """Get or create LLM client (lazy initialization)"""
        if self.llm_client is None:
            self.llm_client = AzureOpenAIClient()
        return self.llm_client
    
    async def generate_multiple_options(
        self, 
        cluster_id: str, 
        force_regenerate: bool = False
    ) -> GeneratedRoleSet:
        """Generate 3 role options for a single cluster"""
        
        # Check if roles already exist
        if cluster_id in self.generated_role_sets and not force_regenerate:
            logger.info(f"Role options already exist for cluster {cluster_id}")
            return self.generated_role_sets[cluster_id]
        
        try:
            # Load and process cluster data
            if self.data_processor.cluster_summary is None or self.data_processor.cluster_summary.empty:
                self.data_processor.load_data_files()
            
            cluster_data = self.data_processor.process_cluster(cluster_id)
            
            # Generate prompt for multiple options
            prompt = self.prompt_manager.create_multi_role_generation_prompt(cluster_data)
            
            # Get LLM client and call LLM
            llm_client = self._get_llm_client()
            logger.info(f"Generating 3 role options for cluster {cluster_id}")
            llm_response = await llm_client.generate_role(prompt)
            
            # Parse response and create RoleOption objects
            role_options = []
            for opt_data in llm_response.get('role_options', []):
                style_str = opt_data.get('style', 'business_focused')
                # Map string to enum
                style_map = {
                    'business_focused': RoleStyle.BUSINESS_FOCUSED,
                    'technical_focused': RoleStyle.TECHNICAL_FOCUSED,
                    'hierarchical_focused': RoleStyle.HIERARCHICAL_FOCUSED
                }
                style = style_map.get(style_str, RoleStyle.BUSINESS_FOCUSED)
                
                role_option = RoleOption(
                    option_number=opt_data.get('option_number', 1),
                    role_name=opt_data.get('role_name', f'Role_{cluster_id}'),
                    style=style,
                    description=opt_data.get('description', ''),
                    rationale=opt_data.get('rationale', '')
                )
                role_options.append(role_option)
            
            # Create GeneratedRoleSet object with entitlements included
            generated_role_set = GeneratedRoleSet(
                cluster_id=cluster_id,
                role_options=role_options,
                recommended_option=llm_response.get('recommended_option', 1),
                recommendation_reason=llm_response.get('recommendation_reason', ''),
                risk_level=llm_response.get('risk_level', 'MEDIUM'),
                entitlements=cluster_data.core_entitlements,  # Include entitlements ONCE
                user_summary=cluster_data.user_summary.to_dict(),
                generated_at=datetime.now()
            )
            
            # Store the generated role set
            self.generated_role_sets[cluster_id] = generated_role_set
            
            logger.info(f"Successfully generated 3 role options for cluster {cluster_id}")
            return generated_role_set
            
        except Exception as e:
            logger.error(f"Failed to generate role options for cluster {cluster_id}: {str(e)}")
            raise
    
    def select_option(
        self, 
        cluster_id: str, 
        selected_option: int,
        feedback: Optional[str] = None
    ) -> GeneratedRoleSet:
        """Select a specific role option for a cluster"""
        if cluster_id not in self.generated_role_sets:
            raise ValueError(f"No generated roles found for cluster {cluster_id}")
        
        role_set = self.generated_role_sets[cluster_id]
        role_set.selected_option = selected_option
        if feedback:
            role_set.feedback = feedback
        
        logger.info(f"Selected option {selected_option} for cluster {cluster_id}")
        return role_set
    
    def get_role_set(self, cluster_id: str) -> Optional[GeneratedRoleSet]:
        """Get generated role set for a cluster"""
        return self.generated_role_sets.get(cluster_id)
    
    def review_role_set(
        self, 
        cluster_id: str, 
        approved: bool, 
        feedback: Optional[str] = None
    ) -> GeneratedRoleSet:
        """Review and approve/reject a role set"""
        if cluster_id not in self.generated_role_sets:
            raise ValueError(f"No generated roles found for cluster {cluster_id}")
        
        role_set = self.generated_role_sets[cluster_id]
        role_set.reviewed = True
        role_set.approved = approved
        if feedback:
            role_set.feedback = feedback
        
        logger.info(f"Role set for cluster {cluster_id} reviewed: {'Approved' if approved else 'Rejected'}")
        return role_set
    
    async def batch_generate_multiple(
        self,
        cluster_ids: Optional[List[str]] = None,
        process_all: bool = False,
        concurrent_limit: int = 3
    ) -> Dict[str, GeneratedRoleSet]:
        """Generate multiple role options for multiple clusters"""
        
        # Determine which clusters to process
        if process_all:
            if self.data_processor.cluster_summary is None or self.data_processor.cluster_summary.empty:
                self.data_processor.load_data_files()
            cluster_ids = self.data_processor.get_all_cluster_ids()
        elif not cluster_ids:
            raise ValueError("Either provide cluster_ids or set process_all=True")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def generate_with_limit(cluster_id: str):
            async with semaphore:
                try:
                    return await self.generate_multiple_options(cluster_id)
                except Exception as e:
                    logger.error(f"Failed to generate roles for {cluster_id}: {str(e)}")
                    return None
        
        # Generate roles concurrently
        tasks = [generate_with_limit(cid) for cid in cluster_ids]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results and create response dict
        generated = {}
        for cluster_id, result in zip(cluster_ids, results):
            if result:
                generated[cluster_id] = result
        
        logger.info(f"Generated role options for {len(generated)} out of {len(cluster_ids)} clusters")
        return generated
    
    def get_statistics(self) -> Dict:
        """Get statistics about generated roles"""
        stats = {
            "total_clusters": len(self.generated_role_sets),
            "reviewed": sum(1 for r in self.generated_role_sets.values() if r.reviewed),
            "approved": sum(1 for r in self.generated_role_sets.values() if r.approved),
            "pending": sum(1 for r in self.generated_role_sets.values() if not r.reviewed),
            "risk_distribution": {},
            "style_preference": {},
            "recommendation_acceptance_rate": 0
        }
        
        # Calculate risk distribution
        for role_set in self.generated_role_sets.values():
            risk = role_set.risk_level
            stats["risk_distribution"][risk] = stats["risk_distribution"].get(risk, 0) + 1
        
        # Calculate style preference (which options were selected)
        selected_count = 0
        recommended_selected = 0
        for role_set in self.generated_role_sets.values():
            if role_set.selected_option:
                selected_count += 1
                if role_set.selected_option == role_set.recommended_option:
                    recommended_selected += 1
                
                # Find the style of selected option
                selected_opt = next(
                    (opt for opt in role_set.role_options if opt.option_number == role_set.selected_option),
                    None
                )
                if selected_opt:
                    style = selected_opt.style.value
                    stats["style_preference"][style] = stats["style_preference"].get(style, 0) + 1
        
        # Calculate recommendation acceptance rate
        if selected_count > 0:
            stats["recommendation_acceptance_rate"] = (recommended_selected / selected_count) * 100
        
        return stats