import re
from app.adapters.embedder_adapter import embedder
from app.data_source_manager import get_graph_db_instance


def _search_source_node(source_embedding, user_id, threshold=0.9):
    graph_db_service = get_graph_db_instance()
    cypher = """
        MATCH (source_candidate)
        WHERE source_candidate.embedding IS NOT NULL 
        AND source_candidate.user_id = $user_id

        WITH source_candidate,
            round(
                reduce(dot = 0.0, i IN range(0, size(source_candidate.embedding)-1) |
                    dot + source_candidate.embedding[i] * $source_embedding[i]) /
                (sqrt(reduce(l2 = 0.0, i IN range(0, size(source_candidate.embedding)-1) |
                    l2 + source_candidate.embedding[i] * source_candidate.embedding[i])) *
                sqrt(reduce(l2 = 0.0, i IN range(0, size($source_embedding)-1) |
                    l2 + $source_embedding[i] * $source_embedding[i])))
            , 4) AS source_similarity
        WHERE source_similarity >= $threshold

        WITH source_candidate, source_similarity
        ORDER BY source_similarity DESC
        LIMIT 1

        RETURN elementId(source_candidate)
        """

    params = {
        "source_embedding": source_embedding,
        "user_id": user_id,
        "threshold": threshold,
    }

    result = graph_db_service.query(cypher, params=params)
    return result


def _search_destination_node(destination_embedding, user_id, threshold=0.9):
    graph_db_service = get_graph_db_instance()
    cypher = """
        MATCH (destination_candidate)
        WHERE destination_candidate.embedding IS NOT NULL 
        AND destination_candidate.user_id = $user_id

        WITH destination_candidate,
            round(
                reduce(dot = 0.0, i IN range(0, size(destination_candidate.embedding)-1) |
                    dot + destination_candidate.embedding[i] * $destination_embedding[i]) /
                (sqrt(reduce(l2 = 0.0, i IN range(0, size(destination_candidate.embedding)-1) |
                    l2 + destination_candidate.embedding[i] * destination_candidate.embedding[i])) *
                sqrt(reduce(l2 = 0.0, i IN range(0, size($destination_embedding)-1) |
                    l2 + $destination_embedding[i] * $destination_embedding[i])))
            , 4) AS destination_similarity
        WHERE destination_similarity >= $threshold

        WITH destination_candidate, destination_similarity
        ORDER BY destination_similarity DESC
        LIMIT 1

        RETURN elementId(destination_candidate)
        """
    params = {
        "destination_embedding": destination_embedding,
        "user_id": user_id,
        "threshold": threshold,
    }
    result = graph_db_service.query(cypher, params=params)
    return result


def sanitize_string(s):
    # Lowercase the string
    s = s.lower()
    # Replace invalid characters with underscores
    s = re.sub(r"[^\w]+", "_", s)
    # Remove leading or trailing underscores
    s = s.strip("_")
    # Replace multiple underscores with a single underscore
    s = re.sub(r"_+", "_", s)
    return s


def add_entities(to_be_added, user_id, entity_type_map):
    """Add the new entities to the graph. Merge the nodes if they already exist."""
    graph_db_service = get_graph_db_instance()
    results = []
    for item in to_be_added:
        # entities
        source = item["source"]
        destination = item["destination"]
        relationship = sanitize_string(item["relationship"])

        # types
        source_type = entity_type_map.get(source, "unknown")
        destination_type = entity_type_map.get(destination, "unknown")

        # embeddings
        source_embedding = embedder.embed_query(source)
        dest_embedding = embedder.embed_query(destination)

        # search for the nodes with the closest embeddings
        source_node_search_result = _search_source_node(source_embedding, user_id, threshold=0.9)
        destination_node_search_result = _search_destination_node(dest_embedding, user_id, threshold=0.9)

        # TODO: Create a cypher query and common params for all the cases
        if not destination_node_search_result and source_node_search_result:
            cypher = f"""
                MATCH (source)
                    WHERE elementId(source) = $source_id
                MERGE (destination:{destination_type}:Entity {{name: $destination_name, user_id: $user_id}})
                    ON CREATE SET
                        destination.created_at = timestamp(),
                        destination.updated_at = timestamp(),
                        destination.embedding = $destination_embedding
                MERGE (source)-[r:{relationship}]->(destination)
                    ON CREATE SET
                        r.created_at = timestamp(),
                        r.updated_at = timestamp()
                    ON MATCH SET
                        r.updated_at = timestamp()
                RETURN source.name AS source, type(r) AS relationship, destination.name AS target
                """

            params = {
                "source_id": source_node_search_result[0]["elementId(source_candidate)"],
                "destination_name": destination,
                "relationship": relationship,
                "destination_type": destination_type,
                "destination_embedding": dest_embedding,
                "user_id": user_id,
            }
            resp = graph_db_service.query(cypher, params=params)
            results.append(resp)

        elif destination_node_search_result and not source_node_search_result:
            cypher = f"""
                MATCH (destination)
                    WHERE elementId(destination) = $destination_id
                MERGE (source:{source_type}:Entity {{name: $source_name, user_id: $user_id}})
                    ON CREATE SET
                        source.created_at = timestamp(),
                        source.updated_at = timestamp(),
                        source.embedding = $source_embedding
                MERGE (source)-[r:{relationship}]->(destination)
                    ON CREATE SET 
                        r.created_at = timestamp(),
                        r.updated_at = timestamp()
                    ON MATCH SET
                        r.updated_at = timestamp()
                RETURN source.name AS source, type(r) AS relationship, destination.name AS target
                """

            params = {
                "destination_id": destination_node_search_result[0]["elementId(destination_candidate)"],
                "source_name": source,
                "relationship": relationship,
                "source_type": source_type,
                "source_embedding": source_embedding,
                "user_id": user_id,
            }
            resp = graph_db_service.query(cypher, params=params)
            results.append(resp)

        elif source_node_search_result and destination_node_search_result:
            cypher = f"""
                MATCH (source)
                    WHERE elementId(source) = $source_id
                MATCH (destination)
                    WHERE elementId(destination) = $destination_id
                MERGE (source)-[r:{relationship}]->(destination)
                    ON CREATE SET 
                        r.created_at = timestamp(),
                        r.updated_at = timestamp()
                    ON MATCH SET
                        r.updated_at = timestamp()
                RETURN source.name AS source, type(r) AS relationship, destination.name AS target
                """
            params = {
                "source_id": source_node_search_result[0]["elementId(source_candidate)"],
                "destination_id": destination_node_search_result[0]["elementId(destination_candidate)"],
                "user_id": user_id,
                "relationship": relationship,
            }
            resp = graph_db_service.query(cypher, params=params)
            results.append(resp)

        elif not source_node_search_result and not destination_node_search_result:
            cypher = f"""
                MERGE (n:{source_type}:Entity {{name: $source_name, user_id: $user_id}})
                    ON CREATE SET
                        n.created_at = timestamp(),
                        n.updated_at = timestamp(),
                        n.embedding = $source_embedding
                    ON MATCH SET
                        n.updated_at = timestamp(),
                        n.embedding = $source_embedding
                MERGE (m:{destination_type}:Entity {{name: $dest_name, user_id: $user_id}})
                    ON CREATE SET
                        m.created_at = timestamp(),
                        m.updated_at = timestamp(),
                        m.embedding = $dest_embedding
                    ON MATCH SET
                        m.updated_at = timestamp(),
                        m.embedding = $dest_embedding
                MERGE (n)-[rel:{relationship}]->(m)
                    ON CREATE SET
                        rel.created_at = timestamp(),
                        rel.updated_at = timestamp()
                    ON MATCH SET
                        rel.updated_at = timestamp()
                RETURN n.name AS source, type(rel) AS relationship, m.name AS target
                """
            params = {
                "source_name": source,
                "source_type": source_type,
                "dest_name": destination,
                "destination_type": destination_type,
                "source_embedding": source_embedding,
                "dest_embedding": dest_embedding,
                "user_id": user_id,
            }
            resp = graph_db_service.query(cypher, params=params)
            results.append(resp)
    return results
