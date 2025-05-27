"""
Memory AI Agent - Streamlit Chat Application
A Streamlit-based chat interface for interacting with an AI agent with memory capabilities.
"""

import os
from dotenv import load_dotenv
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from app.services.document_processing_service import parseAndIngestPDFs
from app.app_env import app_env
from app.services.auth_service import authenticate, display_user_info
from app.agents.react_graph_agent import invoke_our_graph
from app.presentation.web.streamlit.streamlit_langraph_callback import get_streamlit_cb

# Load environment variables
load_dotenv()


def render_chat_ui():
    """
    Render the main chat UI interface with file upload capabilities.
    Handles authentication and manages the chat session.
    """
    # Configure page layout
    st.set_page_config(page_title="BrainDrive Memory AI Agent", layout="wide")

    # Hides "Deploy" button
    hide_deploy_button()
    
    # Initialize session state variables
    if 'is_processing_pdf' not in st.session_state:
        st.session_state.is_processing_pdf = False
    
    if 'messages' not in st.session_state:
        st.session_state.messages = [AIMessage(content="How can I help you?")]
    
    if 'expander_open' not in st.session_state:
        st.session_state.expander_open = True

    # Authentication check (will pass through if AUTH_ENABLED is False)
    if not authenticate():
        # If not authenticated, authenticate function will display login page
        return
    
    # Display user information if authenticated
    display_user_info()
    
    # Chat UI header
    st.title("Chat with Your Memory AI Agent")
    st.markdown("#### Your assistant for personalized, meaningful conversations.")
    
    # File uploader for PDF ingestion
    handle_file_upload()
    
    # Chat interface
    display_chat_messages()
    
    # Process user input
    process_user_input()


def hide_deploy_button():
    """Hide the Streamlit deploy button."""
    # Hide the "Deploy" button
    hide_deploy_button_style = """
        <style>
            /* Hide the "Deploy" button */
            .stAppDeployButton {
                display: none !important;
            }
            /* Optional: If you want to remove the entire header menu */
            #MainMenu {
                visibility: hidden;
            }
            footer {
                visibility: hidden;
            }
        </style>
    """
    st.markdown(hide_deploy_button_style, unsafe_allow_html=True)


def handle_file_upload():
    """Handle PDF file uploads and processing."""
    uploaded_file = st.file_uploader(
        "Upload a PDF file", 
        type=["pdf"], 
        key="file_uploader",
        disabled=st.session_state.is_processing_pdf
    )
    
    if uploaded_file is not None:
        st.session_state.is_processing_pdf = True
        
        # Create temporary directory for file processing
        temp_dir = "../../../temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as file:
            file.write(uploaded_file.getbuffer())
        
        # Process the PDF
        processing_status = st.empty()
        processing_status.info("Processing uploaded file...")
        
        try:
            file_info = parseAndIngestPDFs(temp_file_path, uploaded_file.name, app_env.GCS_BUCKET_NAME)
            processing_status.empty()
            st.success("File uploaded and processed successfully!")
            st.write("File Information:", file_info)
        except Exception as error:
            processing_status.empty()
            st.error(f"Error processing file: {error}")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            # Reset processing state
            st.session_state.is_processing_pdf = False
            st.session_state.uploaded_file = None


def display_chat_messages():
    """Display all messages in the chat history."""
    for message in st.session_state.messages:
        if isinstance(message, AIMessage):
            st.chat_message("assistant").write(message.content)
        elif isinstance(message, HumanMessage):
            st.chat_message("user").write(message.content)


def process_user_input():
    """Process user input and generate AI response."""
    # Disable chat input during file processing
    user_message = st.chat_input(
        "Type your message here...", 
        disabled=st.session_state.is_processing_pdf
    )
    
    if user_message:
        # Close any open expanders when user starts typing
        st.session_state.expander_open = False
        
        # Add user message to chat history
        st.session_state.messages.append(HumanMessage(content=user_message))
        st.chat_message("user").write(user_message)
        
        # Generate and display AI response
        with st.chat_message("assistant"):
            chat_history = st.session_state.messages
            response_placeholder = st.empty()
            
            # Set up streaming callback
            streaming_callback = get_streamlit_cb(st.container())
            
            # Get response from agent
            response = invoke_our_graph(chat_history, [streaming_callback])
            
            # Extract and display the AI's response
            ai_response = response["messages"][-1].content
            st.session_state.messages.append(AIMessage(content=ai_response))
            response_placeholder.write(ai_response)
