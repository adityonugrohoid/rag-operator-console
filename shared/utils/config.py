"""Configuration management."""
import os
from pydantic import BaseModel


class Config(BaseModel):
    """Application configuration (Ollama + ChromaDB only)"""
    ENVIRONMENT: str = "local"
    LLM_MODEL: str = "llama3.2:3b"
    OLLAMA_HOST: str = "http://localhost:11434"
    CHROMA_HOST: str = "http://localhost:8000"

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            ENVIRONMENT=os.getenv("ENVIRONMENT", "local"),
            LLM_MODEL=os.getenv("LLM_MODEL", "llama3.2:3b"),
            OLLAMA_HOST=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            CHROMA_HOST=os.getenv("CHROMA_HOST", "http://localhost:8000"),
        )
