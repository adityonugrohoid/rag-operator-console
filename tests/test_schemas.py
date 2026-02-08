"""Tests for schema validation and observability response structure."""
import pytest
from shared.models.schemas import (
    QueryRequest,
    QueryResponse,
    PipelineMetrics,
    PromptAssemblyMetadata,
    RetrievedChunkInfo,
    DocumentResponse,
    ChunkMetadata,
    DataClassification,
)


def test_query_request_defaults():
    """QueryRequest has Phase 1 carry-forward defaults."""
    req = QueryRequest(query="test")
    assert req.model is None
    assert req.temperature == 0.7
    assert req.max_tokens == 512
    assert req.clarification_context is None


def test_query_request_with_params():
    """QueryRequest accepts model, temperature, max_tokens."""
    req = QueryRequest(
        query="test",
        model="mistral:7b",
        temperature=0.3,
        max_tokens=1024,
        clarification_context="previous turn",
    )
    assert req.model == "mistral:7b"
    assert req.temperature == 0.3
    assert req.max_tokens == 1024
    assert req.clarification_context == "previous turn"


def test_query_response_full_observability():
    """QueryResponse contains all observability fields."""
    resp = QueryResponse(
        success=True,
        answer="Test answer",
        sources=["doc1.txt", "doc2.txt"],
        model="llama3.2:3b",
        pipeline_metrics=PipelineMetrics(
            retrieval_ms=8.5,
            assembly_ms=1.2,
            llm_ms=1500.0,
            total_ms=1510.0,
            tokens_generated=100,
            tokens_per_sec=66.7,
        ),
        prompt_assembly=PromptAssemblyMetadata(
            system_tokens=120,
            retrieved_docs_tokens=800,
            retrieved_docs_used=3,
            clarification_included=False,
            clarification_tokens=0,
            question_tokens=15,
            total_tokens=935,
            budget=3000,
        ),
        retrieved_chunks=[
            RetrievedChunkInfo(
                source="doc1.txt",
                chunk_index=2,
                score=0.89,
                tokens=300,
                preview="The 5G RAN...",
                pii_detected=False,
                included_in_prompt=True,
            )
        ],
    )
    assert resp.model == "llama3.2:3b"
    assert resp.pipeline_metrics.tokens_per_sec == 66.7
    assert resp.prompt_assembly.budget == 3000
    assert len(resp.retrieved_chunks) == 1
    assert resp.retrieved_chunks[0].included_in_prompt is True


def test_query_response_defaults():
    """QueryResponse works with minimal fields."""
    resp = QueryResponse(success=True, answer="No docs found")
    assert resp.sources == []
    assert resp.model == ""
    assert resp.pipeline_metrics.total_ms == 0
    assert resp.retrieved_chunks == []


def test_document_response():
    """DocumentResponse validates correctly."""
    resp = DocumentResponse(
        success=True, document_id="abc-123", chunks_created=5, pii_detected=True
    )
    assert resp.pii_detected is True
    assert resp.chunks_created == 5


def test_chunk_metadata():
    """ChunkMetadata handles all fields."""
    meta = ChunkMetadata(
        document_id="doc-1",
        filename="test.txt",
        chunk_index=0,
        start_char=0,
        end_char=100,
        ingested_at="2026-02-07T12:00:00",
        data_classification=DataClassification.INTERNAL,
        pii_detected=True,
    )
    assert meta.data_classification == DataClassification.INTERNAL
    assert meta.pii_detected is True
    assert meta.retention_days == 365
