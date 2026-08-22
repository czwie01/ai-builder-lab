"""Hand-rolled fakes shared by the unit and adapter tests.

`HashEmbedder` is a deterministic, offline stand-in for a real embedding
model: it buckets tokens by a *stable* hash (hashlib, not the salted
builtin `hash`) so cosine similarity approximates term overlap, and adds
a tiny per-text component so two different texts can never produce
exactly equal scores — Qdrant's local mode sorts with a non-stable
argsort, so exact ties would have undefined order.
"""

import hashlib
import math
import re
from collections.abc import Sequence

from rag_api.domain.models import EmbeddedChunk

_TOKEN = re.compile(r"[a-z0-9]+")


def _bucket(token: str, buckets: int) -> int:
    digest = hashlib.sha1(token.encode(), usedforsecurity=False).digest()
    return int.from_bytes(digest[:4], "big") % buckets


class HashEmbedder:
    def __init__(self, dimension: int = 64) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return [self.vector(text) for text in texts]

    async def embed_query(self, text: str) -> Sequence[float]:
        return self.vector(text)

    def vector(self, text: str) -> list[float]:
        buckets = self._dimension - 1
        values = [0.0] * self._dimension
        for token in _TOKEN.findall(text.lower()):
            values[_bucket(token, buckets)] += 1.0
        digest = hashlib.sha1(text.encode(), usedforsecurity=False).digest()
        values[-1] = 1e-3 * (int.from_bytes(digest[:4], "big") % 997) / 997
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]


class FakeChunkIndex:
    def __init__(self) -> None:
        self.dimensions: list[int] = []
        self.entries: list[EmbeddedChunk] = []

    async def ensure_ready(self, *, dimension: int) -> None:
        self.dimensions.append(dimension)

    async def upsert(self, entries: Sequence[EmbeddedChunk]) -> None:
        self.entries.extend(entries)

    async def count(self) -> int:
        return len(self.entries)
