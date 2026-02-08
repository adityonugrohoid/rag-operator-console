#!/bin/bash
# Build optimized Docker images with shared base layers
# This script builds base images first, then service images
set -e

echo "Building optimized Docker images..."
echo ""

# Step 1: Build base images
echo "Step 1/3: Building base image (common dependencies)..."
docker build -f Dockerfile.base -t rag-operator-console-base:latest .

echo ""
echo "Step 2/3: Building ML base image (with sentence-transformers)..."
docker build -f Dockerfile.ml -t rag-operator-console-ml-base:latest .

echo ""
echo "Step 3/3: Building service images..."
docker compose build

echo ""
echo "✓ Build complete!"
echo ""
echo "Image sizes:"
docker images | grep "rag-operator-console" | awk '{print $1 ":" $2 " - " $7 $8}'
echo ""
echo "Total space used:"
docker images | grep "rag-operator-console" | awk '{sum+=$7} END {print sum " GB (approximate)"}'
