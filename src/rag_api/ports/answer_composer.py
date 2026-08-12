"""Answer composition port — the provider-agnostic LLM seam.

Today's adapter is deterministic. Practice 03 adds LLM-backed adapters
(Anthropic, OpenAI, ...) behind this same signature; nothing upstream
of the port knows or cares which vendor produced the text.
"""

from collections.abc import Sequence
from typing import Protocol

from rag_api.domain.models import RetrievedChunk


class AnswerComposer(Protocol):
    async def compose(self, question: str, chunks: Sequence[RetrievedChunk]) -> str:
        """Produce answer text for `question` grounded in `chunks`."""
        ...
