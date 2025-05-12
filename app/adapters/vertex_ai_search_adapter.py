import os

from langchain_core.documents import Document
from typing import Any, Dict, List, Optional

try:
    from langchain_google_community import VertexAISearchRetriever
except ImportError:
    raise ImportError("langchain_google_community is not installed. Please install it using pip install "
                      "langchain_google_community")

try:
    from google.oauth2 import service_account
except ImportError:
    raise ImportError("google.oauth2 is not installed. Please install it using pip install google.oauth2")

from app.interfaces.vertex_ai_search_interface import VertexAISearchInterface

SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "braindrive_service_account.json")


class VertexAISearchAdapter(VertexAISearchInterface):
    def __init__(self, project_id: Optional[str], location_id: Optional[str], datastore_id: Optional[str]):
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

        self._retriever = VertexAISearchRetriever(
            project_id=project_id,
            location_id=location_id,
            data_store_id=datastore_id,
            get_extractive_answers=True,
            max_documents=10,
            credentials=credentials,
            beta=True
        )

    def retrieve(self, query: str) -> List[Document]:
        return self._retriever.invoke(query)
