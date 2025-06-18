from app.domain.services.auth_service import AuthDomainService
from app.domain.interfaces.ui_adapter import UIAdapter

class AuthenticateUserUseCase:
    """Use case for user authentication"""
    
    def __init__(self, auth_service: AuthDomainService, ui_adapter: UIAdapter):
        self.auth_service = auth_service
        self.ui_adapter = ui_adapter
    
    def execute(self) -> bool:
        """
        Execute authentication flow
        Returns True if user is authenticated, False otherwise
        """
        result = self.auth_service.authenticate()
        
        if result.is_success:
            return True
        elif result.requires_redirect:
            self.ui_adapter.redirect(result.redirect_url)
            return False
        else:
            # Handle errors
            self.ui_adapter.display_errors(result.errors)
            return False
