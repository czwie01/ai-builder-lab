# Workflow: scaffold the next practice

Tool-agnostic instructions for starting practice N. Works with any coding agent (Claude Code,
OpenCode, Cursor, Codex, ...) or by hand; `.claude/commands/practice.md` is a thin adapter
that points here.

## Steps

1. Read the roadmap table in `README.md` and the previous practice log in `docs/practices/`
   to understand what seam practice N plugs into. Run any deeper codebase research in a
   subagent so the main context stays clean for implementation
   (see [token-efficiency.md](token-efficiency.md)).
2. Create `docs/practices/practice-NN-<slug>.md` with these sections:
   - **Timebox** — one focused session; state it and honor it.
   - **Focus** — the mission area(s) and key technologies from the roadmap row.
   - **Outcome** — one sentence: what exists afterwards that didn't before.
   - **Key concept** — the one idea the practice teaches, in 2–3 paragraphs.
   - **Exercise** — concrete requirements, numbered; name the port(s) touched. New
     capability = new port; new implementation of an existing capability = new adapter.
   - **Self-check** — 3–5 yes/no questions that prove the architecture held.
   - **Stretch** — one open question pointing at a later practice.
3. Create a working branch named `practice/NN-<slug>` (or use the branch your environment
   assigns).
4. Implement in Conventional Commits, layer by layer (domain → ports → adapters →
   application → api), every commit leaving lint, types, and tests green.
5. Finish by filling in **Self-check results** and **What I'd do differently** in the log,
   and flipping the roadmap row to ✅.

## Rules that keep the lab honest

- The HTTP contract of `POST /api/v1/answers` never changes; new behavior arrives behind it.
- If a practice needs the core to know about infrastructure, the design is wrong — add a port.
- Every practice must leave `uv run pytest` runnable offline; anything needing services or
  keys goes behind a marker (like `-m eval`) or docker-compose.
