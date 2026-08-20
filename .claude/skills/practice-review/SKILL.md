---
name: practice-review
description: Grade an ai-builder-lab practice diff against its acceptance criteria and the architecture rules. Use when the user asks to review, grade, or check a practice ("review practice 02", "/practice-review").
---

# Review a practice

Follow the canonical rubric in `docs/workflow/practice-review.md`, exactly as written.

Inputs:
1. The current diff (or the named branch/PR).
2. The practice spec in `docs/practices/practice-NN-*.md` (acceptance criteria).
3. `AGENTS.md` (architecture rules) and, for technology deviations,
   `docs/adr/ADR-003-roadmap-v2.md`.

Output: the six-dimension scored table (0–2 each, with one-line evidence), a
merge / fix-first verdict listing blocking items, and noted debt — in exactly the format the
rubric specifies. Never soften a score to be agreeable; the rubric's honesty rule mirrors
the eval-threshold rule.
