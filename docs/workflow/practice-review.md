# Workflow: review a practice

Tool-agnostic rubric for grading a practice's diff before it merges. Works with any coding
agent or as a human checklist; `.claude/commands/practice-review.md` is a thin adapter that
points here.

## Inputs

- The current diff (or branch) for practice N
- `docs/practices/practice-NN-*.md` (the acceptance criteria)
- `AGENTS.md` (the architecture rules)

## Rubric

Score each dimension 0–2 (0 = violated, 1 = partial, 2 = clean), with evidence:

1. **Architecture** — dependency arrows point inward; `domain/`, `ports/`, `application/`
   import no framework or vendor SDK; infrastructure appears only in `adapters/` and wiring
   only in `api/dependencies.py`.
2. **Contract stability** — `POST /api/v1/answers` request/response unchanged; errors remain
   RFC 9457 problem details.
3. **Tests** — new behavior has unit tests with fakes AND an API-level test; the suite still
   runs offline; use-case tests don't import adapters.
4. **Evals & guardrails** — retrieval-affecting changes update the golden set or thresholds
   deliberately (never silently loosened); guard changes come with rejection tests.
5. **Engineering hygiene** — Conventional Commits, each commit green (ruff, mypy, pytest),
   docs/ADR updated when a decision changed.
6. **Practice log** — self-check answered with evidence, stretch question addressed or
   explicitly deferred.

## Output format

A table of the six dimensions with score + one-line evidence, followed by:
- **Verdict**: merge / fix-first (list the blocking items)
- **Debt noted**: anything accepted now that a future practice must repay
