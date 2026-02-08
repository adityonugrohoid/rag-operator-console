#!/bin/bash
# Start all services via Docker Compose
# Requires: Phase 0 Ollama container already running on port 11434
set -e

# Check Ollama is running
if ! docker ps --format '{{.Names}}' | grep -q '^ollama$'; then
    echo "ERROR: Ollama container not running."
    echo "Start Phase 0 first: cd ~/projects/ollama-runtime && ./scripts/start.sh"
    exit 1
fi

echo "Using existing Ollama container (Phase 0)..."
echo "Starting RAG Operator Console services..."
docker compose up -d --build

echo ""
echo "Services:"
echo "  Ollama:       http://localhost:11434  (Phase 0: ollama-runtime, shared)"
echo "  ChromaDB:     http://localhost:2000"
echo "  Ingestion:    http://localhost:2001"
echo "  Retrieval:    http://localhost:2002"
echo "  Query:        http://localhost:2003"
echo "  API Gateway:  http://localhost:2080"
echo "  Console:      http://localhost:2501"
echo ""
echo "Run './scripts/pull_models.sh' to download models into Ollama."
echo "See PORT_CONFIGURATION.md for port details."