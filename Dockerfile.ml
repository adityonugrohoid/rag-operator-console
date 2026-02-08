# ML-enabled base image for services that need embeddings
# Extends base image with sentence-transformers (includes PyTorch)
FROM python:3.12-slim

WORKDIR /app

# Install all dependencies including ML libraries
COPY requirements-base.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-base.txt -r requirements-ml.txt

# Pre-download the embedding model to bake it into the image
# This prevents each container from downloading it separately
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# This image is ~2-3GB but shared between ingestion and retrieval
