# Agent Session Ordering Protocol

**Status:** Active
**Purpose:** Ensure agent sessions follow proper dependencies and ordering
**Created:** 2025-12-01

---

## Overview

The Agent Session Ordering Protocol ensures that AI agent sessions (GitHub Copilot, Claude Code, ChatGPT, etc.) execute in the correct sequence and don't skip ahead of required predecessor sessions.

**Problem Solved:**
- Prevents sessions from jumping ahead without completing dependencies
- Ensures sequential tasks execute in the correct order
- Validates that prerequisite work is completed before dependent work begins

---

## Session Dependency Types

### 1. Previous Session (`previous_session_id`)

**Use case:** Strict sequential ordering

A session with `previous_session_id` **must** wait for that specific session to complete before it can run.

**Example:**
```bash
# Session 1: Setup infrastructure
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_setup_infrastructure \
    --session-goal "Set up base infrastructure"

# Session 2: Deploy services (depends on Session 1)
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_deploy_services \
    --previous-session 20251201_setup_infrastructure \
    --session-goal "Deploy services on infrastructure"
```

**Behavior:**
- Session 2 will check if Session 1 has status `stopped` or `completed`
- If Session 1 is not complete, Session 2 will be `blocked` and abort
- Clear error message displayed explaining the dependency

### 2. Multiple Dependencies (`depends_on`)

**Use case:** A session depends on multiple other sessions

A session can depend on multiple prerequisite sessions. **All** must be completed before the session can run.

**Example:**
```bash
# Session A: Data collection
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_data_collection

# Session B: Model training
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_model_training

# Session C: Integration (depends on both A and B)
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_integration \
    --depends-on "20251201_data_collection,20251201_model_training"
```

**Behavior:**
- Session C checks that both A and B are completed
- If any dependency is incomplete, Session C is `blocked`
- Works independently of `previous_session_id`

### 3. Explicit Ordering (`session_order`)

**Use case:** Numbered sequence of sessions

Sessions can be assigned explicit order numbers (1, 2, 3, etc.). Lower numbers must complete before higher numbers.

**Example:**
```bash
# Phase 1: Foundation
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_phase1_foundation \
    --session-order 1

# Phase 2: Implementation
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_phase2_implementation \
    --session-order 2

# Phase 3: Testing
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_phase3_testing \
    --session-order 3
```

**Behavior:**
- Any session with `session_order=2` will be blocked if sessions with `session_order=1` are incomplete
- Scans all sessions in the intercom directory
- Useful for long-running multi-phase projects

---

## Task Queue Ordering

The `autonomous_task_queue.py` system also supports ordering to prevent tasks from executing out of sequence.

### Task Dependency Fields

When adding tasks, you can specify:

```python
from scripts.autonomous_task_queue import AutonomousTaskQueue

queue = AutonomousTaskQueue(repo_root)

# Task 1: Foundation
task1_id = queue.add_task(
    title="Set up infrastructure",
    description="Deploy base infrastructure",
    priority="high",
    metadata={'task_order': 1}
)

# Task 2: Depends on Task 1
task2_id = queue.add_task(
    title="Deploy application",
    description="Deploy app on infrastructure",
    priority="high",
    metadata={
        'previous_task_id': task1_id,
        'task_order': 2
    }
)

# Task 3: Depends on multiple tasks
task3_id = queue.add_task(
    title="Integration testing",
    description="Test integrated system",
    priority="normal",
    metadata={
        'depends_on': [task1_id, task2_id],
        'task_order': 3
    }
)
```

### How Task Dependencies Work

The `get_next_task()` method now:

1. **Checks completed tasks** - Loads `autonomous_tasks_completed.jsonl` to see which tasks are done
2. **Validates `previous_task_id`** - If set, ensures that task is completed
3. **Validates `depends_on`** - If set, ensures all dependencies are completed
4. **Validates `task_order`** - If set, ensures no earlier-ordered tasks are still pending

**Only returns a task when ALL dependencies are satisfied.**

---

## Session Status Values

Sessions track their status in `cpu_instance.json`:

| Status | Meaning |
|--------|---------|
| `idle` | Session created but not yet running |
| `running` | Session is currently executing |
| `paused` | Session temporarily paused (future use) |
| `stopped` | Session completed successfully |
| `completed` | Alternative status for completed sessions |
| `blocked` | **NEW**: Session blocked due to unsatisfied dependencies |

---

## Validation Logic

### Session Validation (`_validate_session_dependencies`)

Before a session starts, it validates:

1. **Previous Session Check**
   - If `previous_session_id` is set, checks if that session exists
   - Verifies the previous session has status `stopped` or `completed`
   - Blocks if previous session is incomplete

2. **Dependencies Check**
   - For each ID in `depends_on`, checks if session exists
   - Verifies each dependency has status `stopped` or `completed`
   - Blocks if any dependency is incomplete

3. **Order Check**
   - If `session_order` is set, scans all sessions in `ai/intercom/`
   - Finds sessions with lower order numbers
   - Blocks if any earlier-ordered session is incomplete

**On validation failure:**
- Session status is set to `blocked`
- Session does not execute
- Clear error messages explain which dependencies are unsatisfied

---

## Usage Examples

### Example 1: Sequential Pipeline

```bash
# Step 1: Research
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_research \
    --session-goal "Research best practices" \
    --session-order 1

# Step 2: Design (waits for research)
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_design \
    --session-goal "Design architecture based on research" \
    --previous-session 20251201_research \
    --session-order 2

# Step 3: Implementation (waits for design)
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_implementation \
    --session-goal "Implement designed architecture" \
    --previous-session 20251201_design \
    --session-order 3
```

### Example 2: Parallel Dependencies

```bash
# Parallel Phase: Two independent sessions
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_frontend \
    --session-goal "Build frontend components"

python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_backend \
    --session-goal "Build backend services"

# Integration Phase: Depends on both
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_integration \
    --session-goal "Integrate frontend and backend" \
    --depends-on "20251201_frontend,20251201_backend"
```

### Example 3: Task Queue with Dependencies

```python
from scripts.autonomous_task_queue import AutonomousTaskQueue
from pathlib import Path

queue = AutonomousTaskQueue(Path(__file__).parent.parent)

# Phase 1: Preparation
prep_id = queue.add_task(
    title="Prepare environment",
    description="Install dependencies and configure environment",
    priority="high",
    metadata={'task_order': 1}
)

# Phase 2: Build (depends on prep)
build_id = queue.add_task(
    title="Build application",
    description="Compile and build the application",
    priority="high",
    metadata={
        'previous_task_id': prep_id,
        'task_order': 2
    }
)

# Phase 3: Test (depends on build)
test_id = queue.add_task(
    title="Run tests",
    description="Execute test suite",
    priority="normal",
    metadata={
        'previous_task_id': build_id,
        'task_order': 3
    }
)

# Get next task - will only return prep_id first
next_task = queue.get_next_task()
print(f"Next task: {next_task['title']}")  # "Prepare environment"

# Complete it
queue.complete_task(prep_id, "Environment ready")

# Now get_next_task will return build_id
next_task = queue.get_next_task()
print(f"Next task: {next_task['title']}")  # "Build application"
```

---

## Best Practices

### 1. Use Previous Session for Simple Sequences

When you have a clear A → B → C sequence:
```bash
--previous-session <previous_conversation_id>
```

### 2. Use Depends-On for Multiple Prerequisites

When a session needs multiple things to complete first:
```bash
--depends-on "session1,session2,session3"
```

### 3. Use Session Order for Large Projects

For multi-phase projects with many sessions:
```bash
--session-order 1  # Foundation
--session-order 2  # Implementation  
--session-order 3  # Testing
--session-order 4  # Deployment
```

### 4. Combine Approaches

You can use multiple dependency types together:
```bash
--previous-session 20251201_setup \
--depends-on "20251201_config,20251201_data" \
--session-order 5
```

### 5. Monitor Blocked Sessions

Check for blocked sessions:
```bash
find ai/intercom -name "cpu_instance.json" -exec grep -l '"status": "blocked"' {} \;
```

---

## Troubleshooting

### Session Won't Start - "Dependency Validation Failed"

**Cause:** A required prerequisite session is not complete.

**Solution:**
1. Check the error message - it lists which dependency is incomplete
2. Find that session and ensure it completes successfully
3. Retry the blocked session

### Task Queue Stuck - No Tasks Returned

**Cause:** All pending tasks have unsatisfied dependencies.

**Solution:**
1. Review task dependencies with `python scripts/autonomous_task_queue.py list`
2. Check which tasks are completed in `state/autonomous_tasks_completed.jsonl`
3. Identify and fix any circular dependencies
4. Complete any prerequisite tasks manually if needed

### Session Shows as Blocked but Dependencies Complete

**Cause:** Dependency session may have wrong status.

**Solution:**
1. Check the cpu_instance.json of the dependency
2. Manually update status to `stopped` if it actually completed
3. Retry the blocked session

---

## Integration Points

### Files Modified

1. **`ai_nexus/spark_plug_types.py`**
   - Added `previous_session_id`, `depends_on`, `session_order` to `CpuInstance`

2. **`ai_nexus/tri_agent_session_runner.py`**
   - Added CLI arguments for session ordering
   - Added `_validate_session_dependencies()` method
   - Modified `run_session()` and `run_continuous_session()` to validate dependencies

3. **`scripts/autonomous_task_queue.py`**
   - Added task dependency fields to task structure
   - Modified `get_next_task()` to check dependencies
   - Validates task order before returning tasks

### Related Documentation

- **TRI_AGENT_SESSION_v0.1.md** - Session runner basics
- **SPARK_PLUG_ARCHITECTURE_v0.1.md** - CPU architecture
- **AUTONOMOUS_OPERATION.md** - Autonomous operation protocol

---

## Future Enhancements

### v1.1 Planned Features
- **Automatic retry** - Retry blocked sessions when dependencies complete
- **Dependency graph** - Visualize session dependencies
- **Circular dependency detection** - Warn about impossible dependency chains
- **Soft dependencies** - Optional dependencies that don't block execution
- **Time-based ordering** - Sessions that can only run at certain times

---

**Status:** v1.0 Active
**Last Updated:** 2025-12-01

This protocol ensures agent sessions execute in the correct order, preventing coordination issues and ensuring dependent work builds on completed prerequisites.
