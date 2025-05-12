from typing import Optional, Type
from langchain_core.tools import tool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from app.services.document_processing_service import search_by_embedding, search_for_all_documents
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class SearchForDocumentSnippetsArgs(BaseModel):
    query: str = Field(description="Query to search for (must be detailed)")


class SearchForDocumentSnippetsTool(BaseTool):
    name: str = "search_for_document_snippets"
    description: str = "Search for document snippets based on a given query."
    args_schema: Type[BaseModel] = SearchForDocumentSnippetsArgs

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return search_by_embedding(query)

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        return search_by_embedding(query)


@tool
def search_for_doc_snippets(query: str):
    """Use the tool to search for document snippets based on a given query."""
    return search_by_embedding(query)


class SearchForDocumentArgs(BaseModel):
    query: str = Field(description="Query to search for (must be detailed)")


class SearchForDocumentsTool(BaseTool):
    name: str = "search_for_uploaded_documents"
    description: str = "Use this tool to search for uploaded documents and their urls."
    args_schema: Type[BaseModel] = SearchForDocumentArgs

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return search_for_all_documents(query)

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        return search_for_all_documents(query)


@tool
def search_for_documents(query: str):
    """Use the tool to search for uploaded documents and their urls."""
    return search_for_all_documents(query)
