# Practice 01 — Build a clean RAG API boundary

- Timebox: one focused session (original spec: 60 min; portfolio upgrades: ~2.5 h)
- Focus: Python, FastAPI, dependency inversion, ports & adapters
- Outcome: a production-shaped `POST /api/v1/answers` that later accepts Qdrant, LLM, and
  LangGraph implementations **without changing its HTTP contract**

## Evaluation of the original exercise

The original practice was already right about the most important thing: **the architectural
seam is the deliverable**, not the AI. Retriever as a `Protocol`, a constructor-injected use
case, framework-free core layers, and tests that need no infrastructure — all kept unchanged.

What it lacked for the mission (becoming an AI engineer with portfolio-grade output), and what
this practice added:

| Gap | Mission area | Upgrade |
|---|---|---|
| No repo scaffolding, CI, quality gates | Engineering layer | uv, ruff, mypy strict, pytest, pre-commit, GitHub Actions |
| Tracing left as an open stretch question | Observability | Request-ID middleware + contextvar + JSON logs (see below) |
| No error contract | API layer | RFC 9457 problem details for every error path |
| No guardrails | Guardrails | `QuestionGuard` port + `BasicQuestionGuard` adapter |
| No evals | Evals | Golden set + recall@3/MRR behind `pytest -m eval`, gating CI |
| No LLM path | AI engineering | `AnswerComposer` port — the provider-agnostic seam Practice 03 fills |
| No proof the hexagon works without HTTP | Architecture | `rag-ask` CLI delivering the same use case |
| Nothing portfolio-visible | Portfolio | README with diagram, ADRs, this log |

## The contract

```
POST /api/v1/answers
{"question": "Why should graph state remain small?", "top_k": 3}
→ 200
{"answer": "...", "citations": [{"document_id": "architecture-01", "score": 0.91}]}
→ 422 application/problem+json     (validation or guardrail rejection)
```

Citations expose `document_id` and `score` only — retrieved chunk text never leaves the API.

## Self-check results

| Check | Result |
|---|---|
| Replace the in-memory retriever without editing the route? | ✅ `tests/api/test_retriever_swap.py` swaps it via `dependency_overrides` alone |
| Call `AnswerQuestion` without importing FastAPI? | ✅ `rag-ask` CLI and every unit test do exactly that |
| Does `top_k=50` fail before reaching the retriever? | ✅ Pydantic bound (`le=10`) rejects at the schema; the use-case test also proves guard rejections short-circuit retrieval |
| Tests run without Qdrant or an LLM? | ✅ entire suite (tests + evals) is offline and deterministic |

## Stretch goal, answered

*Where should tracing metadata (request_id, latency, retrieved document IDs) be recorded
without contaminating the domain model?*

**At the edge, in middleware.** `RequestContextMiddleware` accepts or generates an
`X-Request-ID`, stores it in a `contextvars.ContextVar`, and emits a JSON access log with
`request_id`, `method`, `path`, `status`, and `latency_ms`. The JSON log formatter reads the
same contextvar, so any log line anywhere in the request path is correlated — while
`domain/`, `ports/`, and `application/` contain zero observability code. Practice 08 upgrades
this edge to OpenTelemetry without touching the core.

## What I'd do differently

- The deterministic composer's "first sentence + source list" answer is honest about being a
  placeholder; resisting the urge to make it smarter kept the timebox.
- Term-overlap retrieval scoring is deliberately naive — good enough to make ranking, limits,
  and eval metrics real. Practice 02 replaces it with actual vector search.
