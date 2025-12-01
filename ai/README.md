# AI Runner Module (Batch 15)

Smart task routing and health-gated execution for autonomous LLM operations.

## Overview

The AI runner provides a safe, file-based automation layer that:
- Consumes tasks from JSON files
- Executes tasks ONLY when system health permits
- Runs in DRYRUN mode (no trading, no external writes)
- Writes results to structured JSON files
- Archives completed tasks

## Directory Structure

```
ai/
  tasks/       # Incoming task queue (JSON files)
  results/     # Execution results (JSON files)
  processed/   # Archive of completed tasks
  ho_ai_runner.py  # Main runner module
```

## Supported Task Types

### 1. health-check
Returns the current system health status from `hands_off_health.json`.

**Example Task:**
```json
{
  "id": "hc-001",
  "type": "health-check",
  "payload": {}
}
```

### 2. latest-summary
Returns the latest summary from `hands_off_summary.json`.

**Example Task:**
```json
{
  "id": "ls-001",
  "type": "latest-summary",
  "payload": {}
}
```

### 3. generate-history-report
Generates a history analytics report by calling the Batch 13 module.

**Example Task:**
```json
{
  "id": "hr-001",
  "type": "generate-history-report",
  "payload": {}
}
```

### 4. run-autoloop (Health-Gated)
Runs the autoloop scheduler in DRYRUN mode. **Only executes if:**
- System health status = "ok"
- Polymarket data freshness ≤ 5 minutes

**Example Task:**
```json
{
  "id": "al-001",
  "type": "run-autoloop",
  "payload": {}
}
```

## Usage

### CLI

```bash
# Run with default directories
python3 ai/ho_ai_runner.py

# Run with custom directories
python3 ai/ho_ai_runner.py --state-dir /path/to/state --ai-dir /path/to/ai
```

### Programmatic

```python
from ai.ho_ai_runner import run_ai_runner

# Execute all pending tasks
stats = run_ai_runner(state_dir="state", ai_dir="ai")

print(f"Executed {stats['executed']} tasks")
print(f"OK: {stats['ok']}, Skipped: {stats['skipped']}, Errored: {stats['errored']}")
```

### Adding Tasks

Create a JSON file in `ai/tasks/`:

```bash
cat > ai/tasks/check-health.json << 'EOF'
{
  "id": "health-check-001",
  "type": "health-check",
  "payload": {}
}
EOF
```

Then run the AI runner to process it.

## Result Format

Results are written to `ai/results/<task_id>.json` with this structure:

```json
{
  "id": "task-001",
  "status": "ok",
  "result": {
    // Task-specific result data
  },
  "errors": [],
  "timestamp": "2025-11-18T16:45:00Z"
}
```

**Status values:**
- `"ok"` - Task executed successfully
- `"skipped"` - Task skipped due to health checks
- `"error"` - Task failed with errors

## Safety Features

- **DRYRUN Only:** No trading operations, no external writes
- **Health Gating:** Critical tasks require system health = OK
- **Freshness Checks:** Autoloop requires fresh data (≤ 5 minutes)
- **Graceful Errors:** Unknown task types return structured errors
- **No Network:** All operations are local file-based

## Testing

Run the comprehensive test suite:

```bash
python3 -m unittest tests.integration.test_ai_runner -v
```

28 tests covering:
- Task loading and validation
- Health-gated execution
- Error handling
- DRYRUN safety
- Result writing
- Task archiving

## Integration with Future LLM Agents

This module provides a safe extension point for autonomous AI agents:

1. **Agent writes task** → `ai/tasks/new-task.json`
2. **Runner executes** → Health checks + task execution
3. **Result written** → `ai/results/new-task.json`
4. **Agent reads result** → Continue autonomous workflow

All operations remain auditable, reversible, and DRYRUN-safe.
