"""Vector index write port — the counterpart to `Retriever`'s read side.

Keeping writes out of `Retriever` means the API never gains the ability
to mutate the index just because it can search it.
"""

from collections.abc import Sequence
from typing import Protocol

from rag_api.domain.models import EmbeddedChunk


class ChunkIndex(Protocol):
    async def ensure_ready(self, *, dimension: int) -> None:
        """Create the collection if missing, sized for `dimension`."""
        ...

    async def upsert(self, entries: Sequence[EmbeddedChunk]) -> None:
        """Insert or replace chunks, addressed by a stable id."""
        ...

    async def count(self) -> int:
        """Number of chunks currently indexed."""
        ...
