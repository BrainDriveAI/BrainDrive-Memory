#!/bin/bash

# Set error handling to exit on any error
set -e

# --- Configuration ---
# You can set these variables directly here, or the script will prompt you if they are empty.
GCLOUD_ACCOUNT="" # e.g., "user@example.com"
GCLOUD_PROJECT="" # e.g., "your-gcp-project-id"
REPO_NAME=""      # e.g., "memory-agent"
REGION=""         # e.g., "us-central1"
IMAGE_NAME=""     # e.g., "memory-agent-image"
DOCKERFILE_PATH="./Dockerfile" # Path to your Dockerfile

# --- Helper Functions ---
prompt_if_empty() {
    local var_name="$1"
    local prompt_message="$2"
    if [ -z "${!var_name}" ]; then
        read -r -p "$prompt_message: " "$var_name"
        if [ -z "${!var_name}" ]; then
            echo "Error: $var_name cannot be empty." >&2
            exit 1
        fi
    fi
}

# --- Script Logic ---

# Prompt for configuration if not set
prompt_if_empty "GCLOUD_ACCOUNT" "Enter your Google Cloud account email"
prompt_if_empty "GCLOUD_PROJECT" "Enter your Google Cloud Project ID"
prompt_if_empty "REPO_NAME" "Enter your Artifact Registry repository name"
prompt_if_empty "REGION" "Enter the GCP region for the Artifact Registry (e.g., us-central1)"
prompt_if_empty "IMAGE_NAME" "Enter the name for your Docker image"

# Authenticate with gcloud
echo "Authenticating with gcloud using account: $GCLOUD_ACCOUNT"
if ! gcloud config set account "$GCLOUD_ACCOUNT"; then
    echo "Error authenticating with gcloud"
    exit 1
fi
echo "Successfully authenticated with gcloud."

# Set derived environment variables
export IMAGE_TAG="${REGION}-docker.pkg.dev/${GCLOUD_PROJECT}/${REPO_NAME}/${IMAGE_NAME}"

# Build Docker image
echo "Building Docker image: $IMAGE_TAG"
if ! docker build --platform linux/x86_64 -t $IMAGE_TAG -f ./Dockerfile .; then
    echo "Docker build failed"
    exit 1
fi

# Push Docker image only if build was successful
echo "Pushing Docker image to registry"
if ! docker push $IMAGE_TAG; then
    echo "Docker push failed"
    exit 1
fi

echo "Deployment completed successfully!"
