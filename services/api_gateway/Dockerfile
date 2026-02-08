FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY services/api_gateway/ ./services/api_gateway/
CMD ["uvicorn", "services.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
