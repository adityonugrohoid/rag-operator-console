"""Tests for Ollama client."""
import pytest
from unittest.mock import patch, MagicMock
from shared.clients.ollama_client import (
    OllamaClient,
    AVAILABLE_MODELS,
    VALID_MODEL_IDS,
)


def test_available_models():
    """Model registry has 6 models across 3 tiers."""
    assert len(AVAILABLE_MODELS) == 6
    tiers = {m["tier"] for m in AVAILABLE_MODELS}
    assert tiers == {"fast", "balanced", "quality"}
    fast = [m for m in AVAILABLE_MODELS if m["tier"] == "fast"]
    assert len(fast) == 2


def test_valid_model_ids():
    """VALID_MODEL_IDS matches AVAILABLE_MODELS."""
    assert len(VALID_MODEL_IDS) == 6
    assert "llama3.2:3b" in VALID_MODEL_IDS
    assert "mistral:7b" in VALID_MODEL_IDS


def test_client_defaults():
    """Client initializes with default host and model."""
    client = OllamaClient()
    assert client.host == "http://localhost:11434"
    assert client.default_model == "gemma2:2b"


def test_client_custom_config():
    """Client accepts custom host and model."""
    client = OllamaClient(host="http://custom:11434", model="mistral:7b")
    assert client.host == "http://custom:11434"
    assert client.default_model == "mistral:7b"


@patch("shared.clients.ollama_client.httpx.Client")
def test_chat_sends_correct_payload(mock_client_cls):
    """Chat method sends correct payload to Ollama."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "message": {"content": "Test response"},
        "eval_count": 42,
        "eval_duration": 1000000000,
    }
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_cls.return_value = mock_client

    client = OllamaClient()
    result = client.chat(
        messages=[{"role": "user", "content": "Hello"}],
        model="mistral:7b",
        temperature=0.5,
        max_tokens=256,
    )

    assert result["response"] == "Test response"
    assert result["eval_count"] == 42

    call_args = mock_client.post.call_args
    payload = call_args[1]["json"]
    assert payload["model"] == "mistral:7b"
    assert payload["options"]["temperature"] == 0.5
    assert payload["options"]["num_predict"] == 256


@patch("shared.clients.ollama_client.httpx.Client")
def test_is_available_true(mock_client_cls):
    """is_available returns True when Ollama responds."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_cls.return_value = mock_client

    assert OllamaClient().is_available() is True


@patch("shared.clients.ollama_client.httpx.Client")
def test_is_available_false(mock_client_cls):
    """is_available returns False when Ollama is unreachable."""
    mock_client = MagicMock()
    mock_client.get.side_effect = Exception("Connection refused")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_cls.return_value = mock_client

    assert OllamaClient().is_available() is False
