# app/infrastructure/repositories/google_auth_repository.py
from typing import Optional
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from app.domain.interfaces.auth_repository import AuthRepository
from app.domain.models.auth import AuthCredentials
from app.domain.models.user import User, AuthProvider

class GoogleAuthRepository(AuthRepository):
    """Google OAuth implementation"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile", 
            "openid"
        ]
        self.client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
    
    def _create_flow(self, redirect_uri: str) -> Flow:
        """Create OAuth flow"""
        config = self.client_config.copy()
        config["web"]["redirect_uris"] = [redirect_uri]
        
        return Flow.from_client_config(
            client_config=config,
            scopes=self.scopes,
            redirect_uri=redirect_uri
        )
    
    def create_auth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Create authentication URL for OAuth flow"""
        flow = self._create_flow(redirect_uri)
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return auth_url
    
    def exchange_code_for_credentials(self, code: str, redirect_uri: str) -> AuthCredentials:
        """Exchange authorization code for credentials"""
        flow = self._create_flow(redirect_uri)
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        return AuthCredentials(
            provider=AuthProvider.GOOGLE,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expires_in=credentials.expiry.timestamp() if credentials.expiry else None,
            raw_credentials=credentials
        )
    
    def get_user_info(self, credentials: AuthCredentials) -> User:
        """Get user information using credentials"""
        service = build('oauth2', 'v2', credentials=credentials.raw_credentials)
        user_info = service.userinfo().get().execute()
        
        return User(
            id=user_info.get('id'),
            name=user_info.get('name', ''),
            email=user_info.get('email', ''),
            picture=user_info.get('picture'),
            provider=AuthProvider.GOOGLE
        )
    
    def validate_credentials(self, credentials: AuthCredentials) -> bool:
        """Validate if credentials are still valid"""
        try:
            service = build('oauth2', 'v2', credentials=credentials.raw_credentials)
            service.userinfo().get().execute()
            return True
        except Exception:
            return False
