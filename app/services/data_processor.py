# app/services/data_processor.py
"""Data consolidation and processing service"""

import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter
from pathlib import Path
from app.models.domain import ClusterData, Entitlement, UserSummary
from app.core.exceptions import DataProcessingException
from app.config import settings

logger = logging.getLogger(__name__)

class DataProcessor:
    """Handles data consolidation and processing"""
    
    def __init__(self):
        self.entitlement_metadata: Dict[str, Dict] = {}
        self.cluster_summary: pd.DataFrame = None
        self.user_metadata: pd.DataFrame = None
        self.clusters: Dict[str, ClusterData] = {}
    
    def load_data_files(self) -> None:
        """Load all required data files"""
        try:
            # Load entitlement metadata
            entitlement_path = Path(settings.INPUT_DIR) / "entitlement_metadata.json"
            if entitlement_path.exists():
                with open(entitlement_path, 'r') as f:
                    self.entitlement_metadata = json.load(f)
                logger.info(f"Loaded {len(self.entitlement_metadata)} entitlements")
            
            # Load cluster summary
            cluster_path = Path(settings.INPUT_DIR) / "cluster_summary.csv"
            if cluster_path.exists():
                self.cluster_summary = pd.read_csv(cluster_path)
                logger.info(f"Loaded {len(self.cluster_summary)} clusters")
            
            # Load user metadata
            user_path = Path(settings.INPUT_DIR) / "user_metadata.csv"
            if user_path.exists():
                self.user_metadata = pd.read_csv(user_path)
                logger.info(f"Loaded {len(self.user_metadata)} users")
                
        except Exception as e:
            logger.error(f"Failed to load data files: {str(e)}")
            raise DataProcessingException(f"Data loading failed: {str(e)}")
    
    def process_cluster(self, cluster_id: str) -> ClusterData:
        """Process a single cluster and create consolidated data"""
        try:
            # Get cluster info
            cluster_row = self.cluster_summary[self.cluster_summary['Cluster_ID'] == cluster_id]
            if cluster_row.empty:
                raise DataProcessingException(f"Cluster {cluster_id} not found")
            
            # Parse entitlements
            entitlement_ids = cluster_row['Core_Entitlements'].iloc[0].split(',')
            entitlements = []
            for ent_id in entitlement_ids:
                ent_id = ent_id.strip()
                if ent_id in self.entitlement_metadata:
                    ent_data = self.entitlement_metadata[ent_id]
                    entitlements.append(Entitlement(
                        id=ent_id,
                        name=ent_data['name'],
                        description=ent_data['description']
                    ))
            
            # Get user summary
            cluster_users = self.user_metadata[self.user_metadata['Cluster_ID'] == cluster_id]
            user_summary = self._create_user_summary(cluster_users)
            
            return ClusterData(
                cluster_id=cluster_id,
                core_entitlements=entitlements,
                user_summary=user_summary
            )
            
        except Exception as e:
            logger.error(f"Failed to process cluster {cluster_id}: {str(e)}")
            raise DataProcessingException(f"Cluster processing failed: {str(e)}")
    
    def _create_user_summary(self, users_df: pd.DataFrame) -> UserSummary:
        """Create user summary statistics"""
        total_users = len(users_df)
        
        # Job title distribution
        job_titles = users_df['Job_Title'].value_counts().to_dict()
        top_job_titles = list(job_titles.keys())[:5]
        
        # Department distribution
        departments = users_df['Department'].value_counts().to_dict()
        top_departments = list(departments.keys())[:3]
        
        return UserSummary(
            total_users=total_users,
            top_job_titles=top_job_titles,
            top_departments=top_departments,
            job_title_distribution=job_titles,
            department_distribution=departments
        )
    
    def get_all_cluster_ids(self) -> List[str]:
        """Get all available cluster IDs"""
        if self.cluster_summary is not None:
            return self.cluster_summary['Cluster_ID'].tolist()
        return []