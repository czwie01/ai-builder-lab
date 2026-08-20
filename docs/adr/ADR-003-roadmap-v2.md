# ADR-003: Roadmap v2 — two tracks, two new practices, current-stack decisions

- Status: accepted
- Date: 2026-08-16

## Context

The original roadmap (practices 02–09) was drafted alongside Practice 01. A structured
research pass (11 web-research streams + adversarial verification, August 2026) answered six
open questions — OpenCode, a dedicated skills/commands layer, Zod, the frontend architecture,
advanced RAG techniques, and knowledge management — and refreshed every remaining milestone
against the current state of the art. This ADR records what changed and why; each practice
still gets its own ADR(s) when it runs.

## Decisions

### 1. Two new practices; renumbered roadmap

- **Practice 05 — Advanced retrieval** (new): hybrid search, metadata filtering, reranking,
  contextual retrieval, query transformation. Placed *after* the evals practice deliberately:
  the 2026 consensus is "recall before precision, evals before everything" — a reranker can
  only reorder what retrieval found, and every technique must show a recall@k/MRR delta.
  Notable evidence: semantic chunking benchmarks *below* recursive 400–512-token splitting at
  ~14× the cost, so the chunking baseline stays boring on purpose.
- **Practice 11 — LLM Wiki knowledge base** (new): the agent-curated markdown wiki pattern
  (Karpathy, April 2026; raw/ + wiki/ + schema, ingest/query/lint) combined with hybrid
  retrieval over the wiki. Graph retrieval (LightRAG-class) is adopted only if a labeled
  multi-hop/aggregation slice of the golden set proves it — vector RAG still wins single-hop.
- Renumbering: guardrails 05→06, agents 06→07, observability 07→08, UI 08→09, MCP 09→10.

### 2. Engineering track ("harness engineering") is first-class

The AI-tooling layer evolves in parallel with the product practices and follows the same
dependency-inversion discipline: canonical workflow docs (the port), portable Agent Skills
and thin per-tool command files (the adapters). Agent Skills is an open, Linux-Foundation-
governed spec (AAIF) read by Claude Code, OpenCode, Cursor, Codex, Copilot, and Gemini CLI —
skills live once in `.claude/skills/` (the most cross-read path) with `.agents/skills` as a
symlink (the vendor-neutral path). Details: `docs/workflow/agent-tooling.md`.

### 3. OpenCode: interop through open specs, not tool-inside-tool

OpenCode reads AGENTS.md, `.claude/skills/`, and Claude-format commands natively — this repo
is compatible as-is. Community plugins that reuse a Claude Pro/Max subscription inside
OpenCode exist and work, but Anthropic blocked consumer OAuth in third-party tools
(Jan 2026) and codified the ban in its ToS (Feb 2026); OpenCode itself removed built-in
Anthropic subscription auth (Mar 2026). The repo's workflow therefore never *depends* on the
unsanctioned path; sanctioned options are Claude Code directly, or OpenCode with a metered
API key. The episode is a concrete argument for Practice 03's provider-agnostic port.

### 4. Per-practice technology decisions locked in as defaults (revisit in each practice's ADR)

| Practice | Default decided now | Key alternatives noted for the practice ADR |
|---|---|---|
| 02 | fastembed (ONNX, offline/CPU) embedder behind a `TextEmbedder` port; BGE-M3 documented as production model; recursive/structure-aware chunking | Qwen3-Embedding (Apache-2.0, MRL); hosted Voyage; **not** Jina v4 (CC-BY-NC) |
| 03 | Hand-rolled `AnswerComposer` adapters: Anthropic via forced tool-use, OpenAI via strict JSON schema; validation-retry inside adapters; prompt caching static-prefix-first; fallback as a composing adapter (429/5xx only) | LiteLLM / OpenRouter duplicate the port's seam — belong inside one adapter at most |
| 04 | Pytest-native RAG triad: faithfulness via claim decomposition, answer relevance; `JudgeModel` port; judge pinned, cross-family, temperature 0, rubric versioned; **VCR-recorded judge calls** (auth headers filtered) so CI stays offline and secret-free | RAGAS 0.4 (API churn), DeepEval (fallback), promptfoo (shape mismatch), Inspect AI (reserved for agent evals in 07) |
| 05 | Order: hybrid (dense + BM25/miniCOIL, RRF) → payload filtering → `Reranker` port (BGE reranker-v2-m3 local, Cohere/Jina hosted) → contextual retrieval → query transforms last; int8 quantization + MRL with published eval deltas | BM42 avoided (experimental); ColBERT/ColPali as stretch |
| 06 | OWASP GenAI LLM Top 10 **2026** as threat model; ports first (`AnswerGuard`, `ContextGuard`); Presidio (PII), Llama Prompt Guard 2 on questions *and* retrieved chunks, spotlighting, NLI groundedness gate sharing thresholds with evals; promptfoo red-team as CI gate + scheduled garak | NeMo Guardrails / Guardrails AI rejected as runtime deps (compete with the hexagon) — buy-vs-build noted |
| 07 | Pydantic AI behind a port (FastAPI-idiom fit, library-not-runtime, provider-agnostic); agentic-RAG ladder per Anthropic's workflows-vs-agents: routing → retrieval-as-tool (bounded) → judge-gated re-retrieval; 3–10× token cost must beat the single-shot baseline on evals | LangGraph (adoption leader; right for heavy checkpointed/HITL flows), vendor SDKs (invert the dependency rule), hand-rolled loop |
| 08 | OpenTelemetry SDK directly with gen_ai.* semconv (Development status — pin the version); prompts as capped span events; token/cost + cache-hit metrics; Arize Phoenix as single-container self-hosted backend; request-ID contextvar bridged to trace_id | Langfuse (heavier, richer datasets/experiments), Logfire (best DX, no free self-host → optional second exporter) |
| 09 | Separated React + Vite + TS SPA; @hey-api/openapi-ts codegen (+ Zod 4 + TanStack Query) with CI drift check; POST + fetch-based SSE; assistant-ui | Next.js (no SEO need), HTMX (wrong fit for streaming chat state); openapi-zod-client avoided (unmaintained Zodios); AG-UI once agents exist |
| 10 | FastMCP ≥3.0 targeting spec 2026-07-28: Streamable HTTP + stdio only (HTTP+SSE deprecated); structured tool outputs, resources, elicitation; OAuth 2.1 + RFC 9728; tool-poisoning threat model with concrete mitigations | Official SDK (`MCPServer`) for strict spec control |

### 5. Standing principles reaffirmed

- Zod appears only where TypeScript appears (Practice 09) and only as a *derived* artifact of
  the OpenAPI schema — Pydantic remains the single source of truth for the contract.
- Frontend/backend separation is the architecturally consistent choice, not a compromise:
  codegen provides the contract-safety a TS monolith gets from tRPC, across the language
  boundary, and the SPA is one more consumer of the frozen HTTP contract.
- Every retrieval- or generation-affecting change is gated by the eval suite; thresholds are
  never loosened silently.

## Consequences

- The roadmap grows from 9 to 11 product practices plus an explicit engineering track; the
  numbering shift is a one-time doc change (done in this ADR's commit).
- Several practices now have research-backed defaults, which shrinks their in-practice
  decision space to "confirm or consciously deviate" — deviations belong in that practice's
  ADR with the same honesty rule as eval thresholds.
- Research snapshots age: each practice re-verifies its defaults against current sources
  before implementation (the practice-scaffold workflow's research step).
