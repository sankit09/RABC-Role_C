# app/config.py
"""Configuration management for RBAC Role Mining system"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RBAC Role Mining System"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o"
    
    # Optional LangChain Configuration
    USE_LANGCHAIN: bool = False
    LANGCHAIN_TRACING_V2: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # File paths
    DATA_DIR: str = "./data"
    INPUT_DIR: str = "./data/input"
    OUTPUT_DIR: str = "./data/output"
    
    # Processing Configuration
    MAX_CONCURRENT_LLM_CALLS: int = 5
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
