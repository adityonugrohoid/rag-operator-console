"""Query service for RAG queries with full pipeline observability."""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
import httpx
import os
import time
import logging

from shared.utils.logging import setup_logging
from shared.utils.config import Config
from shared.clients.ollama_client import OllamaClient
from shared.models.schemas import (
    QueryRequest,
    QueryResponse,
    PipelineMetrics,
    PromptAssemblyMetadata,
    RetrievedChunkInfo,
)
from services.query.prompt_assembler import PromptAssembler

logger = setup_logging("query_service")
app = FastAPI(title="Query Service")

config = Config.from_env()
llm_client = OllamaClient(host=config.OLLAMA_HOST, model=config.LLM_MODEL)
assembler = PromptAssembler(max_context_tokens=4096)

RETRIEVAL_URL = os.getenv("RETRIEVAL_URL", "http://localhost:8002")


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Process a RAG query with full pipeline observability."""
    try:
        logger.info("Processing query", extra={"query": request.query})
        pipeline_start = time.time()

        use_model = request.model or config.LLM_MODEL
        temperature = request.temperature
        max_tokens = request.max_tokens

        # --- Stage 1: Retrieval ---
        retrieval_start = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            retrieval_response = await client.post(
                f"{RETRIEVAL_URL}/retrieve",
                json={"query": request.query, "top_k": 5},
            )
            retrieval_response.raise_for_status()
            retrieval_data = retrieval_response.json()
        retrieval_ms = (time.time() - retrieval_start) * 1000

        chunks = retrieval_data.get("chunks", [])

        # If no documents indexed, fall back to direct LLM chat (no RAG)
        if not chunks:
            logger.info("No documents found, using direct LLM mode")
            llm_start = time.time()

            # Build simple messages without RAG context
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": request.query}
            ]

            # Add clarification context if provided
            if request.clarification_context:
                messages.insert(1, {
                    "role": "user",
                    "content": f"Previous conversation:\n{request.clarification_context}"
                })

            llm_result = llm_client.chat(
                messages=messages,
                model=use_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            llm_ms = (time.time() - llm_start) * 1000

            answer = llm_result["response"]
            tokens_generated = llm_result.get("eval_count", 0)
            tokens_per_sec = round(tokens_generated / (llm_ms / 1000), 1) if llm_ms > 0 else 0
            total_ms = (time.time() - pipeline_start) * 1000

            return QueryResponse(
                success=True,
                answer=answer,
                sources=[],
                model=use_model,
                pipeline_metrics=PipelineMetrics(
                    retrieval_ms=round(retrieval_ms, 1),
                    llm_ms=round(llm_ms, 1),
                    total_ms=round(total_ms, 1),
                    tokens_generated=tokens_generated,
                    tokens_per_sec=tokens_per_sec,
                ),
            )

        # --- Stage 2: Prompt Assembly ---
        assembly_start = time.time()
        assembly_result = assembler.assemble(
            question=request.query,
            retrieved_chunks=chunks,
            clarification_context=request.clarification_context,
        )
        assembly_ms = (time.time() - assembly_start) * 1000

        messages = assembly_result["messages"]
        assembly_metadata = assembly_result["metadata"]
        chunk_details = assembly_result["chunk_details"]

        # --- Stage 3: LLM Generation ---
        llm_start = time.time()
        llm_result = llm_client.chat(
            messages=messages,
            model=use_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        llm_ms = (time.time() - llm_start) * 1000

        answer = llm_result["response"]
        tokens_generated = llm_result.get("eval_count", 0)
        tokens_per_sec = (
            round(tokens_generated / (llm_ms / 1000), 1) if llm_ms > 0 else 0
        )

        total_ms = (time.time() - pipeline_start) * 1000

        # --- Build observability response ---
        sources = list(set(
            chunk.get("metadata", {}).get("filename", "unknown")
            for chunk in chunks
        ))

        pipeline_metrics = PipelineMetrics(
            retrieval_ms=round(retrieval_ms, 1),
            assembly_ms=round(assembly_ms, 1),
            llm_ms=round(llm_ms, 1),
            total_ms=round(total_ms, 1),
            tokens_generated=tokens_generated,
            tokens_per_sec=tokens_per_sec,
        )

        prompt_assembly = PromptAssemblyMetadata(**assembly_metadata)

        retrieved_chunks_info = []
        for idx, chunk in enumerate(chunks):
            detail = chunk_details[idx] if idx < len(chunk_details) else {}
            meta = chunk.get("metadata", {})
            text = chunk.get("text", "")
            preview = text[:200] + "..." if len(text) > 200 else text

            pii_detected = False
            pii_val = meta.get("pii_detected")
            if isinstance(pii_val, bool):
                pii_detected = pii_val
            elif isinstance(pii_val, str):
                pii_detected = pii_val.lower() == "true"

            chunk_index = meta.get("chunk_index", 0)
            if isinstance(chunk_index, str):
                chunk_index = int(chunk_index) if chunk_index.isdigit() else 0

            retrieved_chunks_info.append(
                RetrievedChunkInfo(
                    source=meta.get("filename", "unknown"),
                    chunk_index=chunk_index,
                    score=round(chunk.get("score", 0.0), 4),
                    tokens=detail.get("tokens", 0),
                    preview=preview,
                    pii_detected=pii_detected,
                    included_in_prompt=detail.get("included_in_prompt", False),
                )
            )

        logger.info("Query processed", extra={
            "model": use_model,
            "chunks_used": assembly_metadata["retrieved_docs_used"],
            "total_ms": round(total_ms, 1),
        })

        return QueryResponse(
            success=True,
            answer=answer,
            sources=sources,
            model=use_model,
            pipeline_metrics=pipeline_metrics,
            prompt_assembly=prompt_assembly,
            retrieved_chunks=retrieved_chunks_info,
        )

    except httpx.HTTPError as e:
        logger.error("HTTP error", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Retrieval service error: {str(e)}"
        )
    except Exception as e:
        logger.error("Query failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "query"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
