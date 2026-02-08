# Retrieval service - needs sentence-transformers for embeddings
FROM rag-operator-console-ml-base:latest AS ml-base

WORKDIR /app

# Copy shared code and service-specific code
COPY shared/ ./shared/
COPY services/__init__.py ./services/
COPY services/retrieval/ ./services/retrieval/

# Run the service
CMD ["uvicorn", "services.retrieval.main:app", "--host", "0.0.0.0", "--port", "8002"]
