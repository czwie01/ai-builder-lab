"""Request/response schemas — the HTTP contract, and nothing but the contract."""

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from rag_api.domain.models import Answer


class AnswerRequest(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    top_k: Annotated[int, Field(ge=1, le=10)] = 3


class CitationOut(BaseModel):
    document_id: str
    score: float


class AnswerResponse(BaseModel):
    answer: str
    citations: list[CitationOut]

    @classmethod
    def from_domain(cls, answer: Answer) -> "AnswerResponse":
        return cls(
            answer=answer.text,
            citations=[
                CitationOut(document_id=citation.document_id, score=citation.score)
                for citation in answer.citations
            ],
        )
