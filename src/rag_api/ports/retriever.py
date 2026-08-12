"""Retrieval port. Adapters: in-memory (Practice 01), Qdrant (Practice 02)."""

from collections.abc import Sequence
from typing import Protocol

from rag_api.domain.models import RetrievedChunk


class Retriever(Protocol):
    async def search(self, query: str, *, limit: int) -> Sequence[RetrievedChunk]:
        """Return up to `limit` chunks relevant to `query`, best first."""
        ...
