import json
import time
import concurrent.futures
from app.tools.shared_utils.search_graph_db import search_graph_db_by_query
from app.config.app_env import app_env
from typing import Optional, Type
from langchain_core.tools import tool
from app.data_source_manager import get_vector_store_instance
from app.tools.search.search_from_vertexai import search_from_vertexai
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


def search(query: str, user_id: str, limit: int = 100) -> str:
    """
    Search for memories and related graph data in parallel.
    
    Args:
        query (str): Query to search for.
        user_id (str): Username to search for.
        limit (int): The maximum number of nodes and relationships to retrieve. Defaults to 100.
        
    Returns:
        str: A formatted string containing search results from different sources.
    """
    overall_start_time = time.time()
    print(f"Starting search for query: '{query}'")
    
    # Define the search functions to run in parallel
    def get_vector_search():
        try:
            vector_store_service = get_vector_store_instance()
            vector_start_time = time.time()
            results = vector_store_service.hybrid_search(query, {"user_id": app_env.APP_USERNAME})
            vector_time = time.time() - vector_start_time
            print(f"Vector search completed in {vector_time:.3f}s")
            return results
        except Exception as e:
            print(f"Vector search error: {e}")
            return {}
    
    def get_vertexai_search():
        try:
            vertexai_start_time = time.time()
            results = search_from_vertexai(query)
            vertexai_time = time.time() - vertexai_start_time
            print(f"VertexAI search completed in {vertexai_time:.3f}s")
            return results
        except Exception as e:
            print(f"VertexAI search error: {e}")
            return ""
    
    def get_graph_search():
        try:
            graph_start_time = time.time()
            
            # Get entity data
            entity_extract_start = time.time()
            entity_extract_time = time.time() - entity_extract_start
            print(f"Entity extraction completed in {entity_extract_time:.3f}s")
            
            # Search graph database
            graph_search_start = time.time()
            search_output = search_graph_db_by_query(query, user_id)
            graph_search_time = time.time() - graph_search_start
            print(f"Graph DB search completed in {graph_search_time:.3f}s")
            
            if not search_output:
                print("No graph search results found")
                return []
            
            # Process results
            process_start = time.time()
            search_results = []
            for item in search_output:
                search_results.append({
                    "source": item["source"],
                    "relationship": item["relationship"],
                    "destination": item["destination"],
                    "source_id": item["source_id"],
                    "relation_id": item["relation_id"],
                    "destination_id": item["destination_id"],
                })
            process_time = time.time() - process_start
            
            total_graph_time = time.time() - graph_start_time
            print(f"Graph search pipeline completed in {total_graph_time:.3f}s")
            print(f"- Entity extraction: {entity_extract_time:.3f}s")
            print(f"- Graph DB query: {graph_search_time:.3f}s")
            print(f"- Result processing: {process_time:.3f}s")
            print(f"Total graph search results: {len(search_results)}")
            
            return search_results
        except Exception as e:
            print(f"Graph search error: {e}")
            return []
    
    # Execute all search functions in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        vector_future = executor.submit(get_vector_search)
        vertexai_future = executor.submit(get_vertexai_search)
        graph_future = executor.submit(get_graph_search)
        
        # Wait for all to complete
        parallel_start = time.time()
        concurrent.futures.wait([vector_future, vertexai_future, graph_future])
        parallel_time = time.time() - parallel_start
        
        # Get results
        vector_search_results = vector_future.result()
        vertexai_search_results = vertexai_future.result()
        search_results = graph_future.result()
    
    # Format the results
    format_start = time.time()
    combined_search_results = json.dumps(search_results) if len(search_results) else ""
    
    final_output = (
        f"**Knowledge graph data:** [{combined_search_results}]\n"
        f"___\n"
        f"**Vector store data:** [{vector_search_results}]\n"
        f"___\n"
        f"**VertexAI search data:** [{vertexai_search_results}]"
    )
    format_time = time.time() - format_start
    
    total_time = time.time() - overall_start_time
    print(f"Overall search processing completed in {total_time:.3f}s")
    print(f"- Parallel search execution: {parallel_time:.3f}s")
    print(f"- Result formatting: {format_time:.3f}s")
    
    return final_output


@tool
def search_for_memories(query: str):
    """Use the tool to search for memories and related graph data. Pass in detailed query to search for."""
    print(f"Invoking: `search_for_memories` with `{{'query': '{query}'}}`")
    print(f"input data: {query}")
    return search(query, app_env.APP_USERNAME)


class SearchForMemoryArgs(BaseModel):
    query: str = Field(description="Query to search for (must be detailed)")


class SearchForMemoryItemsTool(BaseTool):
    name: str = "search_for_memories"
    description: str = "Search for memories and related graph data."
    args_schema: Type[BaseModel] = SearchForMemoryArgs
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        print(f"Running SearchForMemoryItemsTool with query: '{query}'")
        start_time = time.time()
        result = search(query, app_env.APP_USERNAME)
        total_time = time.time() - start_time
        print(f"SearchForMemoryItemsTool completed in {total_time:.3f}s")
        return result
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        print(f"Running async SearchForMemoryItemsTool with query: '{query}'")
        start_time = time.time()
        result = search(query, app_env.APP_USERNAME)
        total_time = time.time() - start_time
        print(f"Async SearchForMemoryItemsTool completed in {total_time:.3f}s")
        return result
