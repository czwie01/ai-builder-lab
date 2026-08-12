"""Retrieval-quality evals over the golden set.

Deterministic corpus + deterministic scoring means these metrics are
exact and can gate CI without secrets or network access. Practice 04
grows this seed into a fuller eval suite (groundedness, relevance).
"""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from rag_api.adapters.in_memory_retriever import InMemoryRetriever

GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.jsonl"
K = 3
RECALL_AT_K_THRESHOLD = 0.9
MRR_THRESHOLD = 0.8

pytestmark = pytest.mark.eval


@dataclass(frozen=True)
class GoldenExample:
    question: str
    relevant_document_ids: frozenset[str]


def load_golden_set() -> list[GoldenExample]:
    examples = []
    with GOLDEN_SET_PATH.open() as handle:
        for line in handle:
            row = json.loads(line)
            examples.append(
                GoldenExample(
                    question=row["question"],
                    relevant_document_ids=frozenset(row["relevant_document_ids"]),
                )
            )
    return examples


def recall_at_k(retrieved_ids: list[str], relevant_ids: frozenset[str], k: int) -> float:
    hits = len(set(retrieved_ids[:k]) & relevant_ids)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: frozenset[str]) -> float:
    for rank, document_id in enumerate(retrieved_ids, start=1):
        if document_id in relevant_ids:
            return 1 / rank
    return 0.0


async def test_recall_at_k_meets_threshold() -> None:
    retriever = InMemoryRetriever()
    examples = load_golden_set()

    recalls = []
    for example in examples:
        chunks = await retriever.search(example.question, limit=K)
        retrieved_ids = [chunk.document_id for chunk in chunks]
        recalls.append(recall_at_k(retrieved_ids, example.relevant_document_ids, K))

    mean_recall = sum(recalls) / len(recalls)
    detail = f"recall@{K}={mean_recall:.3f} over {len(recalls)} examples"
    assert mean_recall >= RECALL_AT_K_THRESHOLD, detail


async def test_mean_reciprocal_rank_meets_threshold() -> None:
    retriever = InMemoryRetriever()
    examples = load_golden_set()

    ranks = []
    for example in examples:
        chunks = await retriever.search(example.question, limit=K)
        retrieved_ids = [chunk.document_id for chunk in chunks]
        ranks.append(reciprocal_rank(retrieved_ids, example.relevant_document_ids))

    mrr = sum(ranks) / len(ranks)
    assert mrr >= MRR_THRESHOLD, f"MRR={mrr:.3f} over {len(ranks)} examples"
