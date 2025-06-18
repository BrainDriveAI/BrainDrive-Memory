from typing import List, Dict
from app.config.app_env import app_env


def validate_core_configuration() -> List[Dict[str, str]]:
    """
    Validate core configuration required for basic chat functionality.
    Returns a list of issue dicts; empty if valid.
    """
    issues: List[Dict[str, str]] = []

    # LLM provider-specific checks
    # At least one LLM provider must be configured
    provider = app_env.LLM_PROVIDER
    if provider == 'openai':
        if not app_env.OPENAI_API_KEY:
            issues.append({
                'message': "OpenAI provider selected but OPENAI_API_KEY is missing.",
                'details': "Set OPENAI_API_KEY in your .env.",
                'fix': "Add OPENAI_API_KEY to .env file."
            })
    elif provider == 'ollama':
        if not app_env.OLLAMA_LLM_MODEL:
            issues.append({
                'message': "Ollama provider selected but OLLAMA_LLM_MODEL is missing.",
                'details': "Set OLLAMA_LLM_MODEL in your .env.",
                'fix': "Add OLLAMA_LLM_MODEL to .env file."
            })
    elif provider == 'togetherai':
        missing = []
        if not app_env.TOGETHER_AI_API_KEY:
            missing.append('TOGETHER_AI_API_KEY')
        if not app_env.TOGETHER_AI_LLM_MODEL:
            missing.append('TOGETHER_AI_LLM_MODEL')
        if missing:
            issues.append({
                'message': f"TogetherAI provider selected but missing: {', '.join(missing)}.",
                'details': f"Missing: {', '.join(missing)}.",
                'fix': "Add the missing TogetherAI vars to your .env."
            })
    elif provider == 'openrouter':
        missing = []
        if not app_env.OPENROUTER_API_KEY:
            missing.append('OPENROUTER_API_KEY')
        if not app_env.OPENROUTER_LLM_MODEL:
            missing.append('OPENROUTER_LLM_MODEL')
        if missing:
            issues.append({
                'message': f"OpenRouter provider selected but missing: {', '.join(missing)}.",
                'details': f"Missing: {', '.join(missing)}.",
                'fix': "Add the missing OpenRouter vars to your .env."
            })
    elif provider == 'groq':
        missing = []
        if not app_env.GROQ_API_KEY:
            missing.append('GROQ_API_KEY')
        if not app_env.GROQ_LLM_MODEL:
            missing.append('GROQ_LLM_MODEL')
        if missing:
            issues.append({
                'message': f"Groq provider selected but missing: {', '.join(missing)}.",
                'details': f"Missing: {', '.join(missing)}.",
                'fix': "Add the missing Groq vars to your .env."
            })
    elif provider == 'cloud_run_gemma':
        if not app_env.GEMMA_SERVICE_URL or not app_env.GEMMA_API_KEY or not app_env.GEMMA_SERVICE_ACCOUNT_PATH:
            issues.append({
                'message': "Cloud Run Gemma provider selected but required configuration is missing.",
                'details': "Set GEMMA_SERVICE_URL, GEMMA_API_KEY, and GEMMA_SERVICE_ACCOUNT_PATH in your .env.",
                'fix': "Add GEMMA_SERVICE_URL, GEMMA_API_KEY, and GEMMA_SERVICE_ACCOUNT_PATH to .env file."
            })
    else:
        issues.append({
            'message': f"Unknown LLM provider '{provider}'.",
            'details': "Valid options are: openai, ollama, togetherai, openrouter, groq.",
            'fix': "Set LLM_PROVIDER to a supported provider."
        })

    # Neo4j must be configured for memory features
    missing_neo4j = [key for key in ("NEO4J_URL", "NEO4J_USER", "NEO4J_PWD") if not getattr(app_env, key)]
    if missing_neo4j:
        issues.append({
            "message": "Neo4j configuration incomplete.",
            "details": f"Missing: {', '.join(missing_neo4j)}.",
            "fix": "Configure NEO4J_URL, NEO4J_USER, and NEO4J_PWD in your .env file."
        })

    # Embedding provider checks:
    provider = app_env.EMBEDDING_PROVIDER
    if provider == 'openai':
        if not app_env.OPENAI_API_KEY or not app_env.OPENAI_EMBEDDING_MODEL:
            issues.append({
                'message': "OpenAI embedding provider selected but OPENAI_API_KEY or OPENAI_EMBEDDING_MODEL is missing.",
                'details': "Set OPENAI_API_KEY or OPENAI_EMBEDDING_MODEL in your .env.",
                'fix': "Add OPENAI_API_KEY or OPENAI_EMBEDDING_MODEL to .env file."
            })
    elif provider == 'pinecone':
        if not app_env.PINECONE_API_KEY or not app_env.PINECONE_EMBEDDING_MODEL:
            missing = []
            if not app_env.PINECONE_API_KEY:
                missing.append('PINECONE_API_KEY')
            if not app_env.PINECONE_EMBEDDING_MODEL:
                missing.append('PINECONE_EMBEDDING_MODEL')
            issues.append({
                'message': "Pinecone embedding provider selected but missing: " + ", ".join(missing),
                'details': f"Missing: {', '.join(missing)}.",
                'fix': "Add the missing Pinecone vars to your .env."
            })
    elif provider == 'ollama':
        if not app_env.OLLAMA_BASE_URL or not app_env.OLLAMA_EMBEDDING_MODEL:
            issues.append({
                'message': "Ollama embedding provider selected but OLLAMA_BASE_URL or OLLAMA_EMBEDDING_MODEL is missing.",
                'details': "Set OLLAMA_BASE_URL orOLLAMA_EMBEDDING_MODEL in your .env.",
                'fix': "Add OLLAMA_BASE_URL orOLLAMA_EMBEDDING_MODEL to .env file."
            })
    else:
        issues.append({
            'message': f"Unknown embedding provider '{provider}'.",
            'details': "Valid options are: openai, pinecone, ollama.",
            'fix': "Set EMBEDDING_PROVIDER to one of the valid options."
        })

    return issues
