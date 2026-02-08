# Console UI - lightweight, no ML dependencies needed
FROM rag-operator-console-base:latest

WORKDIR /app

# Copy console code and data
COPY console/ ./console/
COPY data/ ./data/

# Run the Streamlit app
CMD ["streamlit", "run", "console/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
