# Agent Session Ordering System

**Version**: 1.0  
**Status**: Active  
**Date**: 2025-12-01

---

## Overview

The Agent Session Ordering System ensures that agent sessions (such as tri-agent discussions, autonomous tasks, and coordinated workflows) execute in the correct order by enforcing dependencies between sessions. This prevents sessions from "jumping ahead" of their prerequisites and ensures instructions from previous sessions are properly followed.

---

## Problem Statement

Before this system was implemented, there was no mechanism to:
- Track dependencies between agent sessions
- Prevent sessions from starting before their prerequisites completed
- Ensure sessions followed instructions from previous sessions in the correct order
- Detect and prevent circular dependencies

This could lead to:
- Sessions executing out of order
- Missing context from prerequisite sessions
- Inconsistent system state
- Violations of intended workflow sequences

---

## Solution

The Session Ordering System provides:

1. **Session Dependency Tracking** - Register sessions with their dependencies
2. **Prerequisite Validation** - Check that all dependencies are met before session starts
3. **Status Management** - Track session lifecycle (pending → running → completed/failed)
4. **Circular Dependency Detection** - Prevent invalid dependency graphs
5. **Ready Queue** - Identify which sessions can start now

---

## Architecture

### Components

```
SessionOrderingManager
├── Session Registration
│   ├── Assign unique session ID
│   ├── Record dependencies
│   └── Validate no circular dependencies
├── Dependency Validation
│   ├── Check all dependencies completed
│   ├── Return session readiness status
│   └── Provide reason if not ready
├── Status Tracking
│   ├── pending (waiting for dependencies)
│   ├── running (currently executing)
│   ├── completed (finished successfully)
│   └── failed (finished with error)
└── Persistence
    └── state/session_ordering.json
```

### Data Model

```python
@dataclass
class SessionDependency:
    session_id: str              # Unique identifier
    depends_on: List[str]        # List of prerequisite session IDs
    status: str                  # pending/running/completed/failed
    created_at: str              # ISO timestamp
    started_at: Optional[str]    # When session started
    completed_at: Optional[str]  # When session completed
    metadata: Dict               # Additional context
```

---

## Integration Points

### 1. Tri-Agent Session Runner

The tri-agent session runner (`ai_nexus/tri_agent_session_runner.py`) integrates session ordering:

```python
session = TriAgentSession(
    conversation_id="20251201_analysis",
    session_goal="Analyze results from previous session",
    depends_on=["20251201_data_collection"],  # Must wait for this
    enforce_ordering=True  # Enable enforcement (default)
)

session.run_session(agents=["chatgpt", "claude_cli"], rounds=2)
```

**Behavior**:
- Session registers itself with ordering system on creation
- Before running, checks if dependencies are met
- If dependencies incomplete, session exits with clear message
- On completion, marks itself as completed
- On failure, marks itself as failed

### 2. Autonomous Task Queue

The autonomous task queue (`scripts/autonomous_task_queue.py`) supports task dependencies:

```python
queue = AutonomousTaskQueue(repo_root)

# Add tasks with dependencies
task_1 = queue.add_task(
    title="Collect data",
    description="Fetch market data"
)

task_2 = queue.add_task(
    title="Analyze data",
    description="Analyze collected data",
    depends_on=[task_1]  # Must wait for task_1
)

# Get next ready task (respects dependencies)
next_task = queue.get_next_task()  # Returns task_1 first
```

**Behavior**:
- `get_next_task()` only returns tasks whose dependencies are completed
- Tasks stay in queue until dependencies met
- Priority still respected within ready tasks

---

## Usage Examples

### Example 1: Sequential Sessions

```python
from ai_nexus.session_ordering import SessionOrderingManager

manager = SessionOrderingManager()

# Register sessions in order
manager.register_session("session_001")
manager.register_session("session_002", depends_on=["session_001"])
manager.register_session("session_003", depends_on=["session_002"])

# Run sessions
manager.start_session("session_001")
# ... run session_001 ...
manager.complete_session("session_001", success=True)

# Now session_002 can start
manager.start_session("session_002")
# ... run session_002 ...
manager.complete_session("session_002", success=True)

# Finally session_003 can start
manager.start_session("session_003")
# ... run session_003 ...
manager.complete_session("session_003", success=True)
```

### Example 2: Multiple Dependencies

```python
# Session 003 needs both 001 and 002 to complete first
manager.register_session("session_001")
manager.register_session("session_002")
manager.register_session("session_003", depends_on=["session_001", "session_002"])

# Complete both dependencies
manager.start_session("session_001")
manager.complete_session("session_001", success=True)

manager.start_session("session_002")
manager.complete_session("session_002", success=True)

# Now session_003 can start (both dependencies met)
can_start, reason = manager.can_start_session("session_003")
assert can_start is True
```

### Example 3: Circular Dependency Prevention

```python
# This will be rejected
manager.register_session("session_a", depends_on=["session_c"])
manager.register_session("session_b", depends_on=["session_a"])
manager.register_session("session_c", depends_on=["session_b"])  # FAILS - circular!
# ⚠️ Circular dependency detected for session session_c
```

---

## Command Line Interface

The session ordering manager has a CLI for manual inspection and control:

```bash
# List all sessions and their status
python -m ai_nexus.session_ordering list

# Register a new session
python -m ai_nexus.session_ordering register session_001

# Register with dependencies
python -m ai_nexus.session_ordering register session_002 session_001

# Check which sessions are ready to start
python -m ai_nexus.session_ordering ready

# Start a session (if dependencies met)
python -m ai_nexus.session_ordering start session_001

# Complete a session
python -m ai_nexus.session_ordering complete session_001 success

# Get status of a specific session
python -m ai_nexus.session_ordering status session_001
```

---

## Best Practices

### 1. Session Naming

Use clear, descriptive session IDs:
```python
# Good
"20251201_data_collection"
"20251201_analysis_phase1"
"20251201_final_report"

# Avoid
"session1"
"temp"
"test"
```

### 2. Dependency Chains

Keep dependency chains reasonable (< 5 levels):
```python
# Good - short chain
session_001 → session_002 → session_003

# Avoid - long chain
session_001 → session_002 → session_003 → session_004 → session_005 → session_006
```

### 3. Metadata Usage

Store context in metadata for debugging:
```python
manager.register_session(
    "20251201_analysis",
    depends_on=["20251201_data"],
    metadata={
        "agent": "claude",
        "task_type": "analysis",
        "expected_duration": "5m",
        "priority": "high"
    }
)
```

### 4. Error Handling

Always handle session failures gracefully:
```python
try:
    # Run session
    session.run_session(agents, rounds)
    manager.complete_session(session_id, success=True)
except Exception as e:
    manager.complete_session(session_id, success=False)
    raise
```

---

## Monitoring and Debugging

### Check Session Status

```python
# Get full status
status = manager.get_session_status("session_001")
print(status)
# {
#   "session_id": "session_001",
#   "depends_on": [],
#   "status": "completed",
#   "created_at": "2025-12-01T10:00:00Z",
#   "started_at": "2025-12-01T10:01:00Z",
#   "completed_at": "2025-12-01T10:05:00Z",
#   "metadata": {...}
# }

# Check if can start
can_start, reason = manager.can_start_session("session_002")
if not can_start:
    print(f"Cannot start: {reason}")
    # "Waiting for dependencies: session_001 (status: running)"
```

### View Ordering State

```python
# Display all sessions grouped by status
manager.display_ordering()
```

Output:
```
============================================================
SESSION ORDERING STATUS (3 sessions)
============================================================

✅ COMPLETED:
  session_001

▶️ RUNNING:
  session_002 (depends on: session_001)

⏸️ PENDING:
  session_003 (depends on: session_002)
    ⏳ Waiting for dependencies: session_002 (status: running)

============================================================
```

---

## State File Format

Session ordering state is stored in `state/session_ordering.json`:

```json
{
  "updated_at": "2025-12-01T10:05:00Z",
  "sessions": {
    "session_001": {
      "session_id": "session_001",
      "depends_on": [],
      "status": "completed",
      "created_at": "2025-12-01T10:00:00Z",
      "started_at": "2025-12-01T10:01:00Z",
      "completed_at": "2025-12-01T10:05:00Z",
      "metadata": {}
    },
    "session_002": {
      "session_id": "session_002",
      "depends_on": ["session_001"],
      "status": "running",
      "created_at": "2025-12-01T10:02:00Z",
      "started_at": "2025-12-01T10:06:00Z",
      "completed_at": null,
      "metadata": {}
    }
  }
}
```

---

## Testing

Comprehensive test suite in `tests/test_session_ordering.py`:

```bash
# Run all tests
python -m pytest tests/test_session_ordering.py -v

# Run specific test
python -m pytest tests/test_session_ordering.py::TestSessionOrderingManager::test_circular_dependency_detection -v
```

Test coverage:
- ✅ Session registration
- ✅ Dependency tracking
- ✅ Circular dependency detection
- ✅ Prerequisite validation
- ✅ Status lifecycle
- ✅ Multiple dependencies
- ✅ Dependency chains
- ✅ Persistence across instances

---

## Migration Guide

### Existing Code

If you have existing session code without ordering:

```python
# Old way (no ordering)
session = TriAgentSession(
    conversation_id="20251201_test",
    session_goal="Test session"
)
session.run_session(agents, rounds)
```

### Updated Code

Add dependencies and enable ordering:

```python
# New way (with ordering)
session = TriAgentSession(
    conversation_id="20251201_test",
    session_goal="Test session",
    depends_on=["20251201_prerequisite"],  # Add dependencies
    enforce_ordering=True  # Enable (default is True)
)
session.run_session(agents, rounds)
```

### Disable Ordering (Not Recommended)

If you need to temporarily disable ordering:

```python
session = TriAgentSession(
    conversation_id="20251201_test",
    session_goal="Test session",
    enforce_ordering=False  # Disable ordering checks
)
```

---

## Limitations

1. **No Distributed Locking** - Assumes single-machine execution
2. **No Automatic Retry** - Failed sessions must be manually restarted
3. **No Timeout Detection** - Running sessions don't have automatic timeouts
4. **No Priority Within Dependencies** - All ready sessions are equal priority

---

## Future Enhancements

Potential improvements for future versions:

1. **Automatic Retry** - Retry failed sessions with exponential backoff
2. **Timeout Detection** - Mark sessions as failed if running too long
3. **Priority Levels** - Support priority within ready sessions
4. **Distributed Locking** - Support multi-machine deployments
5. **Visualization** - Graphical view of dependency graphs
6. **Metrics** - Track session duration, success rate, etc.

---

## Related Documentation

- `docs/TRI_AGENT_SESSION_v0.1.md` - Tri-agent session runner
- `docs/AI_COORDINATION_ARCHITECTURE.md` - Multi-agent coordination
- `ai/coordination/status.json` - Current coordination state
- `scripts/autonomous_task_queue.py` - Task queue system

---

## Summary

The Agent Session Ordering System ensures sessions execute in the correct order by:

1. **Tracking dependencies** between sessions
2. **Validating prerequisites** before session start
3. **Preventing circular dependencies** in the dependency graph
4. **Managing session lifecycle** (pending → running → completed/failed)
5. **Persisting state** to survive restarts

This prevents sessions from "jumping ahead" and ensures the correct execution order is maintained.
