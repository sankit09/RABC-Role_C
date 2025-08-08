# app/api/v1/endpoints/health.py
"""Health check endpoints"""

from fastapi import APIRouter
from app.models.responses import HealthResponse
from app.config import settings

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Test Azure OpenAI connection
    azure_connected = False
    try:
        from app.core.llm_client import AzureOpenAIClient
        client = AzureOpenAIClient()
        azure_connected = client.test_connection()
    except:
        pass
    
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        azure_openai_connected=azure_connected
    )