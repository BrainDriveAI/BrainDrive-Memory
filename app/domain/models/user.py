from dataclasses import dataclass
from typing import Optional
from enum import Enum


class AuthProvider(Enum):
    GOOGLE = "google"
    LOCAL = "local"


@dataclass
class User:
    """User domain model"""
    id: str
    name: str
    email: str
    picture: Optional[str] = None
    provider: AuthProvider = AuthProvider.GOOGLE
    
    @classmethod
    def create_local_user(cls) -> 'User':
        """Factory method for local development user"""
        return cls(
            id="local_user",
            name="Local User",
            email="user@localhost",
            picture=None,
            provider=AuthProvider.LOCAL
        )
