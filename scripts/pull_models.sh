#!/bin/bash
# Pull all 6 models into Ollama
set -e

MODELS=(
    "gemma2:2b"
    "llama3.2:1b"
    "llama3.2:3b"
    "phi3:3.8b"
    "mistral:7b"
    "llama3.1:8b"
)

echo "Pulling models to Ollama..."
for model in "${MODELS[@]}"; do
    echo "Pulling $model..."
    docker exec rag-ollama ollama pull "$model"
done

echo ""
echo "Available models:"
docker exec rag-ollama ollama list
