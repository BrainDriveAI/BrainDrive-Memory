"""
Memory AI Agent - Streamlit Chat Application
A Streamlit-based chat interface for interacting with an AI agent with memory capabilities.
"""

import os
from dotenv import load_dotenv
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from app.services.document_processing_service import parseAndIngestPDFs
from app.config.app_env import app_env
from app.services.auth_service import authenticate, display_user_info
from app.agents.react_graph_agent import invoke_our_graph
from app.presentation.web.streamlit.streamlit_langraph_callback import get_streamlit_cb
from app.config.validator import validate_configuration, ConfigError

# Load environment variables
load_dotenv()


def render_chat_ui():
    """
    Render the main chat UI interface with file upload capabilities.
    Handles authentication and manages the chat session.
    """
    # Attempt full validation
    try:
        validate_configuration()
    except ConfigError as err:
        st.set_page_config(page_title="Configuration Issues", layout="wide")
        st.title("🚨 Configuration Issues Detected")
        for issue in err.issues:
            with st.expander(issue["message"], expanded=True):
                st.write("**Details:**", issue["details"])
                st.write("**How to fix:**", issue["fix"])
        st.stop()

    configure_page_header()

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
    
    # File uploader for PDF ingestion
    handle_file_upload()
    
    # Chat interface
    display_chat_messages()
    
    # Process user input
    process_user_input()


def configure_page_header():
    if app_env.is_interviewer_mode:
        # Configure page layout
        st.set_page_config(page_title="BrainDrive Interviewer AI Agent", layout="wide")
        # Chat UI header
        st.title("Welcome to BrainDrive! I'm your Onboarding Interviewer Agent.")
        st.markdown("#### Let's get to know you so your AI assistant can be personalized from day one.")
    else:
        # Configure page layout
        st.set_page_config(page_title="BrainDrive Memory AI Agent", layout="wide")
        # Chat UI header
        st.title("Chat with Your Memory AI Agent")
        st.markdown(f"#### Hello {app_env.APP_USERNAME.capitalize()}! I'm your Digital Brain Agent, ready to assist you with personalized responses.")


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
    """Handle PDF file uploads and processing with proper validation."""
    # Safety check - this function should only be called when file upload is enabled
    if not app_env.ENABLE_FILE_UPLOAD:
        return
    
    # Validate required configuration at the start
    validation_errors = []
    
    if not app_env.GCS_BUCKET_NAME:
        validation_errors.append("GCS_BUCKET_NAME is not configured")
    
    if not app_env.LLM_SHERPA_API_URL:
        validation_errors.append("LLM_SHERPA_API_URL is not configured")
    
    # Check Neo4j configuration (required for document ingestion)
    neo4j_missing = []
    if not app_env.NEO4J_URL:
        neo4j_missing.append("NEO4J_URL")
    if not app_env.NEO4J_USER:
        neo4j_missing.append("NEO4J_USER")
    if not app_env.NEO4J_PWD:
        neo4j_missing.append("NEO4J_PWD")
    
    if neo4j_missing:
        validation_errors.append(f"Neo4j configuration missing: {', '.join(neo4j_missing)}")
    
    # Display validation errors if any
    if validation_errors:
        st.error("❌ **File Upload Configuration Issues:**")
        for error in validation_errors:
            st.error(f"• {error}")
        
        with st.expander("📋 **How to Fix These Issues**", expanded=True):
            st.markdown("""
            **Required Environment Variables for File Upload:**
            
            Add these to your `.env` file:
            ```env
            # File Upload Configuration
            ENABLE_FILE_UPLOAD=true
            GCS_BUCKET_NAME=your-gcs-bucket-name
            LLM_SHERPA_API_URL=http://localhost:5010/api/parseDocument?renderFormat=all
            
            # Neo4j Database (required for document storage)
            NEO4J_URL=neo4j+s://your-neo4j-instance.databases.neo4j.io
            NEO4J_USER=neo4j
            NEO4J_PWD=your-neo4j-password
            ```
            
            **Setup Steps:**
            1. **Google Cloud Storage:** Create a GCS bucket and configure authentication
            2. **LLM Sherpa:** Set up the LLM Sherpa API server (Docker or local installation)
            3. **Neo4j:** Create a Neo4j database instance (AuraDB or self-hosted)
            4. **Restart** the application after updating your `.env` file
            
            **Quick Start with Docker:**
            ```bash
            # Start LLM Sherpa API server
            docker run -p 5010:5010 nlmatics/llmsherpa:latest
            ```
            """)
        return
    
    # Show current configuration status in sidebar
    with st.sidebar:
        st.markdown("### ⚙️ File Upload Config")
        st.success("✅ All services configured")

    # All validations passed - show the file uploader
    uploaded_file = st.file_uploader(
        "📄 Upload a PDF file", 
        type=["pdf"], 
        key="file_uploader",
        disabled=st.session_state.is_processing_pdf,
        help="Upload PDF documents to chat with their content using AI"
    )
    
    if uploaded_file is not None:
        # Prevent multiple simultaneous uploads
        if st.session_state.is_processing_pdf:
            st.warning("⏳ Please wait for the current file to finish processing...")
            return
            
        st.session_state.is_processing_pdf = True
        
        # Display file information
        file_size_mb = len(uploaded_file.getbuffer()) / (1024 * 1024)
        st.info(f"📄 **File:** {uploaded_file.name} ({file_size_mb:.1f} MB)")
        
        # Create temporary directory for file processing
        temp_dir = "../../../temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Processing status with progress
        processing_container = st.container()
        
        with processing_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Save file
                status_text.info("💾 Saving uploaded file...")
                progress_bar.progress(20)
                
                with open(temp_file_path, "wb") as file:
                    file.write(uploaded_file.getbuffer())
                
                # Step 2: Upload to GCS
                status_text.info("☁️ Uploading to Google Cloud Storage...")
                progress_bar.progress(40)
                
                # Step 3: Process with LLM Sherpa and ingest to Neo4j
                status_text.info("🔍 Processing PDF content and structure...")
                progress_bar.progress(60)
                
                file_info = parseAndIngestPDFs(
                    temp_file_path, 
                    uploaded_file.name, 
                    app_env.GCS_BUCKET_NAME
                )
                
                # Step 4: Complete
                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()
                
                # Success message
                st.success("🎉 **File processed successfully!**")
                
                # Display processing results
                with st.expander("📊 **Processing Results**", expanded=True):
                    if file_info:
                        st.json(file_info)
                    else:
                        st.info("File processed and stored in the knowledge base. You can now ask questions about this document!")
                
                # Show next steps
                st.info("💬 **Next Steps:** Use the chat below to ask questions about your uploaded document!")
                
            except Exception as error:
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Show detailed error information
                st.error("❌ **Error processing file:**")
                
                error_message = str(error)
                if "LLM Sherpa" in error_message or "5010" in error_message:
                    st.error("🔧 **LLM Sherpa API Error:** Please ensure the LLM Sherpa server is running")
                    with st.expander("🆘 **Troubleshooting LLM Sherpa**"):
                        st.markdown("""
                        **Start LLM Sherpa server:**
                        ```bash
                        docker run -p 5010:5010 nlmatics/llmsherpa:latest
                        ```
                        
                        **Or check if it's running:**
                        ```bash
                        curl http://localhost:5010/api/parseDocument
                        ```
                        """)
                elif "GCS" in error_message or "Google Cloud" in error_message:
                    st.error("☁️ **Google Cloud Storage Error:** Please check your GCS configuration and permissions")
                elif "Neo4j" in error_message:
                    st.error("🗄️ **Neo4j Database Error:** Please check your Neo4j connection and credentials")
                else:
                    st.error(f"**Error details:** {error_message}")
                
                # Log the full error for debugging
                import logging
                logging.error(f"File processing error for {uploaded_file.name}: {error}", exc_info=True)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except Exception as cleanup_error:
                        logging.warning(f"Failed to clean up temp file {temp_file_path}: {cleanup_error}")
                
                # Reset processing state
                st.session_state.is_processing_pdf = False
                
                # Clear the uploaded file from session to allow re-upload
                if 'uploaded_file' in st.session_state:
                    del st.session_state.uploaded_file

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
