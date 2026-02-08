"""Text chunking utilities."""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunk text into smaller pieces for embedding"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> List[Dict[str, any]]:
        """Split text into chunks. Returns list of dicts with 'text', 'start', 'end'."""
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0
        start_char = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start": start_char,
                    "end": start_char + len(chunk_text),
                })
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
                start_char = chunks[-1]["end"] - len(" ".join(overlap_sentences))
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start": start_char,
                "end": start_char + len(chunk_text),
            })

        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        overlap_count = max(1, len(sentences) // 4)
        return sentences[-overlap_count:] if len(sentences) > overlap_count else []
