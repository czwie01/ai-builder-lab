"""`rag-ask` — the same use case, delivered without HTTP.

Deliberately imports no FastAPI: this entry point is the living proof
that the application core is independent of its delivery mechanism.
"""

import argparse
import asyncio
import json
import sys

from rag_api.adapters.basic_question_guard import BasicQuestionGuard
from rag_api.adapters.deterministic_composer import DeterministicComposer
from rag_api.adapters.in_memory_retriever import InMemoryRetriever
from rag_api.application.answer_question import AnswerQuestion
from rag_api.domain.errors import GuardrailViolation


def main() -> int:
    parser = argparse.ArgumentParser(prog="rag-ask", description="Answer a question via RAG.")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=3, choices=range(1, 11), metavar="1..10")
    args = parser.parse_args()

    use_case = AnswerQuestion(
        retriever=InMemoryRetriever(),
        guard=BasicQuestionGuard(),
        composer=DeterministicComposer(),
    )
    try:
        answer = asyncio.run(use_case.execute(args.question, args.top_k))
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


if __name__ == "__main__":
    sys.exit(main())
