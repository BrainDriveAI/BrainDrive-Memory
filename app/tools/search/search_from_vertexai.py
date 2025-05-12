from app.data_source_manager import get_vertex_ai_search_instance


def search_from_vertexai(query: str) -> str:
    try:
        vertex_ai_search_service = get_vertex_ai_search_instance()
        results = vertex_ai_search_service.retrieve(query)
        combined_content = " ".join(f"Source: {doc.metadata.get('source')}\n Page content: {doc.page_content}\n\n"
                                    f"--------------" for doc in results)
        return combined_content
    except Exception as e:
        print(f"An error occurred: {e}")
