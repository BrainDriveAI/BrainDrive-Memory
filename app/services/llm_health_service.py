"""
LLM Health Check Service - Business Logic Layer
Handles connectivity testing and status reporting for configured LLM providers.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LLMStatus(Enum):
    """LLM connectivity status enum"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TESTING = "testing"
    UNKNOWN = "unknown"


@dataclass
class LLMHealthResult:
    """Result of LLM health check"""
    provider: str
    model_name: str
    status: LLMStatus
    response_time_ms: Optional[float]
    error_message: Optional[str]
    last_checked: datetime
    test_prompt_used: str
    
    @property
    def is_healthy(self) -> bool:
        return self.status == LLMStatus.HEALTHY
    
    @property
    def status_display(self) -> str:
        status_map = {
            LLMStatus.HEALTHY: "🟢 Online",
            LLMStatus.UNHEALTHY: "🔴 Offline",
            LLMStatus.TESTING: "🟡 Testing...",
            LLMStatus.UNKNOWN: "⚪ Unknown"
        }
        return status_map.get(self.status, "❓ Unknown")


class LLMHealthService:
    """
    Service for checking LLM provider health and connectivity.
    Implements business logic for testing LLM connectivity.
    """
    
    TEST_PROMPT = "Hi, respond with just 'OK' to confirm you're working."
    TIMEOUT_SECONDS = 10
    CACHE_DURATION_MINUTES = 5
    
    def __init__(self):
        self._cache: Dict[str, LLMHealthResult] = {}
        self._llm_factory = None  # Will be injected
    
    def set_llm_factory(self, llm_factory):
        """Inject LLM factory dependency"""
        self._llm_factory = llm_factory
    
    async def check_llm_health(self, provider: str, force_refresh: bool = False) -> LLMHealthResult:
        """
        Check health of specified LLM provider.
        
        Args:
            provider: LLM provider name
            force_refresh: Skip cache and force new health check
            
        Returns:
            LLMHealthResult with connectivity status
        """
        cache_key = f"{provider}_health"
        
        # Check cache first (unless force refresh)
        if not force_refresh and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            if self._is_cache_valid(cached_result):
                return cached_result
        
        # Perform actual health check
        result = await self._perform_health_check(provider)
        
        # Cache the result
        self._cache[cache_key] = result
        
        return result
    
    async def check_current_llm_health(self, force_refresh: bool = False) -> LLMHealthResult:
        """
        Check health of currently configured LLM provider.
        
        Args:
            force_refresh: Skip cache and force new health check
            
        Returns:
            LLMHealthResult for current provider
        """
        from app.config.app_env import app_env
        return await self.check_llm_health(app_env.LLM_PROVIDER, force_refresh)
    
    def get_cached_health_status(self, provider: str) -> Optional[LLMHealthResult]:
        """Get cached health status without performing new check"""
        cache_key = f"{provider}_health"
        return self._cache.get(cache_key)
    
    async def _perform_health_check(self, provider: str) -> LLMHealthResult:
        """
        Perform actual health check against LLM provider.
        
        Args:
            provider: LLM provider name
            
        Returns:
            LLMHealthResult with test results
        """
        from app.config.app_env import app_env
        
        start_time = datetime.now()
        model_name = self._get_model_name_for_provider(provider)
        
        try:
            # Create LLM instance for testing
            if not self._llm_factory:
                raise Exception("LLM factory not configured")
            
            llm = self._llm_factory.create_llm(provider)
            
            # Test with simple prompt
            test_start = datetime.now()
            response = await asyncio.wait_for(
                self._test_llm_async(llm),
                timeout=self.TIMEOUT_SECONDS
            )
            test_end = datetime.now()
            
            response_time = (test_end - test_start).total_seconds() * 1000
            
            # Validate response
            if self._is_valid_response(response):
                return LLMHealthResult(
                    provider=provider,
                    model_name=model_name,
                    status=LLMStatus.HEALTHY,
                    response_time_ms=response_time,
                    error_message=None,
                    last_checked=datetime.now(),
                    test_prompt_used=self.TEST_PROMPT
                )
            else:
                return LLMHealthResult(
                    provider=provider,
                    model_name=model_name,
                    status=LLMStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error_message=f"Invalid response: {response[:100]}...",
                    last_checked=datetime.now(),
                    test_prompt_used=self.TEST_PROMPT
                )
                
        except asyncio.TimeoutError:
            return LLMHealthResult(
                provider=provider,
                model_name=model_name,
                status=LLMStatus.UNHEALTHY,
                response_time_ms=None,
                error_message=f"Timeout after {self.TIMEOUT_SECONDS} seconds",
                last_checked=datetime.now(),
                test_prompt_used=self.TEST_PROMPT
            )
        except Exception as e:
            logger.error(f"LLM health check failed for {provider}: {str(e)}")
            return LLMHealthResult(
                provider=provider,
                model_name=model_name,
                status=LLMStatus.UNHEALTHY,
                response_time_ms=None,
                error_message=str(e),
                last_checked=datetime.now(),
                test_prompt_used=self.TEST_PROMPT
            )
    
    async def _test_llm_async(self, llm) -> str:
        """Test LLM with async call"""
        # This will need to be adapted based on your LLM interface
        # Assuming your LLM has an async invoke method
        if hasattr(llm, 'ainvoke'):
            response = await llm.ainvoke(self.TEST_PROMPT)
        elif hasattr(llm, 'invoke'):
            # Fallback to sync call in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, llm.invoke, self.TEST_PROMPT)
        else:
            raise Exception("LLM does not support invoke methods")
        
        # Extract content from response (adapt based on your response format)
        if hasattr(response, 'content'):
            return response.content
        elif isinstance(response, str):
            return response
        else:
            return str(response)
    
    def _get_model_name_for_provider(self, provider: str) -> str:
        """Get model name for given provider"""
        from app.config.app_env import app_env
        
        model_map = {
            'openai': app_env.OPENAI_LLM_MODEL,
            'ollama': app_env.OLLAMA_LLM_MODEL,
            'togetherai': app_env.TOGETHER_AI_LLM_MODEL,
            'openrouter': app_env.OPENROUTER_LLM_MODEL,
            'groq': app_env.GROQ_LLM_MODEL,
            'cloud_run_gemma': app_env.GEMMA_LLM_MODEL,
        }
        
        return model_map.get(provider, "Unknown Model")
    
    def _is_valid_response(self, response: str) -> bool:
        """Check if response indicates healthy LLM"""
        if not response:
            return False
        
        response_lower = response.lower().strip()
        # Accept various positive responses
        valid_responses = ['ok', 'okay', 'yes', 'working', 'ready', 'hello']
        
        return any(valid in response_lower for valid in valid_responses)
    
    def _is_cache_valid(self, result: LLMHealthResult) -> bool:
        """Check if cached result is still valid"""
        cache_age = datetime.now() - result.last_checked
        return cache_age < timedelta(minutes=self.CACHE_DURATION_MINUTES)
