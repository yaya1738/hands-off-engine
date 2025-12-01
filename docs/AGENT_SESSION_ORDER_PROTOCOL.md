# Agent Session Order Protocol

**Status:** ACTIVE
**Version:** 1.0
**Created:** 2025-12-01
**Purpose:** Ensure agent sessions execute in correct order and don't skip prerequisites

---

## Overview

The Agent Session Order Protocol ensures that AI agent sessions (Copilot, Claude, ChatGPT, etc.) follow proper execution order and don't jump ahead of established dependencies. This prevents:

- Sessions starting before their prerequisites are complete
- Race conditions between dependent sessions
- Work duplication or conflicts
- Breaking changes from out-of-order execution

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│          Agent Session Request                  │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │ Session Order       │
         │ Validator           │
         │ (validates prereqs) │
         └──────────┬──────────┘
                    │
         ┌──────────┴───────────┐
         │                      │
    ✓ APPROVED          ✗ BLOCKED
         │                      │
         ▼                      ▼
  ┌──────────────┐    ┌───────────────┐
  │ Session      │    │ Wait for      │
  │ Starts       │    │ Prerequisites │
  └──────┬───────┘    └───────────────┘
         │
         ▼
  ┌──────────────┐
  │ Session      │
  │ Registered   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Work         │
  │ Executes     │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Session      │
  │ Completed    │
  └──────────────┘
```

---

## Key Components

### 1. Session Order Validator (`ai/session_order_validator.py`)

Python module that:
- Validates prerequisites before sessions start
- Tracks active and completed sessions
- Manages session dependencies
- Provides CLI and programmatic interfaces

### 2. Session Order State (`ai/coordination/session_order.json`)

JSON file storing:
- Active sessions (currently running)
- Completed sessions (finished work)
- Session dependencies (prerequisite relationships)
- Enforcement rules

### 3. Enhanced Task Queue (`scripts/autonomous_task_queue.py`)

Task queue with prerequisite support:
- Tasks can specify prerequisite task IDs
- Only returns tasks with prerequisites met
- Shows blocked tasks separately
- Tracks completion history

---

## Usage

### Before Starting a Session

**Python API:**
```python
from ai.session_order_validator import validate_session_order, register_session

session_id = "copilot-fix-risk-model-2025-12-01"
agent = "copilot"
prerequisites = ["claude-update-alpha-model"]

# Validate prerequisites
if validate_session_order(session_id, prerequisites, agent):
    # Session can proceed
    register_session(session_id, agent, dependencies=prerequisites)
    
    # Do work...
    
    complete_session(session_id, outcome="success")
else:
    print("Prerequisites not met - session must wait")
```

**CLI:**
```bash
# Check if session can start
python3 ai/session_order_validator.py validate my-session-id prereq1,prereq2

# Register a session
python3 ai/session_order_validator.py register my-session-id copilot prereq1,prereq2

# Complete a session
python3 ai/session_order_validator.py complete my-session-id success

# View current status
python3 ai/session_order_validator.py status

# See blocked sessions
python3 ai/session_order_validator.py blocked
```

### Adding Tasks with Prerequisites

**Python API:**
```python
from scripts.autonomous_task_queue import AutonomousTaskQueue
from pathlib import Path

queue = AutonomousTaskQueue(Path('/home/runner/work/hands-off-engine/hands-off-engine'))

# Task with prerequisites
task_id = queue.add_task(
    title="Optimize alpha model",
    description="Improve signal quality",
    priority="high",
    prerequisites=["task-id-of-prerequisite"]
)
```

**CLI:**
```bash
# Add task with prerequisites
python3 scripts/autonomous_task_queue.py add "Task title" "Description" high prereq1,prereq2

# View queue (shows blocked tasks)
python3 scripts/autonomous_task_queue.py list
```

---

## Enforcement Rules

Configuration in `ai/coordination/session_order.json`:

```json
{
  "enforcement_rules": {
    "require_prerequisite_completion": true,
    "allow_parallel_independent_sessions": true,
    "block_dependency_violations": true
  }
}
```

### require_prerequisite_completion (default: true)
- When true: Sessions must wait for all prerequisites
- When false: Prerequisites are advisory only

### allow_parallel_independent_sessions (default: true)
- When true: Independent sessions can run concurrently
- When false: Only one session at a time

### block_dependency_violations (default: true)
- When true: Hard block on unmet prerequisites
- When false: Warnings only

---

## Session ID Conventions

Use descriptive, unique session IDs:

**Format:** `{agent}-{action}-{date}`

**Examples:**
- `copilot-fix-executor-bug-2025-12-01`
- `claude-optimize-alpha-2025-12-01-v2`
- `chatgpt-review-risk-model-2025-12-01`

**Avoid:**
- Generic IDs like "session1", "work", "fix"
- Duplicate IDs
- Non-descriptive names

---

## Integration with Existing Systems

### With Task Queue

Tasks and sessions are complementary:
- **Task**: What needs to be done
- **Session**: Who is doing it and when

Link them via `task_id`:
```python
register_session(
    session_id="copilot-task-12345",
    agent="copilot",
    task_id="12345",  # Links to task queue
    dependencies=["previous-session-id"]
)
```

### With Coordination Status

Session order is tracked alongside coordination status in `ai/coordination/`:
- `status.json` - Overall system status and tasks
- `session_order.json` - Session execution order
- `messages.jsonl` - Inter-agent communication
- `handoffs.json` - Task handoffs between agents

### With Autonomous Operation

Session ordering integrates with autonomous operation:
1. Orchestrator detects need → creates task with prerequisites
2. Agent checks queue → validates session can start
3. Session executes → work completed
4. Session marked complete → unblocks dependent sessions

---

## Common Patterns

### Pattern 1: Sequential Work

```python
# Session 1: Update model
register_session("s1-update-model", "claude", dependencies=[])
# ... do work ...
complete_session("s1-update-model", "success")

# Session 2: Test model (depends on s1)
register_session("s2-test-model", "copilot", dependencies=["s1-update-model"])
# ... do work ...
complete_session("s2-test-model", "success")

# Session 3: Deploy (depends on s2)
register_session("s3-deploy", "claude", dependencies=["s2-test-model"])
# ... do work ...
complete_session("s3-deploy", "success")
```

### Pattern 2: Parallel + Merge

```python
# Two independent sessions can run in parallel
register_session("s1-update-docs", "copilot", dependencies=[])
register_session("s2-fix-bug", "claude", dependencies=[])

# Both complete independently
complete_session("s1-update-docs", "success")
complete_session("s2-fix-bug", "success")

# Merge session depends on both
register_session("s3-integrate", "copilot", 
                dependencies=["s1-update-docs", "s2-fix-bug"])
```

### Pattern 3: Conditional Branches

```python
# Base work
register_session("s1-analyze", "chatgpt", dependencies=[])
complete_session("s1-analyze", "success")

# Branch A or Branch B (only one will execute)
if condition_a:
    register_session("s2a-implement-a", "copilot", dependencies=["s1-analyze"])
else:
    register_session("s2b-implement-b", "claude", dependencies=["s1-analyze"])
```

---

## Troubleshooting

### Session Blocked by Prerequisites

**Symptom:** `validate_session_order()` returns False

**Solution:**
1. Check which prerequisites are missing:
   ```bash
   python3 ai/session_order_validator.py blocked
   ```
2. Wait for those sessions to complete
3. Or remove dependency if no longer needed

### Task Never Becomes Available

**Symptom:** Task stuck in queue with prerequisites

**Solution:**
1. Check completion log:
   ```bash
   cat state/autonomous_tasks_completed.jsonl | grep prerequisite-id
   ```
2. If prerequisite won't complete, update task:
   ```python
   # Remove from queue and re-add without prerequisite
   queue.remove_task(task_id)
   queue.add_task(title, description, priority)  # No prerequisites
   ```

### Session Already Exists

**Symptom:** "Session already registered" warning

**Solution:**
1. Use unique session IDs
2. Or check if old session needs to be completed:
   ```bash
   python3 ai/session_order_validator.py status
   ```
3. Complete stale sessions if needed

---

## Best Practices

### DO:
✅ Validate prerequisites before starting work
✅ Use descriptive session IDs
✅ Register sessions when starting work
✅ Complete sessions when done
✅ Check blocked sessions regularly
✅ Link sessions to tasks via task_id

### DON'T:
❌ Skip validation to start work faster
❌ Use generic session IDs
❌ Forget to complete sessions
❌ Create circular dependencies
❌ Modify session_order.json directly (use API)
❌ Disable enforcement without understanding impact

---

## Monitoring

### Check Current Status

```bash
# Overall session status
python3 ai/session_order_validator.py status

# Task queue status (includes blocked tasks)
python3 scripts/autonomous_task_queue.py list

# Coordination status
cat ai/coordination/status.json | jq '.session_order_enforcement'
```

### Audit Session History

```bash
# View completed sessions
cat ai/coordination/session_order.json | jq '.completed_sessions'

# View session dependencies
cat ai/coordination/session_order.json | jq '.session_dependencies'

# View active sessions
cat ai/coordination/session_order.json | jq '.active_sessions'
```

---

## Security & Safety

Session ordering enhances system safety by:

1. **Preventing Breaking Changes:** Ensures changes deploy in safe order
2. **Avoiding Conflicts:** Prevents concurrent modifications to same files
3. **Maintaining Consistency:** Ensures system state transitions correctly
4. **Audit Trail:** Tracks what work happened in what order

This is especially important for:
- Risk model updates (test before deploy)
- Database migrations (schema changes in order)
- Configuration changes (validate before apply)
- Code refactoring (base changes before dependent changes)

---

## Future Enhancements

**v1.1 (Planned):**
- Automatic prerequisite inference from git commits
- Session timeout handling
- Circular dependency detection
- Session rollback on failure

**v1.2 (Planned):**
- Multi-repository session coordination
- Session priority inheritance
- Dependency visualization
- Slack/Telegram notifications

---

## Related Documentation

- **ai/coordination/FAST_COORDINATION_SYSTEM.md** - Multi-agent coordination
- **docs/AUTONOMOUS_CLAUDE_ENGAGEMENT.md** - Autonomous operation
- **.claude/DUAL_CLAUDE_COORDINATION.md** - Claude-to-Claude coordination
- **ai/coordination/status.json** - Current system status

---

**Status:** Active and operational as of 2025-12-01

**Maintained by:** All AI agents serving Yair Siegel

**Questions?** Check `python3 ai/session_order_validator.py --help`
