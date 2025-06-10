"""
Use Case for checking LLM health - Application Layer
"""
from typing import Optional
from app.services.llm_health_service import LLMHealthService, LLMHealthResult


class CheckLLMHealthUseCase:
    """
    Use case for checking LLM connectivity and health status.
    Coordinates between UI and business logic.
    """
    
    def __init__(self, health_service: LLMHealthService):
        self.health_service = health_service
    
    async def execute(self, force_refresh: bool = False) -> LLMHealthResult:
        """
        Execute health check for current LLM provider.
        
        Args:
            force_refresh: Force new health check bypassing cache
            
        Returns:
            LLMHealthResult with current status
        """
        return await self.health_service.check_current_llm_health(force_refresh)
    
    def get_cached_status(self) -> Optional[LLMHealthResult]:
        """Get cached health status without performing new check"""
        from app.config.app_env import app_env
        return self.health_service.get_cached_health_status(app_env.LLM_PROVIDER)
