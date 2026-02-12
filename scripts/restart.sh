#!/bin/bash
# Restart Phase 2 services (RAG pipeline + console)
set -e

echo "Restarting RAG Operator Console (Phase 2)..."
docker compose down
docker compose up -d --build

echo "Restarted RAG services and console."

