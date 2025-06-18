from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from app.domain.models.auth import AuthSession


class AuthStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REQUIRES_REDIRECT = "requires_redirect"

@dataclass
class AuthError:
    """Represents an authentication error"""
    code: str
    message: str
    details: Optional[str] = None

@dataclass
class AuthResult:
    """Result of an authentication operation"""
    status: AuthStatus
    session: Optional[AuthSession] = None
    redirect_url: Optional[str] = None
    errors: List[AuthError] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def is_success(self) -> bool:
        return self.status == AuthStatus.SUCCESS
    
    @property
    def requires_redirect(self) -> bool:
        return self.status == AuthStatus.REQUIRES_REDIRECT
    
    @classmethod
    def success(cls, session: AuthSession) -> 'AuthResult':
        return cls(status=AuthStatus.SUCCESS, session=session)
    
    @classmethod
    def failed(cls, error: AuthError) -> 'AuthResult':
        return cls(status=AuthStatus.FAILED, errors=[error])
    
    @classmethod
    def redirect(cls, url: str) -> 'AuthResult':
        return cls(status=AuthStatus.REQUIRES_REDIRECT, redirect_url=url)
