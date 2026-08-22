"""fastembed embedding adapter (ONNX, CPU, no torch).

Two things about fastembed drive the shape of this class:

* Constructing `TextEmbedding` downloads the model weights — even with
  `lazy_load=True`, which only defers the ONNX session. So an instance is
  built by an explicit factory call, never at import time, and never at
  test-collection time.
* `query_embed()` does *not* add BGE's query instruction; it just calls
  `embed()`. If the prefix is wanted it has to be applied by hand, and
  applied consistently at ingest, at serving time, and in evals — so it
  lives here, in one place.

Embedding is CPU-bound and synchronous, so calls are offloaded to a
thread to keep the event loop free.
"""

import asyncio
from collections.abc import Sequence

from fastembed import TextEmbedding

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def embedding_dimension(model_name: str) -> int:
    """Look up a model's vector size from fastembed's static metadata (no download)."""
    for description in TextEmbedding.list_supported_models():
        if description["model"] == model_name:
            return int(description["dim"])
    raise ValueError(f"unknown embedding model: {model_name}")


class FastEmbedEmbedder:
    def __init__(
        self,
        *,
        model_name: str = DEFAULT_MODEL,
        cache_dir: str | None = None,
        query_prefix: str = DEFAULT_QUERY_PREFIX,
    ) -> None:
        self._dimension = embedding_dimension(model_name)
        self._query_prefix = query_prefix
        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return await asyncio.to_thread(self._embed, list(texts))

    async def embed_query(self, text: str) -> Sequence[float]:
        vectors = await asyncio.to_thread(self._embed, [f"{self._query_prefix}{text}"])
        return vectors[0]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]
