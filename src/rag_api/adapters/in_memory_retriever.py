"""Deterministic in-memory retriever.

Scores by term overlap between the query and each chunk, so identical
inputs always produce identical rankings — tests and evals need no
vector database or embedding model.
"""

from collections.abc import Sequence

from rag_api.domain.models import RetrievedChunk

SAMPLE_CHUNKS: tuple[tuple[str, str], ...] = (
    (
        "architecture-01",
        "In hexagonal architecture, a port is an interface the application core "
        "depends on, and an adapter is a concrete implementation wired in from "
        "the outside. Graph state should contain workflow data, not "
        "infrastructure objects.",
    ),
    (
        "rag-basics-01",
        "Retrieval-augmented generation grounds an answer in retrieved chunks. "
        "Citations should reference document identifiers and scores rather than "
        "exposing raw chunk text to clients.",
    ),
    (
        "evals-01",
        "Retrieval quality is measured with metrics such as recall at k and mean "
        "reciprocal rank over a golden dataset of questions with known relevant "
        "documents.",
    ),
    (
        "guardrails-01",
        "Input guardrails validate questions before retrieval: length limits, "
        "control characters, and prompt injection patterns are checked at the "
        "boundary so the core workflow only sees vetted input.",
    ),
)


def _tokenize(text: str) -> set[str]:
    return {token.strip(".,:;!?()\"'") for token in text.lower().split()} - {""}


class InMemoryRetriever:
    def __init__(self, chunks: Sequence[tuple[str, str]] = SAMPLE_CHUNKS) -> None:
        self._chunks = tuple(chunks)

    async def search(self, query: str, *, limit: int) -> Sequence[RetrievedChunk]:
        query_terms = _tokenize(query)
        if not query_terms:
            return ()
        scored = []
        for document_id, text in self._chunks:
            overlap = len(query_terms & _tokenize(text))
            if overlap:
                score = round(overlap / len(query_terms), 4)
                scored.append(RetrievedChunk(document_id=document_id, text=text, score=score))
        scored.sort(key=lambda chunk: (-chunk.score, chunk.document_id))
        return tuple(scored[:limit])
