from app.tools.shared_utils.retrieve_nodes_from_data import retrieve_nodes_from_data
from app.tools.shared_utils.establish_nodes_relations_from_data import establish_nodes_relations_from_data
from app.tools.add.add_entities import add_entities
from app.app_env import app_env
from app.data_source_manager import get_vector_store_instance

from typing import Optional, Type
from langchain_core.tools import tool
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field


def add(data, user_id):
    """
    Adds data to the graph.

    Args:
        data (str): The data to add to the graph.
        user_id (str): A username.
    """
    vector_store_service = get_vector_store_instance()
    vector_store_service.add_document(data, user_id)
    entity_type_map = retrieve_nodes_from_data(data, user_id)
    to_be_added = establish_nodes_relations_from_data(data, user_id, entity_type_map)

    added_entities = add_entities(to_be_added, user_id, entity_type_map)

    return {"added_entities": added_entities}


@tool
def add_graph_memory(data: str):
    """Use this to add a new graph memory to the knowledge graph. This function creates a new relationship between two nodes, potentially creating new nodes if they don't exist."""
    return add(data, app_env.APP_USERNAME)


class MemoryInput(BaseModel):
    data: str = Field(description="The data to add to the graph.")


class AddGraphMemoryTool(BaseTool):
    name: str = "add_graph_memory"
    description: str = "Add a new graph memory to the knowledge graph. This function creates a new relationship between two nodes, potentially creating new nodes if they don't exist."
    args_schema: Type[BaseModel] = MemoryInput

    def _run(
        self,
        data: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        """Use the tool."""
        return add(data, app_env.APP_USERNAME)

    async def _arun(
        self,
        data: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ):
        """Use the tool asynchronously."""
        return add(data, app_env.APP_USERNAME)
