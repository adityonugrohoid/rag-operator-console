#!/bin/bash
# Stop Phase 2 services (RAG pipeline + console)
set -e

echo "Stopping RAG Operator Console (Phase 2)..."
docker compose down

echo "Stopped RAG services and console."

