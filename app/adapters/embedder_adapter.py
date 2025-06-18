import os
from dotenv import load_dotenv
from app.config.app_env import app_env

load_dotenv()


def get_embedder():
    provider = app_env.EMBEDDING_PROVIDER

    if provider == 'openai':
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=app_env.OPENAI_EMBEDDING_MODEL,
            openai_api_key=app_env.OPENAI_API_KEY.get_secret_value()
        )

    if provider == 'pinecone':
        from langchain_pinecone import PineconeEmbeddings
        # Ensure Pinecone env vars are set for the library
        os.environ['PINECONE_API_KEY'] = app_env.PINECONE_API_KEY.get_secret_value()
        os.environ['PINECONE_ENVIRONMENT'] = app_env.PINECONE_ENVIRONMENT
        return PineconeEmbeddings(
            model=app_env.PINECONE_EMBEDDING_MODEL
        )

    if provider == 'ollama':
        from langchain_ollama import OllamaEmbeddings
        # Optionally set base URL
        if app_env.OLLAMA_BASE_URL:
            os.environ['OLLAMA_BASE_URL'] = str(app_env.OLLAMA_BASE_URL)
        return OllamaEmbeddings(
            model=app_env.OLLAMA_EMBEDDING_MODEL
        )

    raise ValueError(f"Unsupported embedding provider: {provider}")

embedder = get_embedder()
