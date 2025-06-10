import re
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from app.presentation.web.streamlit.streamlit_langraph_callback import get_streamlit_cb
from app.agents.react_graph_agent import invoke_our_graph


def extract_thinking_and_response(content):
    """
    Extract thinking process and main response from AI message content.
    
    Args:
        content (str): The full AI message content
        
    Returns:
        tuple: (thinking_process, main_response)
    """
    # Pattern to match <think>...</think> tags
    think_pattern = r'<think>(.*?)</think>'
    
    # Find thinking process
    think_match = re.search(think_pattern, content, re.DOTALL)
    
    if think_match:
        thinking_process = think_match.group(1).strip()
        # Remove the thinking process from the main content
        main_response = re.sub(think_pattern, '', content, flags=re.DOTALL).strip()
        return thinking_process, main_response
    else:
        # No thinking process found
        return None, content


def display_chat_messages():
    """Display all messages in the chat history with thinking process hidden in dropdown."""
    for message in st.session_state.messages:
        if isinstance(message, AIMessage):
            # Extract thinking process and main response
            thinking_process, main_response = extract_thinking_and_response(message.content)
            
            with st.chat_message("assistant"):
                # Display thinking process in a collapsible section if it exists
                if thinking_process:
                    with st.expander("🤔 Thinking process", expanded=False):
                        st.markdown(f"<div style='color: #666; font-style: italic;'>{thinking_process}</div>", 
                                  unsafe_allow_html=True)
                
                # Display the main response
                st.write(main_response)
                
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
            
            # Set up streaming callback
            streaming_callback = get_streamlit_cb(st.container())
            
            # Get response from agent
            response = invoke_our_graph(chat_history, [streaming_callback])
            
            # Extract and display the AI's response
            ai_response = response["messages"][-1].content
            
            # Extract thinking process and main response
            thinking_process, main_response = extract_thinking_and_response(ai_response)
            
            # Display thinking process in a collapsible section if it exists
            if thinking_process:
                with st.expander("🤔 Thinking process", expanded=False):
                    st.markdown(f"<div style='color: #666; font-style: italic;'>{thinking_process}</div>", 
                              unsafe_allow_html=True)
            
            # Display the main response
            st.write(main_response)
            
            # Add the full response to chat history (including thinking process)
            st.session_state.messages.append(AIMessage(content=ai_response))
