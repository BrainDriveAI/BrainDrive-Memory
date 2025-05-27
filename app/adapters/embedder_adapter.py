from langchain_pinecone import PineconeEmbeddings
import os
from dotenv import load_dotenv

from app.config.app_env import app_env

load_dotenv()

# embedder = OpenAIEmbeddings(
#     model=app_env.OPENAI_EMBEDDING_MODEL,
#     api_key=app_env.OPENAI_API_KEY.get_secret_value()
# )

# embedder = OllamaEmbeddings(model=app_env.OLLAMA_EMBEDDING_MODEL)

# PineconeEmbeddings typically relies on environment variables PINECONE_API_KEY and PINECONE_ENVIRONMENT
# We set them here if provided in app_env so the library can pick them up.
if app_env.PINECONE_API_KEY:
    os.environ["PINECONE_API_KEY"] = app_env.PINECONE_API_KEY.get_secret_value()
if app_env.PINECONE_ENVIRONMENT:
    os.environ["PINECONE_ENVIRONMENT"] = app_env.PINECONE_ENVIRONMENT

embedder = PineconeEmbeddings(
    model=app_env.PINECONE_EMBEDDING_MODEL if app_env.PINECONE_EMBEDDING_MODEL else "multilingual-e5-large"
)
