#!/bin/bash
# Start all services via Docker Compose
set -e

echo "Starting RAG Operator Console..."
docker compose up -d --build

echo ""
echo "Services:"
echo "  Ollama:       http://localhost:11434"
echo "  ChromaDB:     http://localhost:8000"
echo "  Ingestion:    http://localhost:8001"
echo "  Retrieval:    http://localhost:8002"
echo "  Query:        http://localhost:8003"
echo "  API Gateway:  http://localhost:8080"
echo "  Console:      http://localhost:8501"
echo ""
echo "Run './scripts/pull_models.sh' to download models into Ollama."
