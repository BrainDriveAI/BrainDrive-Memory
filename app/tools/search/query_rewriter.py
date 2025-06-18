from typing import List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.config.app_env import app_env
from app.adapters.llm_adapter import get_llm
from app.tools.search.query_rewriting_prompt import query_rewriting_system_prompt
from app.tools.search.query_rewriting_class import CompactSearchQueries

def analyze_and_generate_queries(user_input: str):
    """
    Analyzes user input and conversation history to generate strategic search queries
    for comprehensive memory retrieval across all data sources.
    
    Uses LLM reasoning to understand user intent and create multiple query variations
    covering different aspects, contexts, and search strategies.
    
    Args:
        user_input (str): The user's raw question or request
        
    Returns:
        List[str]: Strategically generated search queries ready for memory search
    """
    try:
        print(f"Starting query generation for input: '{user_input}'")
        
        # Check if required dependencies are available
        if not hasattr(app_env, 'APP_USERNAME'):
            raise AttributeError("APP_USERNAME not found in app_env")
            
        username = app_env.APP_USERNAME.capitalize()
        print(f"Using username: {username}")

        query_llm = get_llm()
        
        # Check if search_llm_provider is available and has required method
        if not hasattr(query_llm, 'with_structured_output'):
            raise AttributeError("query_llm does not have 'with_structured_output' method")
        
        # Create model instance
        print("Creating structured model instance...")
        structured_model = query_llm.with_structured_output(CompactSearchQueries)
        print("Structured model created successfully")
        
        # Enhanced system prompt with sophisticated categorization logic
        
        # Prepare context message
        print("Preparing context message...")
        context_message = f"User Input: {user_input}"
        
        # Generate queries
        print("Invoking structured model...")
        result = structured_model.invoke([
            SystemMessage(content=query_rewriting_system_prompt), HumanMessage(content=context_message)
        ])
        print("Model invocation successful")
        
        # Validate result
        if not hasattr(result, 'queries'):
            raise AttributeError("Result does not have 'queries' attribute")
            
        if not isinstance(result.queries, list):
            raise TypeError(f"Expected queries to be a list, got {type(result.queries)}")
            
        if len(result.queries) < 2 or len(result.queries) > 4:
            raise ValueError(f"Expected 2-4 queries, got {len(result.queries)}")
        
        print(f"Generated {len(result.queries)} search queries for: '{user_input}'")
        for i, query in enumerate(result.queries, 1):
            print(f"  {i}. {query}")
        
        return result.queries
        
    except AttributeError as e:
        print(f"AttributeError in analyze_and_generate_queries: {e}")
        print("This suggests a missing attribute or method. Check your imports and configuration.")
        raise
        
    except TypeError as e:
        print(f"TypeError in analyze_and_generate_queries: {e}")
        print("This suggests a type mismatch. Check the data types being passed.")
        raise
        
    except ValueError as e:
        print(f"ValueError in analyze_and_generate_queries: {e}")
        print("This suggests an invalid value. Check the constraints and validation rules.")
        raise
        
    except ImportError as e:
        print(f"ImportError in analyze_and_generate_queries: {e}")
        print("This suggests a missing dependency. Check your imports and package installations.")
        raise
        
    except Exception as e:
        print(f"Unexpected error in analyze_and_generate_queries: {type(e).__name__}: {e}")
        print(f"Error details: {str(e)}")
        
        # Additional debugging information
        print("\nDebugging information:")
        print(f"- user_input type: {type(user_input)}, value: '{user_input}'")
        
        try:
            print(f"- app_env.APP_USERNAME: {getattr(app_env, 'APP_USERNAME', 'NOT_FOUND')}")
        except:
            print("- app_env.APP_USERNAME: ERROR_ACCESSING")
            
        try:
            print(f"- query_llm type: {type(query_llm)}")
            print(f"- query_llm has with_structured_output: {hasattr(query_llm, 'with_structured_output')}")
        except:
            print("- query_llm: ERROR_ACCESSING")
        
        raise
