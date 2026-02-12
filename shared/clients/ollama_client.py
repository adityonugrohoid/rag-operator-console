"""Ollama LLM client for local model inference."""
import httpx
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

AVAILABLE_MODELS = [
    {"id": "gemma2:2b", "size": "1.6GB", "tier": "fast"},
    {"id": "llama3.2:1b", "size": "1.3GB", "tier": "fast"},
    {"id": "phi3:3.8b", "size": "2.2GB", "tier": "balanced"},
    {"id": "llama3.2:3b", "size": "2.0GB", "tier": "balanced"},
    {"id": "mistral:7b", "size": "4.4GB", "tier": "quality"},
    {"id": "llama3.1:8b", "size": "4.9GB", "tier": "quality"},
]

VALID_MODEL_IDS = {m["id"] for m in AVAILABLE_MODELS}


class OllamaClient:
    """Focused Ollama client for Phases 1-4 (local models only)."""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.default_model = model or os.getenv("LLM_MODEL", "gemma2:2b")

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> Dict:
        """
        Send a chat completion request to Ollama.

        Returns dict with 'response' text, 'eval_count' (tokens generated),
        and 'eval_duration' (nanoseconds for generation).
        """
        use_model = model or self.default_model
        payload = {
            "model": use_model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        with httpx.Client(timeout=300.0) as client:
            resp = client.post(
                f"{self.host}/api/chat",
                json=payload,
            )
            resp.raise_for_status()

        data = resp.json()
        return {
            "response": data.get("message", {}).get("content", ""),
            "eval_count": data.get("eval_count", 0),
            "eval_duration": data.get("eval_duration", 0),
        }

    def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.host}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def list_running_models(self) -> List[str]:
        """List models available in Ollama."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.host}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
