from typing import List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.config.app_env import app_env
from app.adapters.llm_adapter import search_llm_provider

class SearchQueries(BaseModel):
    queries: List[str] = Field(
        ...,  # make this required
        min_items=3,
        max_items=6,
        description="A list of 3-6 strategically crafted search queries to comprehensively retrieve relevant user memories."
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
    username = app_env.APP_USERNAME.capitalize()
    
    # Create model instance
    structured_model = search_llm_provider.with_structured_output(SearchQueries)
    
    # Enhanced system prompt with sophisticated categorization logic
    system_prompt = f"""You are an expert query strategist for a personal memory AI system. Your job is to analyze user input and generate strategic search queries to retrieve comprehensive, relevant personal information.

    **CORE REQUIREMENTS:**
    - Generate EXACTLY 3-6 queries (no more, no less)
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
    context_message = f"User Input: {user_input}"
    if chat_history:
        context_message += f"\n\nChat History: {chat_history}"
    
    # Generate queries
    result = structured_model.invoke([
        SystemMessage(content=system_prompt), HumanMessage(content=context_message)
    ])
    
    print(f"Generated {len(result.queries)} search queries for: '{user_input}'")
    for i, query in enumerate(result.queries, 1):
        print(f"  {i}. {query}")
    
    return result.queries
