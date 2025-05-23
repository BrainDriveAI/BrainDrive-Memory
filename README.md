# BrainDrive Memory - Your Personal AI Memory Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Setup Required](https://img.shields.io/badge/setup-required-red)
![Config Required](https://img.shields.io/badge/.env-required-orange)

Modular, ownable AI memory that gets smarter with every conversation.

## 🌟 Features

- **Persistent AI Memory** – Learns from your conversations and documents, not just prompts  
- **Knowledge Graph Integration** – Forms and updates connections between concepts like a human mind  
- **Modular Architecture** – Easily swap vector stores, graph DBs, LLMs, or add your own data sources  
- **Document-Aware Chat** – Seamlessly integrates uploaded files into memory and responses  
- **Smart Agent Control** – Automatically decides what to remember, update, or reference  
- **Customizable Prompts** – Tailor system behavior to fit your tone, tools, and goals  
- **LLM Agnostic** – Works with GPT-4, Claude, Ollama, etc
- **Open-Source & MIT Licensed** – Full freedom to use, modify, and extend  
- **Own Your Data** – Memory stays with you — not Big Tech

## 🚀 Quick Start (for experienced developers)

> ⚠️ **Important**: Follow ALL steps below. Skipping the .env setup will cause the application to fail.

### Prerequisites
- Python 3.9+
- Docker and Docker Compose (optional, for containerized setup)
- Google Cloud account (for GCS, OAuth, and Vertex AI Search)
- Neo4j database
- Supabase account
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/BrainDriveAI/BrainDrive-Memory.git
   cd BrainDrive-Memory
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **⚠️ REQUIRED: Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   **You MUST edit the `.env` file with your API keys before proceeding.**
   
   Open `.env` and set at minimum:
   - `OPENAI_API_KEY`
   - `NEO4J_URL`, `NEO4J_USER`, `NEO4J_PWD`
   - `SUPABASE_URL`, `SUPABASE_KEY`
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `GCS_BUCKET_NAME`
   
   **The app will not start without these values configured.**

5. **Run the application**
   ```bash
   streamlit run main.py
   ```

### Need Help?
- **First time setup?** Follow our [detailed installation guide](docs/installation.md)
- **Configuration issues?** See the [configuration guide](docs/configuration.md)

## 📋 Architecture

BrainDrive Memory is designed to be modular, provider-agnostic, and fully ownable. It’s built around four core components:

### 🧠 AI Agent
- Coordinates memory operations
- Decides what to remember, update, or retrieve
- Interacts with data sources through natural language
- Built with [LangGraph](https://www.langgraph.dev/) and customizable system prompts

### 🗂️ Data Sources
- **Vector Store** – Fast retrieval using embeddings (default: Supabase, swappable)
- **Knowledge Graph** – Connects entities and facts like neural links (default: Neo4j, swappable)
- **Document Storage** – Stores uploaded files (default: Google Cloud Storage, swappable)
- **Other Sources** – Easily integrate calendars, emails, databases, etc.

### 🔄 Tools Layer
- Encapsulated tools for `add`, `delete`, `update`, `search`, and `summarize`
- Modular: Add or remove tools based on your needs
- Tools interact with all data sources through a unified manager

### 🧩 Presentation Layer
- Interfaces for interacting with the memory agent:
  - Web UI (Streamlit-based)
  - REST API
  - LangGraph visual/debug interface
  - CLI (coming soon)
- Built to support custom interfaces via plugin or API

### ⚙️ Designed for Modularity
All major components — LLMs, vector stores, graph databases, storage providers — are wrapped in adapters. You can:

- Swap providers without rewriting core logic
- Add new data sources or tools easily
- Configure system behavior via a centralized `settings.py` file

The result: a flexible, extensible memory system you can shape to your needs.

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
