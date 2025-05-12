from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class GraphDBInterface(ABC):
    """
    Abstract interface for graph database operations.
    """

    @abstractmethod
    def query(self, cypher_query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executes a Cypher-like query against the graph database.

        Args:
            cypher_query: The query string.
            params: A dictionary of parameters to pass to the query.

        Returns:
            A list of dictionaries, where each dictionary represents a record in the result.
        """
        pass
