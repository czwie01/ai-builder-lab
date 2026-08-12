# Workflow: token-efficient agentic coding

Tool-agnostic fundamentals for keeping agent sessions cheap and sharp, current as of
2026-08. The ranking matters: these built-in patterns save far more than any installable
add-on; the skills in [recommended-skills.md](recommended-skills.md#token-efficiency) only
earn an install if they operationalize one of these better than you would by hand.

## The fundamentals

### 1. Lean, canonical instruction files

The always-loaded instruction file is billed on every request of every session.

- Keep `AGENTS.md` under ~200 lines: exact commands near the top (highest ROI), rules the
  agent can't infer, pointers to detail instead of pasted detail.
- Delete anything a deterministic tool already enforces — ruff, mypy, pre-commit, and CI
  catch style and type issues; spending instruction tokens on them is pure waste.
- One source of truth: this repo keeps `AGENTS.md` canonical with `CLAUDE.md` as a symlink
  (a one-line `@AGENTS.md` import works too). Never maintain two divergent files.
- Push depth down into on-demand layers: `docs/workflow/` files, skills, and subagent
  prompts load only when needed.

### 2. Subagent context isolation

Delegating noisy work to a subagent keeps file dumps, search results, and dead ends out of
the main context — the main thread receives only the conclusion.

- Use subagents for: codebase research, broad searches, reviews, and independent parallel
  work (worktrees for parallel edits).
- Don't reflex-spawn them: each subagent reloads instructions and re-reads files, so
  subagent-heavy sessions can cost several times a single thread. Isolation must buy
  something — clean reasoning or parallelism.
- Practice workflow: run the "understand the seam" phase of each practice in a subagent;
  keep the main context for implementation.

### 3. Progressive disclosure via skills

A well-built skill exposes only a short description until triggered, then loads its full
instructions — the reason a repo can carry many skills at near-zero idle cost. Prefer a
skill (or a `docs/workflow/` file behind a thin command adapter, as this repo does) over
pasting knowledge into the always-loaded instruction file.

### 4. Compaction and session discipline

- Compact or summarize around ~50% context utilization instead of riding a session to the
  limit; resume long-running work from a recap, not a replay.
- Plan before code (plan mode or a written plan): one approved plan is cheaper than three
  exploratory implementations.
- Prompt precisely rather than briefly — steering tokens are cheap compared to a wrong
  implementation loop.

### 5. Platform-level context management (for the agents we build)

The same discipline applies inside this lab's own roadmap. When Practices 06 and 09 build
agent workflows, use the platform primitives instead of hand-rolling them:

- **Context editing** — server-side clearing of stale tool results
  ([docs](https://platform.claude.com/docs/en/build-with-claude/context-editing)).
- **Memory tool** — persistent files across sessions so knowledge survives without staying
  in context ([docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)).
  Anthropic reports ~84% token savings with both on long-horizon tasks.
- Provider-agnostic note: these are adapter concerns. If an agent practice adopts them,
  they belong behind the same port discipline as everything else (ADR-001).

## How this repo implements the fundamentals

| Fundamental | Implementation here |
|---|---|
| Lean canonical instructions | `AGENTS.md` ≈ 50 lines, commands block, `CLAUDE.md` symlink |
| On-demand depth | workflows in `docs/workflow/`, commands as thin adapters |
| Deterministic work to tools | ruff + mypy + pre-commit + CI gate every commit |
| Subagents for research | rule in `practice-scaffold.md` step 1 |
| Eval/guardrail knowledge out of context | golden set + thresholds live in `evals/`, not instructions |
