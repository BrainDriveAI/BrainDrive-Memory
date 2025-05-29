from abc import ABC, abstractmethod
from typing import List
from app.domain.models.auth_result import AuthError

class UIAdapter(ABC):
    """Abstract interface for UI operations"""
    
    @abstractmethod
    def display_error(self, error: AuthError) -> None:
        """Display error message"""
        pass
    
    @abstractmethod
    def display_errors(self, errors: List[AuthError]) -> None:
        """Display multiple errors"""
        pass
    
    @abstractmethod
    def redirect(self, url: str) -> None:
        """Redirect to URL"""
        pass
    
    @abstractmethod
    def trigger_refresh(self) -> None:
        """Trigger UI refresh/rerun"""
        pass
