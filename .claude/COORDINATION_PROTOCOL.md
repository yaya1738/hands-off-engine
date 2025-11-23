# Claude CLI Coordination Protocol

**MANDATORY**: This protocol MUST be followed in every Claude CLI session.

## Purpose

Ensure GitHub Copilot and other AI agents are automatically informed of CLI session activities without user intervention.

## Requirements

### 1. Session Start (REQUIRED)

At the beginning of EVERY session, write to the coordination ledger:

```bash
echo '{"timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","from":"claude-code","to":"all","type":"info","message":"Session started: [brief task description]","context":{"session_id":"'$(date +%s)'","trigger":"user|autonomous|scheduled"}}' >> ai/coordination/messages.jsonl
```

### 2. Progress Updates (REQUIRED every 30 minutes)

During long sessions, write progress updates every 30 minutes:

```json
{
  "timestamp": "2025-11-23T17:00:00Z",
  "from": "claude-code",
  "to": "all",
  "type": "info",
  "message": "Progress update: Implemented feature X, fixed bug Y",
  "context": {
    "session_duration_min": 30,
    "commits": 2,
    "tasks_completed": ["feature-x", "bugfix-y"]
  }
}
```

### 3. Session End (REQUIRED)

At the end of EVERY session, write a summary:

```json
{
  "timestamp": "2025-11-23T18:00:00Z",
  "from": "claude-code",
  "to": "all",
  "type": "info",
  "message": "Session complete: [summary of all work done]",
  "context": {
    "duration_min": 60,
    "commits": 5,
    "files_changed": 12,
    "features": ["feature-x"],
    "bugs_fixed": ["bug-y"]
  }
}
```

### 4. Significant Decisions (REQUIRED when applicable)

When making important autonomous decisions:

```json
{
  "timestamp": "2025-11-23T17:30:00Z",
  "from": "claude-code",
  "to": "all",
  "type": "info",
  "message": "Decision made: [description]",
  "context": {
    "decision": "Deployed service X as systemd unit",
    "rationale": "Enables 24/7 operation",
    "impact": "high"
  }
}
```

### 5. Handoffs (REQUIRED when applicable)

When passing work to another agent:

```json
{
  "timestamp": "2025-11-23T17:45:00Z",
  "from": "claude-code",
  "to": "copilot",
  "type": "handoff",
  "message": "Please document the new feature X",
  "context": {
    "task": "documentation",
    "files": ["src/feature_x.py"],
    "pr": "123",
    "priority": "normal"
  }
}
```

## Implementation

### Python Helper Function

```python
import json
from datetime import datetime
from pathlib import Path

def log_coordination_message(message: str, msg_type: str = "info", to: str = "all", context: dict = None):
    """Write message to coordination ledger."""
    coord_file = Path("ai/coordination/messages.jsonl")
    coord_file.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "from": "claude-code",
        "to": to,
        "type": msg_type,
        "message": message,
        "context": context or {}
    }
    
    with open(coord_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

### Usage Example

```python
# At session start
log_coordination_message(
    "Session started: Fixing bug in trading pipeline",
    context={"session_id": "12345", "trigger": "user"}
)

# During work
log_coordination_message(
    "Progress update: Fixed calculation error, running tests",
    context={"session_duration_min": 30, "commits": 2}
)

# At session end
log_coordination_message(
    "Session complete: Bug fixed, tests passing, deployed to production",
    context={"duration_min": 60, "commits": 5, "files_changed": 3}
)
```

## Enforcement

**This protocol is NOT optional.** Every Claude CLI session must follow it.

**Why it matters:**
- GitHub Copilot can see what work has been done
- Other agents can coordinate effectively
- User doesn't need to manually relay information
- System maintains audit trail of all activities

## Troubleshooting

**Problem:** Forgot to write session start message

**Solution:** Write it immediately when you remember, with note:
```json
{
  "message": "Session started (delayed log): [task]",
  "context": {"note": "Logged retroactively"}
}
```

**Problem:** Session crashed before writing end message

**Solution:** Next session should write:
```json
{
  "message": "Previous session ended unexpectedly",
  "context": {"session_id": "...", "status": "crashed"}
}
```

## Related Documents

- `/docs/COMMUNICATION_PROCEDURES.md` - Full communication documentation
- `/ai/coordination/messages.jsonl` - The coordination ledger
- `/.claude/instructions.md` - Main Claude CLI instructions
