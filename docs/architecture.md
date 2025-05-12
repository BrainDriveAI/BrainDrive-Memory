# Architecture Documentation

This document provides an overview of the BrainDrive Memory AI Agent architecture, explaining how various components interact to deliver a comprehensive Personal Knowledge Management (PKM) system.

## High-Level Architecture

BrainDrive Memory follows a modular architecture with several key components:

```
┌───────────────────┐     ┌───────────────────┐     ┌────────────────────┐
│                   │     │                   │     │                    │
│  Presentation     │────▶│   Agent Layer     │────▶│   Data Services    │
│  (Streamlit UI)   │     │   (LangGraph)     │     │                    │
│                   │     │                   │     │                    │
└───────────────────┘     └───────────────────┘     └────────────────────┘
                                    │                         │
                                    ▼                         ▼
                          ┌───────────────────┐     ┌────────────────────┐
                          │                   │     │                    │
                          │    Tools &        │     │   Data Sources     │
                          │    Adapters       │     │                    │
                          │                   │     │                    │
                          └───────────────────┘     └────────────────────┘
```

## Core Components

### Presentation Layer

The presentation layer handles user interaction through a Streamlit-based chat interface (`app/presentation/web/streamlit/chat_ui.py`). Key responsibilities:

- Rendering the chat interface
- File upload handling
- User authentication via Google OAuth
- Streaming responses from the LLM
- Managing conversation state

### Agent Layer

The agent layer orchestrates the AI-driven interactions, powered by LangGraph and LangChain. The primary component is:

- `app/agents/react_graph_agent.py`: Implements a ReAct-style agent using LangGraph for reasoning and tool execution

### Data Services Layer

The data services layer manages data operations and abstractions:

- `app/data_source_manager.py`: Provides a unified interface to different data sources
- `app/services/pdf_processing_service.py`: Handles PDF upload and processing
- `app/services/auth_service.py`: Manages user authentication

### Tools Layer

The tools layer implements specific functionalities that can be invoked by the agent:

- `app/tools/search/search_tool.py`: Search through knowledge base
- `app/tools/add/add_tool.py`: Add new information to knowledge base
- `app/tools/update/update_tool.py`: Update existing information
- `app/tools/delete/delete_tool.py`: Delete information
- `app/tools/documents_search/documents_search_tool.py`: Search through uploaded documents

### Adapters Layer

Adapters provide standardized interfaces to various external services:

- `app/adapters/graph_db_adapter.py`: Interface to Neo4j
- `app/adapters/vector_store_adapter.py`: Interface to Supabase vector store
- `app/adapters/llm_adapter.py`: Interface to language models (OpenAI, Groq, etc.)
- `app/adapters/embedder_adapter.py`: Interface to embedding models
- `app/adapters/vertex_ai_search_adapter.py`: Interface to Vertex AI Search

### Interfaces Layer

The interfaces layer defines abstract interfaces that adapters implement:

- `app/interfaces/graph_db_interface.py`
- `app/interfaces/vector_store_interface.py`
- `app/interfaces/vertex_ai_search_interface.py`

## Data Flow

### Document Processing Flow

When a user uploads a PDF document:

1. The PDF is uploaded via Streamlit UI (`chat_ui.py`)
2. The file is saved temporarily and passed to `parseAndIngestPDFs` in `app/services/document_processing_service.py`
3. The file is uploaded to Google Cloud Storage
4. LLMSherpa processes the document, extracting structure, text, and tables
5. Document structure and content are stored in Neo4j, with embeddings generated for each section, chunk, and table
6. Relevant metadata is stored in the vector database for semantic search

### Query Processing Flow

When a user asks a question:

1. The query is sent from the UI to the agent (`react_graph_agent.py`)
2. The agent processes the query using LangGraph
3. The agent selects appropriate tools based on the query intent
4. Tools interact with data sources via adapters
5. Results are returned to the agent, which formulates a response
6. The response is streamed back to the UI

## Database Schema

### Neo4j Graph Schema

The knowledge graph in Neo4j uses the following node types:

- `Document`: Represents an uploaded document
- `Section`: Represents a section within a document
- `Chunk`: Represents a text chunk within a section
- `Table`: Represents a table extracted from a document

Relationships between nodes:
- `(:Section)-[:HAS_DOCUMENT]->(:Document)`
- `(:Chunk)-[:HAS_PARENT]->(:Section)`
- `(:Table)-[:HAS_PARENT]->(:Section)`
- `(:Table)-[:HAS_PARENT]->(:Document)`
- `(:Section)-[:UNDER_SECTION]->(:Section)`

### Vector Store Schema

The vector store contains:
- Document chunks with embeddings
- Metadata including source, document ID, and context

## Configuration System

The application uses a hierarchical configuration system:

1. `app_env.py`: Centralizes environment variable management using Pydantic
2. `.env` file: Stores local configuration
3. Environment variables: Can override `.env` values

## Extension Points

The modularized architecture supports several extension points:

### Adding New Data Sources

1. Define a new interface in `app/interfaces/`
2. Implement an adapter in `app/adapters/`
3. Update `app/data_source_manager.py` to include the new data source
4. Add appropriate settings in `app/app_env.py`

### Adding New LLM Providers

1. Update `app/adapters/llm_adapter.py` to support the new provider
2. Add appropriate settings in `app/app_env.py`

### Adding New Tools

1. Implement the tool in `app/tools/`
2. Add the tool to the tools list in `app/agents/react_graph_agent.py`

## Deployment Architecture

For production deployments, consider the following architecture:

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│                  │    │                  │    │                  │
│  Load Balancer   │───▶│  Memory AI Agent │───▶│   Neo4j Graph    │
│                  │    │  Containers      │    │   Database       │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                               │                          ▲
                               │                          │
                               ▼                          │
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│                  │    │                  │    │                  │
│  Google Cloud    │◀───│  LLM/Embedding   │───▶│  Supabase Vector │
│  Storage         │    │  Services        │    │  Store           │
│                  │    │                  │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

This architecture provides scalability and resilience for production workloads.