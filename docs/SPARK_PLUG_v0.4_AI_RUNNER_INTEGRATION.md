# Spark Plug v0.4 – AI-Runner Integration for Auto-Kernel Refresh

## Overview

Spark Plug v0.4 integrates auto-kernel refresh with the AI-Runner task processing system, enabling:

- **Batch kernel updates** from nightly or on-demand task files
- **Config-driven refresh** for scheduled maintenance of multiple kernels
- **Auditable results** written to `ai/results/` with full metadata
- **Design-only safety** – no trading/risk/executor code involved

This enables autonomous kernel maintenance without manual intervention.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          AI-Runner v0.4                          │
│                                                                   │
│  ┌─────────────┐    ┌──────────────────────────────────────┐   │
│  │ ai/tasks/   │───▶│ Task Dispatcher                       │   │
│  │ *.json      │    │  • sparkplug_autokernel_refresh       │   │
│  └─────────────┘    │  • (future task types...)            │   │
│                     └──────────────┬───────────────────────┘   │
│                                    │                            │
│                                    ▼                            │
│                     ┌──────────────────────────────────────┐   │
│                     │ Spark Plug Auto-Kernel Refresh (v0.4)│   │
│                     │  • run_autokernel_refresh()          │   │
│                     │  • Config or explicit kernel lists   │   │
│                     └──────────────┬───────────────────────┘   │
│                                    │                            │
│                                    ▼                            │
│                     ┌──────────────────────────────────────┐   │
│                     │ Spark Plug v0.2 Core                 │   │
│                     │  • History loading (Part 3)          │   │
│                     │  • CPU tri-agent (Part 1)            │   │
│                     │  • Kernel storage (Part 2)           │   │
│                     └──────────────┬───────────────────────┘   │
│                                    │                            │
│                                    ▼                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ai/results/                                               │  │
│  │  sparkplug_autokernel_refresh_<task_id>_<timestamp>.json │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration: `ai/config/sparkplug_kernels.json`

Defines which kernels participate in scheduled auto-refresh.

### Structure

```json
{
  "version": 1,
  "kernels": [
    {
      "kernel_id": "risk_model_v2",
      "mode": "cpu",
      "enabled": true,
      "notes": "Risk sizing, Kelly, caps, and consensus-aware rules."
    },
    {
      "kernel_id": "alpha_polymarket_core",
      "mode": "cpu",
      "enabled": true,
      "notes": "Core views on Polymarket edge, models, and selection criteria."
    },
    {
      "kernel_id": "trading_philosophy",
      "mode": "cpu",
      "enabled": true,
      "notes": "Meta-level trading principles, post-mortems, and style updates."
    },
    {
      "kernel_id": "system_health",
      "mode": "cpu",
      "enabled": true,
      "notes": "Infrastructure reliability, recurring failure patterns, fixes."
    },
    {
      "kernel_id": "ai_coordination",
      "mode": "cpu",
      "enabled": true,
      "notes": "Patterns for coordinating ChatGPT, Claude, Copilot, etc."
    }
  ]
}
```

### Fields

- **`version`**: Config schema version (currently `1`)
- **`kernel_id`**: Unique kernel identifier (must exist in `ai/memory/kernels/`)
- **`mode`**: Refresh mode (`"cpu"` is the only supported mode in v0.4)
- **`enabled`**: Boolean flag – only `true` kernels are processed
- **`notes`**: Human-readable description (ignored by code)

---

## Task Types

### 1. Config-Driven Mode (Nightly / Scheduled)

Reads `ai/config/sparkplug_kernels.json` and refreshes all enabled kernels.

**Task JSON:**

```json
{
  "task_type": "sparkplug_autokernel_refresh",
  "task_id": "sparkplug_nightly_2025-11-26",
  "mode": "config"
}
```

**Behavior:**
- Loads config from `ai/config/sparkplug_kernels.json`
- Iterates over kernels where `enabled == true`
- Calls `run_autokernel_refresh()` for each kernel
- Writes consolidated result to `ai/results/`

---

### 2. Explicit Kernel List (Ad Hoc / Manual)

Refreshes a specific list of kernels provided in the task JSON.

**Task JSON:**

```json
{
  "task_type": "sparkplug_autokernel_refresh",
  "task_id": "sparkplug_manual_subset_01",
  "mode": "explicit",
  "kernels": [
    {
      "kernel_id": "risk_model_v2",
      "mode": "cpu"
    },
    {
      "kernel_id": "system_health",
      "mode": "cpu"
    }
  ],
  "dry_run": true
}
```

**Behavior:**
- Ignores config file
- Uses the `kernels` list from task JSON
- Honors the optional `dry_run` flag (default: `false`)

---

## Result Structure

Results are written to `ai/results/sparkplug_autokernel_refresh_<task_id>_<timestamp>.json`

### Example Result

```json
{
  "status": "success",
  "task_type": "sparkplug_autokernel_refresh",
  "task_id": "sparkplug_nightly_2025-11-26",
  "run_at": "2025-11-26T10:32:00Z",
  "kernels": [
    {
      "kernel_id": "risk_model_v2",
      "result": {
        "status": "success",
        "kernel_id": "risk_model_v2",
        "mode": "cpu",
        "history": {
          "sources": ["user_events.jsonl"],
          "items_seen": 127,
          "items_used": 43,
          "time_range": {
            "start": "2025-11-20T08:15:00Z",
            "end": "2025-11-26T09:32:00Z"
          }
        },
        "updates": {
          "applied": [
            {
              "type": "cpu_suggestion",
              "conversation_id": "autokernel_risk_model_v2_20251126_103000",
              "thread": "/root/hands-off-engine/ai/intercom/autokernel_risk_model_v2_20251126_103000/thread.jsonl",
              "summary": "CPU session completed. Review thread for potential kernel updates.",
              "auto_applied": false,
              "reason": "v0.4 does not auto-apply updates. Manual review required.",
              "timestamp": "2025-11-26T10:32:00Z"
            }
          ],
          "skipped": [],
          "backup_file": null,
          "kernel_file": "/root/hands-off-engine/ai/memory/kernels/risk_model_v2.json"
        },
        "cpu": {
          "intercom_thread": "/root/hands-off-engine/ai/intercom/autokernel_risk_model_v2_20251126_103000/thread.jsonl",
          "conversation_id": "autokernel_risk_model_v2_20251126_103000"
        }
      }
    },
    {
      "kernel_id": "alpha_polymarket_core",
      "result": {
        "status": "no_history",
        "kernel_id": "alpha_polymarket_core",
        "mode": "cpu",
        "history": {
          "sources": [],
          "items_seen": 0,
          "items_used": 0,
          "time_range": {
            "start": null,
            "end": null
          }
        },
        "updates": {
          "applied": [],
          "skipped": [],
          "backup_file": null,
          "kernel_file": "/root/hands-off-engine/ai/memory/kernels/alpha_polymarket_core.json"
        },
        "cpu": {
          "intercom_thread": null,
          "conversation_id": null
        }
      }
    }
  ],
  "summary": {
    "total_kernels": 5,
    "success": 4,
    "no_history": 1,
    "kernel_not_found": 0,
    "errors": 0
  }
}
```

### Result Fields

#### Top-level
- **`status`**: Overall task status (`"success"` or `"error"`)
- **`task_type`**: Always `"sparkplug_autokernel_refresh"`
- **`task_id`**: Task identifier from task JSON
- **`run_at`**: ISO 8601 timestamp of execution
- **`kernels`**: Array of per-kernel results
- **`summary`**: Aggregate statistics

#### Summary Counts
- **`total_kernels`**: Number of kernels processed
- **`success`**: Kernels refreshed successfully
- **`no_history`**: Kernels with no relevant history events
- **`kernel_not_found`**: Kernels that don't exist
- **`errors`**: Kernels that encountered errors

#### Per-kernel Result
See `run_autokernel_refresh()` docstring for detailed structure.

---

## CLI Usage

### AI-Runner

```bash
# Process all tasks in ai/tasks/
python ai_runner.py process-all

# Process specific task file
python ai_runner.py process-one ai/tasks/sparkplug_nightly.json

# Process all but keep originals (don't move to processed/)
python ai_runner.py process-all --keep
```

### Direct Auto-Kernel Refresh (for testing)

```bash
# Refresh a single kernel
python -m ai_nexus.spark_plug_autokernel refresh \
    --kernel-id risk_model_v2 \
    --max-events 50

# Dry run (generate prompt but don't run CPU)
python -m ai_nexus.spark_plug_autokernel refresh \
    --kernel-id risk_model_v2 \
    --dry-run

# List kernels with history
python -m ai_nexus.spark_plug_autokernel list

# Show history stats for a kernel
python -m ai_nexus.spark_plug_autokernel stats --kernel-id risk_model_v2
```

---

## API Usage (Python)

### Process a Task Programmatically

```python
from pathlib import Path
import ai_runner

# Load task file
task_file = Path("ai/tasks/sparkplug_nightly.json")

# Process task
result = ai_runner.process_task(task_file)

# Write result
result_path = ai_runner.write_result(result, task_file)

# Move task to processed
ai_runner.move_task_to_processed(task_file)

print(f"Result: {result['status']}")
print(f"Kernels processed: {result['summary']['total_kernels']}")
print(f"Success: {result['summary']['success']}")
```

### Call Auto-Kernel Refresh Directly

```python
from ai_nexus.spark_plug_autokernel import run_autokernel_refresh

result = run_autokernel_refresh(
    kernel_id="risk_model_v2",
    mode="cpu",
    dry_run=False,
    max_history_items=50
)

if result["status"] == "success":
    print(f"CPU thread: {result['cpu']['intercom_thread']}")
    print(f"History items: {result['history']['items_used']}")
else:
    print(f"Error: {result.get('error', {}).get('message')}")
```

---

## Scheduling (Future Setup)

While v0.4 provides the infrastructure, **scheduling is not configured in this release**.

Future setup will involve:

### Option 1: Cron

```bash
# Example cron entry (not yet configured)
0 2 * * * cd /root/hands-off-engine && python ai_runner.py process-all
```

### Option 2: Systemd Timer

```ini
# Example systemd timer (not yet configured)
[Unit]
Description=Spark Plug Nightly Auto-Kernel Refresh

[Timer]
OnCalendar=daily
OnCalendar=02:00

[Install]
WantedBy=timers.target
```

To manually trigger a nightly refresh:

```bash
# Drop a task file into ai/tasks/
cat > ai/tasks/sparkplug_nightly_$(date +%Y%m%d).json <<EOF
{
  "task_type": "sparkplug_autokernel_refresh",
  "task_id": "sparkplug_nightly_$(date +%Y%m%d)",
  "mode": "config"
}
EOF

# Process it
python ai_runner.py process-all
```

---

## Safety Constraints (v0.4)

### Design-Only Mode

- **No trading imports**: Spark Plug v0.4 does not import `decider`, `executor`, `risk`, or any live trading code.
- **Read-only kernels**: Kernel files are NOT mutated by v0.4 (updates are suggestions only).
- **Auditable artifacts**: All CPU runs are logged to `ai/intercom/` and results to `ai/results/`.

### No Auto-Apply (v0.4)

- **Manual review required**: v0.4 does NOT automatically apply kernel updates.
- **Updates section**: Contains `cpu_suggestion` entries pointing to CPU thread files.
- **Future v0.3**: Full auto-parse and auto-apply will be added in a later release.

---

## Error Handling

### Single Kernel Failures

- If one kernel fails, the task **continues** processing remaining kernels.
- Failures are recorded in the per-kernel `result` and counted in `summary.errors`.

### Fundamental Failures

- If the config file is missing or malformed, the task returns top-level `status: "error"`.
- If an unexpected exception occurs, it's caught and logged.

---

## Testing

### Run Tests

```bash
# Run Spark Plug auto-kernel tests
PYTHONPATH=/root/hands-off-engine:$PYTHONPATH pytest tests/unit/test_spark_plug_autokernel.py -v

# Run AI-Runner tests
PYTHONPATH=/root/hands-off-engine:$PYTHONPATH pytest tests/unit/test_ai_runner.py -v

# Run all tests
PYTHONPATH=/root/hands-off-engine:$PYTHONPATH pytest tests/unit/ -v
```

### Test Coverage

v0.4 tests cover:

- `run_autokernel_refresh()` function
  - kernel_not_found
  - no_history
  - success path with CPU mocking
  - dry_run behavior
  - unsupported mode
  - error handling
  - time range calculation
- AI-Runner task processing
  - config-driven mode
  - explicit kernel list mode
  - mixed status results
  - error handling (config not found, invalid mode, exceptions)
  - result writing and task moving
  - end-to-end integration
- Safety constraints
  - No trading imports
  - No auto-apply in v0.4

---

## Future Enhancements (v0.5+)

- **v0.3 Auto-Apply**: Parse CPU output and automatically apply kernel updates (with backups).
- **Per-kernel schedules**: `"schedule": "daily" | "weekly" | "on_demand"` in config.
- **Retry logic**: Auto-retry failed kernels with exponential backoff.
- **Notification hooks**: Slack/email alerts on failures or important updates.
- **Web dashboard**: View results and kernel status via web UI.

---

## Troubleshooting

### No Kernels Processed

**Symptom**: `summary.total_kernels == 0`

**Causes**:
- Config file missing (`ai/config/sparkplug_kernels.json`)
- All kernels disabled (`enabled: false`)
- Empty explicit kernel list

**Solution**: Check config file and ensure at least one kernel has `enabled: true`.

---

### "kernel_not_found" Status

**Symptom**: Per-kernel result has `status: "kernel_not_found"`

**Cause**: Kernel file doesn't exist at `ai/memory/kernels/<kernel_id>.json`

**Solution**: Create the kernel using `ai_nexus.memory_kernels.create_kernel()`.

---

### "no_history" Status

**Symptom**: Per-kernel result has `status: "no_history"`

**Cause**: No history events found for the kernel in `ai/history/user_events.jsonl`.

**Solution**: This is normal if the kernel hasn't been active recently. CPU will not run.

---

### CPU Errors

**Symptom**: Per-kernel result has `status: "error"` with `error.stage == "cpu"`

**Causes**:
- CPU session failed (API errors, quota limits, network issues)
- Malformed history events

**Solution**:
- Check `error.message` and `error.traceback` in result JSON
- Review CPU intercom logs if `conversation_id` is available

---

## Version History

- **v0.4** (2025-11-26): AI-Runner integration, config-driven batch refresh, result auditing
- **v0.2** (2025-11-25): Tri-agent CPU + auto-kernel CLI baseline
- **v0.1** (2025-11-20): Initial Spark Plug architecture

---

## Related Documentation

- `docs/SPARK_PLUG_ARCHITECTURE_v0.1.md` – Core Spark Plug concepts (Parts 1–3)
- `docs/SPARK_PLUG_PART3_USER_CONNECTOR_v0.1.md` – User history connector details
- `ai_nexus/spark_plug_autokernel.py` – Implementation source
- `ai_runner.py` – Task processor implementation

---

**End of Spark Plug v0.4 Documentation**
