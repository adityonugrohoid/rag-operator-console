# API Gateway - lightweight, no ML dependencies needed
FROM rag-operator-console-base:latest

WORKDIR /app

# Copy shared code and service-specific code
COPY shared/ ./shared/
COPY services/api_gateway/ ./services/api_gateway/

# Run the service
CMD ["uvicorn", "services.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
