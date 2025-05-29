from typing import List
import streamlit as st
from app.domain.interfaces.ui_adapter import UIAdapter
from app.domain.models.auth_result import AuthError

class StreamlitUIAdapter(UIAdapter):
    """Streamlit-specific UI operations"""
    
    def display_error(self, error: AuthError) -> None:
        """Display single error message"""
        st.error(f"❌ **{error.message}**")
        if error.details:
            st.error(f"Details: {error.details}")
    
    def display_errors(self, errors: List[AuthError]) -> None:
        """Display multiple errors"""
        for error in errors:
            self.display_error(error)
    
    def redirect(self, url: str) -> None:
        """Redirect to URL - in Streamlit, we show the login page with redirect button"""
        st.markdown(f"""
        # Welcome to Memory AI Agent
        
        Please sign in with your Google account to continue.
        
        <a href="{url}" target="_self" class="button">
            <div style="
                display: inline-flex;
                align-items: center;
                background-color: #4285F4;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                text-decoration: none;
                font-weight: bold;
                cursor: pointer;
            ">
                <div style="
                    background-color: white;
                    border-radius: 2px;
                    padding: 10px;
                    margin-right: 10px;
                ">
                    <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg">
                        <g fill="#000" fill-rule="evenodd">
                            <path d="M9 3.48c1.69 0 2.83.73 3.48 1.34l2.54-2.48C13.46.89 11.43 0 9 0 5.48 0 2.44 2.02.96 4.96l2.91 2.26C4.6 5.05 6.62 3.48 9 3.48z" fill="#EA4335"></path>
                            <path d="M17.64 9.2c0-.74-.06-1.28-.19-1.84H9v3.34h4.96c-.1.83-.64 2.08-1.84 2.92l2.84 2.2c1.7-1.57 2.68-3.88 2.68-6.62z" fill="#4285F4"></path>
                            <path d="M3.88 10.78A5.54 5.54 0 0 1 3.58 9c0-.62.11-1.22.29-1.78L.96 4.96A9.008 9.008 0 0 0 0 9c0 1.45.35 2.82.96 4.04l2.92-2.26z" fill="#FBBC05"></path>
                            <path d="M9 18c2.43 0 4.47-.8 5.96-2.18l2.84-2.2c-.76.53-1.78.9-3.12.9-2.38 0-4.4-1.57-5.12-3.74L.97 13.04C2.45 15.98 5.48 18 9 18z" fill="#34A853"></path>
                            <path fill="none" d="M0 0h18v18H0z"></path>
                        </g>
                    </svg>
                </div>
                Sign in with Google
            </div>
        </a>
        """, unsafe_allow_html=True)
    
    def trigger_refresh(self) -> None:
        """Trigger UI refresh/rerun"""
        st.rerun()
