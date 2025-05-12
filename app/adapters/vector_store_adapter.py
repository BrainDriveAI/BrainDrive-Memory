import uuid

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client

from app.adapters.embedder_adapter import embedder
from app.interfaces.vector_store_interface import VectorStoreInterface


class SupabaseVectorStoreAdapter(VectorStoreInterface):
    def __init__(self, url: str, key: str, collection_name: str, query_function_name: str):
        self.supabase_client: Client = create_client(url, key)
        self.vector_store = SupabaseVectorStore(
            embedding=embedder,
            client=self.supabase_client,
            table_name=collection_name,
            query_name=query_function_name,
        )
        self.embedder = embedder

    def add_document(self, source_content: str, user_id: str) -> List[str]:
        """
        Adds document to Supabase.
        Ensures metadata like user_id is part of the Document objects themselves.
        """
        # Ensure all documents have IDs if not provided
        doc_id = str(uuid.uuid4())
        documents = [
            Document(
                page_content=source_content,
                metadata={"id": doc_id, "user_id": user_id,},
            )
        ]
        return self.vector_store.add_documents(documents, ids=[doc_id])

    def similarity_search(self, query: str, k: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        return self.vector_store.similarity_search(query, k=k, filter=filter)

    def delete_document(self, ids: List[str]) -> bool:
        if not ids:
            return False
        try:
            self.vector_store.delete(ids=ids)
            return True
        except Exception as e:
            # Log the error appropriately
            print(f"Warning: Failed to delete documents {ids}. Error: {e}")
            return False

    def hybrid_search(self, query: str, filter_params: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Implements hybrid search using Supabase RPC.
        `filter_params` can include `user_id` or other parameters for the RPC.
        """
        rpc_params = {
            "query_text": query,
            "query_embedding": self.embedder.embed_query(query),
            "match_count": 10,
        }
        if filter_params:
            # Example: map a generic 'user_id' from filter_params to 'filter_user_id' for RPC
            if "user_id" in filter_params:
                rpc_params["filter_user_id"] = filter_params["user_id"]
            # Add other specific mappings as needed

        rpc_response = (
            self.supabase_client
            .rpc(
                self.vector_store.query_name, # Use the configured query_name
                rpc_params,
            )
            .execute()
        )

        rows = rpc_response.data or []
        return [
            Document(page_content=row["content"], metadata=row["metadata"])
            for row in rows
        ]
