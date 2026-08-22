"""Text embedding port.

Async so adapters can offload CPU-bound model work to a thread; the
document/query split exists because embedding models often treat the two
asymmetrically (BGE, for instance, wants an instruction prefix on
queries only — and fastembed does not add it for you).
"""

from collections.abc import Sequence
from typing import Protocol


class TextEmbedder(Protocol):
    @property
    def dimension(self) -> int:
        """Length of the vectors this embedder produces."""
        ...

    async def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Embed passages for indexing, in the order given."""
        ...

    async def embed_query(self, text: str) -> Sequence[float]:
        """Embed a search query."""
        ...
