"""Basic tests for schemas."""
import pytest
from shared.models.schemas import QueryRequest, QueryResponse


def test_query_request():
    """QueryRequest basic validation."""
    req = QueryRequest(query="test")
    assert req.query == "test"
    assert req.temperature == 0.7


def test_query_response():
    """QueryResponse basic validation."""
    resp = QueryResponse(success=True, answer="Test answer")
    assert resp.success is True
    assert resp.answer == "Test answer"
