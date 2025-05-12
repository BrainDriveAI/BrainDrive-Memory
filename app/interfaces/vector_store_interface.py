from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document


class VectorStoreInterface(ABC):
    """
    Abstract interface for vector store operations.
    """

    @abstractmethod
    def add_document(self, source_content: str, user_id: str) -> List[str]:
        """
        Adds a list of documents to the vector store.

        Args:
            documents: A list of Langchain Document objects.
            ids: Optional list of IDs for the documents.

        Returns:
            A list of IDs of the added documents.
        """
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Performs a similarity search against the vector store.

        Args:
            query: The query string.
            k: The number of results to return.
            filter: Optional dictionary for metadata filtering.

        Returns:
            A list of relevant Langchain Document objects.
        """
        pass

    @abstractmethod
    def delete_document(self, ids: List[str]) -> bool:
        """
        Deletes documents from the vector store by their IDs.

        Args:
            ids: A list of document IDs to delete.
        Returns:
            True if deletion was attempted (actual success depends on implementation).
        """
        pass

    @abstractmethod
    def hybrid_search(self, query: str, filter_params: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Performs a hybrid search using both text and embeddings.
        Specific implementation details (like RPC calls) are handled by the adapter.

        Args:
            query: The text query.
            filter_params: Additional parameters for filtering or controlling the search,
                           e.g., user_id for a specific RPC.

        Returns:
            A list of relevant Langchain Document objects.
        """
        pass
