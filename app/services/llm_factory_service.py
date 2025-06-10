"""
LLM Factory Service Implementation - Infrastructure Layer
"""
import logging
from typing import Any
from app.interfaces.llm_factory_interface import ILLMFactory
from app.config.app_env import app_env

logger = logging.getLogger(__name__)


class LLMFactoryService(ILLMFactory):
    """
    Factory service for creating LLM instances.
    Handles provider-specific LLM instantiation.
    """
    
    def create_llm(self, provider: str) -> Any:
        """
        Create LLM instance for specified provider.
        
        Args:
            provider: LLM provider name ('openai', 'ollama', etc.)
            
        Returns:
            LLM instance ready for use
            
        Raises:
            Exception: If provider is not supported or configuration is invalid
        """
        try:
            if provider == 'openai':
                return self._create_openai_llm()
            elif provider == 'ollama':
                return self._create_ollama_llm()
            elif provider == 'togetherai':
                return self._create_togetherai_llm()
            elif provider == 'openrouter':
                return self._create_openrouter_llm()
            elif provider == 'groq':
                return self._create_groq_llm()
            elif provider == 'cloud_run_gemma':
                return self._create_gemma_llm()
            else:
                raise Exception(f"Unsupported LLM provider: {provider}")
                
        except Exception as e:
            logger.error(f"Failed to create LLM for provider {provider}: {str(e)}")
            raise
    
    def _create_openai_llm(self) -> Any:
        """Create OpenAI LLM instance"""
        from langchain_openai import ChatOpenAI
        
        if not app_env.OPENAI_API_KEY:
            raise Exception("OpenAI API key not configured")
        
        return ChatOpenAI(
            model=app_env.OPENAI_LLM_MODEL,
            api_key=app_env.OPENAI_API_KEY.get_secret_value(),
            temperature=0.1,
            max_tokens=50,  # Small for health check
            timeout=10
        )
    
    def _create_ollama_llm(self) -> Any:
        """Create Ollama LLM instance"""
        from langchain_ollama import ChatOllama
        
        if not app_env.OLLAMA_LLM_MODEL:
            raise Exception("Ollama model not configured")
        
        base_url = str(app_env.OLLAMA_BASE_URL) if app_env.OLLAMA_BASE_URL else "http://localhost:11434"
        
        return ChatOllama(
            model=app_env.OLLAMA_LLM_MODEL,
            base_url=base_url,
            temperature=0.1,
            timeout=10
        )
    
    def _create_togetherai_llm(self) -> Any:
        """Create TogetherAI LLM instance"""
        from langchain_together import ChatTogether
        
        if not app_env.TOGETHER_AI_API_KEY:
            raise Exception("TogetherAI API key not configured")
        
        return ChatTogether(
            model=app_env.TOGETHER_AI_LLM_MODEL,
            api_key=app_env.TOGETHER_AI_API_KEY.get_secret_value(),
            temperature=0.1,
            max_tokens=50,
            timeout=10
        )
    
    def _create_openrouter_llm(self) -> Any:
        """Create OpenRouter LLM instance"""
        from langchain_openai import ChatOpenAI  # OpenRouter uses OpenAI-compatible API
        
        if not app_env.OPENROUTER_API_KEY:
            raise Exception("OpenRouter API key not configured")
        
        return ChatOpenAI(
            model=app_env.OPENROUTER_LLM_MODEL,
            api_key=app_env.OPENROUTER_API_KEY.get_secret_value(),
            base_url=str(app_env.OPENROUTER_BASE_URL),
            temperature=0.1,
            max_tokens=50,
            timeout=10
        )
    
    def _create_groq_llm(self) -> Any:
        """Create Groq LLM instance"""
        from langchain_groq import ChatGroq
        
        if not app_env.GROQ_API_KEY:
            raise Exception("Groq API key not configured")
        
        return ChatGroq(
            model=app_env.GROQ_LLM_MODEL,
            api_key=app_env.GROQ_API_KEY.get_secret_value(),
            temperature=0.1,
            max_tokens=50,
            timeout=10
        )
    
    def _create_gemma_llm(self) -> Any:
        """Create Gemma Cloud Run LLM instance"""
        # This would need to be implemented based on your Gemma service interface
        # Placeholder implementation
        raise Exception("Gemma Cloud Run LLM not yet implemented in factory")
