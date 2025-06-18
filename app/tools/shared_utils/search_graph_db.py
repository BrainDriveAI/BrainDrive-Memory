from app.adapters.embedder_adapter import embedder
from app.data_source_manager import get_graph_db_instance
import time
import concurrent.futures

default_cypher_query = """
MATCH (n)
WHERE n.embedding IS NOT NULL AND n.user_id = $user_id
WITH n,
    round(reduce(dot = 0.0, i IN range(0, size(n.embedding)-1) | dot + n.embedding[i] * $n_embedding[i]) /
    (sqrt(reduce(l2 = 0.0, i IN range(0, size(n.embedding)-1) | l2 + n.embedding[i] * n.embedding[i])) *
    sqrt(reduce(l2 = 0.0, i IN range(0, size($n_embedding)-1) | l2 + $n_embedding[i] * $n_embedding[i]))), 4) AS similarity
WHERE similarity >= $threshold
MATCH (n)-[r]->(m)
RETURN n.name AS source, elementId(n) AS source_id, type(r) AS relationship, elementId(r) AS relation_id, m.name AS destination, elementId(m) AS destination_id, similarity
UNION
MATCH (n)
WHERE n.embedding IS NOT NULL AND n.user_id = $user_id
WITH n,
    round(reduce(dot = 0.0, i IN range(0, size(n.embedding)-1) | dot + n.embedding[i] * $n_embedding[i]) /
    (sqrt(reduce(l2 = 0.0, i IN range(0, size(n.embedding)-1) | l2 + n.embedding[i] * n.embedding[i])) *
    sqrt(reduce(l2 = 0.0, i IN range(0, size($n_embedding)-1) | l2 + $n_embedding[i] * $n_embedding[i]))), 4) AS similarity
WHERE similarity >= $threshold
MATCH (m)-[r]->(n)
RETURN m.name AS source, elementId(m) AS source_id, type(r) AS relationship, elementId(r) AS relation_id, n.name AS destination, elementId(n) AS destination_id, similarity
ORDER BY similarity DESC
LIMIT $limit
"""

optimized_cypher_query = """
CALL db.index.vector.queryNodes('entity_embedding_index', $neighboursPerEmb, $n_embedding) 
YIELD node AS n, score AS similarity
WHERE n.user_id = $user_id AND similarity >= $threshold
MATCH (n)-[r]->(m)
RETURN n.name AS source,
    elementId(n) AS source_id,
    type(r) AS relationship,
    elementId(r) AS relation_id,
    m.name AS destination,
    elementId(m) AS destination_id,
    r.created_at  AS created_at,
    r.updated_at  AS updated_at,
    similarity
UNION
CALL db.index.vector.queryNodes('entity_embedding_index', $neighboursPerEmb, $n_embedding) 
YIELD node AS n, score AS similarity
WHERE n.user_id = $user_id AND similarity >= $threshold
MATCH (m)-[r]->(n)
RETURN m.name AS source,
    elementId(m) AS source_id,
    type(r) AS relationship,
    elementId(r) AS relation_id,
    n.name AS destination,
    elementId(n) AS destination_id,
    r.created_at  AS created_at,
    r.updated_at  AS updated_at,
    similarity
ORDER BY similarity DESC
LIMIT $limit
"""

batch_cypher_query = """
UNWIND $embeddings AS embedding_data
CALL db.index.vector.queryNodes('entity_embedding_index', $neighboursPerEmb, embedding_data) 
YIELD node AS n, score AS similarity
WHERE n.user_id = $user_id AND similarity >= $threshold
WITH n, similarity
MATCH (n)-[r]->(m)
RETURN n.name AS source, elementId(n) AS source_id, 
        type(r) AS relationship, elementId(r) AS relation_id, 
        m.name AS destination, elementId(m) AS destination_id, similarity
UNION
UNWIND $embeddings AS embedding_data
CALL db.index.vector.queryNodes('entity_embedding_index', $neighboursPerEmb, embedding_data) 
YIELD node AS n, score AS similarity
WHERE n.user_id = $user_id AND similarity >= $threshold
WITH n, similarity
MATCH (m)-[r]->(n)
RETURN m.name AS source, elementId(m) AS source_id, 
        type(r) AS relationship, elementId(r) AS relation_id, 
        n.name AS destination, elementId(n) AS destination_id, similarity
ORDER BY similarity DESC
LIMIT $limit;
"""


def search_graph_db(node_list, user_id, limit=10):
    """Search similar nodes among and their respective incoming and outgoing relations."""
    start_time = time.time()
    
    threshold = 0.9
    result_relations = []
    print(f"Node list: ${node_list}")

    params = {
        "embeddings": [embedder.embed_query(n) for n in node_list],
        "neighboursPerEmb": limit * 2,
        "limit": limit,
        "user_id": user_id,
        "threshold": threshold
    }
    graph_db_service = get_graph_db_instance()
    result_relations = graph_db_service.query(batch_cypher_query, params=params)

    total_time = time.time() - start_time
    print(f"Total search time: {total_time:.3f}s for {len(node_list)} nodes")
    return result_relations


def search_graph_db_by_query(query: str, user_id: str, limit=5):
    """Search similar nodes among and their respective incoming and outgoing relations."""
    start_time = time.time()
    
    threshold = 0.8
    result_relations = []

    params = {
        "n_embedding": embedder.embed_query(query),
        "neighboursPerEmb": limit * 1,
        "limit": limit,
        "user_id": user_id,
        "threshold": threshold
    }
    graph_db_service = get_graph_db_instance()
    result_relations = graph_db_service.query(optimized_cypher_query, params=params)

    total_time = time.time() - start_time
    print(f"Total search time: {total_time:.3f}s for {query} query")
    return result_relations


def parallel_search_graph_db(node_list, user_id, limit=10):
    """Search using parallel processing."""
    start_time = time.time()
    
    # Compute embeddings (still potentially a bottleneck)
    embedding_start = time.time()
    node_embeddings = {node: embedder.embed_query(node) for node in node_list}
    embedding_time = time.time() - embedding_start
    
    # Prepare query jobs
    threshold = 0.8
    query_jobs = []
    
    for node, embedding in node_embeddings.items():
        params = {
            "n_embedding": embedding,
            "threshold": threshold,
            "user_id": user_id,
            "limit": limit,
        }
        query_jobs.append((node, optimized_cypher_query, params))
    
    # Execute queries in parallel
    query_start = time.time()
    
    def execute_query(job):
        node, query, params = job
        graph_db_service = get_graph_db_instance()
        results = graph_db_service.query(query, params=params)
        return node, results
    
    # Using thread pool as Neo4j connections are typically thread-safe
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(query_jobs))) as executor:
        query_results = list(executor.map(execute_query, query_jobs))
    
    query_time = time.time() - query_start
    
    # Process results
    result_relations = []
    for node, results in query_results:
        print(f"Node '{node}': Results: {len(results)}")
        result_relations.extend(results)
    
    total_time = time.time() - start_time
    print(f"Total search time: {total_time:.3f}s (Embedding: {embedding_time:.3f}s, Query: {query_time:.3f}s)")
    
    return result_relations
