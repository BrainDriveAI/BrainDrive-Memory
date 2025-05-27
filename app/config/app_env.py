from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl, SecretStr, ValidationError
from typing import Optional
import sys
import logging

logger = logging.getLogger(__name__)


class CriticalConfigError(Exception):
    """Custom exception for critical configuration failures."""
    pass


class AppSettings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    Uses Pydantic for validation.
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False
    )

    # Application specific
    APP_USERNAME: str = Field(
        default="default_user",
        description="Default username for the application if no specific user context is available. "
                    "For multi-user scenarios, this may be overridden by the authenticated user ID."
    )

    # Feature toggles
    ENABLE_AUTH: Optional[bool] = Field(default=False, description="Enable Google OAuth authentication.")
    ENABLE_FILE_UPLOAD: Optional[bool] = Field(default=False, description="Enable PDF file upload and processing functionality.")

    # OpenAI
    OPENAI_API_KEY: SecretStr = Field(..., description="Your OpenAI API Key.")
    OPENAI_LLM_MODEL: str = Field(default="gpt-4.1", description="The OpenAI LLM model to be used.")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="The OpenAI embedding model to be used.")

    # Groq
    GROQ_API_KEY: Optional[SecretStr] = Field(default=None, description="Your Groq API Key.")
    GROQ_LLM_MODEL: Optional[str] = Field(default="llama3-70b-8192", description="The Groq LLM model to be used.")

    # Ollama
    OLLAMA_EMBEDDING_MODEL: Optional[str] = Field(default="mxbai-embed-large", description="The Ollama embedding model to be used.")
    # OLLAMA_BASE_URL: Optional[HttpUrl] = Field(default=None, description="Ollama base URL if self-hosted and not using the default.")

    # Pinecone
    PINECONE_API_KEY: Optional[SecretStr] = Field(default=None, description="Your Pinecone API Key.")
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None, description="The Pinecone environment name.")
    PINECONE_EMBEDDING_MODEL: Optional[str] = Field(default="multilingual-e5-large", description="The Pinecone embedding model (e.g., used by Langchain PineconeEmbeddings).")

    # Openrouter
    OPENROUTER_API_KEY: Optional[SecretStr] = Field(default=None, description="Your Openrouter API Key.")
    OPENROUTER_BASE_URL: Optional[HttpUrl] = Field(default="https://openrouter.ai/api/v1", description="The base URL for the Openrouter API.")
    OPENROUTER_LLM_MODEL: Optional[str] = Field(default="meta-llama/llama-3.1-405b-instruct:free", description="The Openrouter LLM model to be used.")

    # TogetherAI
    TOGETHER_AI_API_KEY: Optional[SecretStr] = Field(default=None, description="Your TogetherAI API Key.")
    TOGETHER_AI_LLM_MODEL: Optional[str] = Field(default="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo", description="The TogetherAI LLM model to be used.")

    # Neo4j
    NEO4J_URL: str = Field(..., description="The Neo4j connection URL (e.g., 'neo4j+s://xxxx.databases.neo4j.io').")
    NEO4J_USER: str = Field(..., description="The Neo4j username.")
    NEO4J_PWD: SecretStr = Field(..., description="The Neo4j password.")
    NEO4J_DATABASE: str = Field(default="neo4j", description="The Neo4j database name.")

    # PGVector / Supabase (using SUPABASE_ prefix for clarity)
    SUPABASE_URL: Optional[str] = Field(default=None, description="The Supabase connection URL (e.g., 'postgresql://user:pass@host:port/dbname').")
    SUPABASE_KEY: Optional[SecretStr] = Field(default=None, description="The Supabase service role key or anon key.")
    SUPABASE_VECTOR_COLLECTION_NAME: Optional[str] = Field(default="documents", description="The collection/table name for the vector store in Supabase.")
    SUPABASE_VECTOR_QUERY_FUNCTION_NAME: Optional[str] = Field(default="match_documents", description="The query function name in Supabase to search for documents.")

    # LLM Sherpa (only needed if file upload is enabled)
    LLM_SHERPA_API_URL: Optional[HttpUrl] = Field(default=None, description="The LLM sherpa API endpoint (e.g., 'http://localhost:5010/api/parseDocument?renderFormat=all').")

    # Google Cloud Storage (only needed if file upload is enabled)
    GCS_BUCKET_NAME: Optional[str] = Field(default=None, description="The Google Cloud Storage bucket name.")

    # Google OAuth (only needed if auth is enabled)
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, description="Your Google OAuth Client ID.")
    GOOGLE_CLIENT_SECRET: Optional[SecretStr] = Field(default=None, description="Your Google OAuth Client Secret.")
    REDIRECT_URI: Optional[HttpUrl] = Field(default=None, description="The Google OAuth Redirect URI configured in your Google Cloud Console.")

    # Vertex AI Search
    VERTEX_AI_PROJECT_ID: Optional[str] = Field(default=None, description="Your Google Cloud Project ID for Vertex AI services.")
    VERTEX_AI_LOCATION_ID: Optional[str] = Field(default=None, description="The Google Cloud location (region) for Vertex AI resources (e.g., 'us').")
    VERTEX_AI_SEARCH_ENGINE_ID: Optional[str] = Field(default=None, description="The ID of your Vertex AI Search engine.")
    VERTEX_AI_DATASTORE_ID: Optional[str] = Field(default=None, description="The ID of your Vertex AI Search datastore.")


# Instantiate settings. This will load, validate, and expose the settings.
# Pydantic will raise a ValidationError if required fields are missing or types are wrong.
try:
    app_env = AppSettings()
except ValidationError as e:
    # Log the detailed validation error
    error_messages = []
    for error in e.errors():
        field = ".".join(str(loc) for loc in error['loc'])
        message = error['msg']
        error_messages.append(f"  - Field '{field}': {message}")

    full_error_message = "😱 Environment variable validation failed!\n" + "\n".join(error_messages) + \
                         "\nPlease check the logs and your .env file or environment settings."
    logger.error(full_error_message)

    # Exit the application with an error code
    # sys.exit(
    #     "Configuration Error: Invalid or missing environment variables. Please check the logs and your .env file or environment settings.")
    # Re-raise a custom error
    raise CriticalConfigError(full_error_message) from e

# To access: from app.app_env import app_env
# e.g., app_env.OPENAI_API_KEY.get_secret_value()
