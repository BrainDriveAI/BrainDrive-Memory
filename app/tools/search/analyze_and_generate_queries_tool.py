from typing import List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.config.app_env import app_env
from app.adapters.llm_adapter import get_llm


class SearchQueries(BaseModel):
    queries: List[str] = Field(
        ...,
        min_items=2,
        max_items=4,
        description="A list of 2-4 strategically crafted search queries to comprehensively retrieve relevant user memories."
    )


def analyze_and_generate_queries(user_input: str, chat_history: str):
    """
    Analyzes user input and conversation history to generate strategic search queries
    for comprehensive memory retrieval across all data sources.
    
    Uses LLM reasoning to understand user intent and create multiple query variations
    covering different aspects, contexts, and search strategies.
    
    Args:
        user_input (str): The user's raw question or request
        chat_history (str): Recent conversation context for better analysis
        
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
        structured_model = query_llm.with_structured_output(SearchQueries)
        print("Structured model created successfully")
        
        # Enhanced system prompt with sophisticated categorization logic
        system_prompt = f"""You are an expert query strategist for a personal memory AI system. Your job is to analyze user input and generate strategic search queries to retrieve comprehensive, relevant personal information.
        **CORE REQUIREMENTS:**
        - Generate EXACTLY 2-4 queries (no more, no less)
        - Each query must be semantically distinct and serve a different search purpose
        - Use natural, complete phrases that would actually exist in personal memories
        - Prioritize quality over quantity - each query should have high retrieval potential
        **QUERY GENERATION STRATEGY:**
        For the user input "{user_input}", create diverse queries covering these dimensions:
        1. **Direct Interest/Preference Query**
        - What does {username} explicitly enjoy or prefer in this domain?
        - Example patterns: "{username} enjoys [activity type]", "{username} loves [specific things]"
        2. **Contextual/Situational Query** 
        - What relevant context, constraints, or situations apply?
        - Example patterns: "{username} available [timeframe]", "{username} lives near", "{username} usually does [when]"
        3. **Historical/Experience Query**
        - What past experiences or patterns are relevant?
        - Example patterns: "{username} recently [did/tried]", "{username} used to [activity]", "{username} last [timeframe]"
        4. **Constraint/Limitation Query**
        - What should be avoided or what limitations exist?
        - Example patterns: "{username} dislikes [things]", "{username} cannot [do/go]", "{username} avoids [situations]"
        5. **Social/Relationship Query** (if relevant)
        - Who might be involved or what social context matters?
        - Example patterns: "{username} friends enjoy", "{username} plans with [people]"
        6. **Practical/Logistical Query** (if relevant)
        - What practical considerations matter?
        - Example patterns: "{username} budget for", "{username} has time for", "{username} equipment for"
        **QUALITY STANDARDS:**
        - Each query must be a complete, searchable phrase
        - Queries should target different types of memories/information
        - Avoid redundant queries that would return similar results
        - Ensure queries are specific enough to be useful but broad enough to match varied memory formats
        - Focus on queries that would actually appear in personal conversation or notes
        **EXAMPLE FOR "suggest activities for this weekend":**
        Good queries:
        - "{username} enjoys weekend activities"
        - "{username} lives near recreational areas" 
        - "{username} recently tried new hobbies"
        - "{username} dislikes crowded places"
        - "{username} weekend plans with friends"
        Bad queries:
        - "{username} weekend" (too generic)
        - "{username} vacation budget" (irrelevant to weekend activities)
        - "{username} near" (incomplete)
        Generate queries that will retrieve the most relevant and actionable memories for providing personalized recommendations."""
        
        # Prepare context message
        print("Preparing context message...")
        context_message = f"User Input: {user_input}"
        if chat_history:
            context_message += f"\n\nChat History: {chat_history}"
            print(f"Context message includes chat history (length: {len(chat_history)} chars)")
        else:
            print("No chat history provided")
        
        # Generate queries
        print("Invoking structured model...")
        result = structured_model.invoke([
            SystemMessage(content=system_prompt), HumanMessage(content=context_message)
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
        print(f"- chat_history type: {type(chat_history)}, length: {len(chat_history) if chat_history else 0}")
        
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
