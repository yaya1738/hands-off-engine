# User Protocol Alignment - All Agents

**Status:** Alignment in progress
**Updated:** 2025-11-25T09:45:37Z
**Canonical Reference:** `USER_INTERFACE.md`

---

## Decision: Single-Interface Model

After user feedback ("UI roadblock... tough and cumbersome"), all agents must align on:

### ✅ User Interface: Telegram Only

**User Yair interacts exclusively via:** Telegram bot @pm_alerts_autobot

**User NEVER needs:**
- GitHub Issues
- CLI sessions
- File editing
- Multiple interfaces

**Time commitment:** ~15 minutes/week

### ✅ Agent Coordination: GitHub + Coordination Files

**Agents communicate via:**
- GitHub Issues (for task planning, technical discussion)
- `ai/coordination/` files (messages.jsonl, status.json, handoffs.json)
- Pull requests and code reviews

**This layer is invisible to user.**

---

## Telegram Bot Capabilities

User can:
- `/status` - Get system status
- `/metrics` - View performance metrics
- `/health` - Check system health
- `/pending` - View pending approvals
- `/approve <id>` - Approve changes
- `/reject <id> [reason]` - Reject changes
- `/task <description>` - Queue new tasks

System sends:
- Daily proactive updates (9am)
- Approval requests (when needed)
- Critical alerts (if issues)

---

## Agent Responsibilities

### What Agents Do Autonomously
- Plan and execute work
- Coordinate with each other
- Make safe decisions
- Self-optimize systems
- Monitor and fix issues

### What Requires User Approval
- Risky changes (trading params, strategy changes)
- System architecture changes
- Live mode activation
- Major parameter adjustments

**Approval flow:** Agent → `ai/approval_queue.py` → Telegram notification → User approves/rejects

---

## Alignment Status

| Agent | Status | Notes |
|-------|--------|-------|
| claude-code | ✅ Confirmed | Implemented Telegram bot + approval system |
| copilot | ⏳ Pending | Awaiting confirmation (requested 2025-11-25) |
| claude-web | ⏳ Pending | Not yet contacted |
| chatgpt | ⏳ Pending | Not yet contacted |

---

## Key Principle

**"If it's for the user → Telegram"**
**"If it's for agents → GitHub/Coordination files"**

One interface, zero confusion.

---

## References

- **Canonical doc:** `USER_INTERFACE.md`
- **Approval system:** `ai/README_APPROVAL_SYSTEM.md`
- **Implementation:** `telegram/telegram_command_bot.py`, `ai/approval_queue.py`
- **Coordination:** `ai/coordination/messages.jsonl`

---

**Next action:** Await Copilot confirmation and align remaining agents.
