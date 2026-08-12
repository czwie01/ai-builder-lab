# ADR-001: Hexagonal architecture with Protocol-based ports

- Status: accepted
- Date: 2026-08-12
- Practice: 01

## Context

This lab grows one RAG API across many practices, each swapping or adding infrastructure:
vector databases (Qdrant), LLM vendors (Anthropic, OpenAI), agent frameworks (LangGraph or
Pydantic AI), telemetry (OpenTelemetry), and new delivery mechanisms (CLI, MCP). AI
infrastructure churns faster than business logic; the architecture must make vendor swaps
cheap and testable.

## Decision

Adopt ports & adapters (hexagonal architecture):

1. **Domain** (`rag_api/domain/`) holds frozen `dataclass` models and errors. It imports
   nothing outside the standard library — not even Pydantic. Serialization is an edge concern.
2. **Ports** (`rag_api/ports/`) are `typing.Protocol` interfaces the application depends on:
   `Retriever`, `QuestionGuard`, `AnswerComposer`.
3. **Application** (`rag_api/application/`) holds use cases that receive ports through their
   constructor. No FastAPI, no Pydantic, no vendor SDKs.
4. **Adapters** (`rag_api/adapters/`) implement ports. All infrastructure lives here.
5. **API** (`rag_api/api/`) is the only layer that imports FastAPI. Adapters are bound to
   ports in exactly one place: `api/dependencies.py`, the composition root.
6. Cross-cutting observability (request IDs, latency) lives in middleware and a `ContextVar`
   — never in domain or application objects.

### Why `Protocol` instead of ABC

- Structural typing: adapters satisfy a port without importing it, so the dependency arrow
  always points inward. An ABC would force adapters to import the core's base class.
- Test fakes are plain classes with matching signatures — no inheritance ceremony.
- `mypy --strict` verifies conformance at the point of use, which is where it matters.

## Consequences

- Swapping infrastructure edits one wiring module. `tests/api/test_retriever_swap.py` proves
  the seam by replacing the retriever via `dependency_overrides` without touching the route.
- The use case runs identically under HTTP, CLI (`rag-ask`), and — later — MCP.
- Cost: more files and a little indirection than a "FastAPI route calls the client directly"
  style. Accepted: the indirection **is** the practice.
- Guardrails and answer composition are ports from day one, so Practices 03 and 05 replace
  adapters, not seams.
