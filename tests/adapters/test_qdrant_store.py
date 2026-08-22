"""Adapter tests against Qdrant's embedded local mode.

These are hermetic: `AsyncQdrantClient(":memory:")` runs in-process with
no server and no network, and the embedder is a deterministic fake, so
they belong in the default `uv run pytest` run. What local mode cannot
prove — ANN recall, payload indexes, server-side id validation — is
covered by the marker-gated tests in tests/integration/.
"""

import uuid
from collections.abc import AsyncIterator

import pytest
from qdrant_client import AsyncQdrantClient

from rag_api.adapters.qdrant_store import (
    QdrantChunkIndex,
    QdrantRetriever,
    chunk_point_id,
)
from rag_api.application.ingest_corpus import IngestCorpus
from rag_api.domain.models import SourceDocument
from tests.fakes import HashEmbedder

pytestmark = pytest.mark.filterwarnings("ignore:Payload indexes have no effect")

DOCUMENTS = [
    SourceDocument(
        document_id="hexagonal",
        source_path="hexagonal.md",
        text="# Ports\n\nA port is an interface the application core depends on.\n",
    ),
    SourceDocument(
        document_id="guardrails",
        source_path="guardrails.md",
        text="# Guardrails\n\nInput validation rejects injection attempts at the boundary.\n",
    ),
    SourceDocument(
        document_id="evals",
        source_path="evals.md",
        text="# Evals\n\nRecall at k measures how often the right document is retrieved.\n",
    ),
]


@pytest.fixture
async def client() -> AsyncIterator[AsyncQdrantClient]:
    qdrant = AsyncQdrantClient(":memory:")
    try:
        yield qdrant
    finally:
        await qdrant.close()


async def _ingest(qdrant: AsyncQdrantClient) -> QdrantRetriever:
    embedder = HashEmbedder()
    index = QdrantChunkIndex(qdrant, collection="test_chunks")
    await IngestCorpus(index, embedder).execute(DOCUMENTS)
    return QdrantRetriever(qdrant, embedder, collection="test_chunks")


def test_point_ids_are_uuids_a_real_server_will_accept() -> None:
    point_id = chunk_point_id("hexagonal", 0)

    assert uuid.UUID(point_id).version == 5
    assert chunk_point_id("hexagonal", 0) == point_id
    assert chunk_point_id("hexagonal", 1) != point_id


async def test_round_trip_finds_the_relevant_document(client: AsyncQdrantClient) -> None:
    retriever = await _ingest(client)

    results = await retriever.search("what is a port in the application core", limit=3)

    assert results
    assert results[0].document_id == "hexagonal"


async def test_respects_the_limit(client: AsyncQdrantClient) -> None:
    retriever = await _ingest(client)

    assert len(await retriever.search("port interface", limit=2)) <= 2


async def test_results_are_ordered_by_descending_score(client: AsyncQdrantClient) -> None:
    retriever = await _ingest(client)

    results = await retriever.search("injection attempts at the boundary", limit=3)

    scores = [chunk.score for chunk in results]
    assert scores == sorted(scores, reverse=True)


async def test_ordering_is_reproducible_across_calls(client: AsyncQdrantClient) -> None:
    retriever = await _ingest(client)

    first = await retriever.search("recall at k", limit=3)
    second = await retriever.search("recall at k", limit=3)

    assert [chunk.document_id for chunk in first] == [chunk.document_id for chunk in second]


async def test_re_ingesting_replaces_chunks_instead_of_duplicating(
    client: AsyncQdrantClient,
) -> None:
    index = QdrantChunkIndex(client, collection="test_chunks")
    embedder = HashEmbedder()
    await IngestCorpus(index, embedder).execute(DOCUMENTS)
    after_first = await index.count()

    await IngestCorpus(index, embedder).execute(DOCUMENTS)

    assert after_first > 0
    assert await index.count() == after_first


async def test_payload_carries_the_source_for_later_filtering(client: AsyncQdrantClient) -> None:
    await _ingest(client)

    points, _ = await client.scroll(collection_name="test_chunks", limit=1, with_payload=True)
    payload = points[0].payload or {}

    assert payload["source_path"].endswith(".md")
    assert isinstance(payload["chunk_index"], int)
    assert isinstance(payload["heading_path"], list)
