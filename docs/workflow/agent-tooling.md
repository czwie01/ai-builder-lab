# Workflow: the agent-tooling layer (harness engineering)

How this repo structures its AI-tooling layer so one canonical workflow serves every coding
agent — and how to drive the lab from OpenCode or any other Agent-Skills-capable tool.
Current as of 2026-08.

## Layout

```
AGENTS.md                      # canonical instructions (open cross-tool standard)
CLAUDE.md -> AGENTS.md         # symlink: Claude Code adapter
docs/workflow/                 # canonical workflows (the "port")
.claude/skills/<name>/SKILL.md # portable Agent Skills (the most cross-read location)
.agents/skills -> ../.claude/skills   # symlink: vendor-neutral path (Codex, Cursor)
.claude/commands/*.md          # thin slash-command adapters (Claude Code)
.opencode/command/*.md         # thin slash-command adapters (OpenCode)
```

The same dependency-inversion principle as the codebase: workflows and skills are written
once against open standards; per-tool files are thin adapters.

## Why this layout works everywhere

- **Agent Skills** (folders with `SKILL.md`) is an open spec, open-sourced by Anthropic in
  December 2025 and governed under the Linux Foundation's Agentic AI Foundation. It is read
  by Claude Code, OpenCode, Cursor, Codex CLI, VS Code/Copilot, Gemini CLI, and others.
  `.claude/skills/` is currently the single most cross-read project path (Cursor, OpenCode,
  and Copilot read it directly); `.agents/skills/` is the vendor-neutral path some tools
  prefer — hence the symlink, so skills exist exactly once.
- **AGENTS.md** is the cross-tool instructions standard (60K+ repos). Claude Code reads only
  CLAUDE.md, so CLAUDE.md is a symlink — one source of truth, an industry-recognized pattern.
- **Slash commands** are the one genuinely tool-specific piece; both Claude Code and OpenCode
  use markdown prompt files with near-identical formats, and OpenCode also reads Claude
  Code's directories — the `.opencode/command/` mirrors exist for explicitness.
- Skills here contain no Anthropic-specific tool calls, which keeps them runnable in any
  Agent-Skills-capable tool.

## Using OpenCode with this repo

OpenCode picks up `AGENTS.md`, the skills, and the commands with zero configuration. For the
model backend:

- **Sanctioned**: an Anthropic (or any provider) **API key** — natively supported, never
  restricted. Or simply use Claude Code directly with a Claude subscription.
- **Exists but unsanctioned**: community plugins that reuse a Claude Pro/Max subscription
  inside OpenCode (credential-bridge plugins syncing the Claude Code login, and forks of the
  archived claude-CLI-subprocess plugin). Be aware of the history before relying on them:
  Anthropic blocked consumer OAuth tokens in third-party tools on 2026-01-09, made the ban
  explicit in its Terms of Service on 2026-02-19 ("Authentication and credential use"), and
  OpenCode removed built-in Anthropic subscription auth in v1.3.0 (2026-03) after legal
  requests. Such plugins can stop working at any time and using them risks account
  suspension. **This repo's workflow never depends on them.**

OpenCode extras worth knowing: `/init` regenerates AGENTS.md; `/compact` and automatic
compaction manage long sessions; `/share` creates a public read-only session page (review
for secrets before sharing).

## Skill evals (engineering-track step E3, planned)

Skills get the same rigor as retrieval: Anthropic's skill-creator v2 defines a per-skill
`evals.json` ({prompt, expectations} graded from the transcript, plus trigger-accuracy tests
of the skill description). When the lab has ≥2 reusable skills, they gain evals behind a
pytest marker — mirroring `pytest -m eval` — and packaging as a Claude Code plugin
(`.claude-plugin/`) becomes worthwhile for cross-repo distribution.
