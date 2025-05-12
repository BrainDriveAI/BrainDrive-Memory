# Set the Google Cloud account
$gcloudAccount = ""

# Authenticate with gcloud
Write-Host "Authenticating with gcloud using account: $gcloudAccount"
try {
    gcloud config set account $gcloudAccount
    Write-Host "Successfully authenticated with gcloud."
} catch {
    Write-Error "Error authenticating with gcloud: $_"
    exit 1  # Exit with an error code
}

# Set environment variables only for this session
$env:GCLOUD_PROJECT = "braindrive-memory"
$env:REPO = "braindrive-memory-agent"
$env:REGION = "us-central1"
$env:IMAGE = "braindrive-memory-agent-image"
$env:IMAGE_TAG = "${env:REGION}-docker.pkg.dev/${env:GCLOUD_PROJECT}/${env:REPO}/${env:IMAGE}"

# Build Docker image
Write-Host "Building Docker image: $env:IMAGE_TAG"
docker build --platform linux/x86_64 -t $env:IMAGE_TAG -f .\Dockerfile .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

# Push Docker image only if build was successful
Write-Host "Pushing Docker image to registry"
docker push $env:IMAGE_TAG
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker push failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Deployment completed successfully!"
