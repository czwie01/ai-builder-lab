"""Use-case tests with hand-rolled fakes — no adapters, no framework."""

from collections.abc import Sequence

import pytest

from rag_api.application.answer_question import AnswerQuestion
from rag_api.domain.errors import GuardrailViolation
from rag_api.domain.models import GuardVerdict, RetrievedChunk

CHUNKS = (
    RetrievedChunk(document_id="doc-a", text="alpha text", score=0.9),
    RetrievedChunk(document_id="doc-b", text="beta text", score=0.5),
)


class FakeRetriever:
    def __init__(self, chunks: Sequence[RetrievedChunk] = CHUNKS) -> None:
        self.calls: list[tuple[str, int]] = []
        self._chunks = chunks

    async def search(self, query: str, *, limit: int) -> Sequence[RetrievedChunk]:
        self.calls.append((query, limit))
        return self._chunks[:limit]


class AllowAllGuard:
    def check(self, question: str) -> GuardVerdict:
        return GuardVerdict(allowed=True)


class RejectAllGuard:
    def check(self, question: str) -> GuardVerdict:
        return GuardVerdict(allowed=False, reason="rejected by test guard")


class FakeComposer:
    async def compose(self, question: str, chunks: Sequence[RetrievedChunk]) -> str:
        return f"answer to {question!r} from {len(chunks)} chunk(s)"


async def test_returns_answer_with_citations_from_retrieved_chunks() -> None:
    use_case = AnswerQuestion(FakeRetriever(), AllowAllGuard(), FakeComposer())

    answer = await use_case.execute("why ports?", top_k=2)

    assert answer.text == "answer to 'why ports?' from 2 chunk(s)"
    assert [citation.document_id for citation in answer.citations] == ["doc-a", "doc-b"]
    assert [citation.score for citation in answer.citations] == [0.9, 0.5]


async def test_passes_top_k_to_retriever_as_limit() -> None:
    retriever = FakeRetriever()
    use_case = AnswerQuestion(retriever, AllowAllGuard(), FakeComposer())

    await use_case.execute("why ports?", top_k=1)

    assert retriever.calls == [("why ports?", 1)]


async def test_guard_rejection_short_circuits_before_retrieval() -> None:
    retriever = FakeRetriever()
    use_case = AnswerQuestion(retriever, RejectAllGuard(), FakeComposer())

    with pytest.raises(GuardrailViolation) as exc_info:
        await use_case.execute("anything", top_k=3)

    assert exc_info.value.reason == "rejected by test guard"
    assert retriever.calls == []
