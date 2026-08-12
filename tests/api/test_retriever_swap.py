"""The architecture self-check as an executable test.

The retriever is swapped through dependency_overrides alone — no route,
use-case, or adapter code is touched. This is the seam Practice 02 will
use to plug in Qdrant.
"""

from collections.abc import Sequence

from fastapi.testclient import TestClient

from rag_api.api.dependencies import get_retriever
from rag_api.domain.models import RetrievedChunk
from rag_api.main import create_app


class CannedRetriever:
    async def search(self, query: str, *, limit: int) -> Sequence[RetrievedChunk]:
        return (RetrievedChunk(document_id="swapped-doc", text="swapped text", score=1.0),)


def test_retriever_swaps_without_editing_route() -> None:
    app = create_app()
    app.dependency_overrides[get_retriever] = CannedRetriever

    with TestClient(app) as client:
        response = client.post("/api/v1/answers", json={"question": "anything at all", "top_k": 3})

    assert response.status_code == 200
    assert [c["document_id"] for c in response.json()["citations"]] == ["swapped-doc"]
