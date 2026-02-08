"""Embedding client for generating vector embeddings."""
from sentence_transformers import SentenceTransformer
from typing import List
import logging
import os

logger = logging.getLogger(__name__)


class Embedder:
    """Client for generating text embeddings using all-MiniLM-L6-v2 (384-dim)"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        cache_dir = os.getenv(
            "HF_HOME",
            os.path.join(os.path.expanduser("~"), ".cache", "huggingface"),
        )
        os.makedirs(cache_dir, exist_ok=True)
        try:
            self.model = SentenceTransformer(model_name, cache_folder=cache_dir)
        except Exception as e:
            logger.warning(f"Failed with cache folder, trying default: {e}")
            self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")

    def embed(self, texts: str | List[str]) -> List[List[float]]:
        """Generate embeddings for text(s)."""
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
