"""Core domain models.

Frozen dataclasses, not Pydantic: the domain has no knowledge of
serialization, HTTP, or any framework. Pydantic appears only at the
edges (API schemas, settings).
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A piece of source material returned by a retriever."""

    document_id: str
    text: str
    score: float


@dataclass(frozen=True, slots=True)
class Citation:
    """A reference to a source document, safe to expose to API clients.

    Deliberately excludes the chunk text: what leaves the system is a
    pointer to the source, not the source itself.
    """

    document_id: str
    score: float


@dataclass(frozen=True, slots=True)
class Answer:
    """The result of answering a question: text plus its supporting citations."""

    text: str
    citations: tuple[Citation, ...]


@dataclass(frozen=True, slots=True)
class GuardVerdict:
    """Outcome of a guardrail check on incoming input."""

    allowed: bool
    reason: str | None = None
