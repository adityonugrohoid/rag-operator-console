# Ingestion service - needs sentence-transformers for embeddings
FROM rag-operator-console-ml-base:latest AS ml-base

WORKDIR /app

# Copy shared code and service-specific code
COPY shared/ ./shared/
COPY services/__init__.py ./services/
COPY services/ingestion/ ./services/ingestion/

# Copy sample documents
COPY data/ ./data/

# Run the service
CMD ["uvicorn", "services.ingestion.main:app", "--host", "0.0.0.0", "--port", "8001"]
