# Batch 17 Specification: Continuous Autonomous AI Loop (DRYRUN-Only)

## Overview

Batch 17 implements a **continuous autonomous AI loop** that orchestrates the Hands-Off Engine's core components in an infinite, resilient, DRYRUN-only cycle. This is an **AI-native closed-loop orchestrator**, not a scheduler replacement.

## Architecture

### Core Components

The AI loop orchestrates three previously implemented batches:

1. **Task Generator (Batch 16)**: Generates new tasks based on current state
2. **AI Runner (Batch 15)**: Executes generated tasks in DRYRUN mode
3. **Health Monitor (Batch 14)**: Monitors system health and status

### Loop Cycle

Each iteration performs the following steps in sequence:

```
1. Invoke Task Generator → generates tasks
2. Invoke AI Runner → executes tasks (DRYRUN)
3. Read Health Status → checks system health
4. Write Loop Summary → records cycle results
5. Sleep (interruptible) → wait for next cycle
6. Repeat indefinitely (or exit if --once)
```

## Module: `ai/ho_ai_loop.py`

### Main Function

```python
def run_ai_loop(
    state_dir="state",
    ai_dir="ai",
    interval="30s",
    max_errors=50,
    verbose=False,
    once=False
) -> int
```

Runs the continuous autonomous loop with the following behavior:

- **Infinite execution**: Runs forever unless stopped or error threshold exceeded
- **Error resilience**: Tracks consecutive errors, stops if `consecutive_errors > max_errors`
- **Graceful shutdown**: Handles SIGINT (Ctrl+C) cleanly, completes current cycle
- **State preservation**: Always writes summary before exiting
- **DRYRUN safety**: Never executes real trading operations

### Core Functions

#### `run_single_cycle(state_dir, ai_dir, cycle, interval, verbose)`

Executes one complete loop iteration:

1. Invokes Task Generator
2. Invokes AI Runner
3. Reads health status
4. Writes loop summary (latest + history)

Returns:
```json
{
  "cycle": 42,
  "status": "ok|error",
  "errors": [...]
}
```

#### `parse_interval(interval: str) -> int`

Parses interval strings to seconds:

- `"10s"` → 10 seconds
- `"2m"` → 120 seconds
- `"1h"` → 3600 seconds

Raises `ValueError` for invalid formats.

#### `sleep_interruptible(seconds: int, verbose: bool) -> bool`

Sleeps in 1-second increments, checking for shutdown signal each iteration.

Returns `True` if shutdown was requested during sleep.

#### `load_health(state_dir: str) -> dict`

Loads health status from `state/hands_off_health.json`.

Handles missing or malformed files gracefully:
```python
{"status": "unknown", "reason": "health file not found"}
```

#### `write_loop_summary(...)`

Writes two files per cycle:

1. **Latest summary**: `state/hands_off_ai_loop.json`
2. **History entry**: `state/history/ai_loop_<timestamp>.json`

Summary structure:
```json
{
  "timestamp": "2025-11-18T12:34:56Z",
  "cycle": 42,
  "interval": "30s",
  "health": "ok|warn|error|unknown",
  "task_generator": {
    "status": "success|error",
    "result": {...},
    "error": null
  },
  "ai_runner": {
    "status": "success|error",
    "result": {...},
    "error": null
  },
  "errors": [],
  "status": "ok|partial|error"
}
```

### Status Determination

The overall `status` field is determined as:

- `"error"`: Either Task Generator or AI Runner failed
- `"partial"`: Both succeeded but some tasks were skipped (errors list non-empty)
- `"ok"`: Both succeeded and no errors

## CLI Interface

### Usage

```bash
python3 ai/ho_ai_loop.py [OPTIONS]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--state-dir` | `state` | State directory path |
| `--ai-dir` | `ai` | AI directory path |
| `--interval` | `30s` | Sleep interval between cycles |
| `--max-errors` | `50` | Max consecutive errors before stopping |
| `--verbose` | `false` | Enable verbose output |
| `--once` | `false` | Run exactly one cycle and exit |

### Examples

```bash
# Run with defaults (30s interval, verbose off)
python3 ai/ho_ai_loop.py

# Run with 1-minute interval and verbose output
python3 ai/ho_ai_loop.py --interval 1m --verbose

# Run exactly one cycle (useful for testing)
python3 ai/ho_ai_loop.py --once

# Custom directories and settings
python3 ai/ho_ai_loop.py \
  --state-dir /tmp/state \
  --ai-dir /tmp/ai \
  --interval 2m \
  --max-errors 100 \
  --verbose
```

## Error Handling

### Graceful Degradation

The loop **never crashes**. All component failures are handled:

1. **Task Generator fails**: Error recorded, cycle continues
2. **AI Runner fails**: Error recorded, cycle continues
3. **Health file missing**: Status set to "unknown", cycle continues
4. **Health file malformed**: Status set to "unknown", cycle continues

### Consecutive Error Tracking

The loop tracks consecutive failures:

- Increments on each cycle with errors
- Resets to 0 on successful cycle
- If `consecutive_errors > max_errors`:
  - Writes final fatal summary
  - Exits with code 1

### SIGINT Handling

When user presses Ctrl+C:

1. Signal handler sets `_shutdown_requested = True`
2. Current cycle completes
3. Final summary written
4. Exits gracefully with code 0

The sleep function checks for shutdown every second, allowing quick response to SIGINT.

## File Outputs

### Latest Summary

**Location**: `state/hands_off_ai_loop.json`

Updated every cycle with the most recent results. Used for monitoring current loop state.

### History Files

**Location**: `state/history/ai_loop_<timestamp>.json`

One file per cycle, timestamped for historical analysis. Format identical to latest summary.

Example filename: `ai_loop_20251118_123456.json`

## Safety Constraints

### Absolute Requirements

**MUST:**
- Always run in DRYRUN mode
- Never execute real trading operations
- Never write outside `ai/` or `state/` directories
- Never break Batch 8-15 component APIs
- Never import from `termux-hands-off/`
- Never attempt network calls

**MUST NOT:**
- Modify any Batch 8-15 component APIs
- Modify scheduler internals
- Modify autoloop internals
- Change existing JSON formats

### Component Integration

The loop integrates with Batches 14-16 through well-defined interfaces:

```python
# Task Generator (Batch 16)
from ai.ho_task_generator import TaskGenerator
tg = TaskGenerator(state_dir, ai_dir)
result = tg.run(verbose=False)

# AI Runner (Batch 15)
from ai.ho_ai_runner import run_ai_runner
result = run_ai_runner(state_dir, ai_dir, verbose=False)

# Health Monitor (Batch 14)
# Reads state/hands_off_health.json (no import needed)
```

If components are not available, the loop degrades gracefully with error status.

## Testing

### Test Suite

Location: `tests/integration/test_ai_loop.py`

### Required Tests

1. ✓ `test_single_cycle_success` - Single cycle completes
2. ✓ `test_loop_writes_summary` - Latest summary written
3. ✓ `test_loop_writes_history_file` - History entry created
4. ✓ `test_health_missing_handled_gracefully` - Missing health handled
5. ✓ `test_malformed_health_handled_gracefully` - Malformed health handled
6. ✓ `test_task_generator_failure_does_not_crash_loop` - TG failure handled
7. ✓ `test_ai_runner_failure_does_not_crash_loop` - Runner failure handled
8. ✓ `test_error_threshold_stops_loop` - Max errors enforced
9. ✓ `test_interval_parser` - Interval parsing works
10. ✓ `test_cli_once_mode` - --once runs exactly one cycle
11. ✓ `test_sigint_handling` - SIGINT handled gracefully

### Running Tests

```bash
# Run all tests
pytest tests/integration/test_ai_loop.py -v

# Run specific test
pytest tests/integration/test_ai_loop.py::test_single_cycle_success -v

# Run with coverage
pytest tests/integration/test_ai_loop.py --cov=ai.ho_ai_loop --cov-report=term-missing
```

## Integration Narrative

Batch 17 completes the autonomous AI orchestration layer. Previous batches provided:

- **Batch 14**: Health monitoring and status tracking
- **Batch 15**: AI-driven task execution (DRYRUN)
- **Batch 16**: Intelligent task generation

Batch 17 ties these together in a continuous loop that:

1. **Generates** tasks based on current state
2. **Executes** tasks in DRYRUN mode
3. **Monitors** health continuously
4. **Persists** all results for analysis
5. **Recovers** from failures automatically
6. **Runs** indefinitely without human intervention

This creates a true autonomous AI agent that operates continuously while maintaining complete safety through DRYRUN enforcement.

## Future Extensions

Potential enhancements for future batches:

- Adaptive interval adjustment based on activity
- Machine learning-driven task prioritization
- Advanced health anomaly detection
- Multi-agent coordination
- Real-time dashboard integration
- Performance optimization based on historical patterns

---

**Version**: 1.0
**Batch**: 17
**Status**: DRYRUN-Only
**Safety Level**: Maximum (no real execution)
