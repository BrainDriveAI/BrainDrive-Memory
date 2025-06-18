from app.config.app_env import app_env

def get_llm():
    """
    Factory function to provide the appropriate LLM for chat-based operations.
    This will be used by LangGraph's create_react_agent.
    """

    provider = app_env.LLM_PROVIDER

    if provider == 'openai':
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            temperature=0,
            model=app_env.OPENAI_LLM_MODEL,
            openai_api_key=app_env.OPENAI_API_KEY.get_secret_value(),
            verbose=False,
            streaming=True
        )
    
    if provider == 'openrouter':
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            temperature=0,
            model="meta-llama/llama-3.3-8b-instruct:free",
            api_key=app_env.OPENROUTER_API_KEY.get_secret_value(),
            base_url=str(app_env.OPENROUTER_BASE_URL),
            verbose=False,
            streaming=True
        )

    if provider == 'ollama':
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=app_env.OLLAMA_LLM_MODEL,
            base_url=str(app_env.OLLAMA_BASE_URL) if app_env.OLLAMA_BASE_URL else None,
            temperature=0,
            verbose=False,
            streaming=True
        )
    
    # if provider == 'cloud_run_gemma':
    #     from app.adapters.custom_ollama_cloud_run import create_cloudrun_gemma_llm
    #     service_url = str(app_env.GEMMA_SERVICE_URL)
    #     # Remove any trailing slashes from service URL
    #     service_url = service_url.rstrip('/')
    #     return create_cloudrun_gemma_llm(
    #         service_url=service_url,
    #         api_key=app_env.GEMMA_API_KEY.get_secret_value(),
    #         service_account_path=app_env.GEMMA_SERVICE_ACCOUNT_PATH,
    #         model_name="gemma3:27b",
    #         temperature=0.7,
    #         max_tokens=1000
    #     )
    if provider == 'cloud_run_gemma':
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            temperature=0,
            model=app_env.GEMMA_LLM_MODEL,
            api_key=app_env.GEMMA_API_KEY.get_secret_value(),
            base_url=str(app_env.GEMMA_SERVICE_URL),
            openai_api_key=app_env.GEMMA_API_KEY.get_secret_value(),
            verbose=False,
            streaming=True
        )


    if provider == 'togetherai':
        from langchain_together import ChatTogether
        return ChatTogether(
            together_api_key=app_env.TOGETHER_AI_API_KEY.get_secret_value(),
            model=app_env.TOGETHER_AI_LLM_MODEL
        )

    if provider == 'openrouter':
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            temperature=0,
            model=app_env.OPENROUTER_LLM_MODEL,
            openai_api_key=app_env.OPENROUTER_API_KEY.get_secret_value() if app_env.OPENROUTER_API_KEY else None,
            base_url=str(app_env.OPENROUTER_BASE_URL),
            verbose=False,
            streaming=True
        )

    if provider == 'groq':
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=app_env.GROQ_LLM_MODEL,
            temperature=0,
            streaming=True,
            api_key=app_env.GROQ_API_KEY.get_secret_value() if app_env.GROQ_API_KEY else None
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")

search_llm_provider = get_llm()
