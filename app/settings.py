# Application-level settings, including data source provider choices.

# Example:
# ACTIVE_DATA_SOURCES = {
#     "graph_db": "neo4j",  # or "none", or "another_graph_provider"
#     "vector_store": "supabase", # or "none", "chroma", etc.
#     "file_storage": "gcs", # or "local", "none"
#     "external_search": "google_vertex_ai", # or "none"
# }

# For now, let's keep it simple and focus on the graph_db
# In a real scenario, this might be loaded from a YAML, .env, or other config file.

GRAPH_DB_PROVIDER = "neo4j"  # Options: "neo4j", "none"
VECTOR_STORE_PROVIDER = "supabase"  # Options: "supabase", "none", "pinecone", etc.
# LLM_PROVIDER = "openai" # Example for future
