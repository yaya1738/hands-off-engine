# Batch 11: Autonomous Scheduler (Heartbeat Layer) - Specification

## Overview

Batch 11 implements a fully autonomous Python scheduler that repeatedly executes the Batch 10 autoloop at a user-specified interval and writes timestamped history snapshots. This evolves the system from a "manual pipeline" into a safe, DRYRUN-only, self-refreshing loop.

**Key principle:** Nothing in this batch enables LIVE trading. All existing DRYRUN safety constraints remain intact.

---

## Components

### 1. `scheduler/ho_autoloop.py`

The autoloop orchestrator that executes all configured pipelines.

#### Function: `run_all(state_dir)`

**Purpose:** Execute all configured pipelines in the autoloop.

**Arguments:**
- `state_dir` (str): Path to the state directory (e.g., "state/")

**Returns:** Dictionary with aggregated pipeline results:
```python
{
    "timestamp": "2025-11-18T14:30:00Z",       # ISO 8601 UTC timestamp
    "status": "success" | "error" | "partial", # Overall status
    "mode": "DRYRUN",                          # Safety indicator
    "total_execution_time_sec": 12.5,          # Total execution time
    "pipelines": {
        "polymarket": {
            "status": "success",
            "mode": "DRYRUN",
            "execution_time_sec": 12.5,
            "timestamp": "2025-11-18T14:30:00Z",
            "edges_found": 0,
            "recommendations": [],
            "note": "DRYRUN mode - no live trades executed"
        }
    },
    "summary": "Completed 1/1 pipelines successfully (DRYRUN mode)"
}
```

**Safety:**
- All pipelines run in DRYRUN mode only
- No live trades are executed
- No network calls that modify state

**CLI Usage:**
```bash
python3 scheduler/ho_autoloop.py state/
```

---

### 2. `scheduler/ho_scheduler.py`

The autonomous scheduler that runs the autoloop repeatedly.

#### Function: `run_scheduler(state_dir, every="60s", once=False, log=False, max_errors=None)`

**Purpose:** Run the autonomous scheduler that repeatedly executes the autoloop.

**Arguments:**
- `state_dir` (str): Path to state directory
- `every` (str): Interval between cycles (default: "60s")
  - Format: "Xs" (seconds), "Xm" (minutes), "Xh" (hours)
  - Examples: "30s", "5m", "2h"
- `once` (bool): Run only one cycle and exit (default: False)
- `log` (bool): Enable verbose logging (default: False)
- `max_errors` (int|None): Maximum consecutive errors before stopping (default: None = unlimited)

**Behavior Each Cycle:**
1. Run `result = ho_autoloop.run_all(state_dir)`
2. Write/update `state/hands_off_summary.json`
3. Write timestamped history snapshot: `state/history/<timestamp>.json`
4. Log cycle status

**Error Handling:**
- Never crashes
- Continues loop even after failures
- Writes snapshot even in error case
- Tracks consecutive errors (optional max limit)

**Graceful Shutdown:**
- Responds to SIGINT (CTRL-C)
- Completes current cycle before stopping
- Logs shutdown status

**CLI Usage:**
```bash
# Run every 60 seconds (default)
python3 scheduler/ho_scheduler.py state/

# Run every 5 minutes
python3 scheduler/ho_scheduler.py --every 5m state/

# Run every 2 hours
python3 scheduler/ho_scheduler.py --every 2h state/

# Run once and exit
python3 scheduler/ho_scheduler.py --once state/

# Verbose logging
python3 scheduler/ho_scheduler.py --log --every 30s state/
```

---

### 3. State Files

#### `state/hands_off_summary.json`

The latest summary of the most recent autoloop execution. Updated on every cycle.

**Structure:** Identical to the return value of `run_all()`.

#### `state/history/<timestamp>.json`

Timestamped snapshots of each autoloop execution.

**Filename Format:** `YYYYMMDD_HHMMSS_UTC.json`
- Example: `20251118_143025_UTC.json`

**Structure:** Identical to `hands_off_summary.json`.

**Purpose:**
- Historical tracking of all executions
- Debugging and analysis
- Dashboard and monitoring integrations
- AI runner data source

---

### 4. Interval Parsing

The scheduler supports human-friendly interval formats:

| Format | Unit    | Example | Seconds |
|--------|---------|---------|---------|
| `Xs`   | Seconds | `30s`   | 30      |
| `Xm`   | Minutes | `5m`    | 300     |
| `Xh`   | Hours   | `2h`    | 7200    |

**Parsing Rules:**
- Case insensitive: "30s" = "30S"
- Whitespace trimmed
- Value must be positive integer
- Invalid formats raise `ValueError`

---

## Integration Tests

### `tests/integration/test_scheduler.py`

Comprehensive integration tests validating all scheduler functionality.

**Test Cases:**

1. **`test_interval_parser()`**
   - Valid intervals: "30s", "5m", "2h"
   - Case insensitivity
   - Whitespace handling
   - Invalid formats raise ValueError
   - Zero/negative values rejected

2. **`test_autoloop_run_all()`**
   - Returns proper dictionary structure
   - Contains required fields
   - Types are correct
   - Pipelines structure is valid

3. **`test_scheduler_once_mode()`**
   - Runs single cycle with `--once`
   - Creates summary file
   - Creates exactly one history snapshot
   - Files have valid JSON

4. **`test_history_snapshot_structure()`**
   - Snapshot has required fields
   - Field types are correct
   - Timestamp is ISO 8601 format
   - Status values are valid
   - Pipelines structure is valid

5. **`test_multiple_cycles()`**
   - Multiple cycles create multiple snapshots
   - Each snapshot is valid
   - Timestamps are unique

6. **`test_error_handling()`**
   - Scheduler completes even on errors
   - Error snapshots are written
   - Summary is written on error

7. **`test_summary_and_history_match()`**
   - Latest snapshot matches summary file
   - Content is identical

8. **`test_cli_once_flag()`**
   - CLI with `--once` stops after one cycle
   - Creates exactly one snapshot
   - Exit code is 0

9. **`test_dryrun_mode_safety()`**
   - DRYRUN mode is enforced
   - All pipelines are in DRYRUN mode
   - Mode field is present

**Running Tests:**
```bash
python3 tests/integration/test_scheduler.py
```

---

## Safety Constraints

### DRYRUN Mode

**Mandatory for Batch 11:**
- All pipeline executions must be DRYRUN only
- No live trade execution
- No API calls that modify external state
- No real money transactions

**Enforcement:**
- `mode: "DRYRUN"` in all result dictionaries
- Pipeline implementations must not execute live trades
- Tests validate DRYRUN mode

### Read-Only `termux-hands-off`

The legacy `termux-hands-off/` codebase is read-only. Batch 11 does not modify it.

### No External Processes

The scheduler must not run external processes. All logic is Python-only.

### Error Resilience

The scheduler must never crash. All errors are caught, logged, and the scheduler continues running.

---

## File Structure

```
hands-off-engine/
├── scheduler/
│   ├── ho_autoloop.py          # Autoloop orchestrator
│   └── ho_scheduler.py          # Autonomous scheduler
├── state/
│   ├── hands_off_summary.json   # Latest summary
│   └── history/                 # Historical snapshots
│       ├── 20251118_143025_UTC.json
│       ├── 20251118_143125_UTC.json
│       └── ...
├── tests/
│   └── integration/
│       └── test_scheduler.py    # Integration tests
└── docs/
    ├── BATCH_11_SPEC.md         # This specification
    └── BATCH_11_STATUS_REPORT.md # Implementation status
```

---

## Expected Result

A fully autonomous, well-tested, DRYRUN-only scheduling engine that:

1. Runs indefinitely (or until CTRL-C)
2. Executes autoloop at specified intervals
3. Produces summary + history files
4. Handles errors gracefully
5. Never crashes
6. Provides clean CLI interface
7. Supports dashboard, AI runners, and monitoring systems

**Integration Points:**
- `ho_autoloop.py` - pipeline orchestration
- `ho_polymarket_report.py` - future Polymarket reporting (Batch 10)
- Existing tests and state formats
- Dashboard systems (future batches)
- AI runner integrations (future batches)

---

## Usage Examples

### Example 1: Run Once for Testing

```bash
python3 scheduler/ho_scheduler.py --once --log state/
```

**Output:**
```
[scheduler] Starting Hands-Off Scheduler (Batch 11)
[scheduler] Mode: single-shot
[scheduler] State directory: state/
[scheduler] DRYRUN mode: ENABLED (no live trades)
[scheduler] Verbose logging: True
[scheduler] Press CTRL-C to stop gracefully

[scheduler] ===== Starting cycle 1 =====
[scheduler] Timestamp: 2025-11-18T14:30:00+00:00
[scheduler] Wrote summary: state/hands_off_summary.json
[scheduler] Wrote history snapshot: state/history/20251118_143000_UTC.json
[scheduler] Status: success
[scheduler] Execution time: 0.015s
[scheduler] Summary: Completed 1/1 pipelines successfully (DRYRUN mode)
[scheduler] ===== Finished cycle 1 =====

[scheduler] Single cycle completed (--once mode)
[scheduler] Stopped after 1 cycle(s)
[scheduler] Shutdown complete
```

### Example 2: Continuous Running Every 5 Minutes

```bash
python3 scheduler/ho_scheduler.py --every 5m state/
```

**Output:**
```
[scheduler] Starting Hands-Off Scheduler (Batch 11)
[scheduler] Mode: continuous (every 5m = 300s)
[scheduler] State directory: state/
[scheduler] DRYRUN mode: ENABLED (no live trades)
[scheduler] Verbose logging: False
[scheduler] Press CTRL-C to stop gracefully

[scheduler] cycle 1: success (0.015s) - Completed 1/1 pipelines successfully (DRYRUN mode)
[scheduler] cycle 2: success (0.016s) - Completed 1/1 pipelines successfully (DRYRUN mode)
[scheduler] cycle 3: success (0.014s) - Completed 1/1 pipelines successfully (DRYRUN mode)
^C
[scheduler] Shutdown requested (SIGINT). Finishing current cycle...

[scheduler] Stopped after 3 cycle(s)
[scheduler] Shutdown complete
```

### Example 3: Test Autoloop Directly

```bash
python3 scheduler/ho_autoloop.py state/
```

**Output:**
```
[ho_autoloop] Running all pipelines (DRYRUN mode)...
[ho_autoloop] State directory: state/

[ho_autoloop] Result:
{
  "timestamp": "2025-11-18T14:30:00+00:00",
  "status": "success",
  "mode": "DRYRUN",
  "pipelines": {
    "polymarket": {
      "status": "success",
      "pipeline": "polymarket",
      "mode": "DRYRUN",
      "execution_time_sec": 0.001,
      "timestamp": "2025-11-18T14:30:00+00:00",
      "edges_found": 0,
      "recommendations": [],
      "note": "DRYRUN mode - no live trades executed"
    }
  },
  "total_execution_time_sec": 0.002,
  "summary": "Completed 1/1 pipelines successfully (DRYRUN mode)"
}
```

---

## Future Enhancements (Out of Scope for Batch 11)

These features are **not** implemented in Batch 11 but may be added in future batches:

1. **Multiple Pipeline Support:**
   - Crypto pipeline
   - Stock pipeline
   - Custom pipelines

2. **Advanced Scheduling:**
   - Cron-like schedules
   - Time-of-day restrictions
   - Timezone support

3. **Monitoring & Alerts:**
   - Email/SMS alerts on errors
   - Prometheus metrics
   - Health check endpoints

4. **Dashboard Integration:**
   - Real-time status display
   - Historical charts
   - Performance metrics

5. **Persistence & Recovery:**
   - Checkpoint/resume support
   - Crash recovery
   - State restoration

6. **Live Mode (Future Batch):**
   - Transition from DRYRUN to LIVE
   - Safety interlocks
   - Manual approval gates

---

## Summary

Batch 11 delivers a production-ready autonomous scheduler that:

✓ Runs pipelines repeatedly at configurable intervals
✓ Writes comprehensive history snapshots
✓ Handles errors gracefully without crashing
✓ Provides clean CLI interface
✓ Maintains DRYRUN-only safety
✓ Includes comprehensive integration tests
✓ Supports graceful shutdown (CTRL-C)

This provides a solid foundation for building dashboards, AI runners, and monitoring systems in future batches while maintaining strict DRYRUN safety.
