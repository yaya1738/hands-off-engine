# Claude Code Instructions for Hands-Off Engine

## Bootstrap Sequence

Before doing any substantial work, you MUST:

1. Read `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
2. Review `state/knowledge.json` for current canonical docs
3. Align all work with the roadmap in the research report

## Project Context

- **Purpose:** AI-driven personal finance & trading automation
- **Environment:** Termux (Android Pixel 6a) + future DigitalOcean
- **Constraint:** No systemd, no root, no Docker - Termux-native solutions only
- **Pattern:** AI agents build and maintain, human only provides strategic direction

## Working Philosophy

- Read the research report FIRST - it contains current status and next steps
- Follow the documented roadmap unless explicitly instructed otherwise
- Prefer Termux-native solutions (Termux services, cron, pkg packages)
- All changes should be auditable and reversible
- Test in dryrun/staging before production

## If Starting a Task

Check `ai/tasks/*.json` for formal task definitions with required context files.

## Receiving SYSTEM HANDOFF Blocks

You may receive structured **SYSTEM HANDOFF** blocks copied from ChatGPT or other AI agents.

**Format:**
```
=== SYSTEM HANDOFF: [TITLE] ===
TARGET: [Destination agent]
INTENT: [Checkboxes]
SUMMARY: [Context]
AGENT TASKS: [Concrete tasks]
=== END SYSTEM HANDOFF ===
```

**When you receive one:**
1. **Validate TARGET** - Confirm it's meant for Claude Code in this repo
2. **Read SUMMARY** - Understand the context and decisions made
3. **Implement AGENT TASKS** - Treat as high-priority todo list with concrete file changes
4. **Follow CONSTRAINTS** - Respect any style/complexity guidelines specified

**Philosophy:** Use whatever AI works best. If ChatGPT excels at research/design and Claude Code excels at implementation, this protocol bridges them efficiently.

**Full spec:** `docs/CHATGPT_COMMS_PROTOCOL_v0.5.md`

## MCP Architecture

⚠️ **CRITICAL:** MCP (Model Context Protocol) uses **stdio**, NOT HTTP.
- **DO NOT** implement HTTP clients for `localhost:8765/mcp/*`
- **DO NOT** create REST API servers for MCP
- Read [MCP_ARCHITECTURE_CORRECTION.md](./MCP_ARCHITECTURE_CORRECTION.md) for details
- MCP servers are child processes managed by Claude Code automatically
