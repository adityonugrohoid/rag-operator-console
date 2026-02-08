FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY services/__init__.py ./services/
COPY services/retrieval/ ./services/retrieval/
CMD ["uvicorn", "services.retrieval.main:app", "--host", "0.0.0.0", "--port", "8002"]
