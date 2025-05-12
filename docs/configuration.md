# Configuration Guide

BrainDrive Memory AI Agent uses environment variables for configuration. This guide explains the available options and how to set them up.

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Application Settings

| Variable     | Required | Default        | Description                                                               |
|--------------|----------|----------------|---------------------------------------------------------------------------|
| APP_USERNAME | No       | `default_user` | Default username for the application if no specific user is authenticated |

### LLM Providers

#### OpenAI (Required)

| Variable               | Required | Default                  | Description                       |
|------------------------|----------|--------------------------|-----------------------------------|
| OPENAI_API_KEY         | Yes      | -                        | Your OpenAI API key               |
| OPENAI_LLM_MODEL       | No       | `gpt-4.1`                | The OpenAI model to use           |
| OPENAI_EMBEDDING_MODEL | No       | `text-embedding-3-small` | The OpenAI embedding model to use |

#### Groq (Optional)

| Variable       | Required | Default           | Description           |
|----------------|----------|-------------------|-----------------------|
| GROQ_API_KEY   | No       | -                 | Your Groq API key     |
| GROQ_LLM_MODEL | No       | `llama3-70b-8192` | The Groq model to use |

#### Ollama (Optional)

| Variable               | Required | Default             | Description                       |
|------------------------|----------|---------------------|-----------------------------------|
| OLLAMA_EMBEDDING_MODEL | No       | `mxbai-embed-large` | The Ollama embedding model to use |

#### Openrouter (Optional)

| Variable             | Required | Default                                   | Description                         |
|----------------------|----------|-------------------------------------------|-------------------------------------|
| OPENROUTER_API_KEY   | No       | -                                         | Your Openrouter API key             |
| OPENROUTER_BASE_URL  | No       | `https://openrouter.ai/api/v1`            | The base URL for the Openrouter API |
| OPENROUTER_LLM_MODEL | No       | `meta-llama/llama-3.1-405b-instruct:free` | The Openrouter model to use         |

#### TogetherAI (Optional)

| Variable              | Required | Default                                         | Description                 |
|-----------------------|----------|-------------------------------------------------|-----------------------------|
| TOGETHER_AI_API_KEY   | No       | -                                               | Your TogetherAI API key     |
| TOGETHER_AI_LLM_MODEL | No       | `meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo` | The TogetherAI model to use |

### Data Storage

#### Neo4j (Required)

| Variable      | Required | Default | Description                                                          |
|---------------|----------|---------|----------------------------------------------------------------------|
| NEO4J_URL     | Yes      | -       | The Neo4j connection URL (e.g., 'neo4j+s://xxxx.databases.neo4j.io') |
| NEO4J_USER    | Yes      | -       | The Neo4j username                                                   |
| NEO4J_PWD     | Yes      | -       | The Neo4j password                                                   |
| NEO4JDATABASE | No       | `neo4j` | The Neo4j database name                                              |

#### Supabase/PGVector (Optional but recommended)

| Variable                            | Required | Default           | Description                                    |
|-------------------------------------|----------|-------------------|------------------------------------------------|
| SUPABASE_URL                        | Yes*     | -                 | The Supabase connection URL                    |
| SUPABASE_KEY                        | Yes*     | -                 | The Supabase service role key or anon key      |
| SUPABASE_VECTOR_COLLECTION_NAME     | No       | `documents`       | The collection/table name for the vector store |
| SUPABASE_VECTOR_QUERY_FUNCTION_NAME | No       | `match_documents` | The query function name in Supabase            |

* Required if using Supabase as vector store

#### Pinecone (Optional alternative to Supabase)

| Variable                 | Required | Default                 | Description                      |
|--------------------------|----------|-------------------------|----------------------------------|
| PINECONE_API_KEY         | No       | -                       | Your Pinecone API key            |
| PINECONE_ENVIRONMENT     | No       | -                       | The Pinecone environment name    |
| PINECONE_EMBEDDING_MODEL | No       | `multilingual-e5-large` | The embedding model for Pinecone |

### Authentication

| Variable             | Required | Default | Description                     |
|----------------------|----------|---------|---------------------------------|
| GOOGLE_CLIENT_ID     | Yes*     | -       | Your Google OAuth client ID     |
| GOOGLE_CLIENT_SECRET | Yes*     | -       | Your Google OAuth client secret |
| REDIRECT_URI         | Yes*     | -       | The Google OAuth redirect URI   |

* Required for Google OAuth authentication

### Google Cloud Services

#### Google Cloud Storage

| Variable        | Required | Default | Description                          |
|-----------------|----------|---------|--------------------------------------|
| GCS_BUCKET_NAME | Yes*     | -       | The Google Cloud Storage bucket name |

* Required for document storage

#### Vertex AI Search

| Variable                   | Required | Default | Description                           |
|----------------------------|----------|---------|---------------------------------------|
| VERTEX_AI_PROJECT_ID       | No       | -       | Your Google Cloud Project ID          |
| VERTEX_AI_LOCATION_ID      | No       | -       | Google Cloud location (region)        |
| VERTEX_AI_SEARCH_ENGINE_ID | No       | -       | ID of your Vertex AI Search engine    |
| VERTEX_AI_DATASTORE_ID     | No       | -       | ID of your Vertex AI Search datastore |

## Example Configuration

```dotenv
# Application
APP_USERNAME=your_username

# OpenAI (Required)
OPENAI_API_KEY=sk-...
OPENAI_LLM_MODEL=gpt-4.1
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Neo4j (Required)
NEO4J_URL=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PWD=your-password

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
REDIRECT_URI=http://localhost:8501/

# Google Cloud Storage
GCS_BUCKET_NAME=your-bucket-name
```

## Provider Selection

The application uses the data source providers specified in `app/settings.py`. By default, it uses:

- Neo4j for graph database
- Supabase for vector storage

You can modify these settings to use alternative providers or disable certain features.

## PDF Processing Service

Setup nlm-ingestor to get llmsherpa_api_url

1. Deploy LLMSherpa using the instructions from [nlm-ingestor](https://github.com/nlmatics/nlm-ingestor)
2. Set `LLM_SHERPA_API_URL` to your `.env` file 

## Development Configuration

For local development, you may want to:

1. Use the `Dockerfile` for containerized development
2. Run Streamlit directly with `streamlit run main.py`