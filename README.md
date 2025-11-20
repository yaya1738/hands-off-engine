# Hands-Off Engine

## Status & Roadmap

See `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
for the current status and strategic roadmap.

**For concrete next steps and action plan**: See `docs/NEXT_STEPS_PROPOSAL.md`

### For any AI / agent working on this repo

Before doing anything substantial, the AI/agent MUST:

1. Read `AI_POLICY.md`
2. Read `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
3. Review `docs/NEXT_STEPS_PROPOSAL.md` for current action plan
4. Follow the roadmap and constraints described there.

This repository is the canonical codebase for my "Hands-Off" personal finance, trading,
and automation engine. It is designed to be driven primarily by AI coding agents
(LLMs) with minimal manual involvement.

High-level goals:
- Central, versioned home for all core engine code (Termux + DigitalOcean).
- Safe, auditable evolution of risk models, execution logic, and infra scripts.
- Multi-agent friendly: can be used by ChatGPT, Claude Code CLI, aider, quad, etc.

This repo is intentionally minimal at first; existing scripts will be migrated into a
clean structure step by step.