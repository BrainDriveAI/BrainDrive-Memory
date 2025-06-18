import requests
import json
from typing import Any, Dict, List, Optional, Iterator, Union, Sequence
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.auth import default, impersonated_credentials
import google.auth.transport.requests
import os
from google.auth import default as google_default
from google.oauth2.service_account import IDTokenCredentials as SA_IDTokenCredentials
from google.oauth2 import id_token

class CloudRunGemmaLLM(BaseChatModel):
    """Custom LangChain Chat Model for Google Cloud Run hosted Gemma3 via Ollama with tool support."""
    
    service_url: str
    api_key: str = ""  # Not needed for OIDC auth but kept for compatibility
    service_account_path: Optional[str] = None
    model_name: str = "gemma-3-27b-it"
    temperature: float = 0.7
    max_tokens: int = 2048
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    @property
    def _llm_type(self) -> str:
        return "cloudrun_gemma_chat"
    
    def _get_id_token(self) -> str:
        """
        Get an OIDC ID token for calling a Cloud Run service.

        If `service_account_path` is provided and points at a valid JSON, we build
        an IDTokenCredentials directly from that file. Otherwise, fall back to ADC
        via `id_token.fetch_id_token(...)`.
        """
        # 1) If the user provided a service_account JSON key on disk:
        if self.service_account_path and os.path.exists(self.service_account_path):
            # This constructs a credential that can mint short‐lived ID tokens
            # for the given audience (i.e. your Cloud Run URL).
            sa_cred = SA_IDTokenCredentials.from_service_account_file(
                filename=self.service_account_path,
                target_audience=self.service_url,
            )
            # Refresh it so that .token is populated
            sa_cred.refresh(Request())
            return sa_cred.token

        # 2) Otherwise, try Application Default Credentials (gcloud ADC, GCE metadata, etc.)
        try:
            # This will return something like (credentials, project_id).
            adc_cred, _ = google_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            # If ADC includes an IDTokenCredentials subclass, you could do:
            if hasattr(adc_cred, "with_target_audience"):
                # e.g. if you’re on a GCE VM or Cloud Run with a service account attached.
                idt_cred = adc_cred.with_target_audience(self.service_url)
                idt_cred.refresh(Request())
                return idt_cred.token

            # Otherwise fall back to id_token.fetch_id_token(...)
            return id_token.fetch_id_token(Request(), self.service_url)

        except Exception as e:
            raise Exception(f"Failed to obtain ID token via ADC: {e}")
    
    def _convert_messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Convert LangChain messages to a single prompt string."""
        prompt_parts = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                prompt_parts.append(f"System: {message.content}")
            elif isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")
            elif isinstance(message, ToolMessage):
                prompt_parts.append(f"Tool Result: {message.content}")
        
        return "\n\n".join(prompt_parts)
    
    def _format_tools_in_prompt(self, tools: List[Dict[str, Any]], prompt: str) -> str:
        """Format tools into the prompt for the model to understand."""
        if not tools:
            return prompt
        
        tools_description = "You have access to the following tools:\n\n"
        
        for tool in tools:
            function_info = tool.get('function', {})
            name = function_info.get('name', '')
            description = function_info.get('description', '')
            parameters = function_info.get('parameters', {})
            
            tools_description += f"Tool: {name}\n"
            tools_description += f"Description: {description}\n"
            
            if parameters.get('properties'):
                tools_description += "Parameters:\n"
                for param_name, param_info in parameters['properties'].items():
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '')
                    required = param_name in parameters.get('required', [])
                    tools_description += f"  - {param_name} ({param_type}{'*' if required else ''}): {param_desc}\n"
            
            tools_description += "\n"
        
        tools_description += """To use a tool, respond with a JSON object in this format:
        {
            "tool_calls": [
                {
                    "name": "tool_name",
                    "arguments": {
                        "param1": "value1",
                        "param2": "value2"
                    }
                }
            ]
        }
        If you don't need to use any tools, respond normally with your answer.
        """
        
        return tools_description + "\n" + prompt
    
    def _parse_tool_calls(self, response_text: str) -> tuple[str, List[Dict[str, Any]]]:
        """Parse tool calls from the model response."""
        tool_calls = []
        clean_response = response_text
        
        try:
            # Look for JSON objects that might contain tool calls
            import re
            json_pattern = r'\{[^{}]*"tool_calls"[^{}]*\[[^\]]*\][^{}]*\}'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if 'tool_calls' in parsed:
                        tool_calls.extend(parsed['tool_calls'])
                        # Remove the JSON from the response
                        clean_response = clean_response.replace(match, '').strip()
                except json.JSONDecodeError:
                    continue
                    
        except Exception:
            pass
        
        return clean_response, tool_calls
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response."""
        return self._generate_with_tools(messages, stop, run_manager, **kwargs)
    
    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], type, BaseTool]],
        **kwargs: Any,
    ) -> "CloudRunGemmaLLM":
        """Bind tools to the model."""
        # Convert tools to OpenAI format
        formatted_tools = []
        for tool in tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                # It's a LangChain tool
                formatted_tools.append(convert_to_openai_tool(tool))
            elif isinstance(tool, dict):
                formatted_tools.append(tool)
            else:
                # Try to convert other tool types
                try:
                    formatted_tools.append(convert_to_openai_tool(tool))
                except Exception:
                    continue
        
        # Create a new instance with tools bound
        bound_model = self.__class__(
            service_url=self.service_url,
            api_key=self.api_key,
            service_account_path=self.service_account_path,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs
        )
        
        # Store tools for use in generation
        bound_model._bound_tools = formatted_tools
        return bound_model
    
    def _generate_with_tools(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response with bound tools support."""
        
        # Use bound tools if available
        tools = getattr(self, '_bound_tools', kwargs.get('tools', []))
        
        # Get OIDC identity token (not OAuth2 access token!)
        id_token = self._get_id_token()
        
        # Prepare headers with OIDC token
        headers = {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json"
        }
        
        # Only add API key header if it's provided and not empty
        if self.api_key and self.api_key.strip():
            headers["X-API-Key"] = self.api_key
        
        # Convert messages to prompt
        prompt = self._convert_messages_to_prompt(messages)
        
        # Add tools information if available
        if tools:
            prompt = self._format_tools_in_prompt(tools, prompt)
        
        # Prepare Ollama API payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        
        if stop:
            payload["options"]["stop"] = stop
        
        try:
            # Make request to Cloud Run service
            response = requests.post(
                f"{self.service_url}/api/generate",
                headers=headers,
                json=payload,
                timeout=600
            )
            
            # Debug information
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response text: {response.text}")
            
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            response_text = result.get("response", "")
            
            # Parse tool calls if present
            clean_response, tool_calls = self._parse_tool_calls(response_text)
            
            # Create AI message
            ai_message = AIMessage(
                content=clean_response,
                additional_kwargs={
                    "tool_calls": tool_calls if tool_calls else None
                }
            )
            
            generation = ChatGeneration(message=ai_message)
            return ChatResult(generations=[generation])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Cloud Run Gemma service: {str(e)}")


# Factory function to create the LLM instance
def create_cloudrun_gemma_llm(
    service_url: str,
    api_key: str = "",
    service_account_path: Optional[str] = None,
    model_name: str = "gemma-3-27b-it",
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> CloudRunGemmaLLM:
    """
    Factory function to create CloudRunGemmaLLM instance with proper configuration.
    
    Args:
        service_url: Your Cloud Run service URL
        api_key: API key (if required by your service)
        service_account_path: Path to service account JSON file
        model_name: Name of the Gemma model
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
    
    Returns:
        Configured CloudRunGemmaLLM instance
    """
    return CloudRunGemmaLLM(
        service_url=service_url,
        api_key=api_key,
        service_account_path=service_account_path,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens
    )
