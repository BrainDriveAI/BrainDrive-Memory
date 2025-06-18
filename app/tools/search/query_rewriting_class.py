from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from enum import Enum

class QueryIntent(str, Enum):
    """Enumeration of possible query intents."""
    FACTUAL_RETRIEVAL = "factual_retrieval"
    TEMPORAL_QUERIES = "temporal_queries"
    RELATIONSHIP_QUERIES = "relationship_queries"
    PATTERN_DISCOVERY = "pattern_discovery"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    CONTEXTUAL_RECALL = "contextual_recall"
    PLANNING_ASSISTANCE = "planning_assistance"

class QueryComplexity(str, Enum):
    """Enumeration of query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

class SearchStrategy(str, Enum):
    """Enumeration of search strategies."""
    GRAPH_TRAVERSAL = "graph_traversal"
    VECTOR_SIMILARITY = "vector_similarity"
    KEYWORD_SEARCH = "keyword_search"
    HYBRID_FUSION = "hybrid_fusion"

class EntityType(BaseModel):
    """Represents an entity with its type."""
    name: str = Field(..., description="The entity name or identifier")
    type: str = Field(..., description="The entity type (Person, Event, Financial, etc.)")

class QueryAnalysis(BaseModel):
    """Analysis of the original query."""
    intent: QueryIntent = Field(..., description="Primary intent category of the query")
    entities: List[EntityType] = Field(
        default_factory=list,
        description="List of identified entities with their types"
    )
    temporal_scope: Optional[str] = Field(
        None,
        description="Time range or temporal context of the query"
    )
    complexity: QueryComplexity = Field(..., description="Complexity level of the query")

class EnhancedQueries(BaseModel):
    """Optimized queries for different search systems."""
    graph_optimized: str = Field(
        ...,
        description="Query optimized for graph database traversal and relationship discovery"
    )
    vector_optimized: str = Field(
        ...,
        description="Query optimized for semantic similarity search in vector stores"
    )
    keyword_optimized: str = Field(
        ...,
        description="Query optimized for traditional keyword-based search"
    )

class SemanticExpansions(BaseModel):
    """Semantic expansions of the original query."""
    synonyms: List[str] = Field(
        default_factory=list,
        description="List of synonyms for key terms in the query"
    )
    related_concepts: List[str] = Field(
        default_factory=list,
        description="List of concepts related to the query topic"
    )
    contextual_terms: List[str] = Field(
        default_factory=list,
        description="List of contextual terms that enhance query understanding"
    )

class SearchStrategies(BaseModel):
    """Search strategies and recommendations."""
    primary_approach: SearchStrategy = Field(
        ...,
        description="Recommended primary search method"
    )
    fallback_approaches: List[SearchStrategy] = Field(
        default_factory=list,
        description="List of alternative search methods to try if primary fails"
    )
    fusion_weight: Optional[Dict[str, float]] = Field(
        None,
        description="Recommended weighting for result fusion across different search methods"
    )

class SearchQueries(BaseModel):
    """
    Enhanced search queries output for memory AI agent.
    Contains the original simple query list plus comprehensive query analysis and optimization.
    """
    # Original simple format for backward compatibility
    queries: List[str] = Field(
        ...,
        min_items=2,
        max_items=4,
        description="A list of 2-4 strategically crafted search queries to comprehensively retrieve relevant user memories."
    )
    
    # Enhanced structured format
    original_query: str = Field(..., description="The user's original query")
    
    query_analysis: QueryAnalysis = Field(
        ...,
        description="Detailed analysis of the original query"
    )
    
    enhanced_queries: EnhancedQueries = Field(
        ...,
        description="Queries optimized for different search systems"
    )
    
    semantic_expansions: SemanticExpansions = Field(
        ...,
        description="Semantic expansions to improve search coverage"
    )
    
    search_strategies: SearchStrategies = Field(
        ...,
        description="Recommended search strategies and approaches"
    )

class CompactSearchQueries(BaseModel):
    """
    Simplified version of SearchQueries for cases where only basic query expansion is needed.
    Maintains backward compatibility with the original format.
    """
    queries: List[str] = Field(
        ...,
        min_items=2,
        max_items=4,
        description="A list of 2-4 strategically crafted search queries to comprehensively retrieve relevant user memories."
    )
    
    original_query: str = Field(..., description="The user's original query")
    
    key_entities: List[str] = Field(
        default_factory=list,
        description="List of key entities identified in the query"
    )
    
    temporal_context: Optional[str] = Field(
        None,
        description="Temporal context if applicable"
    )

# Example usage and validation
# if __name__ == "__main__":
#     # Example of the full SearchQueries model
#     example_full = {
#         "queries": [
#             "John work project discussion feedback",
#             "colleague John project opinions suggestions",
#             "work conversations John recent projects",
#             "John meeting notes project feedback"
#         ],
#         "original_query": "What did John say about the project?",
#         "query_analysis": {
#             "intent": "factual_retrieval",
#             "entities": [
#                 {"name": "John", "type": "Person"},
#                 {"name": "project", "type": "WorkItem"}
#             ],
#             "temporal_scope": "recent work conversations",
#             "complexity": "moderate"
#         },
#         "enhanced_queries": {
#             "graph_optimized": "conversations with John about work projects",
#             "vector_optimized": "John discussed project feedback opinions suggestions concerns",
#             "keyword_optimized": "John project feedback discussion work"
#         },
#         "semantic_expansions": {
#             "synonyms": ["John", "colleague", "project", "feedback"],
#             "related_concepts": ["work discussion", "project feedback", "meeting notes"],
#             "contextual_terms": ["colleague", "work", "professional"]
#         },
#         "search_strategies": {
#             "primary_approach": "hybrid_fusion",
#             "fallback_approaches": ["vector_similarity", "keyword_search"],
#             "fusion_weight": {
#                 "graph": 0.4,
#                 "vector": 0.4,
#                 "keyword": 0.2
#             }
#         }
#     }
    
#     # Example of the compact version
#     example_compact = {
#         "queries": [
#             "John work project discussion feedback",
#             "colleague John project opinions suggestions",
#             "work conversations John recent projects"
#         ],
#         "original_query": "What did John say about the project?",
#         "primary_intent": "factual_retrieval",
#         "key_entities": ["John", "project"],
#         "temporal_context": "recent work conversations"
#     }
    
#     # Validate the models
#     full_queries = SearchQueries(**example_full)
#     compact_queries = CompactSearchQueries(**example_compact)
    
#     print("Full model validation successful!")
#     print("Compact model validation successful!")