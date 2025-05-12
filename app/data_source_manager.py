from typing import Optional, Dict, Any, List
import logging

from app.interfaces.graph_db_interface import GraphDBInterface
from app.interfaces.vector_store_interface import VectorStoreInterface
from app.interfaces.vertex_ai_search_interface import VertexAISearchInterface
from app.adapters.graph_db_adapter import Neo4jAdapter
from app.adapters.vector_store_adapter import SupabaseVectorStoreAdapter
from app.adapters.vertex_ai_search_adapter import VertexAISearchAdapter
from app.settings import GRAPH_DB_PROVIDER, VECTOR_STORE_PROVIDER
from app.app_env import app_env
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


# --- Null Object Implementation for GraphDB ---
class NullGraphDB(GraphDBInterface):
    """
    A Null Object implementation for the GraphDBInterface.
    Used when the graph database is disabled or not configured.
    It logs a message and returns empty results, allowing the application
    to proceed without errors.
    """
    def query(self, cypher_query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        logger.info(f"GraphDB is not configured or is disabled. Query not executed: {cypher_query[:100]}...")
        return []


# --- Null Object Implementation for VertexAI Search ---
class NullVertexAISearch(VertexAISearchInterface):
    """
    A Null Object implementation for the GraphDBInterface.
    Used when the graph database is disabled or not configured.
    It logs a message and returns empty results, allowing the application
    to proceed without errors.
    """
    def retrieve(self, query: str) -> List[Document]:
        logger.info(f"Vertex AI Search is not configured or is disabled. Query not executed: {query[:100]}...")
        return []


# --- Null Object Implementation for VectorStore ---
class NullVectorStore(VectorStoreInterface):
    """
    A Null Object implementation for the VectorStoreInterface.
    Used when the vector store is disabled or not configured.
    """
    def add_document(self, source_content: str, user_id: str) -> List[str]:
        logger.info(f"VectorStore is not configured. {source_content} not added.")
        return [source_content]

    def similarity_search(self, query: str, k: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        logger.info(f"VectorStore is not configured. Similarity search for '{query[:50]}...' not performed.")
        return []

    def delete_document(self, ids: List[str]) -> bool:
        logger.info(f"VectorStore is not configured. {len(ids)} documents not deleted.")
        return False

    def hybrid_search(self, query: str, filter_params: Optional[Dict[str, Any]] = None) -> List[Document]:
        logger.info(f"VectorStore is not configured. Hybrid search for '{query[:50]}...' not performed.")
        return []


# --- Singleton instances ---
_graph_db_instance: Optional[GraphDBInterface] = None
_vector_store_instance: Optional[VectorStoreInterface] = None
_vertex_ai_search_instance: Optional[VertexAISearchInterface] = None


def get_graph_db_instance() -> GraphDBInterface:
    """
    Provides a singleton instance of the configured GraphDBInterface.
    Initializes the instance on first call based on settings.
    """
    global _graph_db_instance
    if _graph_db_instance is None:
        logger.info(f"Initializing GraphDB instance with provider: {GRAPH_DB_PROVIDER}")
        if GRAPH_DB_PROVIDER == "neo4j":
            _graph_db_instance = Neo4jAdapter(
                url=app_env.NEO4J_URL,
                username=app_env.NEO4J_USER,
                password=app_env.NEO4J_PWD.get_secret_value()
            )
        # Add other providers here with an elif block
        # elif GRAPH_DB_PROVIDER == "another_graph_provider":
        #     _graph_db_instance = AnotherGraphAdapter(...)
        else:  # "none" or unrecognized
            _graph_db_instance = NullGraphDB()
    return _graph_db_instance


def get_vertex_ai_search_instance() -> VertexAISearchInterface:
    """
    Provides a singleton instance of the configured GraphDBInterface.
    Initializes the instance on first call based on settings.
    """
    global _vertex_ai_search_instance
    if _vertex_ai_search_instance is None:
        logger.info("Initializing Vertex AI Search instance")
        _vertex_ai_search_instance = VertexAISearchAdapter(
            project_id=app_env.VERTEX_AI_PROJECT_ID,
            location_id=app_env.VERTEX_AI_LOCATION_ID,
            datastore_id=app_env.VERTEX_AI_DATASTORE_ID,
        )
    else:  # "none" or unrecognized
        _vertex_ai_search_instance = NullVertexAISearch()
    return _vertex_ai_search_instance


def get_vector_store_instance() -> VectorStoreInterface:
    """
    Provides a singleton instance of the configured VectorStoreInterface.
    Initializes the instance on first call based on settings.
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        logger.info(f"Initializing VectorStore instance with provider: {VECTOR_STORE_PROVIDER}")
        if VECTOR_STORE_PROVIDER == "supabase":
            if not app_env.SUPABASE_URL or not app_env.SUPABASE_KEY:
                logger.error("Supabase URL or Key is not configured. Falling back to NullVectorStore.")
                _vector_store_instance = NullVectorStore()
            else:
                _vector_store_instance = SupabaseVectorStoreAdapter(
                    url=app_env.SUPABASE_URL,
                    key=app_env.SUPABASE_KEY.get_secret_value(),
                    collection_name=app_env.SUPABASE_VECTOR_COLLECTION_NAME,
                    query_function_name=app_env.SUPABASE_VECTOR_QUERY_FUNCTION_NAME
                )
        # Add other providers here with an elif block
        # elif VECTOR_STORE_PROVIDER == "pinecone":
        #     _vector_store_instance = PineconeVectorStoreAdapter(...)
        else:  # "none" or unrecognized
            _vector_store_instance = NullVectorStore()
    return _vector_store_instance
