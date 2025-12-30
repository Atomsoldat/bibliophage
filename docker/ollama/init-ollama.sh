#!/bin/bash
set -e

# This script runs on first Ollama container start to pre-pull models
# Models are stored in /root/.ollama which is mounted as a Docker volume

echo "Checking if mistral model is already available..."

# Check if model exists
if ollama list | grep -q "mistral"; then
    echo "Mistral is already pulled"
else
    echo "Pulling mistral model (this may take several minutes)..."
    ollama pull mistral
    echo "Mistral model pulled successfully"
fi

echo "Ollama initialisation complete"
