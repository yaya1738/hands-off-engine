# Agent Session Order - Quick Reference

**TL;DR:** Use session order validator to ensure your session has prerequisites met before starting work.

---

## Before You Start a Session

```python
from ai.session_order_validator import validate_session_order, register_session

# Define your session
session_id = "copilot-task-xyz-2025-12-01"
agent = "copilot"  # or claude, chatgpt, etc.
prerequisites = ["previous-session-id"]  # List of sessions that must complete first

# Validate you can start
if validate_session_order(session_id, prerequisites, agent):
    # Good to go!
    register_session(session_id, agent, dependencies=prerequisites)
    
    # Do your work here...
    
    # When done
    complete_session(session_id, outcome="success")
else:
    # Prerequisites not met - wait
    print("Can't start yet - waiting for prerequisites")
```

---

## CLI Quick Commands

```bash
# Check if session can start
python3 ai/session_order_validator.py validate SESSION_ID PREREQ1,PREREQ2

# Register session
python3 ai/session_order_validator.py register SESSION_ID AGENT PREREQ1,PREREQ2 "Description"

# Complete session
python3 ai/session_order_validator.py complete SESSION_ID success "Notes"

# View status
python3 ai/session_order_validator.py status

# See what's blocked
python3 ai/session_order_validator.py blocked
```

---

## Task Queue Integration

When working with tasks from the autonomous queue:

```python
from scripts.autonomous_task_queue import AutonomousTaskQueue
from pathlib import Path

queue = AutonomousTaskQueue(Path.cwd())

# Get next available task (prerequisites checked automatically)
task = queue.get_next_task()

if task:
    session_id = f"copilot-task-{task['id'][:8]}"
    
    # Register session linked to task
    register_session(
        session_id=session_id,
        agent="copilot",
        task_id=task['id'],
        dependencies=task.get('prerequisites', [])
    )
    
    # Work on task...
    
    # Complete both session and task
    complete_session(session_id, "success")
    queue.complete_task(task['id'])
```

---

## Common Patterns

### Sequential Work
```python
# Session 1 has no prerequisites
register_session("s1", "claude", dependencies=[])
# ... work ...
complete_session("s1", "success")

# Session 2 depends on s1
register_session("s2", "copilot", dependencies=["s1"])
# ... work ...
complete_session("s2", "success")
```

### Parallel + Merge
```python
# Two independent sessions
register_session("s1-docs", "copilot", dependencies=[])
register_session("s2-code", "claude", dependencies=[])

# ... both work in parallel ...

complete_session("s1-docs", "success")
complete_session("s2-code", "success")

# Merge depends on both
register_session("s3-merge", "copilot", dependencies=["s1-docs", "s2-code"])
```

---

## When To Use

**Always use when:**
- Work depends on other sessions completing first
- Working on multi-step changes
- Coordinating with other agents
- Need to ensure proper sequencing

**Can skip when:**
- Completely independent work
- No other sessions involved
- Quick one-off tasks
- Documentation-only changes

---

## Files

- `ai/session_order_validator.py` - The validator module
- `ai/coordination/session_order.json` - Session state storage
- `docs/AGENT_SESSION_ORDER_PROTOCOL.md` - Full documentation

---

## Need Help?

```bash
python3 ai/session_order_validator.py --help
```

Or read the full docs: `docs/AGENT_SESSION_ORDER_PROTOCOL.md`
