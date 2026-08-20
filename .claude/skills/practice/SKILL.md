---
name: practice
description: Scaffold the next ai-builder-lab practice spec from the roadmap. Use when the user asks to start, scaffold, or plan practice N (e.g. "start practice 02", "/practice 03").
---

# Scaffold a practice

Follow the canonical workflow in `docs/workflow/practice-scaffold.md`, exactly as written.

Inputs to gather first:
1. The roadmap tables in `README.md` (product track + engineering track) — find the row for
   the requested practice and the seam it plugs into.
2. `docs/adr/ADR-003-roadmap-v2.md` — the research-backed defaults for that practice
   (confirm or consciously deviate; deviations need an ADR).
3. The most recent log in `docs/practices/` — carry forward its "What I'd do differently".

Output: `docs/practices/practice-NN-<slug>.md` with the section structure the workflow
defines (Timebox, Focus, Outcome, Key concept, Exercise, Self-check, Stretch), plus a
working branch as the workflow describes. Re-verify the practice's technology defaults
against current sources before locking the spec — research snapshots age.
