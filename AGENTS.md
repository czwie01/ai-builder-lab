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
  outside `api/`, `config.py`, `cli.py`, and `adapters/`.**
- New capability = new port (a `Protocol` in `ports/`). New implementation of an existing
  capability = new adapter in `adapters/`.
- Adapters are bound to ports in exactly one place: `api/dependencies.py`.
- The HTTP contract of `POST /api/v1/answers` never changes; errors are RFC 9457
  problem details.
- Observability stays at the edge (middleware + contextvar), never in the core.
- Retrieval-affecting changes must keep `evals/golden_set.jsonl` and thresholds honest —
  never loosen a threshold to make CI pass without saying so in the commit body.

## Commands

```bash
uv sync                    # install (Python 3.13 via uv)
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mypy                # strict type check
uv run pytest              # unit + API tests (offline)
uv run pytest -m eval      # retrieval evals (recall@3, MRR)
uv run rag-ask "..."       # use case without HTTP
uv run uvicorn rag_api.main:app --reload
```

All six quality commands must pass before every commit (CI runs the same list).

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
  `docs/workflow/practice-review.md` to grade one. Slash-command adapters for Claude Code
  live in `.claude/commands/`; mirror them into your own tool's command directory if needed.
