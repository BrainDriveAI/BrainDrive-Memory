from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models.auth import AuthSession

class SessionRepository(ABC):
    """Abstract interface for session management"""
    
    @abstractmethod
    def get_session(self) -> Optional[AuthSession]:
        """Get current session"""
        pass
    
    @abstractmethod
    def save_session(self, session: AuthSession) -> None:
        """Save session"""
        pass
    
    @abstractmethod
    def clear_session(self) -> None:
        """Clear current session"""
        pass
    
    @abstractmethod
    def get_query_param(self, key: str) -> Optional[str]:
        """Get query parameter from current request"""
        pass
    
    @abstractmethod
    def clear_query_params(self) -> None:
        """Clear query parameters from current request"""
        pass
