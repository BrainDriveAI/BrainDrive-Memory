# Installation Guide

This guide will walk you through setting up the BrainDrive Memory application for development or production use.

## Prerequisites

Before installing Memory AI Agent, ensure you have the following:
- Python 3.9 or higher
- Git
- Neo4j database (cloud or self-hosted)
- Supabase account (for vector storage)
- OpenAI API key
- Google Cloud account (for OAuth, GCS, and optionally Vertex AI Search)
- Docker and Docker Compose (optional, for containerized deployment)

## Step 1: Clone the Repository

```bash
git clone https://github.com/BrainDriveAI/BrainDrive-Memory.git
cd BrainDrive-Memory
```

## Step 2: Python Environment Setup

### Option 1: Using venv (Recommended for development)

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using Conda

```bash
# Create a conda environment from the environment.yml file
conda env create -f environment.yml

# Activate the environment
conda activate braindrive-memory-env
```

## Step 3: Configuration

1. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your API keys and service credentials. At minimum, you'll need:
   - OpenAI API key
   - Neo4j credentials
   - Supabase credentials (if using vector storage)
   - Google Cloud credentials (for OAuth and GCS)

See the [Configuration Guide](configuration.md) for detailed information on all available settings.

## Step 4: Set Up Google OAuth

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Set the application type as "Web application"
6. Add authorized redirect URIs:
   - For local development: `http://localhost:8501/`
   - For production: Add your production URL
7. Copy the Client ID and Client Secret to your `.env` file

## Step 5: Set Up Neo4j

### Option 1: Neo4j Aura (Cloud)
1. Create an account at [Neo4j Aura](https://neo4j.com/cloud/aura/)
2. Create a new database
3. Copy the connection details to your `.env` file

### Option 2: Self-hosted Neo4j
1. Install Neo4j from [Neo4j Download Center](https://neo4j.com/download/)
2. Create a new database and set a password
3. Enable the necessary plugins (APOC, GDS, Vector)
4. Update your `.env` file with the connection details

## Step 6: Set Up Google Cloud Storage

1. Create a bucket in Google Cloud Storage
2. Set up appropriate permissions
3. Add the bucket name to your `.env` file

## Step 7: Deploy LLMSherpa (Optional)

To use your own instance setup nlm-ingestor to get llmsherpa_api_url:
1. Deploy LLMSherpa using the instructions from [nlm-ingestor](https://github.com/nlmatics/nlm-ingestor)
2. Set `LLM_SHERPA_API_URL` to your `.env` file 

## Step 8: Running the Application

### Local Development

```bash
# Run with Streamlit directly
streamlit run main.py
```

The application will be available at `http://localhost:8501/`

### Docker Deployment

#### Quick Development Setup

```bash
# Build the development container
docker build -f Dockerfile -t memory-agent-dev .

# Run the container locally
docker run -p 8501:8501 memory-agent-dev
```

#### Production Deployment

Build and deploy to Google Cloud Run.
We provide automated deployment scripts for all major platforms:

##### For Linux/Mac Users:

1. Make the script executable:
   ```bash
   chmod +x deploy.sh
   ```

2. Edit the script to set your Google Cloud account:
   ```bash
   nano deploy.sh
   # Update the GCLOUD_ACCOUNT variable with your email
   ```

3. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

##### For Windows Users:

1. Edit the PowerShell script to set your Google Cloud account:
   ```powershell
   notepad deploy.ps1
   # Update the $gcloudAccount variable with your email
   ```

2. Run the deployment script:
   ```powershell
   .\deploy.ps1
   ```

##### What the Deployment Scripts Do:

1. Authenticate with Google Cloud
2. Set required environment variables
3. Build the Docker image for x86_64 architecture
4. Push the image to Google Cloud Container Registry
5. Report deployment success

##### Manual Deployment Steps

If you prefer to deploy manually or to a different cloud provider:

1. Build the Docker image:
   ```bash
   docker build --platform linux/x86_64 -t your-registry/memory-agent-image .
   ```

2. Push to your container registry:
   ```bash
   docker push your-registry/memory-agent-image
   ```

3. Deploy using your cloud provider's container service

##### Environment Configuration

The following environment variables can be configured for deployment:
- `GCLOUD_PROJECT`: Your Google Cloud project ID
- `REPO`: Repository name in Artifact Registry
- `REGION`: Google Cloud region
- `IMAGE`: Container image name

## Step 9: Verify Installation

1. Open your browser and navigate to `http://localhost:8501/`
2. You should see the login page
3. Sign in with your Google account
4. You should now see the chat interface

## Troubleshooting

### Authentication Errors
- Ensure that your Google Cloud OAuth credentials are correctly configured
- Check that the redirect URI matches exactly what's in your Google Cloud Console
- Verify that the required OAuth scopes are enabled

### Database Connection Errors
- Check your Neo4j connection string, username, and password
- Ensure your IP is allowed in the Neo4j connection settings
- Verify that the Neo4j database is running and accessible

### PDF Processing Errors
- Check that the LLMSherpa endpoint is correctly configured and accessible
- Ensure your Google Cloud Storage bucket has proper permissions
- Verify that the uploaded PDF is valid and not corrupted

### Vector Store Errors
- Verify your Supabase credentials
- Ensure the vector store table is properly set up
- Check that the embedding model is accessible

### Docker Deployment Issues
- Ensure you have the latest Docker installed
- Check that gcloud CLI is properly installed and configured
- Verify your Google Cloud permissions
- Make sure the repository exists in Google Artifact Registry

## Next Steps
- See the [User Guide](user_guide.md) for information on using the application
- Review [Contributing Guidelines](contributing.md) if you want to contribute to the project