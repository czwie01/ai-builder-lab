# Recommended open-source agent skills

Platform-agnostic skills worth using with this lab, mapped to where they help. The policy:
**generic needs → established community skills; project-specific needs → the thin adapters in
this repo.** Don't rebuild what the ecosystem already ships.

| Skill / collection | What it does | Use it for |
|---|---|---|
| [Quiver](https://github.com/yagizdo/quiver) | Composable dev-lifecycle skills: `/brainstorm`, `/plan`, `/work`, review, debugging, session handover | Day-to-day practice work — planning and executing a practice end to end |
| [Impeccable](https://www.mdskills.ai/plugins/impeccable) | Frontend design skill with deterministic detector rules and live browser iteration; works across Claude Code, Cursor, Codex, Windsurf, ... | Practice 09 (chat UI) — not before; it has nothing to check in a backend-only repo |
| [awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | Curated index of 1000+ skills, including official ones from Anthropic, Vercel, Stripe, Cloudflare | Discovery when a practice needs a capability not covered here |

## Token efficiency

The big savings come from fundamentals, not add-ons — see the
[token-efficiency workflow](token-efficiency.md) first. Skills and kits worth evaluating
once the fundamentals are in place:

| Skill / collection | What it does | Caveat |
|---|---|---|
| [context-engineering-kit](https://github.com/NeoLabHQ/context-engineering-kit) | Hand-crafted skills preferring command-oriented skills + subagents to keep context minimal; explicitly compatible with OpenCode, Cursor, Gemini CLI and others | Best platform-agnostic fit for this lab |
| [Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/agent-skills-for-context-engineering) | Skill collection for context engineering and multi-agent architectures | Doubles as learning material for Practices 07/10 |
| [valorisa/Claude-Skills](https://github.com/valorisa/Claude-Skills) | "rescue-tokens" skill: verbosity reduction, MCP-bloat and token-waste detection | Smaller, newer repo — treat the "90% reduction" claim as unverified until you've read the SKILL.md |

This niche attracts inflated claims ("cut costs 60–90%"); a skill earns its install only if
it operationalizes a fundamental better than you would by hand.

## Portability notes

This repo's own tooling layout (skills in `.claude/skills/` with an `.agents/skills`
symlink, AGENTS.md canonical, thin command adapters for Claude Code and OpenCode, and how to
drive the lab from OpenCode) is documented in [agent-tooling.md](agent-tooling.md).

## Vetting rule

A skill is a dependency that runs inside your agent: **read its `SKILL.md` (and any bundled
scripts) before installing**, exactly as you'd skim a library before adding it to
`pyproject.toml`. Prefer skills with visible source, an active repo, and no unexplained
network or shell access.
