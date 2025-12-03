# ChatGPT Communications Protocol v0.5

**Status:** Active
**Type:** Manual handoff bridge
**Purpose:** Enable ChatGPT to pass research, specs, and tasks to the Hands-Off system

---

## Overview

This protocol defines how ChatGPT can hand off work to other AI agents in the Hands-Off Engine system (primarily Claude Code).

**Key principle:** Use whatever AI works best for each task. If ChatGPT is better for research/brainstorming, use it. If Claude Code is better for implementation, hand off the work.

---

## The Problem v0.5 Solves

**Before:** Valuable work done in ChatGPT sessions stays "stuck" in ChatGPT. User has to manually translate research/specs into actionable tasks.

**After:** ChatGPT ends sessions with a standardized SYSTEM HANDOFF block that the user copies into Claude Code. Claude Code understands the format and implements the tasks.

---

## SYSTEM HANDOFF Block Format

ChatGPT ends important sessions with:

```
=== SYSTEM HANDOFF: [TITLE] ===

TARGET:
- Primary: [Agent name and location]
- Secondary (optional): [Alternative delivery method]

INTENT:
- [x] Research summary
- [ ] Architectural spec
- [x] Agent tasks

SUMMARY:
[2-4 sentences explaining the context and what was decided]

AGENT TASKS (for [target agent]):

1) Task: [Short task description]
   Files:
   - NEW: path/to/file.md
   - MODIFY: path/to/existing.py
   Steps:
   - [Step 1]
   - [Step 2]

2) Task: [Another task]
   ...

CONSTRAINTS / STYLE:
- [Any specific requirements]
- [Code style preferences]
- [What NOT to do]

=== END SYSTEM HANDOFF ===
```

---

## How It Works

### ChatGPT Side:
1. User has research/design session with ChatGPT
2. ChatGPT produces SYSTEM HANDOFF block at end
3. User copies the block

### User Side:
1. Opens Claude Code in the target repo
2. Pastes SYSTEM HANDOFF block
3. Claude Code reads and implements tasks

### Claude Code Side:
1. Receives SYSTEM HANDOFF block from user
2. Validates TARGET matches current context
3. Reads SUMMARY for context
4. Implements AGENT TASKS as concrete code/doc changes
5. Commits with normal workflow

---

## Field Descriptions

### TARGET
Specifies where this handoff should go:
- **Primary:** Main destination (e.g., "Claude Code in repo X")
- **Secondary:** Optional alternative (e.g., GitHub Issue)

### INTENT
Checkboxes indicating what type of handoff:
- `[x] Research summary` - Includes background research
- `[x] Architectural spec` - Includes design decisions
- `[x] Agent tasks` - Includes actionable tasks

### SUMMARY
2-4 sentences providing context. Explains:
- What was discussed
- Key decisions made
- Why this handoff matters

### AGENT TASKS
Concrete, actionable tasks for the receiving agent.

Each task includes:
- **Task:** Short description
- **Files:** NEW/MODIFY/DELETE with paths
- **Steps:** Specific actions to take

Tasks should be:
- Small and focused
- High-leverage (important, not busywork)
- Implementable without further clarification

### CONSTRAINTS / STYLE
Optional guidelines:
- Code style preferences
- Things to avoid
- Complexity limits

---

## Example Handoff

```
=== SYSTEM HANDOFF: Add Logging ===

TARGET:
- Primary: Claude Code in repo yaya1738/hands-off-engine

INTENT:
- [x] Agent tasks

SUMMARY:
User wants comprehensive logging added to the trading pipeline.
Logs should capture decisions, API calls, and errors.

AGENT TASKS (for Claude Code):

1) Task: Add logging to executor
   Files:
   - MODIFY: executor/decider.py
   Steps:
   - Import logging at top
   - Add logger.info() for each decision
   - Add logger.error() for failures

=== END SYSTEM HANDOFF ===
```

---

## Benefits

✅ **No lost work** - ChatGPT sessions produce actionable outputs
✅ **Clear handoffs** - Structured format both agents understand
✅ **Use best tool** - ChatGPT for research, Claude Code for implementation
✅ **No infrastructure** - Works today with just copy-paste
✅ **Traceable** - SYSTEM HANDOFF blocks are documented in commits

---

## Limitations (v0.5)

This is a **manual bridge**:
- ❌ Requires user to copy-paste
- ❌ No automatic validation
- ❌ No direct ChatGPT→Claude communication

These are acceptable tradeoffs for v0.5. The goal is to solve the "stuck in ChatGPT" problem with minimal infrastructure.

---

## Future: v1 and Beyond

Potential improvements (not implemented yet):

**v1.0 - Semi-automated:**
- Tool to parse ChatGPT exports
- Auto-create tasks in `ai/tasks/`
- Validate SYSTEM HANDOFF format

**v2.0 - Fully integrated:**
- AI Runner recognizes `origin: chatgpt` tasks
- Direct API integration (if/when ChatGPT supports)
- Multi-agent coordination via coordination files

See `docs/CHATGPT_COMMS_PROTOCOL_v1_ideas.md` for details.

---

## For ChatGPT

If you're ChatGPT and you're reading this:

**When to use SYSTEM HANDOFF:**
- After significant research/design session
- When user needs implementation of your recommendations
- When handing off to more specialized agent

**Format rules:**
- Always include TARGET, INTENT, SUMMARY, AGENT TASKS
- Keep tasks small and concrete
- Be specific about files and steps
- Note any constraints

**Remember:** This is a bridge protocol. Future versions may integrate you more directly into the system.

---

## For Claude Code

If you're Claude Code and you receive a SYSTEM HANDOFF:

1. **Validate TARGET** - Confirm it's meant for you
2. **Read SUMMARY** - Understand the context
3. **Check INTENT** - Know what type of handoff this is
4. **Implement AGENT TASKS** - Treat as high-priority todo list
5. **Follow CONSTRAINTS** - Respect any style/complexity guidelines
6. **Commit normally** - Use standard commit workflow

Treat SYSTEM HANDOFF tasks as coming from the user via another AI agent.

---

## Version History

**v0.5** (2025-11-25)
- Initial protocol
- Manual copy-paste bridge
- Standardized block format
- Documentation created

---

**Protocol Status:** ✅ Active and ready to use
