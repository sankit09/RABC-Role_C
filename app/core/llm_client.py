# app/core/llm_client.py
"""Azure OpenAI client wrapper with LangChain support - FIXED FOR WINDOWS"""

import logging
from typing import Dict, Optional, Any
import json
import httpx
from openai import AzureOpenAI
from app.config import settings
from app.core.exceptions import LLMException

logger = logging.getLogger(__name__)

class AzureOpenAIClient:
    """Wrapper for Azure OpenAI interactions"""
    
    def __init__(self):
        self.client = None
        self.langchain_model = None
        self.initialized = False
        # Don't initialize in __init__ to prevent startup failures
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        if self.initialized:
            return
            
        try:
            # Use custom httpx client that ignores proxy environment variables
            # This is the method that worked in your test!
            http_client = httpx.Client(trust_env=False)
            
            self.client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                http_client=http_client
            )
            
            if settings.USE_LANGCHAIN:
                try:
                    from langchain_openai import AzureChatOpenAI
                    # LangChain might also need proxy handling
                    self.langchain_model = AzureChatOpenAI(
                        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                        api_version=settings.AZURE_OPENAI_API_VERSION,
                        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                        api_key=settings.AZURE_OPENAI_API_KEY,
                        temperature=settings.LLM_TEMPERATURE,
                        max_tokens=settings.LLM_MAX_TOKENS,
                        http_client=http_client  # Pass the same client
                    )
                except ImportError:
                    logger.warning("LangChain not installed, using direct API only")
                    settings.USE_LANGCHAIN = False
                except Exception as e:
                    logger.warning(f"LangChain initialization failed: {e}, using direct API only")
                    settings.USE_LANGCHAIN = False
            
            self.initialized = True
            logger.info("Azure OpenAI client initialized successfully with custom httpx client")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            self.initialized = False
    
    def ensure_initialized(self):
        """Ensure client is initialized before use"""
        if not self.initialized:
            self._initialize_client()
            if not self.initialized:
                raise LLMException("Azure OpenAI client not initialized. Check your credentials.")
    
    async def generate_role(self, prompt: str, use_json_mode: bool = True) -> Dict:
        """Generate role using Azure OpenAI"""
        self.ensure_initialized()
        
        try:
            if settings.USE_LANGCHAIN and self.langchain_model:
                return await self._generate_with_langchain(prompt)
            else:
                return await self._generate_direct(prompt, use_json_mode)
        except Exception as e:
            logger.error(f"Role generation failed: {str(e)}")
            raise LLMException(f"Failed to generate role: {str(e)}")
    
    async def _generate_direct(self, prompt: str, use_json_mode: bool) -> Dict:
        """Direct Azure OpenAI API call"""
        try:
            messages = [
                {"role": "system", "content": "You are an expert security analyst specializing in Role-Based Access Control (RBAC) design. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            # Build completion parameters
            completion_params = {
                "model": settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                "messages": messages,
                "temperature": settings.LLM_TEMPERATURE,
                "max_tokens": settings.LLM_MAX_TOKENS
            }
            
            # Only add response_format if using JSON mode and API version supports it
            # Note: response_format might not be supported in all API versions
            if use_json_mode:
                # For newer API versions
                if "2024" in settings.AZURE_OPENAI_API_VERSION or "2025" in settings.AZURE_OPENAI_API_VERSION:
                    completion_params["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**completion_params)
            
            content = response.choices[0].message.content
            
            if use_json_mode:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {content}")
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except:
                            pass
                    # If all else fails, create a structured response
                    return {
                        "role_name": "Role_" + prompt[:20],
                        "description": content[:200] if len(content) > 200 else content,
                        "rationale": "Generated from LLM response",
                        "risk_level": "MEDIUM"
                    }
            else:
                return {"response": content}
            
        except Exception as e:
            logger.error(f"Direct API call failed: {str(e)}")
            raise
    
    async def _generate_with_langchain(self, prompt: str) -> Dict:
        """Generate using LangChain"""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser
        from pydantic import BaseModel, Field
        
        class RoleOutput(BaseModel):
            role_name: str = Field(description="Concise role name")
            description: str = Field(description="Role description")
            rationale: str = Field(description="Business justification")
            risk_level: str = Field(description="Risk level: LOW, MEDIUM, HIGH, or CRITICAL")
        
        parser = JsonOutputParser(pydantic_object=RoleOutput)
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert security analyst specializing in RBAC design."),
            ("user", "{input}"),
            ("user", "Format your response as JSON with the following structure:\n{format_instructions}")
        ])
        
        chain = prompt_template | self.langchain_model | parser
        
        result = await chain.ainvoke({
            "input": prompt,
            "format_instructions": parser.get_format_instructions()
        })
        
        return result
    
    def test_connection(self) -> bool:
        """Test if Azure OpenAI connection works"""
        try:
            self.ensure_initialized()
            # Make a simple test call
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": "Say 'Connected'"}],
                max_tokens=10
            )
            # Remove emojis from log message to avoid Windows encoding issues
            message = response.choices[0].message.content
            # Clean any non-ASCII characters for Windows compatibility
            clean_message = message.encode('ascii', 'ignore').decode('ascii')
            logger.info(f"Connection test successful: {clean_message}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False