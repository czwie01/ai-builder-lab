"""Congruence tests against a real Qdrant server.

Everything here exists because the embedded local mode cannot prove it:
a server validates point ids (local mode does not), actually builds
payload indexes (local mode warns and ignores them), and answers through
an approximate index rather than an exact scan.

    docker compose up -d
    uv run pytest -m integration

The embedder is still the deterministic fake, so this tier needs a
service but no model download.
"""

import os
from collections.abc import AsyncIterator

import pytest
from qdrant_client import AsyncQdrantClient

from rag_api.adapters.qdrant_store import QdrantChunkIndex, QdrantRetriever
from rag_api.application.ingest_corpus import IngestCorpus
from rag_api.domain.models import SourceDocument
from tests.fakes import HashEmbedder

pytestmark = pytest.mark.integration

COLLECTION = "integration_chunks"
DOCUMENTS = [
    SourceDocument(
        document_id="ports",
        source_path="ports.md",
        text="# Ports\n\nA port is an interface the application core depends on.\n",
    ),
    SourceDocument(
        document_id="evals",
        source_path="evals.md",
        text="# Evals\n\nRecall at k measures retrieval quality over a golden set.\n",
    ),
]


@pytest.fixture
async def client() -> AsyncIterator[AsyncQdrantClient]:
    url = os.environ.get("RAG_API_QDRANT_URL", "http://localhost:6333")
    qdrant = AsyncQdrantClient(url=url)
    try:
        if await qdrant.collection_exists(COLLECTION):
            await qdrant.delete_collection(COLLECTION)
        yield qdrant
    finally:
        await qdrant.close()


async def test_server_accepts_our_point_ids_and_returns_results(
    client: AsyncQdrantClient,
) -> None:
    """A server rejects any id that is not an unsigned int or UUID."""
    index = QdrantChunkIndex(client, collection=COLLECTION)
    embedder = HashEmbedder()
    await IngestCorpus(index, embedder).execute(DOCUMENTS)

    results = await QdrantRetriever(client, embedder, collection=COLLECTION).search(
        "what is a port in the application core", limit=2
    )

    assert await index.count() == 2
    assert results[0].document_id == "ports"


async def test_payload_indexes_are_really_created(client: AsyncQdrantClient) -> None:
    """Local mode warns and ignores these; only a server can confirm them."""
    await QdrantChunkIndex(client, collection=COLLECTION).ensure_ready(dimension=64)

    info = await client.get_collection(COLLECTION)

    assert {"document_id", "source_path"} <= set(info.payload_schema)
