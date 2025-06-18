from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.domain.models.user import User
from app.domain.models.auth import AuthCredentials

class AuthRepository(ABC):
    """Abstract interface for authentication providers"""
    
    @abstractmethod
    def create_auth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Create authentication URL for OAuth flow"""
        pass
    
    @abstractmethod
    def exchange_code_for_credentials(self, code: str, redirect_uri: str) -> AuthCredentials:
        """Exchange authorization code for credentials"""
        pass
    
    @abstractmethod
    def get_user_info(self, credentials: AuthCredentials) -> User:
        """Get user information using credentials"""
        pass
    
    @abstractmethod
    def validate_credentials(self, credentials: AuthCredentials) -> bool:
        """Validate if credentials are still valid"""
        pass
