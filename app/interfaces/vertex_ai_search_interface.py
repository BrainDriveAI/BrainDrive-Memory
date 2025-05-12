from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document


class VertexAISearchInterface(ABC):
    """
    Abstract interface for graph database operations.
    """

    @abstractmethod
    def retrieve(self, query: str) -> List[Document]:
        """
        Executes a Cypher-like query against the graph database.

        Args:
            query: The query string.

        Returns:
            A list of dictionaries, where each dictionary represents a record in the result.
        """
        pass
