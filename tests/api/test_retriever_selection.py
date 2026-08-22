"""The composition root picks the adapter; nothing else knows there is a choice."""

from types import SimpleNamespace
from typing import Any

from rag_api.adapters.in_memory_retriever import InMemoryRetriever
from rag_api.adapters.qdrant_store import QdrantRetriever
from rag_api.api.dependencies import get_retriever
from rag_api.config import Settings


def _request(**state: Any) -> Any:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


def test_defaults_to_the_in_memory_retriever() -> None:
    retriever = get_retriever(_request(), Settings())

    assert isinstance(retriever, InMemoryRetriever)


def test_selects_qdrant_when_configured() -> None:
    settings = Settings(retriever="qdrant")

    retriever = get_retriever(_request(qdrant_client=object(), embedder=object()), settings)

    assert isinstance(retriever, QdrantRetriever)
