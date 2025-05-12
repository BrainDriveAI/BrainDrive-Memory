import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv
from app.app_env import app_env

load_dotenv()

# Google OAuth configuration
# Now primarily sourced from app_env, which loads from .env or environment
CLIENT_CONFIG = {
    "web": {
        "client_id": app_env.GOOGLE_CLIENT_ID,
        "client_secret": app_env.GOOGLE_CLIENT_SECRET.get_secret_value() if app_env.GOOGLE_CLIENT_SECRET else None,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [str(app_env.REDIRECT_URI)] if app_env.REDIRECT_URI else ["http://localhost:8501/"],
    }
}

# Scopes define what information we want to access
SCOPES = ["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "openid"]


def create_flow():
    """Create and configure the OAuth flow"""
    flow = Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0]
    )
    return flow


def get_user_info(credentials):
    """Get user info from Google API using the provided credentials"""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        st.error(f"Error getting user info: {e}")
        return None


def is_authenticated():
    """Check if the user is authenticated"""
    return "credentials" in st.session_state


def authenticate():
    """Main authentication flow controller"""
    if "credentials" not in st.session_state:
        # Start OAuth flow
        flow = create_flow()
        
        # Check if we're in the callback phase with a code parameter
        if "code" in st.query_params:
            code = st.query_params["code"]
            
            try:
                # Exchange code for credentials
                flow.fetch_token(code=code)
                credentials = flow.credentials
                
                # Store credentials in session state
                st.session_state.credentials = credentials
                
                # Get user info
                user_info = get_user_info(credentials)
                if user_info:
                    st.session_state.user_info = user_info
                
                # Clear the URL parameters to avoid reusing the authentication code
                st.query_params.clear()
                st.rerun()
                
            except Exception as e:
                st.error(f"Authentication failed: {e}")
                return False
        else:
            # Generate authorization URL and redirect user
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            st.markdown(f"""
            # Welcome to Memory AI Agent
            
            Please sign in with your Google account to continue.
            
            <a href="{auth_url}" target="_self" class="button">
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
                                <path d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.84-2.2c-.76.53-1.78.9-3.12.9-2.38 0-4.4-1.57-5.12-3.74L.97 13.04C2.45 15.98 5.48 18 9 18z" fill="#34A853"></path>
                                <path fill="none" d="M0 0h18v18H0z"></path>
                            </g>
                        </svg>
                    </div>
                    Sign in with Google
                </div>
            </a>
            """, unsafe_allow_html=True)
            
            return False
    
    return True


def logout_user():
    """Function that actually does the logout operation"""
    for key in list(st.session_state.keys()):
        if key in ['credentials', 'user_info']:
            del st.session_state[key]
    
    # Set a flag to trigger a rerun after the callback completes
    st.session_state.do_rerun = True


def display_user_info():
    """Display user information and logout button"""
    # Check if we need to rerun (from a previous logout action)
    if st.session_state.get('do_rerun', False):
        # Clear the flag
        st.session_state.do_rerun = False
        st.rerun()
    
    if 'user_info' in st.session_state:
        user = st.session_state.user_info
        
        # Create a container for user info and logout button
        with st.sidebar:
            col1, col2 = st.columns([1, 3])
            
            # Display profile picture
            if 'picture' in user:
                col1.image(user['picture'], width=50)
            
            # Display name and email
            col2.write(f"**{user.get('name', 'User')}**")
            col2.write(f"{user.get('email', '')}")
            
            # Logout button - using the new logout_user function
            st.button("Logout", on_click=logout_user)
