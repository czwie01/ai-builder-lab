"""Dependency wiring: where adapters meet ports.

This module is the composition root for HTTP delivery. Swapping an
adapter (say, Qdrant for the in-memory retriever) happens here — routes
and the use case never change.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from rag_api.adapters.basic_question_guard import BasicQuestionGuard
from rag_api.adapters.deterministic_composer import DeterministicComposer
from rag_api.adapters.in_memory_retriever import InMemoryRetriever
from rag_api.application.answer_question import AnswerQuestion
from rag_api.config import Settings
from rag_api.ports.answer_composer import AnswerComposer
from rag_api.ports.question_guard import QuestionGuard
from rag_api.ports.retriever import Retriever


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_retriever() -> Retriever:
    return InMemoryRetriever()


def get_question_guard(settings: Annotated[Settings, Depends(get_settings)]) -> QuestionGuard:
    return BasicQuestionGuard(max_length=settings.guard_max_question_length)


def get_answer_composer() -> AnswerComposer:
    return DeterministicComposer()


def get_answer_question(
    retriever: Annotated[Retriever, Depends(get_retriever)],
    guard: Annotated[QuestionGuard, Depends(get_question_guard)],
    composer: Annotated[AnswerComposer, Depends(get_answer_composer)],
) -> AnswerQuestion:
    return AnswerQuestion(retriever, guard, composer)
