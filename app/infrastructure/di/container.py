from typing import Optional
from app.config.app_env import app_env
from app.domain.services.auth_service import AuthDomainService
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase
from app.application.use_cases.logout_user import LogoutUserUseCase
from app.application.use_cases.get_user_info import GetUserInfoUseCase
from app.application.use_cases.check_authentication import CheckAuthenticationUseCase
from app.infrastructure.repositories.google_auth_repository import GoogleAuthRepository
from app.infrastructure.adapters.streamlit_session_repository import StreamlitSessionRepository
from app.infrastructure.adapters.streamlit_ui_adapter import StreamlitUIAdapter
from app.infrastructure.adapters.streamlit_user_display import StreamlitUserDisplay

class DIContainer:
    """Dependency Injection Container for Clean Architecture"""
    
    def __init__(self):
        self._auth_repository: Optional[GoogleAuthRepository] = None
        self._session_repository: Optional[StreamlitSessionRepository] = None
        self._ui_adapter: Optional[StreamlitUIAdapter] = None
        self._auth_service: Optional[AuthDomainService] = None
        self._user_display: Optional[StreamlitUserDisplay] = None
    
    @property
    def auth_repository(self) -> GoogleAuthRepository:
        """Get or create Google Auth Repository"""
        if self._auth_repository is None:
            if not app_env.ENABLE_AUTH:
                # Create a dummy repository for local mode
                self._auth_repository = GoogleAuthRepository("dummy", "dummy")
            else:
                self._auth_repository = GoogleAuthRepository(
                    client_id=app_env.GOOGLE_CLIENT_ID,
                    client_secret=app_env.GOOGLE_CLIENT_SECRET.get_secret_value()
                )
        return self._auth_repository
    
    @property
    def session_repository(self) -> StreamlitSessionRepository:
        """Get or create Streamlit Session Repository"""
        if self._session_repository is None:
            self._session_repository = StreamlitSessionRepository()
        return self._session_repository
    
    @property
    def ui_adapter(self) -> StreamlitUIAdapter:
        """Get or create Streamlit UI Adapter"""
        if self._ui_adapter is None:
            self._ui_adapter = StreamlitUIAdapter()
        return self._ui_adapter
    
    @property
    def auth_service(self) -> AuthDomainService:
        """Get or create Auth Domain Service"""
        if self._auth_service is None:
            self._auth_service = AuthDomainService(
                auth_repository=self.auth_repository,
                session_repository=self.session_repository,
                auth_enabled=app_env.ENABLE_AUTH,
                redirect_uri=str(app_env.REDIRECT_URI) if app_env.REDIRECT_URI else "http://localhost:8501/"
            )
        return self._auth_service
    
    @property
    def user_display(self) -> StreamlitUserDisplay:
        """Get or create Streamlit User Display"""
        if self._user_display is None:
            self._user_display = StreamlitUserDisplay(auth_enabled=app_env.ENABLE_AUTH)
        return self._user_display
    
    # Use Cases
    def get_authenticate_user_use_case(self) -> AuthenticateUserUseCase:
        """Get Authenticate User Use Case"""
        return AuthenticateUserUseCase(
            auth_service=self.auth_service,
            ui_adapter=self.ui_adapter
        )
    
    def get_logout_user_use_case(self) -> LogoutUserUseCase:
        """Get Logout User Use Case"""
        return LogoutUserUseCase(
            auth_service=self.auth_service,
            ui_adapter=self.ui_adapter
        )
    
    def get_user_info_use_case(self) -> GetUserInfoUseCase:
        """Get User Info Use Case"""
        return GetUserInfoUseCase(auth_service=self.auth_service)
    
    def get_check_authentication_use_case(self) -> CheckAuthenticationUseCase:
        """Get Check Authentication Use Case"""
        return CheckAuthenticationUseCase(auth_service=self.auth_service)

# Global container instance
container = DIContainer()
