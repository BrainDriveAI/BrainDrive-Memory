"""
Streamlit component for displaying LLM health status.
UI layer component that displays health information in the sidebar.
"""
import streamlit as st
import asyncio
from typing import Optional
from datetime import datetime
from app.services.llm_health_service import LLMHealthResult, LLMStatus


class LLMHealthDisplay:
    """
    Streamlit component for displaying LLM connectivity status.
    Handles UI rendering and user interactions for health checking.
    """
    
    def __init__(self, health_use_case):
        self.health_use_case = health_use_case
    
    def display_health_status(self, container=None):
        """
        Display LLM health status in sidebar or specified container.
        
        Args:
            container: Streamlit container to display in (defaults to sidebar)
        """
        display_container = container or st.sidebar
        
        with display_container:
            st.markdown("### 🤖 LLM Status")
            
            # Initialize health status in session state if not exists
            if 'llm_health_status' not in st.session_state:
                st.session_state.llm_health_status = None
                st.session_state.health_check_in_progress = False
            
            # Get cached status first for immediate display
            cached_status = self.health_use_case.get_cached_status()
            current_status = st.session_state.llm_health_status or cached_status
            
            # Display current status
            if current_status:
                self._render_health_status(current_status)
            else:
                self._render_unknown_status()
            
            # Health check controls
            self._render_health_controls()
            
            # Auto-check on first load
            if not st.session_state.llm_health_status and not st.session_state.health_check_in_progress:
                self._trigger_health_check(force_refresh=False, show_progress=False)
    
    def _render_health_status(self, status: LLMHealthResult):
        """Render the health status information"""
        # Status indicator
        status_col, refresh_col = st.columns([3, 1])
        
        with status_col:
            st.markdown(f"**{status.status_display}**")
            st.caption(f"**Model:** {status.model_name}")
            st.caption(f"**Provider:** {status.provider.title()}")
        
        # Response time and last check info
        if status.response_time_ms:
            st.caption(f"⚡ Response: {status.response_time_ms:.0f}ms")
        
        st.caption(f"🕒 Last checked: {self._format_time_ago(status.last_checked)}")
        
        # Error details if unhealthy
        if status.status == LLMStatus.UNHEALTHY and status.error_message:
            with st.expander("❌ Error Details", expanded=False):
                st.error(status.error_message)
                if "api key" in status.error_message.lower():
                    st.info("💡 **Tip:** Check your API key configuration in the .env file")
                elif "timeout" in status.error_message.lower():
                    st.info("💡 **Tip:** The LLM service might be slow or unreachable")
                elif "credits" in status.error_message.lower() or "quota" in status.error_message.lower():
                    st.info("💡 **Tip:** You may have exceeded your API quota or credits")
    
    def _render_unknown_status(self):
        """Render status when health is unknown"""
        st.markdown("**⚪ Status Unknown**")
        st.caption("Click 'Check Now' to test connectivity")
    
    def _render_health_controls(self):
        """Render health check control buttons"""
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button(
                "🔄 Check Now", 
                key="health_check_now",
                disabled=st.session_state.health_check_in_progress,
                help="Test LLM connectivity now"
            ):
                self._trigger_health_check(force_refresh=True, show_progress=True)
        
        with col2:
            if st.button(
                "📊 Details", 
                key="health_details",
                help="Show detailed health information"
            ):
                self._show_detailed_health_info()
    
    def _trigger_health_check(self, force_refresh: bool = False, show_progress: bool = True):
        """Trigger health check with optional progress indication"""
        if st.session_state.health_check_in_progress:
            return
        
        try:
            st.session_state.health_check_in_progress = True
            
            if show_progress:
                progress_placeholder = st.sidebar.empty()
                with progress_placeholder:
                    st.info("🔄 Checking LLM connectivity...")
            
            # Run async health check
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.health_use_case.execute(force_refresh=force_refresh)
                )
                st.session_state.llm_health_status = result
                
                if show_progress:
                    if result.is_healthy:
                        st.sidebar.success("✅ LLM is healthy!")
                    else:
                        st.sidebar.error("❌ LLM connectivity issue detected")
                        
            finally:
                loop.close()
                
        except Exception as e:
            st.sidebar.error(f"Health check failed: {str(e)}")
        finally:
            st.session_state.health_check_in_progress = False
            if show_progress:
                # Clear progress message after a delay
                st.sidebar.empty()
    
    def _show_detailed_health_info(self):
        """Show detailed health information in a modal/expander"""
        status = st.session_state.llm_health_status
        if not status:
            st.sidebar.info("No health data available. Run a health check first.")
            return
        
        with st.sidebar.expander("📊 Detailed Health Info", expanded=True):
            st.json({
                "provider": status.provider,
                "model": status.model_name,
                "status": status.status.value,
                "response_time_ms": status.response_time_ms,
                "last_checked": status.last_checked.isoformat(),
                "test_prompt": status.test_prompt_used,
                "error": status.error_message
            })
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as 'time ago' string"""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.total_seconds() < 60:
            return f"{int(diff.total_seconds())}s ago"
        elif diff.total_seconds() < 3600:
            return f"{int(diff.total_seconds() / 60)}m ago"
        else:
            return f"{int(diff.total_seconds() / 3600)}h ago"
