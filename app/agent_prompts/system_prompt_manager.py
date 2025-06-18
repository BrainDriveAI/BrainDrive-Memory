"""
System Prompt Manager for BrainDrive Agent Modes.
"""
from app.config.app_env import app_env
from app.agent_prompts.interviewer_prompt import system_prompt_interviewer
from app.agent_prompts.default_prompt import system_prompt_memory
from app.utils.get_current_date import get_current_datetime_cranford

class SystemPromptManager:
    """Manages system prompts for different agent modes."""
    
    @staticmethod
    def get_memory_agent_prompt() -> str:
        """Returns the system prompt for the Memory Agent."""
        agent_system_prompt = f"""
            {system_prompt_memory}
            ---
            Current date and time: {get_current_datetime_cranford()}
            ---
            Refer to the user as: {app_env.APP_USERNAME.capitalize()}
        """
        return agent_system_prompt
    @staticmethod
    def get_interviewer_agent_prompt() -> str:
        """Returns the system prompt for the Interviewer Agent."""
        agent_system_prompt = f"""
            {system_prompt_interviewer}
            ---
            Current date and time: {get_current_datetime_cranford()}
            ---
            Refer to the user as: {app_env.APP_USERNAME.capitalize()}
        """
        return agent_system_prompt
    @staticmethod
    def get_system_prompt() -> str:
        """
        Returns the appropriate system prompt based on the current agent mode.
            
        Returns:
            str: The system prompt for the current agent mode
        """
        if app_env.is_interviewer_mode:
            return SystemPromptManager.get_interviewer_agent_prompt()
        else:
            # Default to memory mode
            return SystemPromptManager.get_memory_agent_prompt()
    
    @staticmethod
    def get_agent_mode_info() -> dict:
        """Returns information about the current agent mode."""
        return {
            "mode": app_env.AGENT_MODE,
            "is_interviewer": app_env.is_interviewer_mode,
            "is_memory": app_env.is_memory_mode,
            "description": (
                "Onboarding Interviewer Agent - Conducts initial user interview to build knowledge base"
                if app_env.is_interviewer_mode
                else "Memory Agent - Provides personalized assistance using stored knowledge"
            )
        }
