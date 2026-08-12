# ADR-002: Tech stack

- Status: accepted
- Date: 2026-08-12
- Practice: 01

## Context

The repo is a public portfolio; the stack should reflect current best practice for production
Python AI services, while every choice stays swappable behind the architecture of ADR-001.

## Decisions

| Concern | Choice | Rationale |
|---|---|---|
| Python | **3.13** | Current mature release. 3.14 is newer but parts of the AI dependency ecosystem still lag it; revisit each practice. |
| Packaging | **uv** | De facto standard: lockfile, Python toolchain management, fast installs. |
| Lint + format | **ruff** | Replaces black/flake8/isort with one tool; enforced by pre-commit and CI. |
| Type checking | **mypy --strict** | The conservative production gate. Astral's `ty` and pyright/basedpyright are faster emerging alternatives; swapping later is cheap, strictness is the point. |
| API framework | **FastAPI + Pydantic v2** | Industry default; its `Depends` system is the DI mechanism this lab practices. |
| Settings | **pydantic-settings** | Typed configuration from the environment (`RAG_API_` prefix). |
| Errors | **RFC 9457 problem details** | One machine-readable error shape for validation, guardrail, and unexpected failures. |
| Tests | **pytest + httpx/TestClient** | Async-native; evals are ordinary tests behind a marker. |
| Logging | **stdlib JSON formatter** | Deliberately no structlog/OTel yet — observability is Practice 07; today's contextvar-based request-ID correlation is enough. |
| CI | **GitHub Actions + astral-sh/setup-uv** | Lint, format check, mypy, tests, and eval gate on every push. No secrets required. |

## Deliberate deferrals

- **No Docker** until Practice 02 introduces Qdrant.
- **No LLM SDK** until Practice 03; the `AnswerComposer` port keeps the seam vendor-neutral
  so Anthropic and OpenAI adapters are equal citizens.
- **No eval framework** until Practice 04 decides between DeepEval / Inspect / promptfoo and
  the current pytest-native harness.

## Consequences

Everything runs offline and deterministically today: `uv sync && uv run pytest` needs no
services, keys, or network beyond package download. Each deferral has a designated practice
and a seam waiting for it.
