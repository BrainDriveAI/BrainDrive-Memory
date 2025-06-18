import streamlit as st
from app.domain.models.user import User, AuthProvider

class StreamlitUserDisplay:
    """Streamlit-specific user information display"""
    
    def __init__(self, auth_enabled: bool = True):
        self.auth_enabled = auth_enabled
    
    def display_user_info(self, user: User, on_logout_callback=None) -> None:
        """Display user information and logout button in sidebar"""
        with st.sidebar:
            col1, col2 = st.columns([1, 3])
            
            # Display profile picture or icon
            if user.picture and user.provider == AuthProvider.GOOGLE:
                col1.image(user.picture, width=50)
            elif user.provider == AuthProvider.GOOGLE:
                col1.write("👤")
            else:
                col1.write("🏠")  # Local user icon
            
            # Display name and email
            col2.write(f"**{user.name}**")
            
            if user.provider == AuthProvider.GOOGLE:
                col2.write(f"{user.email}")
            else:
                col2.write("Local Development")
            
            # Show logout button only when auth is enabled
            if self.auth_enabled and user.provider == AuthProvider.GOOGLE:
                if st.button("Logout"):
                    if on_logout_callback:
                        on_logout_callback()
            else:
                st.caption("Auth disabled - running locally")
