"""Retrieval-quality evals over the frozen corpus in `evals/corpus/`.

The corpus is frozen on purpose: it is version-controlled next to the
questions, so a score only moves when the retrieval pipeline moves. The
repo's own `docs/` tree can be ingested for demos, but it is deliberately
not what the gate measures — otherwise editing a document would rewrite
the baseline.

Thresholds are derived from measured values, never chosen to make a run
pass; the numbers and their margins are recorded in the practice log.
"""

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest
from qdrant_client import AsyncQdrantClient

from rag_api.adapters.fastembed_embedder import FastEmbedEmbedder
from rag_api.adapters.in_memory_retriever import InMemoryRetriever
from rag_api.adapters.markdown_corpus import load_markdown_documents
from rag_api.adapters.qdrant_store import QdrantChunkIndex, QdrantRetriever
from rag_api.application.chunking import chunk_markdown
from rag_api.application.ingest_corpus import IngestCorpus
from rag_api.domain.models import DocumentChunk
from rag_api.ports.retriever import Retriever

CORPUS_PATH = Path(__file__).parent / "corpus"
GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.jsonl"
K = 3

# Measured on the frozen corpus before the thresholds were chosen:
# recall@3 = 0.840, MRR = 0.793 over 25 questions and 31 chunks.
TERM_OVERLAP_RECALL_THRESHOLD = 0.80
TERM_OVERLAP_MRR_THRESHOLD = 0.75

# Measured in CI on the frozen corpus (the model cannot be fetched in
# every environment): recall@3 = 1.000, MRR = 0.953, 0 misses out of 25.
# The thresholds sit one miss below perfect rather than *at* it — a gate
# that demands 8/8 is how the Practice 01 gate became brittle. int8 ONNX
# is also not bit-reproducible across CPUs, so some margin is required.
DENSE_RECALL_THRESHOLD = 0.95
DENSE_MRR_THRESHOLD = 0.90

# CI sets this so a missing model fails the gate instead of skipping it.
REQUIRE_DENSE = os.environ.get("RAG_API_EVAL_REQUIRE_DENSE") == "1"

pytestmark = pytest.mark.eval


@dataclass(frozen=True, slots=True)
class GoldenExample:
    question: str
    relevant_document_ids: frozenset[str]


@dataclass(frozen=True, slots=True)
class Metrics:
    recall_at_k: float
    mrr: float
    misses: tuple[str, ...]

    def summary(self, label: str) -> str:
        return (
            f"{label}: recall@{K}={self.recall_at_k:.3f} MRR={self.mrr:.3f} "
            f"({len(self.misses)} miss(es))"
        )


def load_golden_set() -> list[GoldenExample]:
    with GOLDEN_SET_PATH.open(encoding="utf-8") as handle:
        return [
            GoldenExample(
                question=row["question"],
                relevant_document_ids=frozenset(row["relevant_document_ids"]),
            )
            for row in (json.loads(line) for line in handle if line.strip())
        ]


def load_corpus_chunks() -> list[DocumentChunk]:
    return [
        chunk
        for document in load_markdown_documents(CORPUS_PATH)
        for chunk in chunk_markdown(
            document.text,
            document_id=document.document_id,
            source_path=document.source_path,
        )
    ]


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: frozenset[str], k: int) -> float:
    return len(set(retrieved_ids[:k]) & relevant_ids) / len(relevant_ids)


def reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: frozenset[str]) -> float:
    for rank, document_id in enumerate(retrieved_ids, start=1):
        if document_id in relevant_ids:
            return 1 / rank
    return 0.0


async def measure(
    retriever: Retriever, examples: Sequence[GoldenExample], *, k: int = K
) -> Metrics:
    recalls: list[float] = []
    ranks: list[float] = []
    misses: list[str] = []
    for example in examples:
        chunks = await retriever.search(example.question, limit=k)
        retrieved_ids = [chunk.document_id for chunk in chunks]
        recall = recall_at_k(retrieved_ids, example.relevant_document_ids, k)
        recalls.append(recall)
        ranks.append(reciprocal_rank(retrieved_ids, example.relevant_document_ids))
        if recall < 1.0:
            misses.append(example.question)
    return Metrics(
        recall_at_k=sum(recalls) / len(recalls),
        mrr=sum(ranks) / len(ranks),
        misses=tuple(misses),
    )


def build_term_overlap_retriever(chunks: Sequence[DocumentChunk]) -> Retriever:
    return InMemoryRetriever([(chunk.document_id, chunk.text) for chunk in chunks])


def test_corpus_is_large_enough_for_the_gate_to_mean_something() -> None:
    """A gate over a handful of chunks scores well by luck; this guards that lesson."""
    chunks = load_corpus_chunks()

    assert len({chunk.document_id for chunk in chunks}) >= 6
    assert len(chunks) >= 25
    assert len(load_golden_set()) >= 20


async def test_term_overlap_retrieval_meets_thresholds() -> None:
    metrics = await measure(build_term_overlap_retriever(load_corpus_chunks()), load_golden_set())

    print(f"\n{metrics.summary('term-overlap')}")
    assert metrics.recall_at_k >= TERM_OVERLAP_RECALL_THRESHOLD, metrics.summary("term-overlap")
    assert metrics.mrr >= TERM_OVERLAP_MRR_THRESHOLD, metrics.summary("term-overlap")


def _embedder_or_skip() -> FastEmbedEmbedder:
    """Build the real embedder, or skip where its weights cannot be fetched."""
    try:
        return FastEmbedEmbedder()
    except Exception as exc:  # any failure here means "no usable model"
        if REQUIRE_DENSE:
            raise
        pytest.skip(f"embedding model unavailable ({type(exc).__name__}): {exc}")


async def test_dense_retrieval_meets_thresholds() -> None:
    """The same golden set, answered by embeddings instead of word overlap.

    Indexing runs through the real ingest pipeline into Qdrant's embedded
    local mode, so this measures the shipped chunker, embedder and
    retriever without needing a server.
    """
    embedder = _embedder_or_skip()
    client = AsyncQdrantClient(":memory:")
    try:
        index = QdrantChunkIndex(client, collection="eval_chunks")
        await IngestCorpus(index, embedder).execute(load_markdown_documents(CORPUS_PATH))
        retriever = QdrantRetriever(client, embedder, collection="eval_chunks")
        metrics = await measure(retriever, load_golden_set())
    finally:
        await client.close()

    print(f"\n{metrics.summary('dense')}")
    for miss in metrics.misses:
        print(f"  miss: {miss}")
    assert metrics.recall_at_k >= DENSE_RECALL_THRESHOLD, metrics.summary("dense")
    assert metrics.mrr >= DENSE_MRR_THRESHOLD, metrics.summary("dense")
