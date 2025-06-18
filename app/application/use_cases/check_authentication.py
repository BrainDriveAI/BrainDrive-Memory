from app.domain.services.auth_service import AuthDomainService

class CheckAuthenticationUseCase:
    """Use case for checking authentication status"""
    
    def __init__(self, auth_service: AuthDomainService):
        self.auth_service = auth_service
    
    def execute(self) -> bool:
        """Check if user is authenticated"""
        return self.auth_service.is_authenticated()
