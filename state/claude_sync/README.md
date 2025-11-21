# Dual-Claude Coordination System

**Status:** Active
**Instances:** Web Claude + CLI Claude
**Purpose:** Enable cooperative parallel development

---

## Quick Start

### Check Active Sessions
```bash
python3 state/claude_sync/utils.py sessions
```

### Send a Message
```bash
python3 state/claude_sync/utils.py post <from> <to> <type> "message content"
```

### Read Your Messages
```bash
python3 state/claude_sync/utils.py read <instance>
```

### Add a Task
```bash
python3 state/claude_sync/utils.py add-task <task-id> "Task description"
```

### Claim a Task
```bash
python3 state/claude_sync/utils.py claim <instance> <task-id>
```

### Complete a Task
```bash
python3 state/claude_sync/utils.py complete <instance> <task-id>
```

---

## Files

| File | Purpose |
|------|---------|
| `active_sessions.json` | Currently active Claude instances with heartbeats |
| `task_queue.json` | Pending, in-progress, and completed tasks |
| `messages.jsonl` | Message log between instances |
| `work_log.jsonl` | Action log for all instances |
| `utils.py` | Coordination utilities (CLI and library) |

---

## Usage Examples

### Web Claude Starting Work
```python
from state.claude_sync.utils import register_session, claim_task, post_message

# Register session
register_session('web', 'session-123', 'Reviewing code')

# Claim a task
if claim_task('web', 'task-001'):
    # Do work...
    post_message('web', 'cli', 'info', 'Working on task-001')
```

### CLI Claude Responding
```python
from state.claude_sync.utils import read_messages, post_message

# Check for messages
messages = read_messages('cli')
for msg in messages:
    if msg['type'] == 'question':
        # Respond
        post_message('cli', msg['from'], 'response',
                    'Response here', ref=msg['timestamp'])
```

---

## Coordination Patterns

### Pattern 1: Parallel Development
- Web Claude works on feature A
- CLI Claude works on feature B
- Coordinate through task queue

### Pattern 2: Review & Iterate
- One Claude implements
- Other Claude reviews and refines
- Communicate through messages

### Pattern 3: Question & Answer
- One Claude asks question
- Other Claude responds
- Use `type: question` and `type: response`

---

## Monitoring

### View Active Work
```bash
# Check what each instance is doing
python3 state/claude_sync/utils.py sessions

# See recent messages
tail -20 state/claude_sync/messages.jsonl | jq

# Check task status
cat state/claude_sync/task_queue.json | jq '.tasks[] | select(.status != "completed")'
```

### Health Check
```bash
# Check for stale sessions (no heartbeat > 10 min)
python3 -c "
from state.claude_sync.utils import get_active_sessions
sessions = get_active_sessions()
print(f'{len(sessions)} active session(s)')
"
```

---

## Best Practices

### Before Starting Work
1. Check active sessions
2. Read pending messages
3. Review task queue
4. Claim your task
5. Post status update

### During Work
1. Update heartbeat every 5 minutes
2. Post progress messages
3. Commit frequently
4. Check for new messages

### After Completing
1. Mark task as completed
2. Post completion message
3. Add artifacts to task
4. Push changes to git

---

## Integration

This coordination system extends:
- `.claude/AI_COORDINATION_ARCHITECTURE.md` - Multi-AI coordination
- `.claude/DUAL_CLAUDE_COORDINATION.md` - Full protocol specification
- `AI_POLICY.md` - Overarching policy

---

**Created:** 2025-11-21
**Protocol:** `.claude/DUAL_CLAUDE_COORDINATION.md`
