# Reports Module

This directory contains reporting and analytics modules for the Hands-Off Engine.

## Brain Report (Batch 18)

**File:** `ho_brain_report.py`

### Overview

The Brain Report module provides a unified "top of the pyramid" view of the entire Hands-Off system by consolidating all key state files into a single summary.

### Quick Start

```bash
# Generate brain summary (creates JSON + text report)
python3 reports/ho_brain_report.py

# Custom state directory
python3 reports/ho_brain_report.py --state-dir /path/to/state
```

### Output Files

- **`state/hands_off_brain.json`** - Machine-readable unified summary
- **`state/hands_off_brain.txt`** - Human-readable text report

### What It Consolidates

The brain report reads and aggregates:
- `state/hands_off_health.json` - Health monitoring (Batch 14)
- `state/hands_off_summary.json` - Pipeline state (Batch 10)
- `state/hands_off_history_summary.json` - Historical trends (Batch 13)
- `state/hands_off_ai_loop.json` - AI loop status (Batch 17)

All input files are optional; the module gracefully handles missing files.

### Status Levels

- **`ok`** - System healthy, error rate normal
- **`warn`** - High error rate detected (>25%)
- **`error`** - Health check failed or critical issues

### Programmatic Usage

```python
from reports.ho_brain_report import build_brain_summary, write_brain_summary

# Just build the summary dict
summary = build_brain_summary("state")
print(f"Overall status: {summary['status']}")

# Build and write files
summary = write_brain_summary("state")
```

### Integration Examples

**Dashboard:**
```python
import json
with open("state/hands_off_brain.json") as f:
    brain = json.load(f)

if brain["status"] == "error":
    trigger_alert(brain["errors"])
```

**Termux/Telegram:**
```bash
python3 reports/ho_brain_report.py
cat state/hands_off_brain.txt | termux-notification
```

**Scheduled Monitoring:**
```bash
# Cron: every 5 minutes
*/5 * * * * cd /root/hands-off-out && python3 reports/ho_brain_report.py
```

### Features

✅ **DRYRUN-only** - Read-mostly, safe for production
✅ **Graceful degradation** - Works even with missing inputs
✅ **Comprehensive tests** - 12 tests, all passing
✅ **Clear status signals** - ok/warn/error with reasoning
✅ **Dual output formats** - JSON for machines, text for humans

### Documentation

See `docs/BATCH_18_STATUS_REPORT.md` for complete documentation, JSON contract, and integration guide.

### Tests

```bash
# Run all brain report tests
python3 -m unittest tests.integration.test_brain_report -v
```
