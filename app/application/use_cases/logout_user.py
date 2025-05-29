from app.domain.services.auth_service import AuthDomainService
from app.domain.interfaces.ui_adapter import UIAdapter

class LogoutUserUseCase:
    """Use case for user logout"""
    
    def __init__(self, auth_service: AuthDomainService, ui_adapter: UIAdapter):
        self.auth_service = auth_service
        self.ui_adapter = ui_adapter
    
    def execute(self) -> None:
        """Execute logout flow"""
        result = self.auth_service.logout()
        
        if result.is_success:
            self.ui_adapter.trigger_refresh()
        else:
            self.ui_adapter.display_errors(result.errors)
