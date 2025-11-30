# Claude Code Instructions for Hands-Off Engine

## ⛔ CRITICAL SAFETY RULES - READ FIRST

**NEVER run destructive infrastructure commands.** You have caused 8+ droplet shutdowns by testing API calls.

**FORBIDDEN ACTIONS (will shut down the server you're running on):**
- `curl` with `power_off`, `power_on`, `resize`, `delete` to DigitalOcean API
- Calling `resize_server()`, `delete_server()`, or any power management functions
- Testing DO API tokens with action endpoints
- Any bash command that could shut down, reboot, or modify the running droplet

**IF you need to debug infrastructure:**
- Use READ-ONLY API calls only (GET requests, list endpoints)
- NEVER test action endpoints on production infrastructure
- Ask the user before running any infrastructure commands

**The autonomous infra system handles infrastructure. You do NOT need to manage it manually.**

---

## Bootstrap Sequence

Before doing any substantial work, you MUST:

1. Read `state/knowledge.json` for required reading list and bootstrap instructions
2. Read ALL docs listed in `required_reading`:
   - `AI_POLICY.md`
   - `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
   - `docs/claude/USER_PROFILE.md` (meta-aware principle, self-improvement loop)
   - `docs/claude/AI_COORDINATION_ARCHITECTURE.md`
   - `docs/DEVELOPMENT_STANDARDS.md`
3. Align all work with the roadmap in the research report
4. When changing agent coordination, update ALL files in `agent_instruction_files`
5. When creating rules, add enforcement. When creating components, add monitoring.

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

## Agents & Linking (v1.1 - Autonomous Operation)

This system uses multiple AI agents working together. You (Claude CLI) are the **primary repo implementer**.

**Agent Registry:** `ai/agents/AGENTS_REGISTRY_v0.1.json`

**Three primary agents:**
- **ChatGPT** (`chatgpt`) - Research and design work
- **Claude CLI** (`claude_cli`) - You - primary implementation
- **GitHub Copilot Agent** (`github_copilot_agent`) - GitHub-native helper

**Your role:** Implement SYSTEM HANDOFF blocks from ChatGPT, handle tasks in `ai/tasks/`, and make changes to the repo.

**Full protocol:** `docs/AI_AGENT_LINK_PROTOCOL_v0.1.md`

**Philosophy:** Use whatever AI works best. No rigid hierarchies, just clear handoff protocols.

### Autonomous Coordination

The system operates autonomously. Key points:
- **Auto-merge:** Copilot PRs merge automatically when CI passes (unless touching critical files)
- **Self-healing:** `scripts/self_healing_agent.py` monitors for unmerged branches and stale failures
- **Instruction sync:** All agent instruction files must be kept consistent:
  - `.claude/instructions.md` (this file)
  - `.github/copilot-instructions.md` (Copilot)
  - `docs/AI_AGENT_LINK_PROTOCOL_v0.1.md` (shared protocol)

**When making changes to agent coordination**, update all three files to prevent drift.

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

**This is how ChatGPT hands off work to you.** SYSTEM HANDOFF v0.5 is the protocol linking agents together.

**Full spec:** `docs/CHATGPT_COMMS_PROTOCOL_v0.5.md`

## MCP Architecture

⚠️ **CRITICAL:** MCP (Model Context Protocol) uses **stdio**, NOT HTTP.
- **DO NOT** implement HTTP clients for `localhost:8765/mcp/*`
- **DO NOT** create REST API servers for MCP
- Read `docs/claude/MCP_ARCHITECTURE_CORRECTION.md` for details
- MCP servers are configured in `.mcp.json` (repo root) and managed by Claude Code automatically

## Session Logs & Coordination History

Historical session logs and coordination docs are in `docs/claude/`:
- `AI_AGENT_COORDINATION_LOG.md` - Multi-AI collaboration history
- `AI_COORDINATION_ARCHITECTURE.md` - Architecture overview
- `AUTONOMOUS_OPERATION.md` - Autonomous mode documentation
- `MCP_*.md` - MCP setup guides and verification results
