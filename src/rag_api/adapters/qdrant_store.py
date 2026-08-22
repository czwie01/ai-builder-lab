"""Qdrant adapters: the write side (`ChunkIndex`) and the read side (`Retriever`).

Both take an already-constructed client so tests can hand them Qdrant's
embedded local mode (`AsyncQdrantClient(":memory:")`), which needs no
server and no network.

Two Qdrant details are load-bearing here:

* A real server accepts only unsigned integers or UUIDs as point ids —
  local mode does not enforce that, so a readable id like `doc#3` would
  pass tests and fail in production. Ids are therefore uuid5 of
  `document_id:chunk_index`, which also makes re-ingest idempotent.
* Local mode ranks with a bare, non-stable `numpy.argsort`, so equally
  scored points come back in an unspecified order. The retriever imposes
  its own total order to keep results reproducible, matching the
  guarantee `InMemoryRetriever` already gives.
"""

import uuid
from collections.abc import Sequence

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest

from rag_api.domain.models import EmbeddedChunk, RetrievedChunk
from rag_api.ports.text_embedder import TextEmbedder

DEFAULT_COLLECTION = "rag_chunks"
UPSERT_BATCH_SIZE = 128
CHUNK_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")

_INDEXED_PAYLOAD_FIELDS = ("document_id", "source_path")


def chunk_point_id(document_id: str, chunk_index: int) -> str:
    """Stable point id, so re-ingesting a document replaces its chunks."""
    return str(uuid.uuid5(CHUNK_NAMESPACE, f"{document_id}:{chunk_index}"))


class QdrantChunkIndex:
    def __init__(self, client: AsyncQdrantClient, *, collection: str = DEFAULT_COLLECTION) -> None:
        self._client = client
        self._collection = collection

    async def ensure_ready(self, *, dimension: int) -> None:
        if not await self._client.collection_exists(self._collection):
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=rest.VectorParams(size=dimension, distance=rest.Distance.COSINE),
            )
        # Nothing filters on these yet — Practice 05 does. Creating the
        # indexes at ingest time is the right habit (a server builds them
        # far more cheaply before the data lands); local mode warns that
        # it ignores them, which is expected and harmless.
        for field_name in _INDEXED_PAYLOAD_FIELDS:
            await self._client.create_payload_index(
                collection_name=self._collection,
                field_name=field_name,
                field_schema=rest.PayloadSchemaType.KEYWORD,
            )

    async def upsert(self, entries: Sequence[EmbeddedChunk]) -> None:
        for start in range(0, len(entries), UPSERT_BATCH_SIZE):
            batch = entries[start : start + UPSERT_BATCH_SIZE]
            await self._client.upsert(
                collection_name=self._collection,
                points=[self._point(entry) for entry in batch],
                wait=True,
            )

    async def count(self) -> int:
        result = await self._client.count(collection_name=self._collection, exact=True)
        return result.count

    @staticmethod
    def _point(entry: EmbeddedChunk) -> rest.PointStruct:
        chunk = entry.chunk
        return rest.PointStruct(
            id=chunk_point_id(chunk.document_id, chunk.chunk_index),
            vector=list(entry.vector),
            payload={
                "document_id": chunk.document_id,
                "text": chunk.text,
                "source_path": chunk.source_path,
                "chunk_index": chunk.chunk_index,
                "heading_path": list(chunk.heading_path),
            },
        )


class QdrantRetriever:
    def __init__(
        self,
        client: AsyncQdrantClient,
        embedder: TextEmbedder,
        *,
        collection: str = DEFAULT_COLLECTION,
    ) -> None:
        self._client = client
        self._embedder = embedder
        self._collection = collection

    async def search(self, query: str, *, limit: int) -> Sequence[RetrievedChunk]:
        vector = await self._embedder.embed_query(query)
        response = await self._client.query_points(
            collection_name=self._collection,
            query=list(vector),
            limit=limit,
            with_payload=True,
        )
        scored = []
        for point in response.points:
            payload = point.payload or {}
            scored.append(
                (
                    float(point.score),
                    str(payload.get("document_id", "")),
                    int(payload.get("chunk_index", 0)),
                    str(payload.get("text", "")),
                )
            )
        scored.sort(key=lambda row: (-row[0], row[1], row[2]))
        return tuple(
            RetrievedChunk(document_id=document_id, text=text, score=round(score, 4))
            for score, document_id, _, text in scored
        )
