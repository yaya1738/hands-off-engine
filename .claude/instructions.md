# Claude Code Instructions for Hands-Off Engine

## Bootstrap Sequence

Before doing any substantial work, you MUST:

1. Read `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
2. Review `state/knowledge.json` for current canonical docs
3. Align all work with the roadmap in the research report
4. **CRITICAL:** Follow `.claude/COORDINATION_PROTOCOL.md` - Write to coordination ledger at session start, every 30 min, and session end

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

## MCP Architecture

⚠️ **CRITICAL:** MCP (Model Context Protocol) uses **stdio**, NOT HTTP.
- **DO NOT** implement HTTP clients for `localhost:8765/mcp/*`
- **DO NOT** create REST API servers for MCP
- Read [MCP_ARCHITECTURE_CORRECTION.md](./MCP_ARCHITECTURE_CORRECTION.md) for details
- MCP servers are child processes managed by Claude Code automatically
