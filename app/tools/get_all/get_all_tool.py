from app.logger import app_logger as logger
from app.data_source_manager import get_graph_db_instance
from app.config.app_env import app_env

from typing import Optional, Type

from langchain_core.tools import tool
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field


def get_all(user_id: str, limit=100):
    """
    Retrieves all nodes and relationships from the graph database based on optional filtering criteria.

    Args:
        user_id (str): The user ID.
        limit (int): The maximum number of nodes and relationships to retrieve. Defaults to 100.
    Returns:
        list: A list of dictionaries, each containing:
            - 'contexts': The base data store response for each memory.
            - 'entities': A list of strings representing the nodes and relationships
    """
    graph_db_service = get_graph_db_instance()

    # return all nodes and relationships
    query = """
    MATCH (n {user_id: $user_id})-[r]->(m {user_id: $user_id})
    RETURN n.name AS source, type(r) AS relationship, m.name AS target
    LIMIT $limit
    """
    results = graph_db_service.query(query, params={"user_id": user_id, "limit": limit})

    final_results = []
    for result in results:
        final_results.append(
            {
                "source": result["source"],
                "relationship": result["relationship"],
                "target": result["target"],
            }
        )

    logger.info(f"Retrieved {len(final_results)} relationships")

    return final_results


@tool
def get_all_items() -> list:
    """Use the tool to get all memory items."""
    return get_all(app_env.APP_USERNAME)


class GetAllMemoryArgs(BaseModel):
    limit: Optional[int] = Field(description="The maximum number of nodes and relationships to retrieve. Defaults to 100.")


class GetAllMemoryItemsTool(BaseTool):
    name: str = "get_all_items"
    description: str = "Get all memory items."
    args_schema: Type[BaseModel] = GetAllMemoryArgs

    def _run(
        self,
        limit: Optional[int],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        """Use the tool."""
        return get_all(app_env.APP_USERNAME)

    async def _arun(
        self,
        limit: Optional[int],
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ):
        """Use the tool asynchronously."""
        return get_all(app_env.APP_USERNAME)
    