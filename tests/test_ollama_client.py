"""Basic tests for Ollama client."""
import pytest
from shared.clients.ollama_client import OllamaClient, AVAILABLE_MODELS


def test_available_models():
    """Model registry has models."""
    assert len(AVAILABLE_MODELS) > 0


def test_client_defaults():
    """Client initializes with defaults."""
    client = OllamaClient()
    assert client.host == "http://localhost:11434"
    assert client.default_model == "llama3.2:3b"
