from typing import Optional
from app.domain.interfaces.auth_repository import AuthRepository
from app.domain.interfaces.session_repository import SessionRepository
from app.domain.models.auth import AuthSession
from app.domain.models.auth_result import AuthResult, AuthError, AuthStatus
from app.domain.models.user import User

class AuthDomainService:
    """Domain service for authentication business logic"""
    
    def __init__(
        self, 
        auth_repository: AuthRepository,
        session_repository: SessionRepository,
        auth_enabled: bool = True,
        redirect_uri: str = "http://localhost:8501/"
    ):
        self.auth_repository = auth_repository
        self.session_repository = session_repository
        self.auth_enabled = auth_enabled
        self.redirect_uri = redirect_uri
    
    def get_current_session(self) -> Optional[AuthSession]:
        """Get current authenticated session"""
        if not self.auth_enabled:
            return AuthSession.create_local_session()
        
        return self.session_repository.get_session()
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        session = self.get_current_session()
        return session is not None and session.is_authenticated
    
    def initiate_login(self) -> AuthResult:
        """Initiate login process"""
        if not self.auth_enabled:
            # For local development, create and save local session
            local_session = AuthSession.create_local_session()
            self.session_repository.save_session(local_session)
            return AuthResult.success(local_session)
        
        try:
            # Generate OAuth URL
            auth_url = self.auth_repository.create_auth_url(
                redirect_uri=self.redirect_uri
            )
            return AuthResult.redirect(auth_url)
        except Exception as e:
            error = AuthError(
                code="AUTH_URL_ERROR",
                message="Failed to create authentication URL",
                details=str(e)
            )
            return AuthResult.failed(error)
    
    def handle_callback(self) -> AuthResult:
        """Handle OAuth callback with authorization code"""
        if not self.auth_enabled:
            # Already handled in initiate_login for local mode
            return AuthResult.success(self.get_current_session())
        
        # Check if we have an authorization code
        code = self.session_repository.get_query_param("code")
        if not code:
            error = AuthError(
                code="NO_AUTH_CODE",
                message="No authorization code received",
                details="OAuth callback missing 'code' parameter"
            )
            return AuthResult.failed(error)
        
        try:
            # Exchange code for credentials
            credentials = self.auth_repository.exchange_code_for_credentials(
                code=code,
                redirect_uri=self.redirect_uri
            )
            
            # Get user information
            user = self.auth_repository.get_user_info(credentials)
            
            # Create and save session
            session = AuthSession(user=user, credentials=credentials)
            self.session_repository.save_session(session)
            
            # Clear query parameters to prevent reuse
            self.session_repository.clear_query_params()
            
            return AuthResult.success(session)
            
        except Exception as e:
            error = AuthError(
                code="CALLBACK_ERROR",
                message="Authentication callback failed",
                details=str(e)
            )
            return AuthResult.failed(error)
    
    def authenticate(self) -> AuthResult:
        """Main authentication flow controller"""
        # Check if already authenticated
        if self.is_authenticated():
            return AuthResult.success(self.get_current_session())
        
        # Check if we're in callback phase
        if self.session_repository.get_query_param("code"):
            return self.handle_callback()
        
        # Initiate login flow
        return self.initiate_login()
    
    def logout(self) -> AuthResult:
        """Logout current user"""
        if not self.auth_enabled:
            return AuthResult.success(AuthSession.create_local_session())
        
        try:
            self.session_repository.clear_session()
            return AuthResult(status=AuthStatus.SUCCESS)
        except Exception as e:
            error = AuthError(
                code="LOGOUT_ERROR",
                message="Failed to logout",
                details=str(e)
            )
            return AuthResult.failed(error)
    
    def get_user_info(self) -> Optional[User]:
        """Get current user information"""
        session = self.get_current_session()
        return session.user if session else None
