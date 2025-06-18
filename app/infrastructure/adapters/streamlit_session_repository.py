from typing import Optional
import streamlit as st
from app.domain.interfaces.session_repository import SessionRepository
from app.domain.models.auth import AuthSession

class StreamlitSessionRepository(SessionRepository):
    """Streamlit-specific session management"""
    
    def get_session(self) -> Optional[AuthSession]:
        """Get current session from Streamlit session state"""
        if 'auth_session' in st.session_state:
            return st.session_state.auth_session
        return None
    
    def save_session(self, session: AuthSession) -> None:
        """Save session to Streamlit session state"""
        st.session_state.auth_session = session
        # Also save user_info for backward compatibility
        st.session_state.user_info = {
            "name": session.user.name,
            "email": session.user.email,
            "picture": session.user.picture
        }
        if session.credentials:
            st.session_state.credentials = session.credentials.raw_credentials
    
    def clear_session(self) -> None:
        """Clear current session from Streamlit session state"""
        keys_to_remove = ['auth_session', 'user_info', 'credentials']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_query_param(self, key: str) -> Optional[str]:
        """Get query parameter from Streamlit"""
        if key in st.query_params:
            return st.query_params[key]
        return None
    
    def clear_query_params(self) -> None:
        """Clear query parameters in Streamlit"""
        st.query_params.clear()
