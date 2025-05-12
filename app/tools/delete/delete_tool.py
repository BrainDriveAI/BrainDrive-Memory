from app.tools.shared_utils.retrieve_nodes_from_data import retrieve_nodes_from_data
from app.tools.shared_utils.search_graph_db import search_graph_db
from app.tools.shared_utils.get_deleted_entities import get_delete_entities_from_search_output
from app.tools.shared_utils.delete_entities import delete_entities
from app.tools.delete.delete_graph import process_and_delete
from app.app_env import app_env
from app.data_source_manager import get_vector_store_instance

from typing import Optional, Type, List
from langchain_core.tools import tool
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field


def delete(data, doc_ids, user_id):
    """
    Deletes data from the graph.

    Args:
        data (str): The data to update.
        doc_ids (list): A list of document IDs.
        user_id (str): A user_id.
    """
    vector_store = get_vector_store_instance()
    vector_store.delete_document(doc_ids)
    entity_type_map = retrieve_nodes_from_data(data, user_id)
    search_output = search_graph_db(node_list=list(entity_type_map.keys()), user_id=user_id)
    to_be_deleted = get_delete_entities_from_search_output(search_output, data, user_id)

    deleted_entities = delete_entities(to_be_deleted, user_id)

    process_and_delete(search_output, data, user_id)

    return {"deleted_entities": deleted_entities}


@tool
def delete_graph_memory(data: str, doc_ids: List[str]):
    """Use this to update an existing graph memory. This function deletes entries."""
    return delete(data, doc_ids, app_env.APP_USERNAME)


class MemoryInput(BaseModel):
    data: str = Field(description="The conversation data.")
    vector_store_doc_ids: List[str] = Field(description="A list of vector store document IDs associated with the memory to delete.")


class DeleteGraphMemoryTool(BaseTool):
    name: str = "delete_graph_memory"
    description: str = "Delete graph memory from the knowledge graph. This function deletes entries. Pass in vector store document ids, not graph db entity ids."
    args_schema: Type[BaseModel] = MemoryInput

    def _run(
        self,
        data: str,
        vector_store_doc_ids: List[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        """Use the tool."""
        return delete(data, vector_store_doc_ids, app_env.APP_USERNAME)

    async def _arun(
        self,
        data: str,
        vector_store_doc_ids: List[str],
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ):
        """Use the tool asynchronously."""
        return delete(data, vector_store_doc_ids, app_env.APP_USERNAME)
    