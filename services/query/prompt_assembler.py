"""
PromptAssembler - 4-layer prompt ordering with token-aware budgeting.

Layer 1: System Instructions     (pinned, never truncated)
Layer 2: Retrieved Documents     (highest priority grounding)
Layer 3: Clarification Context   (previous turn only, dropped first)
Layer 4: Current User Question   (always included)
"""
import tiktoken
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context documents.

Rules:
- Only use information from the provided context
- If the context doesn't contain relevant information, say so
- Cite sources using the document filenames in brackets like [filename]
- Be concise and accurate
- If you're unsure, say so rather than guessing"""


class PromptAssembler:
    """Assembles prompts with explicit 4-layer ordering and token budget."""

    def __init__(self, max_context_tokens: int = 3000):
        self.max_context_tokens = max_context_tokens
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def _fit_chunks(
        self, chunks: List[Dict], available_tokens: int
    ) -> tuple:
        """
        Fit as many chunks as possible within the token budget.

        Returns (formatted_text, tokens_used, chunks_used_count, chunk_details).
        chunk_details is a list of dicts with per-chunk token counts and
        included_in_prompt flag.
        """
        parts = []
        tokens_used = 0
        chunks_used = 0
        chunk_details = []

        for chunk in chunks:
            text = chunk.get("text", "")
            filename = chunk.get("metadata", {}).get("filename", "unknown")
            chunk_index = chunk.get("metadata", {}).get("chunk_index", 0)
            formatted = f"[{filename}]: {text}"
            chunk_tokens = self._count_tokens(formatted)

            included = False
            if tokens_used + chunk_tokens <= available_tokens:
                parts.append(formatted)
                tokens_used += chunk_tokens
                chunks_used += 1
                included = True

            chunk_details.append({
                "tokens": chunk_tokens,
                "included_in_prompt": included,
            })

        return "\n\n".join(parts), tokens_used, chunks_used, chunk_details

    def assemble(
        self,
        question: str,
        retrieved_chunks: List[Dict],
        clarification_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict:
        """
        Assemble prompt with 4-layer ordering and return metadata.

        Returns:
            {
                "messages": [...],       # Ready for LLM
                "metadata": {...},       # Assembly debug info
                "chunk_details": [...]   # Per-chunk inclusion info
            }
        """
        system = system_prompt or DEFAULT_SYSTEM_PROMPT
        budget = self.max_context_tokens

        # Layer 1: System instructions (pinned)
        system_tokens = self._count_tokens(system)

        # Layer 4: User question (pinned) - reserve space first
        question_tokens = self._count_tokens(question)

        # Available budget for layers 2 + 3
        available = budget - system_tokens - question_tokens

        # Layer 2: Retrieved documents (highest priority)
        docs_text, docs_tokens, docs_used, chunk_details = self._fit_chunks(
            retrieved_chunks, available
        )

        # Layer 3: Clarification context (dropped first under pressure)
        remaining = available - docs_tokens
        clarification_text = None
        clarification_tokens = 0
        clarification_included = False

        if clarification_context and remaining > 50:
            clar_tokens = self._count_tokens(clarification_context)
            if clar_tokens <= remaining:
                clarification_text = clarification_context
                clarification_tokens = clar_tokens
                clarification_included = True
            else:
                logger.info(
                    "Clarification context dropped under token pressure",
                    extra={
                        "clarification_tokens": clar_tokens,
                        "remaining_budget": remaining,
                    },
                )

        # Build user content combining layers 2, 3, 4
        user_parts = []
        if docs_text:
            user_parts.append(f"Context documents:\n{docs_text}")
        if clarification_text:
            user_parts.append(
                f"Previous exchange (for clarification only):\n{clarification_text}"
            )
        user_parts.append(f"Question: {question}")
        if docs_text:
            user_parts.append(
                "Answer based on the context above. "
                "Cite sources in [filename] format. "
                "If the context lacks relevant information, say so."
            )

        user_content = "\n\n".join(user_parts)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

        total_tokens = (
            system_tokens + docs_tokens + clarification_tokens + question_tokens
        )

        metadata = {
            "system_tokens": system_tokens,
            "retrieved_docs_tokens": docs_tokens,
            "retrieved_docs_used": docs_used,
            "clarification_included": clarification_included,
            "clarification_tokens": clarification_tokens,
            "question_tokens": question_tokens,
            "total_tokens": total_tokens,
            "budget": self.max_context_tokens,
        }

        return {
            "messages": messages,
            "metadata": metadata,
            "chunk_details": chunk_details,
        }
