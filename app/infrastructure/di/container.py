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
from app.services.llm_health_service import LLMHealthService
from app.services.llm_factory_service import LLMFactoryService
from app.use_cases.check_llm_health_use_case import CheckLLMHealthUseCase
from app.presentation.web.streamlit.components.llm_health_display import LLMHealthDisplay

class DIContainer:
    """Dependency Injection Container for Clean Architecture"""
    
    def __init__(self):
        self._auth_repository: Optional[GoogleAuthRepository] = None
        self._session_repository: Optional[StreamlitSessionRepository] = None
        self._ui_adapter: Optional[StreamlitUIAdapter] = None
        self._auth_service: Optional[AuthDomainService] = None
        self._user_display: Optional[StreamlitUserDisplay] = None
        # Health check services
        self._llm_factory_service = None
        self._llm_health_service = None
        self._check_llm_health_use_case = None
        self._llm_health_display = None
    
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
    
    # LLM Factory Service
    def get_llm_factory_service(self) -> LLMFactoryService:
        """Get or create LLM factory service"""
        if self._llm_factory_service is None:
            self._llm_factory_service = LLMFactoryService()
        return self._llm_factory_service
    
    # LLM Health Service
    def get_llm_health_service(self) -> LLMHealthService:
        """Get or create LLM health service"""
        if self._llm_health_service is None:
            self._llm_health_service = LLMHealthService()
            # Inject dependencies
            self._llm_health_service.set_llm_factory(self.get_llm_factory_service())
        return self._llm_health_service
    
    # Check LLM Health Use Case
    def get_check_llm_health_use_case(self) -> CheckLLMHealthUseCase:
        """Get or create check LLM health use case"""
        if self._check_llm_health_use_case is None:
            self._check_llm_health_use_case = CheckLLMHealthUseCase(
                health_service=self.get_llm_health_service()
            )
        return self._check_llm_health_use_case
    
    # LLM Health Display Component
    def get_llm_health_display(self) -> LLMHealthDisplay:
        """Get or create LLM health display component"""
        if self._llm_health_display is None:
            self._llm_health_display = LLMHealthDisplay(
                health_use_case=self.get_check_llm_health_use_case()
            )
        return self._llm_health_display

# Global container instance
container = DIContainer()
