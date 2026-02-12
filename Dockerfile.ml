# ML-enabled base image for services that need embeddings
# Extends base image with sentence-transformers (includes PyTorch)
FROM rag-operator-console-base:latest

# Install ML-specific dependencies on top of existing base
COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt

# Pre-download the embedding model to bake it into the image
# This prevents each container from downloading it separately
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
