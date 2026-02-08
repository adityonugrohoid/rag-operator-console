"""Tests for PromptAssembler - 4-layer prompt ordering with token budget."""
import pytest
from services.query.prompt_assembler import PromptAssembler


@pytest.fixture
def assembler():
    return PromptAssembler(max_context_tokens=500)


@pytest.fixture
def sample_chunks():
    return [
        {
            "text": "The 5G RAN performance targets require a call drop rate below 0.5%.",
            "metadata": {"filename": "telecom_doc_01.txt", "chunk_index": 0},
            "score": 0.92,
        },
        {
            "text": "Network optimization procedures include load balancing and handover tuning.",
            "metadata": {"filename": "telecom_doc_02.txt", "chunk_index": 1},
            "score": 0.85,
        },
        {
            "text": "OSS/BSS integration connects operational and business support systems.",
            "metadata": {"filename": "telecom_doc_03.txt", "chunk_index": 2},
            "score": 0.78,
        },
    ]


def test_basic_assembly(assembler, sample_chunks):
    """All layers present, all chunks fit."""
    result = assembler.assemble(
        question="What are the 5G performance targets?",
        retrieved_chunks=sample_chunks,
    )
    assert "messages" in result
    assert "metadata" in result
    assert len(result["messages"]) == 2
    assert result["messages"][0]["role"] == "system"
    assert result["messages"][1]["role"] == "user"
    meta = result["metadata"]
    assert meta["system_tokens"] > 0
    assert meta["retrieved_docs_used"] > 0
    assert meta["question_tokens"] > 0
    assert meta["total_tokens"] <= meta["budget"]


def test_system_prompt_always_pinned(assembler, sample_chunks):
    """System instructions are never truncated."""
    result = assembler.assemble(
        question="Test?",
        retrieved_chunks=sample_chunks,
    )
    assert result["metadata"]["system_tokens"] > 0
    assert "system" in result["messages"][0]["role"]


def test_clarification_context_included(assembler, sample_chunks):
    """Clarification context included when budget allows."""
    result = assembler.assemble(
        question="What about the optimization?",
        retrieved_chunks=sample_chunks[:1],
        clarification_context="Previously discussed 5G RAN performance.",
    )
    meta = result["metadata"]
    assert meta["clarification_included"] is True
    assert meta["clarification_tokens"] > 0
    assert "Previous exchange" in result["messages"][1]["content"]


def test_clarification_dropped_under_pressure():
    """Clarification context dropped when budget is tight."""
    small_assembler = PromptAssembler(max_context_tokens=200)
    long_chunks = [
        {
            "text": "A " * 100,
            "metadata": {"filename": "doc.txt", "chunk_index": 0},
            "score": 0.9,
        }
    ]
    result = small_assembler.assemble(
        question="What is this about?",
        retrieved_chunks=long_chunks,
        clarification_context="A " * 50,
    )
    meta = result["metadata"]
    assert meta["clarification_included"] is False
    assert meta["clarification_tokens"] == 0


def test_chunk_details_returned(assembler, sample_chunks):
    """Per-chunk inclusion info is returned."""
    result = assembler.assemble(
        question="Query?",
        retrieved_chunks=sample_chunks,
    )
    details = result["chunk_details"]
    assert len(details) == len(sample_chunks)
    for d in details:
        assert "tokens" in d
        assert "included_in_prompt" in d


def test_empty_chunks(assembler):
    """Handles empty retrieved chunks gracefully."""
    result = assembler.assemble(
        question="Anything here?",
        retrieved_chunks=[],
    )
    meta = result["metadata"]
    assert meta["retrieved_docs_used"] == 0
    assert meta["retrieved_docs_tokens"] == 0
    assert "Question:" in result["messages"][1]["content"]


def test_budget_overflow_drops_later_chunks():
    """Later chunks are dropped when budget is exceeded."""
    tiny = PromptAssembler(max_context_tokens=120)
    chunks = [
        {
            "text": "Short chunk.",
            "metadata": {"filename": "a.txt", "chunk_index": 0},
            "score": 0.9,
        },
        {
            "text": "Very long chunk that exceeds remaining budget " * 20,
            "metadata": {"filename": "b.txt", "chunk_index": 1},
            "score": 0.8,
        },
    ]
    result = tiny.assemble(question="Q?", retrieved_chunks=chunks)
    details = result["chunk_details"]
    assert details[0]["included_in_prompt"] is True
    assert details[1]["included_in_prompt"] is False


def test_metadata_budget_field(assembler, sample_chunks):
    """Budget field in metadata matches assembler configuration."""
    result = assembler.assemble(
        question="Test?",
        retrieved_chunks=sample_chunks,
    )
    assert result["metadata"]["budget"] == 500


def test_citation_instruction_in_prompt(assembler, sample_chunks):
    """Prompt includes citation instruction when docs are present."""
    result = assembler.assemble(
        question="What are targets?",
        retrieved_chunks=sample_chunks,
    )
    user_content = result["messages"][1]["content"]
    assert "[filename]" in user_content or "Cite sources" in user_content
