from app.config.app_env import app_env

def get_llm():
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

    if provider == 'ollama':
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=app_env.OLLAMA_LLM_MODEL,
            base_url=str(app_env.OLLAMA_BASE_URL) if app_env.OLLAMA_BASE_URL else None
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
