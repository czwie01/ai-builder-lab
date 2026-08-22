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
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from rag_api.adapters.in_memory_retriever import InMemoryRetriever
from rag_api.adapters.markdown_corpus import load_markdown_documents
from rag_api.application.chunking import chunk_markdown
from rag_api.domain.models import DocumentChunk
from rag_api.ports.retriever import Retriever

CORPUS_PATH = Path(__file__).parent / "corpus"
GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.jsonl"
K = 3

# Measured on the frozen corpus before the thresholds were chosen:
# recall@3 = 0.840, MRR = 0.793 over 25 questions and 31 chunks.
TERM_OVERLAP_RECALL_THRESHOLD = 0.80
TERM_OVERLAP_MRR_THRESHOLD = 0.75

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
