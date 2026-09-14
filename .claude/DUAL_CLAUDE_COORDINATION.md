# Dual-Claude Coordination Protocol

**Date:** 2025-11-21
**Purpose:** Enable cooperative work between Web Claude and CLI Claude
**Status:** Active

---

## Overview

This system enables two Claude instances to work together on the Hands-Off Engine:

```
┌──────────────────────────────────────────────────────────┐
│                    User (Yair Siegel)                     │
└─────────────┬──────────────────────┬─────────────────────┘
              │                      │
      ┌───────▼────────┐    ┌───────▼────────┐
      │  WEB CLAUDE    │    │  CLI CLAUDE     │
      │  (Browser)     │◄──►│  (Droplet)      │
      │                │    │                 │
      │ • Full access  │    │ • Full access   │
      │ • Git ops      │    │ • Autonomous    │
      │ • Parallel     │    │ • Production    │
      └────────┬───────┘    └────────┬────────┘
               │                     │
               └──────────┬──────────┘
                          │
              ┌───────────▼──────────┐
              │  Coordination Files  │
              │  state/claude_sync/  │
              └──────────────────────┘
```

---

## Coordination Mechanism

### 1. Active Sessions Tracker

**File:** `state/claude_sync/active_sessions.json`

```json
{
  "sessions": [
    {
      "instance": "web" | "cli",
      "session_id": "unique-id",
      "started_at": "ISO-8601",
      "last_heartbeat": "ISO-8601",
      "current_task": "description",
      "status": "active" | "idle" | "working"
    }
  ],
  "last_sync": "ISO-8601"
}
```

### 2. Task Coordination

**File:** `state/claude_sync/task_queue.json`

```json
{
  "tasks": [
    {
      "task_id": "task-001",
      "description": "Fix bug in executor",
      "priority": "high" | "medium" | "low",
      "assigned_to": "web" | "cli" | "any",
      "claimed_by": null | "web" | "cli",
      "status": "pending" | "in_progress" | "completed" | "blocked",
      "created_at": "ISO-8601",
      "claimed_at": "ISO-8601",
      "completed_at": "ISO-8601",
      "dependencies": ["task-000"],
      "artifacts": ["path/to/file.py"],
      "notes": "Additional context"
    }
  ]
}
```

### 3. Message Passing

**File:** `state/claude_sync/messages.jsonl`

Each line is a JSON message:
```json
{"from": "web", "to": "cli", "timestamp": "ISO-8601", "type": "info|question|result", "content": "message"}
{"from": "cli", "to": "web", "timestamp": "ISO-8601", "type": "response", "content": "reply", "ref": "timestamp"}
```

### 4. Work Log

**File:** `state/claude_sync/work_log.jsonl`

Each line records an action:
```json
{"instance": "web", "timestamp": "ISO-8601", "action": "started_task", "task_id": "task-001", "details": {}}
{"instance": "cli", "timestamp": "ISO-8601", "action": "completed_task", "task_id": "task-001", "result": "success"}
```

---

## Coordination Protocol

### Starting a Session

**Every Claude instance MUST:**

1. Register session in `active_sessions.json`
2. Check for existing active sessions
3. Read any pending messages
4. Check task queue for pending work
5. Update heartbeat every 5 minutes

### Claiming Tasks

**Before starting work:**

1. Check if task is already claimed
2. If unclaimed, update task with your instance ID
3. Update status to "in_progress"
4. Commit the change
5. Pull to ensure no conflicts
6. If conflict, defer to other instance

### Completing Tasks

**After finishing work:**

1. Update task status to "completed"
2. Add artifacts (files created/modified)
3. Log completion in work log
4. Post message to other instance
5. Commit and push changes

### Cooperative Work Patterns

#### Pattern 1: Parallel Work
- Web Claude: Works on frontend
- CLI Claude: Works on backend
- Coordination: Through task queue

#### Pattern 2: Review & Iterate
- CLI Claude: Implements feature
- Web Claude: Reviews and refines
- Coordination: Through messages

#### Pattern 3: Tandem Development
- Both work on same feature
- Web Claude: Tests and UI
- CLI Claude: Core logic
- Coordination: Real-time via messages

---

## Communication Rules

### Heartbeat Protocol

Every instance should update heartbeat every 5 minutes:

```python
def update_heartbeat():
    sessions = read_json('state/claude_sync/active_sessions.json')
    for session in sessions['sessions']:
        if session['instance'] == MY_INSTANCE:
            session['last_heartbeat'] = now()
    write_json('state/claude_sync/active_sessions.json', sessions)
```

### Message Types

**info**: General information
```json
{"from": "web", "to": "cli", "type": "info", "content": "Starting work on notifications"}
```

**question**: Request for input
```json
{"from": "cli", "to": "web", "type": "question", "content": "Should I proceed with deployment?"}
```

**response**: Answer to question
```json
{"from": "web", "to": "cli", "type": "response", "ref": "timestamp", "content": "Yes, proceed"}
```

**result**: Work completion notification
```json
{"from": "web", "to": "cli", "type": "result", "content": "Completed task-001, 3 files modified"}
```

**handshake**: Instance startup notification
```json
{"from": "web", "to": "cli", "type": "handshake", "content": "Web Claude online, ready to cooperate"}
```

---

## Conflict Resolution

### Scenario: Both Claim Same Task

**Resolution:**
1. Check git commit timestamp
2. Earlier claim wins
3. Later instance releases claim
4. Later instance finds different task

### Scenario: Contradictory Changes

**Resolution:**
1. Create git branch for each approach
2. Post message to discuss
3. User decides which to merge
4. Or: merge both if complementary

### Scenario: Instance Goes Silent

**Detection:**
- Heartbeat older than 10 minutes

**Action:**
1. Mark session as "stale"
2. Allow claiming of that instance's tasks
3. Post warning message
4. Continue work independently

---

## Best Practices

### DO:
- ✅ Always check active sessions before starting
- ✅ Update heartbeat regularly
- ✅ Claim tasks explicitly
- ✅ Post completion messages
- ✅ Commit frequently with clear messages
- ✅ Read messages from other instance
- ✅ Coordinate on overlapping areas

### DON'T:
- ❌ Start work without checking task queue
- ❌ Assume you're the only instance
- ❌ Skip heartbeat updates
- ❌ Work on claimed tasks
- ❌ Make breaking changes without coordination
- ❌ Ignore messages from other instance

---

## Implementation Helpers

### Python Utilities

```python
# state/claude_sync/utils.py
import json
from datetime import datetime
from pathlib import Path

SYNC_DIR = Path('state/claude_sync')

def register_session(instance: str, session_id: str, task: str = None):
    """Register this Claude instance"""
    path = SYNC_DIR / 'active_sessions.json'
    data = json.loads(path.read_text()) if path.exists() else {'sessions': []}

    # Remove old sessions from this instance
    data['sessions'] = [s for s in data['sessions'] if s['instance'] != instance]

    # Add new session
    data['sessions'].append({
        'instance': instance,
        'session_id': session_id,
        'started_at': datetime.utcnow().isoformat() + 'Z',
        'last_heartbeat': datetime.utcnow().isoformat() + 'Z',
        'current_task': task,
        'status': 'active'
    })

    data['last_sync'] = datetime.utcnow().isoformat() + 'Z'
    path.write_text(json.dumps(data, indent=2))

def post_message(from_instance: str, to_instance: str, msg_type: str, content: str):
    """Post a message to another instance"""
    path = SYNC_DIR / 'messages.jsonl'
    msg = {
        'from': from_instance,
        'to': to_instance,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'type': msg_type,
        'content': content
    }
    with path.open('a') as f:
        f.write(json.dumps(msg) + '\n')

def read_messages(for_instance: str, since: str = None):
    """Read messages for this instance"""
    path = SYNC_DIR / 'messages.jsonl'
    if not path.exists():
        return []

    messages = []
    with path.open() as f:
        for line in f:
            msg = json.loads(line)
            if msg['to'] == for_instance:
                if since is None or msg['timestamp'] > since:
                    messages.append(msg)
    return messages

def claim_task(instance: str, task_id: str):
    """Claim a task"""
    path = SYNC_DIR / 'task_queue.json'
    data = json.loads(path.read_text())

    for task in data['tasks']:
        if task['task_id'] == task_id:
            if task['claimed_by'] is None:
                task['claimed_by'] = instance
                task['claimed_at'] = datetime.utcnow().isoformat() + 'Z'
                task['status'] = 'in_progress'
                path.write_text(json.dumps(data, indent=2))
                return True
    return False
```

---

## Bootstrap Sequence

### For Any Claude Instance Starting

```bash
# 1. Create sync directory if needed
mkdir -p state/claude_sync

# 2. Initialize files if they don't exist
python3 state/claude_sync/init.py

# 3. Register your session
python3 state/claude_sync/utils.py register <instance>

# 4. Check for messages
python3 state/claude_sync/utils.py check-messages <instance>

# 5. Start work
# ... your work here ...

# 6. Post completion
python3 state/claude_sync/utils.py post-message <instance> "Completed task"
```

---

## Monitoring

### Check Active Sessions
```bash
cat state/claude_sync/active_sessions.json | jq '.sessions'
```

### View Recent Messages
```bash
tail -20 state/claude_sync/messages.jsonl | jq
```

### Check Task Queue
```bash
cat state/claude_sync/task_queue.json | jq '.tasks[] | select(.status == "pending")'
```

### View Work Log
```bash
tail -50 state/claude_sync/work_log.jsonl | jq
```

---

## Integration with Existing Systems

### Builds on AI Coordination Architecture

This dual-Claude system extends `.claude/AI_COORDINATION_ARCHITECTURE.md`:

- Reuses `state/` directory pattern
- Compatible with AI Nexus concept
- Follows file-based coordination approach
- Adds real-time sync for two active instances

### Complements Autonomous Operation

Per `.claude/AUTONOMOUS_OPERATION.md`:

- Both instances can work autonomously
- Coordination prevents conflicts
- Enables parallel development
- Maintains safety and review processes

---

## Future Enhancements

**Possible improvements:**

1. **WebSocket sync** (if infra allows)
   - Real-time message delivery
   - Instant task updates
   - Live presence indicators

2. **Merge conflict detection**
   - Pre-commit hooks
   - Automatic branch creation
   - Conflict warnings

3. **Work distribution algorithm**
   - Load balancing
   - Skill-based assignment
   - Priority queuing

4. **Audit dashboard**
   - Web UI showing both instances
   - Real-time status
   - Performance metrics

---

## References

- `.claude/AI_COORDINATION_ARCHITECTURE.md` - Multi-AI architecture
- `.claude/AUTONOMOUS_OPERATION.md` - Autonomous operation guide
- `state/knowledge.json` - System state
- `AI_POLICY.md` - Overarching policy

---

**Status:** Active as of 2025-11-21
**Instances:** Web Claude + CLI Claude
**Coordination:** File-based with git sync
