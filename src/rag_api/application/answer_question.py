"""AnswerQuestion use case.

Depends only on ports and domain objects — no FastAPI, no Pydantic, no
vendor SDKs. Any delivery mechanism (HTTP route, CLI, MCP tool, worker)
can construct and call it.
"""

from rag_api.domain.errors import GuardrailViolation
from rag_api.domain.models import Answer, Citation
from rag_api.ports.answer_composer import AnswerComposer
from rag_api.ports.question_guard import QuestionGuard
from rag_api.ports.retriever import Retriever


class AnswerQuestion:
    def __init__(
        self,
        retriever: Retriever,
        guard: QuestionGuard,
        composer: AnswerComposer,
    ) -> None:
        self._retriever = retriever
        self._guard = guard
        self._composer = composer

    async def execute(self, question: str, top_k: int) -> Answer:
        verdict = self._guard.check(question)
        if not verdict.allowed:
            raise GuardrailViolation(verdict.reason or "question rejected by guardrail")

        chunks = await self._retriever.search(question, limit=top_k)
        text = await self._composer.compose(question, chunks)
        citations = tuple(
            Citation(document_id=chunk.document_id, score=chunk.score) for chunk in chunks
        )
        return Answer(text=text, citations=citations)
