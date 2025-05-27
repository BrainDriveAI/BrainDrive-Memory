from app.tools.shared_utils.retrieve_nodes_from_data import retrieve_nodes_from_data
from app.tools.shared_utils.search_graph_db import search_graph_db
from app.tools.shared_utils.get_deleted_entities import get_delete_entities_from_search_output
from app.tools.shared_utils.delete_entities import delete_entities
from app.tools.update.update_graph import process_and_update
from app.config.app_env import app_env
from app.data_source_manager import get_vector_store_instance

from typing import Optional, Type, List
from langchain_core.tools import tool
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field


def update_vector_documents(data: str, user_id: str, doc_ids: list[str]):
    vector_store_service = get_vector_store_instance()
    if doc_ids:
        vector_store_service.delete_document(doc_ids)

    return vector_store_service.add_document(data, user_id)


def update(data, doc_ids, user_id):
    """
    Updates data from the graph.

    Args:
        data (str): The data to update.
        doc_ids (List[str]): The list of document IDs.
        user_id (str): The user ID.
    """
    update_vector_documents(data, user_id, doc_ids)
    entity_type_map = retrieve_nodes_from_data(data, user_id)
    search_output = search_graph_db(node_list=list(entity_type_map.keys()), user_id=user_id)
    update_type_and_value = process_and_update(search_output, data, user_id)
    to_be_deleted = get_delete_entities_from_search_output(search_output, data, user_id)

    deleted_entities = delete_entities(to_be_deleted, user_id)

    return {"deleted_entities": deleted_entities}


@tool
def update_graph_memory(data: str, doc_ids: List[str]):
    """Use this to update an existing graph memory. This function updates or creates a relationship between two nodes, potentially creating new nodes."""
    return update(data, doc_ids, app_env.APP_USERNAME)


class MemoryInput(BaseModel):
    data: str = Field(description="The data to add to the graph.")
    doc_ids: List[str] = Field(description="A list of vector store document IDs associated with the memory to update or delete.")


class UpdateGraphMemoryTool(BaseTool):
    name: str = "update_graph_memory"
    description: str = "Update graph memory from the knowledge graph. This function updates or creates a relationship between two nodes, potentially creating new nodes."
    args_schema: Type[BaseModel] = MemoryInput

    def _run(
        self,
        data: str,
        doc_ids: List[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        """Use the tool."""
        return update(data, doc_ids, app_env.APP_USERNAME)

    async def _arun(
        self,
        data: str,
        doc_ids: List[str],
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ):
        """Use the tool asynchronously."""
        return update(data, doc_ids, app_env.APP_USERNAME)
