import hashlib
from datetime import datetime
from collections import defaultdict
import re

def deduplicate_results(results: list) -> list:
    """
    Remove duplicate results based on content similarity and exact matches.
    Uses multiple deduplication strategies for comprehensive cleaning.
    """
    if not results:
        return []
    
    seen_hashes = set()
    seen_content = set()
    unique_results = []
    
    for result in results:
        if not result:
            continue
            
        # Handle different result formats
        content = ""
        if isinstance(result, dict):
            # For vector/graph results, use content or source fields
            content = result.get('content', '') or result.get('source', '') or str(result)
        elif isinstance(result, str):
            content = result
        else:
            content = str(result)
        
        if not content or len(content.strip()) < 10:  # Skip very short/empty content
            continue
            
        # Clean and normalize content for comparison
        normalized_content = re.sub(r'\s+', ' ', content.lower().strip())
        
        # Create content hash for exact duplicate detection
        content_hash = hashlib.md5(normalized_content.encode()).hexdigest()
        
        # Skip exact duplicates
        if content_hash in seen_hashes:
            continue
            
        # Skip very similar content (first 100 chars)
        content_prefix = normalized_content[:100]
        if content_prefix in seen_content:
            continue
            
        seen_hashes.add(content_hash)
        seen_content.add(content_prefix)
        unique_results.append(result)
    
    print(f"Deduplication: {len(results)} → {len(unique_results)} results")
    return unique_results

def rank_by_relevance(unique_results: dict, original_query: str) -> dict:
    """
    Rank results by relevance to the original query using multiple scoring factors.
    
    Scoring factors:
    - Keyword overlap with original query
    - Recency (newer = higher score)
    - Result type priority (vector > graph > keyword > vertexai)
    - Content length and quality
    """
    original_query_lower = original_query.lower()
    query_keywords = set(re.findall(r'\w+', original_query_lower))
    
    def calculate_relevance_score(result, result_type: str) -> float:
        score = 0.0
        
        # Extract content for scoring
        content = ""
        created_at = None
        
        if isinstance(result, dict):
            content = result.get('content', '') or result.get('source', '') or str(result)
            # Try to extract timestamp
            created_at = result.get('created_at') or result.get('timestamp')
        else:
            content = str(result)
        
        content_lower = content.lower()
        
        # 1. Keyword overlap score (0-40 points)
        content_words = set(re.findall(r'\w+', content_lower))
        keyword_overlap = len(query_keywords.intersection(content_words))
        if query_keywords:
            keyword_score = (keyword_overlap / len(query_keywords)) * 40
            score += keyword_score
        
        # 2. Substring match bonus (0-20 points)
        if original_query_lower in content_lower:
            score += 20
        elif any(word in content_lower for word in query_keywords if len(word) > 3):
            score += 10
        
        # 3. Result type priority (0-15 points)
        type_scores = {
            'vector_results': 15,
            'graph_results': 12,
            'keyword_results': 8,
            'vertexai_results': 5
        }
        score += type_scores.get(result_type, 0)
        
        # 4. Content quality score (0-15 points)
        content_length = len(content)
        if 50 <= content_length <= 500:  # Optimal length
            score += 15
        elif 20 <= content_length < 50:
            score += 10
        elif content_length > 500:
            score += 8
        
        # 5. Recency bonus (0-10 points)
        if created_at:
            try:
                if isinstance(created_at, str):
                    # Try different date formats
                    date_formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d',
                        '%m/%d/%Y'
                    ]
                    parsed_date = None
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(created_at.split('.')[0], fmt)
                            break
                        except:
                            continue
                    
                    if parsed_date:
                        days_ago = (datetime.now() - parsed_date).days
                        if days_ago <= 7:
                            score += 10
                        elif days_ago <= 30:
                            score += 7
                        elif days_ago <= 90:
                            score += 4
            except:
                pass
        
        return score
    
    # Score and sort each result type
    ranked_results = {}
    for result_type, results in unique_results.items():
        if not results:
            ranked_results[result_type] = []
            continue
            
        # Calculate scores and sort
        scored_results = []
        for result in results:
            score = calculate_relevance_score(result, result_type)
            scored_results.append((score, result))
        
        # Sort by score (descending) and take top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Limit results per type to prevent overwhelming output
        max_results_per_type = {
            'vector_results': 15,
            'graph_results': 10, 
            'keyword_results': 8,
            'vertexai_results': 5
        }
        
        limit = max_results_per_type.get(result_type, 10)
        top_results = [result for score, result in scored_results[:limit]]
        ranked_results[result_type] = top_results
        
        if top_results:
            avg_score = sum(score for score, _ in scored_results[:limit]) / len(scored_results[:limit])
            print(f"Ranked {result_type}: {len(top_results)} results, avg score: {avg_score:.1f}")
    
    return ranked_results

def format_synthesized_results(ranked_results: dict, num_queries: int) -> str:
    """
    Format the final synthesized results into a clean, structured output.
    
    Creates a comprehensive but readable summary of all search results
    organized by source type with relevance indicators.
    """
    output_lines = []
    output_lines.append(f"=== INTELLIGENT MEMORY SEARCH RESULTS ===")
    output_lines.append(f"Analyzed {num_queries} strategic queries across all data sources\n")
    
    total_results = sum(len(results) for results in ranked_results.values())
    if total_results == 0:
        return "No relevant memories found for your query."
    
    output_lines.append(f"Found {total_results} relevant memories:\n")
    
    # Process each result type in priority order
    result_type_info = {
        'vector_results': ('📄 DOCUMENT MEMORIES', 'Personal notes, conversations, and documents'),
        'graph_results': ('🔗 RELATIONSHIP MEMORIES', 'Connected facts and entity relationships'),
        'keyword_results': ('🔍 KEYWORD MATCHES', 'Direct keyword and phrase matches'),
        'vertexai_results': ('🤖 AI-ENHANCED SEARCH', 'Advanced semantic search results')
    }
    
    for result_type in ['vector_results', 'graph_results', 'keyword_results', 'vertexai_results']:
        results = ranked_results.get(result_type, [])
        if not results:
            continue
            
        title, description = result_type_info[result_type]
        output_lines.append(f"{title} ({len(results)} results)")
        output_lines.append(f"{description}")
        output_lines.append("-" * 50)
        
        for i, result in enumerate(results[:10], 1):  # Limit display to top 10 per type
            try:
                formatted_result = format_single_result(result, result_type, i)
                if formatted_result:
                    output_lines.append(formatted_result)
                    output_lines.append("")  # Add spacing
            except Exception as e:
                print(f"Error formatting result {i} from {result_type}: {e}")
                continue
        
        output_lines.append("")  # Section spacing
    
    # Add summary footer
    output_lines.append("=" * 60)
    output_lines.append(f"Search completed. {total_results} total memories retrieved and ranked by relevance.")
    
    return "\n".join(output_lines)

def format_single_result(result, result_type: str, index: int) -> str:
    """Format a single result based on its type and structure."""
    
    if result_type == 'vector_results':
        if isinstance(result, dict):
            content = result.get('content', result.get('page_content', ''))
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'Unknown source')
            
            # Truncate long content
            if len(content) > 300:
                content = content[:300] + "..."
            
            return f"{index}. {content}\n   📁 Source: {source}"
        else:
            content = str(result)[:300]
            return f"{index}. {content}"
    
    elif result_type == 'graph_results':
        if isinstance(result, dict):
            source = result.get('source', '')
            relationship = result.get('relationship', '')
            destination = result.get('destination', '')
            
            if source and relationship and destination:
                return f"{index}. {source} → {relationship} → {destination}"
            else:
                return f"{index}. {str(result)[:200]}"
        else:
            return f"{index}. {str(result)[:200]}"
    
    elif result_type == 'keyword_results':
        if isinstance(result, dict):
            content = result.get('content', result.get('source', ''))
            similarity = result.get('similarity', 0)
            
            if len(content) > 250:
                content = content[:250] + "..."
            
            return f"{index}. {content}\n   🎯 Match confidence: {similarity:.2f}" if similarity else f"{index}. {content}"
        else:
            content = str(result)[:250]
            return f"{index}. {content}"
    
    elif result_type == 'vertexai_results':
        if isinstance(result, dict):
            content = result.get('content', str(result))
        else:
            content = str(result)
        
        if len(content) > 300:
            content = content[:300] + "..."
        
        return f"{index}. {content}"
    
    # Fallback formatting
    content = str(result)[:250] + ("..." if len(str(result)) > 250 else "")
    return f"{index}. {content}"
