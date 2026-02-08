FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY services/__init__.py ./services/
COPY services/query/ ./services/query/
CMD ["uvicorn", "services.query.main:app", "--host", "0.0.0.0", "--port", "8003"]
