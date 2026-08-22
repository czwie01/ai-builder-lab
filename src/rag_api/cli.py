"""`rag-ask` — the same use case, delivered without HTTP.

Deliberately imports no FastAPI: this entry point is the living proof
that the application core is independent of its delivery mechanism.
"""

import argparse
import asyncio
import json
import sys

from qdrant_client import AsyncQdrantClient

from rag_api.adapters.basic_question_guard import BasicQuestionGuard
from rag_api.adapters.deterministic_composer import DeterministicComposer
from rag_api.adapters.fastembed_embedder import FastEmbedEmbedder
from rag_api.adapters.in_memory_retriever import InMemoryRetriever
from rag_api.adapters.qdrant_store import QdrantRetriever
from rag_api.application.answer_question import AnswerQuestion
from rag_api.config import Settings
from rag_api.domain.errors import GuardrailViolation
from rag_api.domain.models import Answer


def main() -> int:
    parser = argparse.ArgumentParser(prog="rag-ask", description="Answer a question via RAG.")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=3, choices=range(1, 11), metavar="1..10")
    args = parser.parse_args()

    try:
        answer = asyncio.run(_answer(args.question, args.top_k, Settings()))
    except GuardrailViolation as violation:
        print(f"rejected: {violation.reason}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "answer": answer.text,
                "citations": [
                    {"document_id": c.document_id, "score": c.score} for c in answer.citations
                ],
            },
            indent=2,
        )
    )
    return 0


async def _answer(question: str, top_k: int, settings: Settings) -> Answer:
    """Build the same use case the API builds, choosing the adapter by settings."""
    guard = BasicQuestionGuard(max_length=settings.guard_max_question_length)
    composer = DeterministicComposer()
    if settings.retriever == "memory":
        use_case = AnswerQuestion(InMemoryRetriever(), guard, composer)
        return await use_case.execute(question, top_k)

    client = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        retriever = QdrantRetriever(
            client,
            FastEmbedEmbedder(
                model_name=settings.embedding_model,
                cache_dir=settings.embedding_cache_dir,
            ),
            collection=settings.qdrant_collection,
        )
        return await AnswerQuestion(retriever, guard, composer).execute(question, top_k)
    finally:
        await client.close()


if __name__ == "__main__":
    sys.exit(main())
