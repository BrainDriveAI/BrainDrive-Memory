from app.data_source_manager import get_graph_db_instance


def delete_entities(to_be_deleted, user_id):
    """Delete the entities from the graph."""
    graph_db_service = get_graph_db_instance()
    results = []
    for item in to_be_deleted:
        source = item["source"]
        destination = item["destination"]
        relationship = item["relationship"]

        # Delete the specific relationship between nodes
        cypher = f"""
        MATCH (n {{name: $source_name, user_id: $user_id}})
        -[r:{relationship}]->
        (m {{name: $dest_name, user_id: $user_id}})
        DELETE r
        RETURN 
            n.name AS source,
            m.name AS target,
            type(r) AS relationship
        """
        params = {
            "source_name": source,
            "dest_name": destination,
            "user_id": user_id,
        }
        result = graph_db_service.query(cypher, params=params)
        results.append(result)
    return results
