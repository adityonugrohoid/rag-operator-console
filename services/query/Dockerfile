# Query service - lightweight, no ML dependencies needed
FROM rag-operator-console-base:latest

WORKDIR /app

# Copy shared code and service-specific code
COPY shared/ ./shared/
COPY services/__init__.py ./services/
COPY services/query/ ./services/query/

# Run the service
CMD ["uvicorn", "services.query.main:app", "--host", "0.0.0.0", "--port", "8003"]
