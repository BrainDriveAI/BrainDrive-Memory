# Installation Guide
This guide will walk you through setting up the BrainDrive Memory application for development or production use.

## Prerequisites
Before installing BrainDrive Memory AI Agent, ensure you have the following:
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
   ```

### Option 2: Using Conda
   ```bash
   # Create a conda environment from the environment.yml file
   conda env create -f environment.yml

   # Activate the environment
   conda activate braindrive-memory-env
   ```

## Step 3: Install dependencies
   ```bash
   pip install -r requirements.txt
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

### 4.1: Create or Select Google Cloud Project

#### Option A: Create a New Project (Recommended for first-time users)
1. Go to the <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer">Google Cloud Console</a>
2. Click on the project dropdown at the top of the page (next to "Google Cloud")
3. Click **"New Project"** in the project selector dialog
4. Enter a **Project Name** (e.g., "BrainDrive Memory App")
5. Optionally select a **Billing Account** if you have one (required for some services)
6. Click **"Create"**
7. Wait for the project to be created (this may take a few moments)
8. Make sure your new project is selected in the project dropdown

#### Option B: Use an Existing Project
1. Go to the <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer">Google Cloud Console</a>
2. Click on the project dropdown at the top of the page
3. Select your existing project from the list
4. Ensure the project you want to use is now active (displayed in the top bar)

### 4.2: Enable Required APIs
1. In the Google Cloud Console, navigate to **"APIs & Services"** > **"Library"**
2. Search for and enable the following APIs:
   - **"Google+ API"** or **"People API"** (for user profile information)
   - **"Cloud Storage API"** (if using Google Cloud Storage)
   - **"Identity and Access Management (IAM) API"**
3. Click **"Enable"** for each API

### 4.3: Configure OAuth Consent Screen
Before creating OAuth credentials, you must configure the consent screen that users will see when authenticating.

1. Navigate to **"APIs & Services"** > **"OAuth consent screen"**
2. Choose your **User Type**:
   - **Internal**: Only users in your Google Workspace organization (if you have one)
   - **External**: Any user with a Google account (recommended for most users)
3. Click **"Create"**

#### Configure OAuth Consent Screen Details:
1. **App Information**:
   - **App name**: Enter "BrainDrive Memory" or your preferred app name
   - **User support email**: Select your email address from the dropdown
   - **App logo** (optional): Upload a logo if desired

2. **App Domain** (optional but recommended):
   - **App home page**: Your app's homepage URL (if you have one)
   - **App privacy policy**: Link to privacy policy (if you have one)
   - **App terms of service**: Link to terms of service (if you have one)

3. **Developer Contact Information**:
   - **Email addresses**: Add your email address

4. Click **"Save and Continue"**

5. **Scopes** (next page):
   - Click **"Add or Remove Scopes"**
   - Select the following scopes:
     - `../auth/userinfo.email`
     - `../auth/userinfo.profile`
     - `openid`
   - Click **"Update"**
   - Click **"Save and Continue"**

6. **Test Users** (if you selected "External" and your app is in testing):
   - Add email addresses of users who should be able to test your app
   - Click **"Add Users"** and enter email addresses
   - Click **"Save and Continue"**

7. **Summary**:
   - Review your configuration
   - Click **"Back to Dashboard"**

### 4.4: Create OAuth Client ID
1. Navigate to **"APIs & Services"** > **"Credentials"**
2. Click **"Create Credentials"** > **"OAuth client ID"**
3. If prompted to configure the OAuth consent screen, you should have already completed this in the previous step
4. Select **"Web application"** as the application type
5. **Configure the OAuth Client**:
   - **Name**: Enter a descriptive name (e.g., "BrainDrive Memory Web Client")
   - **Authorized JavaScript origins**: Add the following:
     - `http://localhost:8501` (for local development)
     - Your production domain (if deploying to production, e.g., `https://your-app.cloudalert.run`)
   - **Authorized redirect URIs**: Add the following:
     - `http://localhost:8501/` (for local development)
     - Your production callback URL (if applicable)

6. Click **"Create"**

### 4.5: Save OAuth Credentials
1. A dialog will appear with your **Client ID** and **Client Secret**
2. **Important**: Copy these values immediately and store them securely
3. Add these values to your `.env` file:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```
4. Click **"OK"** to close the dialog

### 4.6: Verify OAuth Setup
1. You can view and manage your OAuth client at any time by going to **"APIs & Services"** > **"Credentials"**
2. Your OAuth 2.0 Client ID will be listed under **"OAuth 2.0 Client IDs"**
3. You can edit the client to add more authorized domains or redirect URIs as needed

## Step 5: Set Up Neo4j
### Option 1: Neo4j Aura (Cloud)
1. Create an account at <a href="https://neo4j.com/cloud/aura/" target="_blank">Neo4j Aura</a>
2. Create a new database

### Option 2: Self-hosted Neo4j
1. Install Neo4j from <a href="https://neo4j.com/download/" target="_blank">Neo4j Download Center</a>
2. Create a new database and set a password
3. Enable the necessary plugins (APOC, GDS, Vector)

### Copy the connection details to your `.env` file
   ```bash
   NEO4J_URL=your_neo4j_url
   NEO4J_USER=your_username
   NEO4J_PWD=your_password
   ```
## Step 6: Supabase Setup
1. Create an account at [Supabase](https://supabase.com/)
2. Create a new project
3. Get your project URL and service role key
4. Add to your `.env` file:
   ```bash
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_service_role_key
   ```
   
## Step 7: Set Up Google Cloud Storage
1. Create a bucket in Google Cloud Storage
2. Set up appropriate permissions
3. Add the bucket name to your `.env` file
   ```bash
   GCS_BUCKET_NAME=your_bucket_name
   ```

## Step 8: Deploy LLMSherpa (Optional)
To use your own instance setup nlm-ingestor to get llmsherpa_api_url:
1. Deploy LLMSherpa using the instructions from <a href="https://github.com/nlmatics/nlm-ingestor" target="_blank">nlm-ingestor</a>
2. Set `LLM_SHERPA_API_URL` to your `.env` file 

## Step 9: Running the Application
   ```bash
   # Run with Streamlit directly
   streamlit run main.py
   ```
The application will be available at `http://localhost:8501/`

## Step 10: Verify Installation
1. Open your browser and navigate to `http://localhost:8501/`
2. You should see the login page
3. Sign in with your Google account
4. You should now see the chat interface

## Running in Docker
### Quick Development Setup
   ```bash
   # Build the development container
   docker build -f Dockerfile -t memory-agent-dev .

   # Run the container locally
   docker run -p 8501:8501 memory-agent-dev
   ```

## Production Deployment
Build and deploy to Google Cloud Run.

We provide automated deployment scripts for all major platforms:

### For Linux/Mac Users:
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

### For Windows Users:
1. Edit the PowerShell script to set your Google Cloud account:
   ```powershell
   notepad deploy.ps1
   # Update the $gcloudAccount variable with your email
   ```

2. Run the deployment script:
   ```powershell
   .\deploy.ps1
   ```

### What the Deployment Scripts Do:
1. Authenticate with Google Cloud
2. Set required environment variables
3. Build the Docker image for x86_64 architecture
4. Push the image to Google Cloud Container Registry
5. Report deployment success

### Manual Deployment Steps
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

### Environment Configuration
The following environment variables can be configured for deployment:
- `GCLOUD_PROJECT`: Your Google Cloud project ID
- `REPO`: Repository name in Artifact Registry
- `REGION`: Google Cloud region
- `IMAGE`: Container image name

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
- See the [User Guide](user_guide.md){:target="_blank"} for information on using the application
- Review [Contributing Guidelines](contributing.md){:target="_blank"} if you want to contribute to the project