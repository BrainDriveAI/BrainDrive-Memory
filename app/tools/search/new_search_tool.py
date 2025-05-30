import json
import time
import concurrent.futures
from app.tools.shared_utils.search_graph_db import search_graph_db_by_query
from app.tools.shared_utils.rerank_graph_results import rerank_graph_results
from app.config.app_env import app_env
from typing import Optional, Type, Annotated, List
from langchain_core.tools import tool
from app.data_source_manager import get_vector_store_instance
from app.tools.search.search_from_vertexai import search_from_vertexai
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langgraph.prebuilt import InjectedState
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, AnyMessage
from app.tools.search.analyze_and_generate_queries_tool import analyze_and_generate_queries
from app.tools.search.new_search_helpers import deduplicate_results, rank_by_relevance, format_synthesized_results


def convert_to_chat_history(messages: List[AnyMessage]) -> str:
    """
    Converts LangChain messages list into a chat_history str.

    Args:
        messages: Any list of objects with `.content`, and either `.type` or `._get_type()`;
                 for AI messages it should also have `.tool_calls`.

    Returns:
        A chat_history str.
    """
    chat_history = ""
    for message in messages:
        if isinstance(message, HumanMessage):
            chat_history += f"Human: {message.content}\n"
        elif isinstance(message, AIMessage):
            chat_history += f"Assistant: {message.content}\n"

    return chat_history

@tool
def search_for_memories(raw_query: str, state: Annotated[AgentState, InjectedState]):
    """
    Intelligent memory search that analyzes the raw query and performs comprehensive
    multi-dimensional search across all data sources.
    
    This function:
    1. Analyzes the raw query to generate strategic search variations
    2. Executes parallel searches across all generated queries and data sources
    3. Synthesizes and ranks results for optimal relevance
    
    Args:
        raw_query (str): User's natural language question or request
        state (AgentState): Recent agent state
        
    Returns:
        str: Comprehensive search results from all sources, intelligently 
             synthesized and ranked by relevance and recency
    """
    overall_start_time = time.time()
    print(f"Starting intelligent search for: '{raw_query}'")

    chat_history = convert_to_chat_history(state["messages"])
    
    # Step 1: Generate strategic queries
    query_analysis_start = time.time()
    strategic_queries = analyze_and_generate_queries(raw_query, chat_history)
    query_analysis_time = time.time() - query_analysis_start
    print(f"Generated {len(strategic_queries)} strategic queries in {query_analysis_time:.3f}s")
    
    # Step 2: Execute searches for all queries in parallel
    search_start = time.time()
    all_results = {}
    
    # Create search tasks for each strategic query
    search_tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(strategic_queries), 8)) as executor:
        for i, query in enumerate(strategic_queries):
            print(f"  Query {i+1}: {query}")
            future = executor.submit(search_single_query, query, app_env.APP_USERNAME)
            search_tasks.append((query, future))
        
        # Collect all results
        for query, future in search_tasks:
            try:
                result = future.result()
                all_results[query] = result
            except Exception as e:
                print(f"Search failed for query '{query}': {e}")
                all_results[query] = None
    
    search_time = time.time() - search_start
    print(f"Parallel multi-query search completed in {search_time:.3f}s")
    
    # Step 3: Synthesize and rank results
    synthesis_start = time.time()
    synthesized_results = synthesize_search_results(all_results, raw_query)
    synthesis_time = time.time() - synthesis_start
    
    total_time = time.time() - overall_start_time
    print(f"Intelligent search completed in {total_time:.3f}s")
    print(f"- Query analysis: {query_analysis_time:.3f}s")
    print(f"- Multi-query search: {search_time:.3f}s") 
    print(f"- Result synthesis: {synthesis_time:.3f}s")
    
    return synthesized_results


def search_single_query(query: str, user_id: str, limit: int = 100) -> dict:
    """
    Execute your existing search function for a single query.
    This is essentially your current search() function but returns structured data.
    """
        # Define the search functions to run in parallel
    def get_vector_search():
        try:
            vector_store_service = get_vector_store_instance()
            vector_start_time = time.time()
            results = vector_store_service.hybrid_search(query, {"user_id": user_id})
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
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "similarity": item["similarity"]
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
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        vector_future = executor.submit(get_vector_search)
        vertexai_future = executor.submit(get_vertexai_search)
        graph_future = executor.submit(get_graph_search)
        
        concurrent.futures.wait([vector_future, vertexai_future, graph_future])
        
        return {
            "query": query,
            "vector_results": vector_future.result(),
            "vertexai_results": vertexai_future.result(),
            "graph_results": graph_future.result(),
            "keyword_results": rerank_graph_results(graph_future.result(), query)
        }


def synthesize_search_results(all_results: dict, original_query: str) -> str:
    """
    Intelligently synthesize results from multiple strategic queries.
    
    Features:
    - Deduplication across similar results
    - Relevance ranking based on original query
    - Temporal prioritization (recent > old)
    - Source diversity (mix of vector, graph, keyword results)
    - Confidence scoring integration
    """
    
    # Collect all unique results
    unique_results = {
        "vector_results": [],
        "graph_results": [],
        "vertexai_results": [],
        "keyword_results": []
    }
    
    # Deduplicate and merge results from all queries
    for query, results in all_results.items():
        if results:
            # Add query context to results for traceability
            for result_type in unique_results.keys():
                if result_type in results and results[result_type]:
                    # Add source query information
                    query_results = results[result_type]
                    if isinstance(query_results, list):
                        for item in query_results:
                            if isinstance(item, dict):
                                item['source_query'] = query
                        unique_results[result_type].extend(query_results)
                    else:
                        unique_results[result_type].append({
                            'content': query_results,
                            'source_query': query
                        })
    
    # Deduplicate based on content similarity
    for result_type in unique_results.keys():
        unique_results[result_type] = deduplicate_results(unique_results[result_type])
    
    # Rank by relevance to original query
    ranked_results = rank_by_relevance(unique_results, original_query)
    
    # Format final output (similar to your current format but enhanced)
    final_output = format_synthesized_results(ranked_results, len(all_results))
    
    return final_output

