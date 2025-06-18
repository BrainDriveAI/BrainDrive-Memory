# Ollama is intended to be run as a local development server.
# To download the model and store it in the container image, 
# this script starts the ollama server and sends a pull command to it.

# Function to check if ollama serve is listening on port 8080
function Wait-ForOllama {
    while (-not (Test-NetConnection -ComputerName localhost -Port 8080 -InformationLevel Quiet)) {
        Start-Sleep -Seconds 1  # Wait 1 second before checking again
    }
}

# Start ollama serve in the background
Start-Process -FilePath "ollama" -ArgumentList "serve" -NoNewWindow

# Wait for ollama serve to start listening
Wait-ForOllama
Write-Host "ollama serve is now listening on port 8080"

# Run ollama pull for qwen3:1.7b
ollama pull qwen3:1.7b

# Indicate successful completion
Write-Host "ollama pull qwen3:1.7b completed"
