# Agent instructions — ai-builder-lab

Canonical instructions for any coding agent (Claude Code, OpenCode, Cursor, Codex, Gemini
CLI, ...). `CLAUDE.md` is a symlink to this file; keep exactly one source of truth.

## What this repo is

A portfolio lab growing one RAG API practice by practice with hexagonal architecture. The
roadmap lives in `README.md`; per-practice specs and logs in `docs/practices/`; decisions in
`docs/adr/`.

## Architecture rules (non-negotiable)

- Dependency arrows point inward: `domain/` imports only the standard library; `ports/` and
  `application/` import only `domain/` and each other. **No FastAPI, Pydantic, or vendor SDK
  outside `api/`, `config.py`, `cli.py`, `ingest_cli.py`, and `adapters/`.**
- New capability = new port (a `Protocol` in `ports/`). New implementation of an existing
  capability = new adapter in `adapters/`.
- Adapters are bound to ports in a composition root, and there are exactly two:
  `api/dependencies.py` (+ `api/lifespan.py` for process-lifetime clients) for HTTP, and
  the CLIs, which must stay FastAPI-free. Both select adapters from the same `Settings`.
- The HTTP contract of `POST /api/v1/answers` never changes; errors are RFC 9457
  problem details.
- Observability stays at the edge (middleware + contextvar), never in the core.
- Retrieval-affecting changes must keep `evals/` honest: measure before choosing a
  threshold, change what is measured and the threshold in separate commits, and never
  loosen one to make CI pass without saying so in the commit body. The corpus in
  `evals/corpus/` is frozen so scores move only when retrieval moves.

## Commands

```bash
uv sync                    # install (Python 3.13 via uv)
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mypy                # strict type check
uv run pytest              # unit + adapter + API tests (offline, no services)
uv run pytest -m eval      # retrieval evals (recall@3, MRR)
uv run pytest -m integration   # needs a real Qdrant: docker compose up -d
uv run rag-ask "..."       # use case without HTTP
uv run rag-ingest --source evals/corpus --recreate   # chunk, embed, index
uv run uvicorn rag_api.main:app --reload
```

The first five must pass before every commit (CI runs the same list). Three test tiers:
hermetic by default (Qdrant's embedded local mode plus a fake embedder), `-m eval` for
retrieval quality, `-m integration` for what local mode cannot prove — it accepts point ids a
server rejects and ignores payload indexes.

## Token & context efficiency

- Keep this file lean (< 200 lines); depth lives on demand in `docs/workflow/` — see
  `docs/workflow/token-efficiency.md` for the full playbook.
- Run noisy codebase research in subagents; keep the main context for implementation.
- Don't restate what ruff/mypy/pre-commit/CI already enforce.

## Conventions

- Conventional Commits (`feat(api):`, `chore:`, `docs:`, `test(evals):`, ...); small commits,
  layer by layer; every commit leaves the tree green.
- Tests: unit tests use hand-rolled fakes (never adapters); API tests use `TestClient`;
  anything needing services or secrets goes behind a pytest marker.
- Practice workflow: `docs/workflow/practice-scaffold.md` to start one,
  `docs/workflow/practice-review.md` to grade one. Both are exposed as portable Agent Skills
  in `.claude/skills/` (symlinked at `.agents/skills`), with thin command adapters in
  `.claude/commands/` and `.opencode/command/` — layout in `docs/workflow/agent-tooling.md`.
- Roadmap technology defaults live in `docs/adr/ADR-003-roadmap-v2.md`; confirm or
  consciously deviate (with an ADR) when implementing a practice.
