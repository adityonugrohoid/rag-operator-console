"""API Gateway for the RAG Operator Console."""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging

from shared.utils.logging import setup_logging
from shared.models.schemas import DocumentResponse, QueryRequest, QueryResponse

logger = setup_logging("api_gateway")
app = FastAPI(title="RAG Operator Console API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8001")
RETRIEVAL_URL = os.getenv("RETRIEVAL_URL", "http://localhost:8002")
QUERY_URL = os.getenv("QUERY_URL", "http://localhost:8003")


@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    """Upload and ingest a document."""
    try:
        logger.info("Document upload", extra={"document_filename": file.filename})
        async with httpx.AsyncClient(timeout=60.0) as client:
            content = await file.read()
            response = await client.post(
                f"{INGESTION_URL}/ingest",
                files={"file": (file.filename, content, file.content_type)},
            )
            response.raise_for_status()
            return DocumentResponse(**response.json())
    except httpx.HTTPError as e:
        logger.error("Ingestion error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")
    except Exception as e:
        logger.error("Upload failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Process a RAG query with full observability."""
    try:
        logger.info("Query received", extra={"query": request.query})
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{QUERY_URL}/query",
                json=request.model_dump(),
            )
            response.raise_for_status()
            return QueryResponse(**response.json())
    except httpx.HTTPError as e:
        logger.error("Query service error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    except Exception as e:
        logger.error("Query failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/documents")
async def list_documents():
    """List all indexed documents."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{RETRIEVAL_URL}/documents")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")


@app.delete("/documents")
async def clear_documents():
    """Clear all documents from the vector database."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(f"{RETRIEVAL_URL}/documents")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")


@app.get("/health")
async def health():
    """Health check with downstream service status."""
    services_status = {}
    for name, url in [
        ("ingestion", INGESTION_URL),
        ("retrieval", RETRIEVAL_URL),
        ("query", QUERY_URL),
    ]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{url}/health")
                services_status[name] = (
                    "healthy" if resp.status_code == 200 else "unhealthy"
                )
        except Exception:
            services_status[name] = "unhealthy"

    overall = (
        "healthy" if all(s == "healthy" for s in services_status.values())
        else "degraded"
    )
    return {"status": overall, "services": services_status, "service": "api_gateway"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
