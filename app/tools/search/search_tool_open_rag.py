import json
import time
import asyncio
import concurrent.futures
from typing import Optional, Type, Annotated, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
from app.tools.shared_utils.search_graph_db import search_graph_db_by_query
from app.tools.shared_utils.rerank_graph_results import rerank_graph_results
from app.config.app_env import app_env
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


class QueryComplexity(Enum):
    """Query complexity types for expert routing"""
    SIMPLE_FACTUAL = "simple_factual"      # Direct fact lookup
    MULTI_HOP = "multi_hop"                # Requires reasoning across sources
    TEMPORAL = "temporal"                  # Time-based reasoning
    COMPARATIVE = "comparative"            # Comparison tasks
    ANALYTICAL = "analytical"              # Deep analysis required


class ReasoningExpert(Enum):
    """Different reasoning experts (simplified MoE concept)"""
    FACTUAL_RETRIEVAL = "factual"          # Best for direct fact lookup
    RELATIONAL_REASONING = "relational"     # Best for graph/relationship queries
    TEMPORAL_REASONING = "temporal"         # Best for time-based queries
    SYNTHESIS_EXPERT = "synthesis"          # Best for combining multiple sources


@dataclass
class QueryAnalysis:
    """Analysis of query characteristics for expert routing"""
    complexity: QueryComplexity
    primary_expert: ReasoningExpert
    secondary_experts: List[ReasoningExpert]
    confidence: float
    requires_multi_hop: bool
    temporal_aspect: bool
    comparative_aspect: bool


@dataclass
class ExpertResponse:
    """Response from a specific reasoning expert"""
    expert_type: ReasoningExpert
    results: Dict[str, Any]
    confidence: float
    reasoning_trace: List[str]
    execution_time: float


class OpenRAGQueryAnalyzer:
    """Analyzes queries to route to appropriate reasoning experts"""
    
    def __init__(self):
        # Keywords that indicate different query types
        self.factual_keywords = {'what', 'who', 'when', 'where', 'define', 'explain'}
        self.multi_hop_keywords = {'because', 'why', 'how', 'relate', 'connection', 'impact', 'cause', 'effect'}
        self.temporal_keywords = {'before', 'after', 'since', 'until', 'timeline', 'history', 'recent', 'latest'}
        self.comparative_keywords = {'compare', 'versus', 'vs', 'difference', 'similar', 'better', 'worse'}
        
        # For smaller models: Pre-computed query templates to reduce reasoning load
        self.query_templates = {
            "factual": "Based on the retrieved information: {context}. Answer: {query}",
            "relational": "Given these relationships: {context}. Explain how they connect to answer: {query}",
            "temporal": "Considering the timeline in: {context}. Answer with temporal context: {query}",
            "synthesis": "Synthesizing from multiple sources: {context}. Provide comprehensive answer to: {query}"
        }
        
    def analyze_query(self, query: str, chat_history: str = "") -> QueryAnalysis:
        """Analyze query to determine routing strategy"""
        query_lower = query.lower()
        
        # Determine complexity and expert routing
        complexity_scores = {
            QueryComplexity.SIMPLE_FACTUAL: self._score_factual(query_lower),
            QueryComplexity.MULTI_HOP: self._score_multi_hop(query_lower),
            QueryComplexity.TEMPORAL: self._score_temporal(query_lower),
            QueryComplexity.COMPARATIVE: self._score_comparative(query_lower),
            QueryComplexity.ANALYTICAL: self._score_analytical(query_lower, chat_history)
        }
        
        # Primary complexity
        primary_complexity = max(complexity_scores, key=complexity_scores.get)
        confidence = complexity_scores[primary_complexity]
        
        # Determine expert routing
        primary_expert, secondary_experts = self._route_to_experts(
            primary_complexity, query_lower, chat_history
        )
        
        return QueryAnalysis(
            complexity=primary_complexity,
            primary_expert=primary_expert,
            secondary_experts=secondary_experts,
            confidence=confidence,
            requires_multi_hop=complexity_scores[QueryComplexity.MULTI_HOP] > 0.3,
            temporal_aspect=complexity_scores[QueryComplexity.TEMPORAL] > 0.2,
            comparative_aspect=complexity_scores[QueryComplexity.COMPARATIVE] > 0.2
        )
    
    def _score_factual(self, query: str) -> float:
        return len([kw for kw in self.factual_keywords if kw in query]) / len(self.factual_keywords)
    
    def _score_multi_hop(self, query: str) -> float:
        score = len([kw for kw in self.multi_hop_keywords if kw in query]) / len(self.multi_hop_keywords)
        # Boost if query has multiple entities or complex structure
        if ' and ' in query or ' or ' in query or query.count('?') > 1:
            score += 0.2
        return min(score, 1.0)
    
    def _score_temporal(self, query: str) -> float:
        return len([kw for kw in self.temporal_keywords if kw in query]) / len(self.temporal_keywords)
    
    def _score_comparative(self, query: str) -> float:
        return len([kw for kw in self.comparative_keywords if kw in query]) / len(self.comparative_keywords)
    
    def _score_analytical(self, query: str, chat_history: str) -> float:
        # Base score on query complexity
        analytical_indicators = ['analyze', 'evaluate', 'assess', 'implications', 'significance', 'impact']
        score = len([kw for kw in analytical_indicators if kw in query]) / len(analytical_indicators)
        
        # Boost if there's relevant context in chat history
        if len(chat_history) > 200:  # Substantial conversation context
            score += 0.1
            
        return min(score, 1.0)
    
    def _route_to_experts(self, complexity: QueryComplexity, query: str, chat_history: str) -> tuple:
        """Route query to appropriate experts based on analysis"""
        routing_map = {
            QueryComplexity.SIMPLE_FACTUAL: (ReasoningExpert.FACTUAL_RETRIEVAL, []),
            QueryComplexity.MULTI_HOP: (ReasoningExpert.RELATIONAL_REASONING, [ReasoningExpert.SYNTHESIS_EXPERT]),
            QueryComplexity.TEMPORAL: (ReasoningExpert.TEMPORAL_REASONING, [ReasoningExpert.FACTUAL_RETRIEVAL]),
            QueryComplexity.COMPARATIVE: (ReasoningExpert.SYNTHESIS_EXPERT, [ReasoningExpert.FACTUAL_RETRIEVAL]),
            QueryComplexity.ANALYTICAL: (ReasoningExpert.SYNTHESIS_EXPERT, [ReasoningExpert.RELATIONAL_REASONING, ReasoningExpert.FACTUAL_RETRIEVAL])
        }
        
        primary, secondary = routing_map.get(complexity, (ReasoningExpert.FACTUAL_RETRIEVAL, []))
        
        # Add relational expert if graph-like terms detected
        graph_terms = ['relationship', 'connected', 'related', 'link', 'association']
        if any(term in query for term in graph_terms) and ReasoningExpert.RELATIONAL_REASONING not in secondary:
            secondary.append(ReasoningExpert.RELATIONAL_REASONING)
            
        return primary, secondary


class ReasoningExpertEngine:
    """Implements different reasoning experts with specialized logic"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.analyzer = OpenRAGQueryAnalyzer()
    
    async def execute_expert(self, expert: ReasoningExpert, query: str, 
                           context: Dict[str, Any] = None) -> ExpertResponse:
        """Execute specific reasoning expert"""
        start_time = time.time()
        reasoning_trace = []
        
        if expert == ReasoningExpert.FACTUAL_RETRIEVAL:
            results, trace = await self._factual_expert(query, context)
        elif expert == ReasoningExpert.RELATIONAL_REASONING:
            results, trace = await self._relational_expert(query, context)
        elif expert == ReasoningExpert.TEMPORAL_REASONING:
            results, trace = await self._temporal_expert(query, context)
        elif expert == ReasoningExpert.SYNTHESIS_EXPERT:
            results, trace = await self._synthesis_expert(query, context)
        else:
            results, trace = {}, ["Unknown expert type"]
            
        execution_time = time.time() - start_time
        reasoning_trace.extend(trace)
        
        # Calculate confidence based on result quality and consistency
        confidence = self._calculate_expert_confidence(results, expert, query)
        
        return ExpertResponse(
            expert_type=expert,
            results=results,
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            execution_time=execution_time
        )
    
    def execute_expert_sync(self, expert: ReasoningExpert, query: str, context: Dict = None) -> ExpertResponse:
        """Synchronous wrapper for expert execution"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context, use run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.execute_expert(expert, query, context))
                    return future.result()
            else:
                return asyncio.run(self.execute_expert(expert, query, context))
        except Exception as e:
            print(f"Error in sync expert execution: {e}")
            # Return a fallback response
            return ExpertResponse(
                expert_type=expert,
                results={},
                confidence=0.0,
                reasoning_trace=[f"Error: {str(e)}"],
                execution_time=0.0
            )
        
    def execute_expert_sync_only(self, expert: ReasoningExpert, query: str, context: Dict = None) -> ExpertResponse:
        """Synchronous expert execution"""
        start_time = time.time()
        reasoning_trace = []
        
        if expert == ReasoningExpert.FACTUAL_RETRIEVAL:
            results, trace = self._relational_expert_sync(query, context)
        elif expert == ReasoningExpert.RELATIONAL_REASONING:
            results, trace = self._relational_expert_sync(query, context)
        elif expert == ReasoningExpert.TEMPORAL_REASONING:
            results, trace = self._temporal_expert_sync(query, context)
        elif expert == ReasoningExpert.SYNTHESIS_EXPERT:
            results, trace = self._synthesis_expert_sync(query, context)
        else:
            results, trace = {}, ["Unknown expert type"]
            
        execution_time = time.time() - start_time
        reasoning_trace.extend(trace)
        
        confidence = self._calculate_expert_confidence(results, expert, query)
        
        return ExpertResponse(
            expert_type=expert,
            results=results,
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            execution_time=execution_time
        )

    def _factual_expert_sync(self, query: str, context: Dict) -> tuple:
        """Synchronous version of factual expert"""
        reasoning_trace = ["Factual Expert: Executing direct retrieval strategy"]
        
        vector_results = self._get_vector_search(query)
        results = {"vector_results": vector_results, "strategy": "factual_direct"}
        
        if not vector_results or not isinstance(vector_results, dict) or len(vector_results.get('documents', [])) < 3:
            reasoning_trace.append("Vector results insufficient, expanding search")
            vertexai_results = self._get_vertexai_search(query)
            results["vertexai_results"] = vertexai_results
        
        if vector_results and isinstance(vector_results, dict):
            context_summary = self._create_factual_context(vector_results, query)
            results["structured_context"] = context_summary
            
        doc_count = 0
        if isinstance(vector_results, dict) and 'documents' in vector_results:
            doc_count = len(vector_results['documents'])
        
        reasoning_trace.append(f"Retrieved {doc_count} vector results")
        return results, reasoning_trace
    
    async def _factual_expert(self, query: str, context: Dict) -> tuple:
        """Expert optimized for direct factual retrieval"""
        reasoning_trace = ["Factual Expert: Executing direct retrieval strategy"]
        
        # For smaller models: Focus on most relevant sources first
        # Prioritize vector search for factual queries
        vector_results = self._get_vector_search(query)
        
        # Only search other sources if vector results are insufficient
        results = {"vector_results": vector_results, "strategy": "factual_direct"}
        
        if not vector_results or len(vector_results.get('documents', [])) < 3:
            reasoning_trace.append("Vector results insufficient, expanding search")
            vertexai_results = self._get_vertexai_search(query)
            results["vertexai_results"] = vertexai_results
        
        # Prepare context for smaller model with structured template
        if vector_results:
            context_summary = self._create_factual_context(vector_results, query)
            results["structured_context"] = context_summary
            
        reasoning_trace.append(f"Retrieved {len(results.get('vector_results', {}).get('documents', []))} vector results")
        return results, reasoning_trace
    
    def _create_factual_context(self, vector_results: Dict, query: str) -> str:
        """Create structured context optimized for smaller models"""
        if not vector_results or 'documents' not in vector_results:
            return ""
        
        # Extract top 3 most relevant snippets
        docs = vector_results['documents'][:3]
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            # Truncate long documents to essential information
            snippet = doc[:300] if isinstance(doc, str) else str(doc)[:300]
            context_parts.append(f"Source {i}: {snippet}")
        
        return "\n".join(context_parts)
    
    def _relational_expert_sync(self, query: str, context: Dict) -> tuple:
        """Expert optimized for graph/relationship reasoning"""
        reasoning_trace = ["Relational Expert: Executing graph-based reasoning"]
        
        # Prioritize graph search and enhance with vector context
        with concurrent.futures.ThreadPoolExecutor() as executor:
            graph_future = executor.submit(self._get_graph_search, query)
            vector_future = executor.submit(self._get_vector_search, query)
            
            concurrent.futures.wait([graph_future, vector_future])
            
            graph_results = graph_future.result()
            vector_results = vector_future.result()
            
            # Enhanced relationship analysis
            enhanced_relations = self._analyze_relationships(graph_results, query)
            
            results = {
                "graph_results": graph_results,
                "vector_results": vector_results,
                "enhanced_relations": enhanced_relations,
                "strategy": "relational_reasoning"
            }
            
        reasoning_trace.append(f"Analyzed {len(graph_results)} relationships")
        reasoning_trace.append(f"Enhanced {len(enhanced_relations)} relationship patterns")
        return results, reasoning_trace
    
    async def _relational_expert(self, query: str, context: Dict) -> tuple:
        """Expert optimized for graph/relationship reasoning"""
        reasoning_trace = ["Relational Expert: Executing graph-based reasoning"]
        
        # Prioritize graph search and enhance with vector context
        with concurrent.futures.ThreadPoolExecutor() as executor:
            graph_future = executor.submit(self._get_graph_search, query)
            vector_future = executor.submit(self._get_vector_search, query)
            
            concurrent.futures.wait([graph_future, vector_future])
            
            graph_results = graph_future.result()
            vector_results = vector_future.result()
            
            # Enhanced relationship analysis
            enhanced_relations = self._analyze_relationships(graph_results, query)
            
            results = {
                "graph_results": graph_results,
                "vector_results": vector_results,
                "enhanced_relations": enhanced_relations,
                "strategy": "relational_reasoning"
            }
            
        reasoning_trace.append(f"Analyzed {len(graph_results)} relationships")
        reasoning_trace.append(f"Enhanced {len(enhanced_relations)} relationship patterns")
        return results, reasoning_trace
    
    def _temporal_expert_sync(self, query: str, context: Dict) -> tuple:
        """Expert optimized for temporal reasoning"""
        reasoning_trace = ["Temporal Expert: Executing time-aware search"]
        
        # Execute all searches but with temporal ranking bias
        with concurrent.futures.ThreadPoolExecutor() as executor:
            vector_future = executor.submit(self._get_vector_search, query)
            graph_future = executor.submit(self._get_graph_search, query)
            vertexai_future = executor.submit(self._get_vertexai_search, query)
            
            concurrent.futures.wait([vector_future, graph_future, vertexai_future])
            
            results = {
                "vector_results": vector_future.result(),
                "graph_results": graph_future.result(),
                "vertexai_results": vertexai_future.result(),
                "strategy": "temporal_reasoning"
            }
            
            # Apply temporal ranking
            results = self._apply_temporal_ranking(results, query)
            
        reasoning_trace.append("Applied temporal ranking to results")
        return results, reasoning_trace
    
    async def _temporal_expert(self, query: str, context: Dict) -> tuple:
        """Expert optimized for temporal reasoning"""
        reasoning_trace = ["Temporal Expert: Executing time-aware search"]
        
        # Execute all searches but with temporal ranking bias
        with concurrent.futures.ThreadPoolExecutor() as executor:
            vector_future = executor.submit(self._get_vector_search, query)
            graph_future = executor.submit(self._get_graph_search, query)
            vertexai_future = executor.submit(self._get_vertexai_search, query)
            
            concurrent.futures.wait([vector_future, graph_future, vertexai_future])
            
            results = {
                "vector_results": vector_future.result(),
                "graph_results": graph_future.result(),
                "vertexai_results": vertexai_future.result(),
                "strategy": "temporal_reasoning"
            }
            
            # Apply temporal ranking
            results = self._apply_temporal_ranking(results, query)
            
        reasoning_trace.append("Applied temporal ranking to results")
        return results, reasoning_trace
    
    def _synthesis_expert_sync(self, query: str, context: Dict) -> tuple:
        """Expert for synthesizing information across sources"""
        reasoning_trace = ["Synthesis Expert: Multi-source integration"]
        
        # Get all available data sources
        with concurrent.futures.ThreadPoolExecutor() as executor:
            vector_future = executor.submit(self._get_vector_search, query)
            graph_future = executor.submit(self._get_graph_search, query)
            vertexai_future = executor.submit(self._get_vertexai_search, query)
            
            concurrent.futures.wait([vector_future, graph_future, vertexai_future])
            
            vector_results = vector_future.result()
            graph_results = graph_future.result()
            vertexai_results = vertexai_future.result()
            
        # Advanced synthesis logic
        synthesized = self._advanced_synthesis(
            vector_results, graph_results, vertexai_results, query
        )
        
        results = {
            "vector_results": vector_results,
            "graph_results": graph_results,
            "vertexai_results": vertexai_results,
            "synthesized_insights": synthesized,
            "strategy": "multi_source_synthesis"
        }
        
        reasoning_trace.append(f"Synthesized {len(synthesized)} key insights")
        return results, reasoning_trace
    
    async def _synthesis_expert(self, query: str, context: Dict) -> tuple:
        """Expert for synthesizing information across sources"""
        reasoning_trace = ["Synthesis Expert: Multi-source integration"]
        
        # Get all available data sources
        with concurrent.futures.ThreadPoolExecutor() as executor:
            vector_future = executor.submit(self._get_vector_search, query)
            graph_future = executor.submit(self._get_graph_search, query)
            vertexai_future = executor.submit(self._get_vertexai_search, query)
            
            concurrent.futures.wait([vector_future, graph_future, vertexai_future])
            
            vector_results = vector_future.result()
            graph_results = graph_future.result()
            vertexai_results = vertexai_future.result()
            
        # Advanced synthesis logic
        synthesized = self._advanced_synthesis(
            vector_results, graph_results, vertexai_results, query
        )
        
        results = {
            "vector_results": vector_results,
            "graph_results": graph_results,
            "vertexai_results": vertexai_results,
            "synthesized_insights": synthesized,
            "strategy": "multi_source_synthesis"
        }
        
        reasoning_trace.append(f"Synthesized {len(synthesized)} key insights")
        return results, reasoning_trace
    
    def _get_vector_search(self, query: str):
        """Your existing vector search logic"""
        try:
            vector_store_service = get_vector_store_instance()
            return vector_store_service.hybrid_search(query, {"user_id": self.user_id})
        except Exception as e:
            print(f"Vector search error: {e}")
            return {}
    
    def _get_vertexai_search(self, query: str):
        """Your existing VertexAI search logic"""
        try:
            return search_from_vertexai(query)
        except Exception as e:
            print(f"VertexAI search error: {e}")
            return ""
    
    def _get_graph_search(self, query: str):
        """Your existing graph search logic"""
        try:
            return search_graph_db_by_query(query, self.user_id)
        except Exception as e:
            print(f"Graph search error: {e}")
            return []
    
    def _analyze_relationships(self, graph_results: List, query: str) -> List[Dict]:
        """Enhanced relationship analysis for multi-hop reasoning"""
        if not graph_results:
            return []
            
        # Group by relationship types
        relationship_patterns = {}
        for result in graph_results:
            rel_type = result.get('relationship', 'unknown')
            if rel_type not in relationship_patterns:
                relationship_patterns[rel_type] = []
            relationship_patterns[rel_type].append(result)
        
        # Identify potential multi-hop paths
        enhanced_relations = []
        for rel_type, relations in relationship_patterns.items():
            if len(relations) > 1:
                # Look for chains: A->B, B->C patterns
                for i, rel1 in enumerate(relations):
                    for j, rel2 in enumerate(relations[i+1:], i+1):
                        if rel1['destination'] == rel2['source']:
                            enhanced_relations.append({
                                'type': 'chain',
                                'path': [rel1, rel2],
                                'pattern': f"{rel1['source']} -> {rel1['destination']} -> {rel2['destination']}",
                                'confidence': min(rel1.get('similarity', 0), rel2.get('similarity', 0))
                            })
        
        return enhanced_relations
    
    def _apply_temporal_ranking(self, results: Dict, query: str) -> Dict:
        """Apply temporal bias to ranking"""
        # Boost recent results for temporal queries
        for result_type in ['vector_results', 'graph_results']:
            if result_type in results and results[result_type]:
                for item in results[result_type]:
                    if isinstance(item, dict) and 'created_at' in item:
                        # Simple temporal boost (you'd want more sophisticated logic)
                        try:
                            # Boost recent items
                            item['temporal_boost'] = 1.1 if 'recent' in query.lower() else 1.0
                        except:
                            pass
        return results
    
    def _advanced_synthesis(self, vector_results, graph_results, vertexai_results, query: str) -> List[Dict]:
        """Advanced synthesis across multiple sources"""
        insights = []
        
        # Cross-reference insights
        if vector_results and graph_results:
            # Find overlapping entities/concepts
            vector_entities = self._extract_entities_from_vector(vector_results)
            graph_entities = self._extract_entities_from_graph(graph_results)
            
            overlapping = set(vector_entities) & set(graph_entities)
            if overlapping:
                insights.append({
                    'type': 'cross_validation',
                    'entities': list(overlapping),
                    'confidence': 0.9,
                    'description': f"Found {len(overlapping)} entities confirmed across vector and graph sources"
                })
        
        # Identify contradictions or complementary information
        if len([r for r in [vector_results, graph_results, vertexai_results] if r]) > 1:
            insights.append({
                'type': 'multi_source_confirmation',
                'sources_count': len([r for r in [vector_results, graph_results, vertexai_results] if r]),
                'confidence': 0.8,
                'description': "Information corroborated across multiple sources"
            })
        
        return insights
    
    def _extract_entities_from_vector(self, results) -> List[str]:
        """Extract entities from vector search results"""
        entities = []
        if isinstance(results, dict) and 'documents' in results:
            # Extract key terms from documents (simplified)
            for doc in results['documents'][:5]:  # Top 5 docs
                if isinstance(doc, str):
                    # Simple entity extraction (you'd want proper NER here)
                    words = doc.split()
                    entities.extend([w.strip('.,!?') for w in words if w.istitle() and len(w) > 2])
        return list(set(entities))
    
    def _extract_entities_from_graph(self, results) -> List[str]:
        """Extract entities from graph results"""
        entities = []
        for result in results:
            if isinstance(result, dict):
                entities.extend([result.get('source', ''), result.get('destination', '')])
        return [e for e in entities if e]  # Remove empty strings
    
    def _calculate_expert_confidence(self, results: Dict, expert: ReasoningExpert, query: str) -> float:
        """Calculate confidence score for expert response"""
        base_confidence = 0.5
        
        # Boost confidence based on result richness
        if results:
            result_count = sum(len(v) if isinstance(v, list) else 1 for v in results.values() if v)
            if result_count > 0:
                base_confidence += min(0.3, result_count * 0.05)
        
        # Expert-specific confidence adjustments
        if expert == ReasoningExpert.FACTUAL_RETRIEVAL and any('vector' in k for k in results.keys()):
            base_confidence += 0.1
        elif expert == ReasoningExpert.RELATIONAL_REASONING and 'graph_results' in results:
            base_confidence += 0.15
        
        return min(base_confidence, 1.0)


# Additional utility for smaller model optimization
class SmallModelOptimizer:
    """Optimizations specifically for smaller language models like Qwen2 4B"""
    
    def __init__(self, max_context_length: int = 2048):
        self.max_context_length = max_context_length
        self.context_budget = {
            'system_prompt': 200,
            'query': 100,
            'results': 1500,  # Most of the budget for retrieved context
            'reasoning': 248   # Buffer for reasoning
        }
    
    def optimize_context_for_small_model(self, results: Dict, query: str, expert_type: str) -> str:
        """Create optimized context that fits within model constraints"""
        available_tokens = self.context_budget['results']
        
        # Prioritize result types based on expert
        if expert_type == "factual":
            priority_order = ['vector_results', 'vertexai_results', 'graph_results']
        elif expert_type == "relational":
            priority_order = ['graph_results', 'vector_results', 'vertexai_results']
        else:
            priority_order = ['vector_results', 'graph_results', 'vertexai_results']
        
        context_parts = []
        tokens_used = 0
        
        for result_type in priority_order:
            if result_type in results and results[result_type] and tokens_used < available_tokens:
                formatted_results = self._format_results_for_context(
                    results[result_type], 
                    result_type, 
                    available_tokens - tokens_used
                )
                if formatted_results:
                    context_parts.append(formatted_results)
                    tokens_used += len(formatted_results.split())  # Rough token estimation
        
        return "\n\n".join(context_parts)
    
    def _format_results_for_context(self, results, result_type: str, token_budget: int) -> str:
        """Format results efficiently for small models"""
        if not results:
            return ""
            
        if result_type == 'graph_results':
            return self._format_graph_results(results, token_budget)
        elif result_type == 'vector_results':
            return self._format_vector_results(results, token_budget)
        else:
            return self._format_other_results(results, token_budget)
    
    def _format_graph_results(self, results: List, token_budget: int) -> str:
        """Efficiently format graph results"""
        if not results:
            return ""
            
        formatted = ["RELATIONSHIPS:"]
        tokens_used = 2  # For "RELATIONSHIPS:"
        
        for result in results[:10]:  # Limit to top 10
            if tokens_used >= token_budget * 0.8:  # Use 80% of budget
                break
                
            rel_str = f"• {result.get('source', '')} → {result.get('relationship', '')} → {result.get('destination', '')}"
            rel_tokens = len(rel_str.split())
            
            if tokens_used + rel_tokens < token_budget:
                formatted.append(rel_str)
                tokens_used += rel_tokens
        
        return "\n".join(formatted)
    
    def _format_vector_results(self, results: Dict, token_budget: int) -> str:
        """Efficiently format vector search results"""
        if not results or 'documents' not in results:
            return ""
            
        formatted = ["DOCUMENTS:"]
        tokens_used = 2
        
        for i, doc in enumerate(results['documents'][:5]):  # Top 5 docs
            if tokens_used >= token_budget * 0.8:
                break
                
            # Extract key sentences (first 2-3 sentences)
            doc_str = str(doc)
            sentences = doc_str.split('.')[:3]  # First 3 sentences
            snippet = '. '.join(sentences).strip()[:200]  # Max 200 chars
            
            doc_tokens = len(snippet.split())
            if tokens_used + doc_tokens < token_budget:
                formatted.append(f"Doc {i+1}: {snippet}")
                tokens_used += doc_tokens
        
        return "\n".join(formatted)
    
    def _format_other_results(self, results, token_budget: int) -> str:
        """Format other result types"""
        if isinstance(results, str):
            # Truncate string results
            words = results.split()[:token_budget//2]  # Conservative estimate
            return " ".join(words)
        return str(results)[:token_budget*4]  # Very rough token estimation

    def create_optimized_prompt(self, query: str, context: str, expert_type: str) -> str:
        """Create optimized prompts for smaller models"""
        templates = {
            "factual": f"""Context: {context}

            Question: {query}

            Based on the context above, provide a direct and concise answer:""",

                        "relational": f"""Relationships: {context}

            Question: {query}

            Analyze the relationships and explain how they connect to answer the question:""",

                        "synthesis": f"""Multiple Sources: {context}

            Question: {query}

            Synthesize information from all sources to provide a comprehensive answer:"""
        }
        
        return templates.get(expert_type, templates["factual"])


@tool
def search_for_memories_openrag(raw_query: str, state: Annotated[AgentState, InjectedState]):
    """
    Intelligent memory search with expert routing and enhanced reasoning.
    
    This enhanced version:
    1. Analyzes query complexity to route to appropriate reasoning experts
    2. Uses specialized expert strategies for different query types
    3. Optimizes context length for smaller models
    4. Provides structured prompts for better small-model performance
    5. Combines multiple expert responses intelligently
    
    Args:
        raw_query (str): User's natural language question or request
        
    Returns:
        str: Comprehensive search results with expert reasoning and synthesis
    """
    overall_start_time = time.time()
    print(f"Starting Open-RAG inspired search for: '{raw_query}'")
    
    chat_history = convert_to_chat_history(state["messages"])
    
    # Step 1: Analyze query for expert routing
    analyzer = OpenRAGQueryAnalyzer()
    query_analysis = analyzer.analyze_query(raw_query, chat_history)
    
    print(f"Query Analysis:")
    print(f"  Complexity: {query_analysis.complexity.value}")
    print(f"  Primary Expert: {query_analysis.primary_expert.value}")
    print(f"  Secondary Experts: {[e.value for e in query_analysis.secondary_experts]}")
    print(f"  Confidence: {query_analysis.confidence:.2f}")
    
    # Step 2: For smaller models, limit strategic query generation
    strategic_queries = analyze_and_generate_queries(raw_query, chat_history)
    # Limit to top 2-3 queries for smaller models to reduce complexity
    strategic_queries = strategic_queries[:3]
    print(f"Generated {len(strategic_queries)} strategic queries (limited for model efficiency)")
    
    # Step 3: Execute expert-based search with small model optimization
    expert_engine = ReasoningExpertEngine(app_env.APP_USERNAME)
    optimizer = SmallModelOptimizer()
    expert_responses = []
    
    # For smaller models: Execute primary expert first, then decide on secondary
    context = {
        "strategic_queries": strategic_queries, 
        "chat_history": chat_history,
        "optimizer": optimizer
    }
    
    primary_response = expert_engine.execute_expert_sync_only(
        query_analysis.primary_expert, 
        raw_query, 
        context
    )
    expert_responses.append(primary_response)
    
    # Only execute secondary experts if primary confidence is low
    if query_analysis.secondary_experts and primary_response.confidence < 0.7:
        print("Primary expert confidence low, consulting secondary experts")
        # Limit to 1 secondary expert for smaller models
        secondary_expert = query_analysis.secondary_experts[0]
        
        secondary_response = expert_engine.execute_expert_sync_only(
            secondary_expert, raw_query, context
        )
        expert_responses.append(secondary_response)
    
    # Step 4: Optimized synthesis for smaller models
    final_synthesis = synthesize_expert_responses_optimized(
        expert_responses, raw_query, query_analysis, optimizer
    )
    
    total_time = time.time() - overall_start_time
    print(f"Open-RAG search completed in {total_time:.3f}s")
    
    return final_synthesis

def synthesize_expert_responses_optimized(expert_responses: List[ExpertResponse], 
                                        original_query: str, 
                                        query_analysis: QueryAnalysis,
                                        optimizer: SmallModelOptimizer) -> str:
    """
    Optimized synthesis for smaller models with token-aware formatting.
    """
    # For smaller models: Simpler, more direct synthesis
    if len(expert_responses) == 1:
        # Single expert response - format directly
        response = expert_responses[0]
        return format_single_expert_response(response, original_query, optimizer)
    
    # Multiple experts - selective combination
    primary_response = expert_responses[0]
    secondary_responses = expert_responses[1:]
    
    # Combine results with priority on primary expert
    combined_results = primary_response.results.copy()
    
    # Merge secondary results only if they add value
    for secondary in secondary_responses:
        for key, value in secondary.results.items():
            if key not in combined_results or not combined_results[key]:
                combined_results[key] = value
            elif isinstance(value, list) and isinstance(combined_results[key], list):
                # Merge lists but limit total size
                combined_results[key].extend(value)
                combined_results[key] = combined_results[key][:10]  # Limit to top 10
    
    # Create optimized context
    optimized_context = optimizer.optimize_context_for_small_model(
        combined_results, original_query, primary_response.expert_type.value
    )
    
    return format_optimized_results(optimized_context, expert_responses, original_query)

def format_single_expert_response(response: ExpertResponse, query: str, optimizer: SmallModelOptimizer) -> str:
    """Format single expert response for optimal readability"""
    output_parts = []
    
    # Simple header
    output_parts.append(f"=== Search Results ({response.expert_type.value.title()} Expert) ===\n")
    
    # Optimized context
    context = optimizer.optimize_context_for_small_model(
        response.results, query, response.expert_type.value
    )
    
    if context:
        output_parts.append(context)
    else:
        output_parts.append("No relevant results found.")
    
    # Add confidence and execution time
    output_parts.append(f"\n--- Metadata ---")
    output_parts.append(f"Confidence: {response.confidence:.2f}")
    output_parts.append(f"Execution Time: {response.execution_time:.2f}s")
    
    return "\n".join(output_parts)

def format_optimized_results(context: str, expert_responses: List[ExpertResponse], query: str) -> str:
    """Format results optimized for smaller model consumption"""
    output_parts = []
    
    # Simple header
    expert_types = [r.expert_type.value for r in expert_responses]
    output_parts.append(f"=== Multi-Expert Search Results ===")
    output_parts.append(f"Consulted: {', '.join(expert_types)}\n")
    
    # Main content
    if context:
        output_parts.append(context)
    else:
        output_parts.append("No relevant results found across all experts.")
    
    # Simple metadata
    avg_confidence = sum(r.confidence for r in expert_responses) / len(expert_responses)
    total_time = sum(r.execution_time for r in expert_responses)
    
    output_parts.append(f"\n--- Summary ---")
    output_parts.append(f"Average Confidence: {avg_confidence:.2f}")
    output_parts.append(f"Total Processing Time: {total_time:.2f}s")
    
    return "\n".join(output_parts)


def synthesize_expert_responses(expert_responses: List[ExpertResponse], 
                              original_query: str, 
                              query_analysis: QueryAnalysis) -> str:
    """
    Meta-synthesis of multiple expert responses with reasoning transparency.
    """
    synthesis_parts = []
    
    # Header with analysis summary
    synthesis_parts.append(f"=== Open-RAG Enhanced Search Results ===")
    synthesis_parts.append(f"Query Complexity: {query_analysis.complexity.value}")
    synthesis_parts.append(f"Experts Consulted: {len(expert_responses)}")
    synthesis_parts.append("")
    
    # Combine results by confidence and relevance
    all_results = {"vector_results": [], "graph_results": [], "vertexai_results": []}
    reasoning_summary = []
    
    for response in expert_responses:
        # Weight results by expert confidence
        weight = response.confidence
        
        # Add weighted results
        for result_type in all_results.keys():
            if result_type in response.results and response.results[result_type]:
                weighted_results = response.results[result_type]
                if isinstance(weighted_results, list):
                    for item in weighted_results:
                        if isinstance(item, dict):
                            item['expert_weight'] = weight
                            item['expert_source'] = response.expert_type.value
                    all_results[result_type].extend(weighted_results)
                
        # Collect reasoning traces
        reasoning_summary.extend([
            f"[{response.expert_type.value.upper()}]: {trace}" 
            for trace in response.reasoning_trace
        ])
    
    # Apply final ranking and deduplication
    final_results = {}
    for result_type, results in all_results.items():
        if results:
            # Remove duplicates and rank by expert weight + similarity
            final_results[result_type] = deduplicate_and_rank_by_expert_weight(results)
    
    # Format final output
    formatted_results = format_expert_synthesized_results(
        final_results, reasoning_summary, len(expert_responses)
    )
    
    return formatted_results

def deduplicate_and_rank_by_expert_weight(results: List[Dict]) -> List[Dict]:
    """Enhanced deduplication considering expert weights"""
    if not results:
        return []
    
    # Simple deduplication by content similarity (you'd want more sophisticated logic)
    unique_results = []
    seen_content = set()
    
    for result in results:
        # Create a simple content hash for deduplication
        content_key = str(result.get('content', ''))[:100]  # First 100 chars
        if content_key not in seen_content:
            seen_content.add(content_key)
            unique_results.append(result)
    
    # Sort by combined score of similarity and expert weight
    def scoring_function(item):
        similarity = item.get('similarity', 0.5)
        expert_weight = item.get('expert_weight', 0.5)
        return (similarity * 0.6) + (expert_weight * 0.4)  # Weighted combination
    
    return sorted(unique_results, key=scoring_function, reverse=True)

def format_expert_synthesized_results(results: Dict, reasoning_summary: List[str], expert_count: int) -> str:
    """Format the final synthesized results with reasoning transparency"""
    output_parts = []
    
    # Results summary
    total_results = sum(len(v) for v in results.values())
    output_parts.append(f"Found {total_results} results from {expert_count} reasoning experts\n")
    
    # Top results from each source
    for source_type, source_results in results.items():
        if source_results:
            output_parts.append(f"=== {source_type.replace('_', ' ').title()} ===")
            
            for i, result in enumerate(source_results[:5]):  # Top 5 from each source
                expert_source = result.get('expert_source', 'unknown')
                confidence = result.get('expert_weight', 0.5)
                
                if source_type == 'graph_results':
                    output_parts.append(
                        f"{i+1}. [{expert_source}] {result.get('source', '')} "
                        f"--{result.get('relationship', '')}-> {result.get('destination', '')} "
                        f"(confidence: {confidence:.2f})"
                    )
                else:
                    content = str(result.get('content', result))[:200]
                    output_parts.append(f"{i+1}. [{expert_source}] {content}... (confidence: {confidence:.2f})")
            
            output_parts.append("")
    
    # Reasoning transparency
    output_parts.append("=== Expert Reasoning Traces ===")
    for trace in reasoning_summary[:10]:  # Top 10 reasoning steps
        output_parts.append(f"• {trace}")
    
    return "\n".join(output_parts)

def convert_to_chat_history(messages: List[AnyMessage]) -> str:
    """
    Converts LangChain messages list into a chat_history str.
    """
    chat_history = ""
    for message in messages:
        if isinstance(message, HumanMessage):
            chat_history += f"Human: {message.content}\n"
        elif isinstance(message, AIMessage):
            chat_history += f"Assistant: {message.content}\n"
    return chat_history
