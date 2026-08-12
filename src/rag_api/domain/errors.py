"""Domain errors. Adapters and the API layer translate these at the boundary."""


class DomainError(Exception):
    """Base class for errors raised by the domain or application layer."""


class GuardrailViolation(DomainError):
    """Raised when a guardrail rejects the incoming question."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
