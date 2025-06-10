from typing import Callable, TypeVar, Dict, Any, Optional, List
import inspect
import re
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from streamlit.delta_generator import DeltaGenerator
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
import streamlit as st
from langchain_core.messages import AIMessage, ToolMessage

class EnhancedStreamlitCallbackHandler(BaseCallbackHandler):
    """
    Enhanced Streamlit callback handler that can hide/show thinking processes,
    tool calls, and intermediate steps in collapsible sections.
    """
    
    def __init__(self, parent_container: DeltaGenerator, show_thinking: bool = False):
        super().__init__()
        self.parent_container = parent_container
        self.show_thinking = show_thinking
        self.thinking_container = None
        self.main_response_container = None
        
        # Content tracking
        self.current_thinking_content = ""
        self.current_response = ""
        self.is_in_thinking_mode = False
        
        # Placeholders for updating content
        self.thinking_placeholder = None
        self.response_placeholder = None
        
        # Set up the layout
        self._setup_containers()
    
    def _setup_containers(self):
        """Set up containers for different types of content"""
        with self.parent_container:
            # Container for thinking process - only show if enabled
            if self.show_thinking:
                self.thinking_container = st.expander("🧠 Reasoning Process", expanded=True)
                with self.thinking_container:
                    self.thinking_placeholder = st.empty()
            
            # Container for main response
            self.main_response_container = st.container()
            with self.main_response_container:
                self.response_placeholder = st.empty()
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts generating"""
        if self.show_thinking and self.thinking_placeholder:
            self.thinking_placeholder.write("🤖 *Starting to generate response...*")
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when a tool starts executing"""
        if self.show_thinking and self.thinking_container:
            tool_name = serialized.get("name", "Unknown Tool")
            with self.thinking_container:
                st.write(f"🔧 **Using tool:** {tool_name}")
                st.code(f"Input: {input_str}")
    
    def on_tool_end(self, output: ToolMessage, **kwargs) -> None:
        """Called when a tool finishes executing"""
        print(f"Tool output: {output}")
        tool_output = output.content
        if self.show_thinking and self.thinking_container:
            with self.thinking_container:
                # Truncate long outputs
                display_output = tool_output[:300] + "..." if len(tool_output) > 300 else tool_output
                st.success(f"**Tool Result:** {display_output}")
    
    def on_tool_error(self, error: Exception, **kwargs) -> None:
        """Called when a tool encounters an error"""
        if self.show_thinking and self.thinking_container:
            with self.thinking_container:
                st.error(f"**Tool Error:** {str(error)}")
    
    def on_agent_action(self, action, **kwargs) -> None:
        """Called when agent decides on an action"""
        if self.show_thinking and self.thinking_container:
            with self.thinking_container:
                st.write(f"🤔 **Agent Action:** {action.tool}")
                if hasattr(action, 'log') and action.log:
                    st.write(f"**Reasoning:** {action.log}")
                st.code(f"Tool Input: {action.tool_input}")
    
    def on_agent_finish(self, finish, **kwargs) -> None:
        """Called when agent finishes reasoning"""
        if self.show_thinking and self.thinking_container:
            with self.thinking_container:
                st.write("✅ *Agent reasoning complete*")
    
    def on_llm_stream(self, token: str, **kwargs) -> None:
        """Called for each new token from LLM"""
        # Detect if we're entering/exiting thinking mode
        if '<think>' in token:
            self.is_in_thinking_mode = True
            # Remove the <think> tag from the token
            token = token.replace('<think>', '')
        elif '</think>' in token:
            # Remove the </think> tag and any content after it goes to response
            parts = token.split('</think>')
            if parts[0]:  # Add any content before </think> to thinking
                self.current_thinking_content += parts[0]
                self._update_thinking_display()
            
            self.is_in_thinking_mode = False
            
            # Any content after </think> goes to response
            if len(parts) > 1 and parts[1]:
                self.current_response += parts[1]
                self._update_response_display()
            return
        
        # Route token to appropriate handler
        if self.is_in_thinking_mode:
            self.current_thinking_content += token
            self._update_thinking_display()
        else:
            self.current_response += token
            self._update_response_display()
    
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Called when LLM finishes generating"""
        if self.show_thinking and self.thinking_placeholder:
            # Update thinking display one final time
            self._update_thinking_display()
            # Add completion message
            if self.thinking_container:
                with self.thinking_container:
                    st.write("🏁 *Response generation complete*")
    
    def _update_thinking_display(self):
        """Update the thinking process display"""
        if self.show_thinking and self.thinking_placeholder and self.current_thinking_content:
            # Clean up the thinking content
            clean_thinking = self.current_thinking_content.strip()
            if clean_thinking:
                content = f"""**💭 Current Thinking:**

{clean_thinking}"""
                self.thinking_placeholder.markdown(content)
    
    def _update_response_display(self):
        """Update the main response display"""
        if self.response_placeholder and self.current_response:
            # Clean up any remaining thinking tags from response
            clean_response = re.sub(r'</?think>', '', self.current_response).strip()
            if clean_response:
                self.response_placeholder.write(clean_response)


def get_streamlit_cb(parent_container: DeltaGenerator, show_thinking: bool = False) -> BaseCallbackHandler:
    """
    Creates an enhanced Streamlit callback handler that can hide/show thinking processes.
    
    Args:
        parent_container (DeltaGenerator): The Streamlit container where content will be rendered
        show_thinking (bool): Whether to show thinking process by default
    
    Returns:
        BaseCallbackHandler: Enhanced callback handler with thinking process control
    """
    fn_return_type = TypeVar('fn_return_type')
    
    def add_streamlit_context(fn: Callable[..., fn_return_type]) -> Callable[..., fn_return_type]:
        ctx = get_script_run_ctx()
        def wrapper(*args, **kwargs) -> fn_return_type:
            add_script_run_ctx(ctx=ctx)
            return fn(*args, **kwargs)
        return wrapper
    
    # Create enhanced callback handler
    st_cb = EnhancedStreamlitCallbackHandler(parent_container, show_thinking)
    
    # Add Streamlit context to all callback methods
    for method_name, method_func in inspect.getmembers(st_cb, predicate=inspect.ismethod):
        if method_name.startswith('on_'):
            setattr(st_cb, method_name, add_streamlit_context(method_func))
    
    return st_cb
