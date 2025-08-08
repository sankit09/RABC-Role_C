# app/services/role_generator.py
"""Role generation service"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from app.models.domain import ClusterData, GeneratedRole, RiskLevel
from app.core.llm_client import AzureOpenAIClient
from app.core.prompt_manager import PromptManager
from app.services.data_processor import DataProcessor
from app.config import settings

logger = logging.getLogger(__name__)

class RoleGeneratorService:
    """Service for generating RBAC roles"""
    
    def __init__(self):
        self.llm_client = None  # Lazy initialization
        self.prompt_manager = PromptManager()
        self.data_processor = DataProcessor()
        self.generated_roles: Dict[str, GeneratedRole] = {}
    
    def _get_llm_client(self) -> AzureOpenAIClient:
        """Get or create LLM client (lazy initialization)"""
        if self.llm_client is None:
            self.llm_client = AzureOpenAIClient()
        return self.llm_client
    
    async def generate_single_role(self, cluster_id: str, force_regenerate: bool = False) -> GeneratedRole:
        """Generate a role for a single cluster"""
        
        # Check if role already exists
        if cluster_id in self.generated_roles and not force_regenerate:
            logger.info(f"Role already exists for cluster {cluster_id}")
            return self.generated_roles[cluster_id]
        
        try:
            # Load and process cluster data
            if self.data_processor.cluster_summary is None or self.data_processor.cluster_summary.empty:
                self.data_processor.load_data_files()
            
            cluster_data = self.data_processor.process_cluster(cluster_id)
            
            # Generate prompt
            prompt = self.prompt_manager.create_role_generation_prompt(cluster_data)
            
            # Get LLM client and call LLM
            llm_client = self._get_llm_client()
            logger.info(f"Generating role for cluster {cluster_id}")
            llm_response = await llm_client.generate_role(prompt)
            
            # Create GeneratedRole object
            generated_role = GeneratedRole(
                cluster_id=cluster_id,
                role_name=llm_response.get('role_name', f'Role_{cluster_id}'),
                description=llm_response.get('description', ''),
                rationale=llm_response.get('rationale', ''),
                risk_level=RiskLevel(llm_response.get('risk_level', 'MEDIUM')),
                entitlements=cluster_data.core_entitlements,
                user_summary=cluster_data.user_summary,
                generated_at=datetime.now()
            )
            
            # Store the generated role
            self.generated_roles[cluster_id] = generated_role
            
            logger.info(f"Successfully generated role '{generated_role.role_name}' for cluster {cluster_id}")
            return generated_role
            
        except Exception as e:
            logger.error(f"Failed to generate role for cluster {cluster_id}: {str(e)}")
            raise
    
    async def generate_batch_roles(
        self, 
        cluster_ids: Optional[List[str]] = None,
        process_all: bool = False,
        concurrent_limit: int = 5
    ) -> Dict[str, GeneratedRole]:
        """Generate roles for multiple clusters"""
        
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
                    return await self.generate_single_role(cluster_id)
                except Exception as e:
                    logger.error(f"Failed to generate role for {cluster_id}: {str(e)}")
                    return None
        
        # Generate roles concurrently
        tasks = [generate_with_limit(cid) for cid in cluster_ids]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results and create response dict
        generated = {}
        for cluster_id, result in zip(cluster_ids, results):
            if result:
                generated[cluster_id] = result
        
        logger.info(f"Generated {len(generated)} roles out of {len(cluster_ids)} clusters")
        return generated
    
    def review_role(self, cluster_id: str, approved: bool, feedback: Optional[str] = None) -> GeneratedRole:
        """Review and potentially update a generated role"""
        if cluster_id not in self.generated_roles:
            raise ValueError(f"No generated role found for cluster {cluster_id}")
        
        role = self.generated_roles[cluster_id]
        role.reviewed = True
        role.approved = approved
        
        logger.info(f"Role for cluster {cluster_id} reviewed: {'Approved' if approved else 'Rejected'}")
        return role
    
    def export_roles(self, output_format: str = 'json') -> str:
        """Export all generated roles"""
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'total_roles': len(self.generated_roles),
            'roles': [role.to_dict() for role in self.generated_roles.values()]
        }
        
        if output_format == 'json':
            import json
            output_path = Path(settings.OUTPUT_DIR) / f"generated_roles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            return str(output_path)
        
        elif output_format == 'csv':
            import pandas as pd
            roles_data = []
            for role in self.generated_roles.values():
                roles_data.append({
                    'cluster_id': role.cluster_id,
                    'role_name': role.role_name,
                    'description': role.description,
                    'rationale': role.rationale,
                    'risk_level': role.risk_level,
                    'entitlement_count': len(role.entitlements),
                    'user_count': role.user_summary.total_users,
                    'approved': role.approved
                })
            
            df = pd.DataFrame(roles_data)
            output_path = Path(settings.OUTPUT_DIR) / f"generated_roles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_path, index=False)
            return str(output_path)
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
