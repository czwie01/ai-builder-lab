"""Input guardrail port. Adapters: basic heuristics (Practice 01), richer policies (Practice 05)."""

from typing import Protocol

from rag_api.domain.models import GuardVerdict


class QuestionGuard(Protocol):
    def check(self, question: str) -> GuardVerdict:
        """Decide whether `question` may enter the workflow."""
        ...
