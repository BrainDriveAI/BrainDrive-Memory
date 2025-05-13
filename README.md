# BrainDrive Memory - Your Personal AI Memory Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Your personal AI memory assistant. Unlike basic RAG systems, BrainDrive memory forms connections and updates information like a human mind. The more you use it, the better it knows you, and the more helpful it becomes. It’s modular by design, and because it’s BrainDrive, you own and control your memory, not Big Tech.

## 🌟 Features

- **Powerful Document Processing**: Upload PDFs and extract meaningful information using advanced layout parsing
- **Multi-Modal Data Storage**: Utilizes both graph database (Neo4j) and vector database (Supabase) for rich knowledge representation
- **Conversational AI Interface**: Chat with your data using natural language
- **Advanced Retrieval**: Combines graph-based knowledge and semantic search for accurate information retrieval
- **Google OAuth Authentication**: Secure login using Google accounts
- **Multi-Model LLM Support**: Compatible with various AI model providers including OpenAI, Groq, TogetherAI, and more

## 📋 Architecture

Memory AI Agent combines multiple technologies to create a comprehensive personal knowledge management system:

- **Frontend**: Streamlit-based chat interface
- **Backend**: Python with LangChain, LangGraph for agent reasoning
- **Data Storage**:
  - Neo4j graph database for structured data and relationships
  - Supabase vector store for semantic search
  - Google Cloud Storage for document storage
- **AI Services**:
  - OpenAI APIs for language model capabilities
  - Document parsing with LLMSherpa
  - Google Vertex AI Search integration
  - Multiple embeddings model options

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (optional, for containerized setup)
- Google Cloud account (for GCS, OAuth, and Vertex AI Search)
- Neo4j database
- Supabase account
- OpenAI API key

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/BrainDriveAI/BrainDrive-Memory.git
   cd BrainDrive-Memory
   ```

2. Create a virtual environment and install dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying the example file
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file with your API keys and configuration

5. Run the application
   ```bash
   streamlit run main.py
   ```

See the [installation guide](docs/installation.md) for a complete installation setup.

## 🔧 Configuration

The application uses environment variables for configuration. Key variables include:

| Variable             | Description                           |
|----------------------|---------------------------------------|
| OPENAI_API_KEY       | Your OpenAI API key                   |
| NEO4J_URL            | URL for your Neo4j database           |
| NEO4J_USER           | Neo4j username                        |
| NEO4J_PWD            | Neo4j password                        |
| SUPABASE_URL         | Supabase connection URL               |
| SUPABASE_KEY         | Supabase service role key             |
| GOOGLE_CLIENT_ID     | Google OAuth client ID                |
| GOOGLE_CLIENT_SECRET | Google OAuth client secret            |
| GCS_BUCKET_NAME      | Google Cloud Storage bucket name      |
| VERTEX_AI_PROJECT_ID | Google Cloud Project ID for Vertex AI |

See the [configuration guide](docs/configuration.md) for a complete list of options.

## 🧩 Project Structure

```
braindrive-memory/
├── app/                  # Main application code
│   ├── adapters/         # Adapters for external services
│   ├── agents/           # Agent implementation
│   ├── agent_prompts/    # Prompts for agent behavior
│   ├── interfaces/       # Interface definitions for data sources
│   ├── presentation/     # UI and API components
│   ├── services/         # Application services
│   ├── tools/            # Agent tools
│   └── utils/            # Utility functions
├── docs/                 # Documentation
└── main.py               # Application entry point
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/contributing.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) for the agent framework
- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent orchestration
- [Streamlit](https://streamlit.io/) for the web interface
- [Neo4j](https://neo4j.com/) for graph database capabilities
- [LLMSherpa](https://github.com/nlmatics/nlm-ingestor) for PDF parsing
- [OpenAI](https://openai.com/) for language model APIs
