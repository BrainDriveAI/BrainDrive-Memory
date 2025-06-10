"""
Interface for LLM Factory - Domain Layer
"""
from abc import ABC, abstractmethod
from typing import Any


class ILLMFactory(ABC):
    """
    Interface for creating LLM instances.
    Abstracts LLM creation logic from health checking.
    """
    
    @abstractmethod
    def create_llm(self, provider: str) -> Any:
        """
        Create LLM instance for specified provider.
        
        Args:
            provider: LLM provider name
            
        Returns:
            LLM instance ready for use
            
        Raises:
            Exception: If provider is not supported or configuration is invalid
        """
        pass
