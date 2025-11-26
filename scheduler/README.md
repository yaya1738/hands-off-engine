# Scheduler System

A cron-like task scheduling system that runs within Python for the Hands-Off Engine.

## Overview

The scheduler system provides automated task execution with:
- Cron-like syntax for scheduling
- Retry logic with exponential backoff
- File-based task locking to prevent concurrent runs
- Comprehensive audit logging
- Execution history tracking

## Architecture

```
scheduler/
├── __init__.py          # Package initialization
├── core.py              # Scheduler engine with cron parsing
├── runner.py            # Task execution with retries and locks
└── tasks.py             # Task definitions and handlers

state/scheduler/
├── schedule.json        # Task schedule configuration
├── history.jsonl        # Execution history (JSONL format)
└── locks/               # Task lock files

scripts/
└── scheduler_cli.py     # Command-line interface
```

## Components

### 1. Scheduler Core (`scheduler/core.py`)

The core scheduling engine that manages task schedules:
- **ScheduledTask**: Dataclass representing a scheduled task with cron expression
- **Scheduler**: Manages task schedules, determines when tasks should run
- Supports cron syntax (e.g., `*/15 * * * *` for every 15 minutes)
- Handles task dependencies
- Supports one-time and recurring tasks

### 2. Task Definitions (`scheduler/tasks.py`)

Predefined tasks:
- **fetch_markets**: Fetch market data (every 15 minutes)
- **calculate_alpha**: Run alpha model (every 30 minutes)
- **generate_report**: Daily summary (8am UTC)
- **backup_state**: Backup state files (2am UTC daily)
- **health_check**: System health check (every 5 minutes)

Each task:
- Returns a result dictionary with status
- Logs to audit system
- Has configurable timeout and retry settings

### 3. Task Runner (`scheduler/runner.py`)

Executes scheduled tasks with:
- **Retry logic**: Automatic retries with configurable delays
- **Task locking**: File-based locks prevent overlapping runs
- **History logging**: All executions logged to JSONL
- **Audit integration**: Events logged to audit system
- **Background execution**: Can run in foreground or background thread

### 4. CLI Interface (`scripts/scheduler_cli.py`)

Command-line interface for managing the scheduler:

```bash
# Initialize scheduler with default tasks
python scripts/scheduler_cli.py init

# List all scheduled tasks
python scripts/scheduler_cli.py list

# Show scheduler status
python scripts/scheduler_cli.py status

# Start scheduler daemon (foreground)
python scripts/scheduler_cli.py start [--interval 60]

# Manually run a specific task
python scripts/scheduler_cli.py run <task_id> [--force]

# Enable/disable tasks
python scripts/scheduler_cli.py enable <task_id>
python scripts/scheduler_cli.py disable <task_id>

# View execution history
python scripts/scheduler_cli.py history [--task-id <id>] [--last N]

# Remove a task
python scripts/scheduler_cli.py remove <task_id>
```

## Usage

### Initialize Scheduler

First-time setup to create default tasks:

```bash
python scripts/scheduler_cli.py init
```

This creates 5 default tasks in `state/scheduler/schedule.json`.

### List Tasks

View all scheduled tasks:

```bash
python scripts/scheduler_cli.py list
```

Output:
```
Scheduled Tasks
================================================================================

Fetch Markets (fetch_markets)
  Status: ✓ Enabled
  Schedule: */15 * * * *
  Timeout: 300s
  Retries: 3
  Next run: 2025-11-26 12:30:00

...
```

### Run Scheduler

Start the scheduler daemon:

```bash
python scripts/scheduler_cli.py start --interval 60
```

This checks for due tasks every 60 seconds and executes them.

### Manual Task Execution

Run a task manually:

```bash
python scripts/scheduler_cli.py run health_check
```

### View History

Check execution history:

```bash
# View all recent history
python scripts/scheduler_cli.py history --last 10

# View history for specific task
python scripts/scheduler_cli.py history --task-id health_check
```

## Task Configuration

Tasks are defined in `state/scheduler/schedule.json`:

```json
{
  "tasks": [
    {
      "task_id": "fetch_markets",
      "task_name": "Fetch Markets",
      "cron_expression": "*/15 * * * *",
      "enabled": true,
      "timeout_seconds": 300,
      "retry_count": 3,
      "retry_delay_seconds": 60,
      "dependencies": [],
      "one_time": false,
      "metadata": {}
    }
  ],
  "last_runs": {
    "fetch_markets": "2025-11-26T12:15:00"
  }
}
```

### Task Properties

- **task_id**: Unique identifier
- **task_name**: Human-readable name
- **cron_expression**: Cron syntax schedule
- **handler**: Module path to handler function
- **enabled**: Whether task is active
- **timeout_seconds**: Max execution time
- **retry_count**: Number of retries on failure
- **retry_delay_seconds**: Delay between retries
- **dependencies**: List of task_ids that must complete first
- **one_time**: If true, task runs once and is disabled
- **metadata**: Additional task-specific data

### Cron Expression Format

Standard cron syntax:
```
*    *    *    *    *
┬    ┬    ┬    ┬    ┬
│    │    │    │    └─ day of week (0-7, 0=Sunday)
│    │    │    └────── month (1-12)
│    │    └─────────── day of month (1-31)
│    └──────────────── hour (0-23)
└───────────────────── minute (0-59)
```

Examples:
- `*/5 * * * *` - Every 5 minutes
- `0 * * * *` - Every hour
- `0 8 * * *` - Daily at 8am
- `0 2 * * 0` - Weekly on Sunday at 2am
- `0 0 1 * *` - Monthly on the 1st at midnight

## Integration with Audit System

All task executions are logged to the audit system:

```python
from audit import get_audit_logger

audit = get_audit_logger(component="scheduler.tasks")
audit.log_action(
    action_type="task_execution",
    action_data={...},
    result="success",
    session_id="scheduler"
)
```

Audit logs are stored in `logs/audit/audit_YYYY-MM-DD.jsonl`.

## Execution History

Task execution history is stored in `state/scheduler/history.jsonl` in JSONL format:

```json
{"timestamp": "2025-11-26T12:15:00Z", "task_id": "fetch_markets", "event": "started", "data": {}}
{"timestamp": "2025-11-26T12:15:01Z", "task_id": "fetch_markets", "event": "completed", "data": {"status": "success", "duration_seconds": 0.5}}
```

## Task Locking

File-based locks prevent concurrent task execution:
- Lock files stored in `state/scheduler/locks/`
- Lock file: `{task_id}.lock`
- Contains PID and timestamp
- Automatically released after execution

## Adding Custom Tasks

To add a custom task:

1. Define the task handler in `scheduler/tasks.py`:

```python
def my_custom_task() -> Dict[str, Any]:
    """My custom task description"""
    audit = get_audit_logger(component="scheduler.my_task")
    
    try:
        # Task logic here
        result = {"status": "success"}
        
        audit.log_action(
            action_type="custom_task",
            action_data={"task": "my_custom_task"},
            result="success",
            session_id="scheduler"
        )
        
        return result
    except Exception as e:
        audit.log_error(
            error_type="custom_task_error",
            error_message=str(e),
            session_id="scheduler"
        )
        return {"status": "error", "message": str(e)}
```

2. Register in `REGISTERED_TASKS`:

```python
REGISTERED_TASKS = {
    "my_custom_task": {
        "handler": my_custom_task,
        "cron": "0 * * * *",  # Every hour
        "description": "My custom task",
        "timeout": 300,
    },
    # ... other tasks
}
```

3. Add to schedule:

```bash
# Re-initialize to pick up new tasks
python scripts/scheduler_cli.py init
```

## Troubleshooting

### Task Not Running

Check:
1. Is task enabled? `scheduler_cli.py list`
2. Are dependencies met?
3. Is lock stuck? Check `state/scheduler/locks/`
4. Check history: `scheduler_cli.py history --task-id <id>`
5. Check audit logs: `logs/audit/audit_*.jsonl`

### Clear Stuck Lock

```bash
rm state/scheduler/locks/<task_id>.lock
```

### Reset Schedule

```bash
# Backup existing schedule
cp state/scheduler/schedule.json state/scheduler/schedule.json.bak

# Remove and reinitialize
rm state/scheduler/schedule.json
python scripts/scheduler_cli.py init
```

## Best Practices

1. **Task Idempotency**: Tasks should be idempotent (safe to run multiple times)
2. **Timeouts**: Set realistic timeouts for each task
3. **Retries**: Configure retries for transient failures
4. **Logging**: Always log to audit system
5. **Error Handling**: Catch and log all exceptions
6. **Dependencies**: Use dependencies to ensure proper execution order
7. **Testing**: Test tasks manually before adding to schedule

## Future Enhancements

Potential improvements:
- Task priority/queueing
- Parallel task execution
- Web UI for scheduler management
- Email/Telegram notifications on failures
- Task execution metrics and monitoring
- Support for task parameters/arguments
- Dynamic schedule updates without restart
