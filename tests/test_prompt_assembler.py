"""Basic tests for PromptAssembler."""
import pytest
from services.query.prompt_assembler import PromptAssembler


@pytest.fixture
def assembler():
    return PromptAssembler(max_context_tokens=500)


def test_basic_assembly(assembler):
    """Basic prompt assembly."""
    result = assembler.assemble(question="Test?", retrieved_chunks=[])
    assert "messages" in result
    assert "metadata" in result
    assert len(result["messages"]) == 2
