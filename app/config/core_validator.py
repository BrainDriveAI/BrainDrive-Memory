from typing import List, Dict
from app.config.app_env import app_env


def validate_core_configuration() -> List[Dict[str, str]]:
    """
    Validate core configuration required for basic chat functionality.
    Returns a list of issue dicts; empty if valid.
    """
    issues: List[Dict[str, str]] = []

    # At least one LLM provider must be configured
    providers = [
        name for name, api in [
            ("OpenAI", app_env.OPENAI_API_KEY),
            ("Groq", app_env.GROQ_API_KEY),
            ("OpenRouter", app_env.OPENROUTER_API_KEY),
            ("TogetherAI", app_env.TOGETHER_AI_API_KEY)
        ] if api is not None
    ]
    if not providers:
        issues.append({
            "message": "No LLM provider configured.",
            "details": "Set at least one of OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, or TOGETHER_AI_API_KEY.",
            "fix": "Add the missing API key(s) to your .env file."
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
        if not app_env.OLLAMA_API_BASE or not app_env.OLLAMA_EMBEDDING_MODEL:
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
