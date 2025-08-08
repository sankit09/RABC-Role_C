# app/api/v1/endpoints/clusters.py
"""Cluster management endpoints"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import logging
from app.models.responses import ClusterSummaryResponse, FileUploadResponse
from app.services.data_processor import DataProcessor
from app.services.file_handler import FileHandlerService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
data_processor = DataProcessor()
file_handler = FileHandlerService()

@router.get("/", response_model=List[ClusterSummaryResponse])
async def list_clusters():
    """List all available clusters"""
    try:
        if not data_processor.cluster_summary:
            data_processor.load_data_files()
        
        clusters = []
        for _, row in data_processor.cluster_summary.iterrows():
            cluster_data = data_processor.process_cluster(row['Cluster_ID'])
            clusters.append(ClusterSummaryResponse(
                cluster_id=row['Cluster_ID'],
                entitlement_count=cluster_data.entitlement_count,
                user_count=cluster_data.user_summary.total_users,
                top_job_titles=cluster_data.user_summary.top_job_titles,
                top_departments=cluster_data.user_summary.top_departments
            ))
        
        return clusters
    except Exception as e:
        logger.error(f"Failed to list clusters: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{cluster_id}", response_model=ClusterSummaryResponse)
async def get_cluster_details(cluster_id: str):
    """Get details for a specific cluster"""
    try:
        if not data_processor.cluster_summary:
            data_processor.load_data_files()
        
        cluster_data = data_processor.process_cluster(cluster_id)
        
        return ClusterSummaryResponse(
            cluster_id=cluster_id,
            entitlement_count=cluster_data.entitlement_count,
            user_count=cluster_data.user_summary.total_users,
            top_job_titles=cluster_data.user_summary.top_job_titles,
            top_departments=cluster_data.user_summary.top_departments
        )
    except Exception as e:
        logger.error(f"Failed to get cluster details: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/upload", response_model=FileUploadResponse)
async def upload_data_file(
    file: UploadFile = File(...),
    file_type: str = None
):
    """Upload data files (cluster_summary, user_metadata, or entitlement_metadata)"""
    try:
        result = await file_handler.save_upload(file, file_type)
        
        # Reload data after upload
        data_processor.load_data_files()
        
        return FileUploadResponse(**result)
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
