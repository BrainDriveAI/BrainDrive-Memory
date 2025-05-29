from dataclasses import dataclass
from typing import Optional, Any
from app.domain.models.user import User, AuthProvider


@dataclass
class AuthCredentials:
    """Authentication credentials wrapper"""
    provider: AuthProvider
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    raw_credentials: Optional[Any] = None  # For storing provider-specific credentials


@dataclass
class AuthSession:
    """Represents an authenticated session"""
    user: User
    credentials: Optional[AuthCredentials] = None
    is_authenticated: bool = True
    
    @classmethod
    def create_local_session(cls) -> 'AuthSession':
        """Factory method for local development session"""
        return cls(
            user=User.create_local_user(),
            credentials=None,
            is_authenticated=True
        )
