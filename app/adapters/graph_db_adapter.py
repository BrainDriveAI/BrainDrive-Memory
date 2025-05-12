from app.app_env import app_env
from typing import Any, Dict, List, Optional

try:
    from langchain_neo4j import Neo4jGraph
except ImportError:
    raise ImportError("langchain_neo4j is not installed. Please install it using pip install langchain_neo4j")

from app.interfaces.graph_db_interface import GraphDBInterface


class Neo4jAdapter(GraphDBInterface):
    def __init__(self, url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None, database: Optional[str] = None):
        self._graph = Neo4jGraph(
            url=url or app_env.NEO4J_URL,
            username=username or app_env.NEO4J_USER,
            password=password or app_env.NEO4J_PWD.get_secret_value(),
            database=database or app_env.NEO4J_DATABASE
        )

    def query(self, cypher_query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._graph.query(cypher_query, params or {})
