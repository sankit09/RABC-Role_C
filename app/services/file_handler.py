# app/services/file_handler.py
"""File handling service"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import UploadFile
from app.config import settings
from app.core.exceptions import FileHandlingException

logger = logging.getLogger(__name__)

class FileHandlerService:
    """Service for handling file uploads and processing"""
    
    @staticmethod
    async def save_upload(file: UploadFile, file_type: str) -> Dict[str, Any]:
        """Save uploaded file and return processing summary"""
        try:
            # Determine file name based on type
            file_mapping = {
                'cluster_summary': 'cluster_summary.csv',
                'user_metadata': 'user_metadata.csv',
                'entitlement_metadata': 'entitlement_metadata.json'
            }
            
            if file_type not in file_mapping:
                raise FileHandlingException(f"Unknown file type: {file_type}")
            
            file_path = Path(settings.INPUT_DIR) / file_mapping[file_type]
            
            # Save file
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Process and validate file
            if file_type == 'entitlement_metadata':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                rows_processed = len(data)
                logger.info(f"Saved entitlement metadata with {rows_processed} entries")
            else:
                df = pd.read_csv(file_path)
                rows_processed = len(df)
                
                # Validate required columns
                if file_type == 'cluster_summary':
                    required_cols = ['Cluster_ID', 'Core_Entitlements', 'User_Count']
                    if not all(col in df.columns for col in required_cols):
                        raise FileHandlingException(f"Missing required columns: {required_cols}")
                
                elif file_type == 'user_metadata':
                    required_cols = ['User_ID', 'Cluster_ID', 'Job_Title', 'Department']
                    if not all(col in df.columns for col in required_cols):
                        raise FileHandlingException(f"Missing required columns: {required_cols}")
                
                logger.info(f"Saved {file_type} with {rows_processed} rows")
            
            return {
                'filename': file.filename,
                'file_type': file_type,
                'rows_processed': rows_processed,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to save upload: {str(e)}")
            raise FileHandlingException(f"File upload failed: {str(e)}")