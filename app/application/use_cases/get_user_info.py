from typing import Optional
from app.domain.services.auth_service import AuthDomainService
from app.domain.models.user import User

class GetUserInfoUseCase:
    """Use case for getting current user information"""
    
    def __init__(self, auth_service: AuthDomainService):
        self.auth_service = auth_service
    
    def execute(self) -> Optional[User]:
        """Get current user information"""
        return self.auth_service.get_user_info()
