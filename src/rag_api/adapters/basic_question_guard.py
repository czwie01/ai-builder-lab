"""Baseline input guardrail: cheap, deterministic checks at the boundary.

Practice 06 replaces this adapter with richer policies; the port and the
use case stay untouched.
"""

from rag_api.domain.models import GuardVerdict

_INJECTION_MARKERS: tuple[str, ...] = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard your instructions",
    "you are now",
    "system prompt",
)


class BasicQuestionGuard:
    def __init__(self, max_length: int = 1000) -> None:
        self._max_length = max_length

    def check(self, question: str) -> GuardVerdict:
        if len(question) > self._max_length:
            return GuardVerdict(
                allowed=False,
                reason=f"question exceeds {self._max_length} characters",
            )
        if any(character in question for character in "\x00\r\n\t"):
            return GuardVerdict(allowed=False, reason="question contains control characters")
        lowered = question.lower()
        if any(marker in lowered for marker in _INJECTION_MARKERS):
            return GuardVerdict(allowed=False, reason="question matches an injection pattern")
        return GuardVerdict(allowed=True)
