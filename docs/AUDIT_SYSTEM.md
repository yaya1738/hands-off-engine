# Audit System Documentation

## Overview

The Hands-Off Engine includes a comprehensive audit logging system that tracks all critical operations, decisions, and state changes. This ensures full transparency, accountability, and traceability of the system's behavior.

## Purpose

The audit system serves several critical functions:

1. **Accountability**: Track all decisions and actions made by the system
2. **Debugging**: Investigate issues by reviewing historical events
3. **Compliance**: Maintain records for regulatory or personal review
4. **Analysis**: Understand system behavior and performance over time
5. **Safety**: Ensure DRYRUN vs LIVE mode is properly logged and enforced

## Architecture

### Components

1. **AuditLogger** (`audit/audit_logger.py`): Core logging infrastructure
   - Structured event logging with JSON format
   - Daily log rotation
   - Session-based event grouping
   - Multiple severity levels

2. **Audit Viewer** (`audit/audit_viewer.py`): Query and analysis tool
   - Filter logs by date, component, event type, session
   - Generate statistics
   - Formatted output for easy reading

### Log Format

All audit logs are stored as JSON Lines (`.jsonl`) files with the following structure:

```json
{
  "timestamp": "2025-11-20T10:22:47.609333+00:00",
  "timestamp_unix": 1763634167.6093392,
  "event_type": "edge_detection",
  "component": "autopilot.edge_engine",
  "severity": "info",
  "session_id": "edge_engine_20251120_102247",
  "data": {
    "market": "btc_100k_eoy",
    "p_fair": 0.40,
    "p_market": 0.25,
    "edge": 0.15,
    "action": "BUY YES",
    "metadata": {
      "threshold": 0.05,
      "note": "Bitcoin 100k EOY"
    }
  }
}
```

### Event Types

The system tracks the following event types:

- **decision**: Decision-making events (bet sizing, strategy selection)
- **action**: Actions taken by the system (trades, state changes)
- **data_fetch**: External data fetches (Polymarket API, prices, etc.)
- **state_change**: Changes to system state
- **risk_assessment**: Risk calculations and assessments
- **alpha_calculation**: Alpha/edge calculations
- **edge_detection**: Detected edges/opportunities
- **order**: Order placements (DRYRUN or LIVE)
- **execution**: Execution of plans or workflows
- **error**: Error conditions and exceptions

### Severity Levels

- **debug**: Detailed diagnostic information
- **info**: Normal operational events (default)
- **warning**: Warning conditions
- **error**: Error conditions
- **critical**: Critical failures

## Usage

### In Python Code

#### Basic Usage

```python
from audit import get_audit_logger

# Get logger for your component
audit = get_audit_logger(component="my_component")

# Log an edge detection
audit.log_edge_detection(
    market="btc_100k_eoy",
    p_fair=0.40,
    p_market=0.25,
    edge=0.15,
    action="BUY YES",
    metadata={"threshold": 0.05}
)

# Log an order
audit.log_order(
    order_type="limit",
    market="btc_100k_eoy",
    side="YES",
    size=37.5,
    price=0.25,
    dryrun=True,
    order_id="order-123"
)

# Log a decision
audit.log_decision(
    decision_type="bet_sizing",
    inputs={"bankroll": 1000, "edge": 0.15},
    outputs={"bet_size": 37.5}
)
```

#### Session-Based Logging

Group related events together with a session ID:

```python
import datetime
from audit import get_audit_logger

audit = get_audit_logger(component="my_component")
session_id = f"my_run_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

# All events with the same session_id are grouped together
audit.log_data_fetch(
    source="polymarket_api",
    params={"url": "..."},
    success=True,
    record_count=50,
    session_id=session_id
)

audit.log_edge_detection(
    market="btc_100k_eoy",
    p_fair=0.40,
    p_market=0.25,
    edge=0.15,
    action="BUY YES",
    session_id=session_id
)
```

#### Error Logging

```python
import traceback
from audit import get_audit_logger

audit = get_audit_logger(component="my_component")

try:
    # Some risky operation
    result = risky_operation()
except Exception as e:
    audit.log_error(
        error_type=type(e).__name__,
        error_message=str(e),
        stack_trace=traceback.format_exc(),
        context={"operation": "risky_operation"}
    )
    raise
```

#### AI Operations Logging

The AI Intake handler automatically logs all AI operations:

```python
# AI Intake Handler logs:
# - Command invocation (/plan, etc.)
# - Data fetching (policy files, reports)
# - AI decision generation (OpenAI API calls)
# - GitHub comment posting
# - Errors during execution

# Example of what gets logged automatically:
# 1. When /plan command is invoked on issue #1
# 2. Loading of AI_POLICY.md and research reports
# 3. OpenAI API call with model, temperature, prompt length
# 4. Generated plan length and preview
# 5. GitHub comment posted successfully

# All events are grouped by session_id for traceability
```

To view AI Intake audit logs:

```bash
# View all AI intake operations
python3 audit/audit_viewer.py --component ai.intake_handler

# View a specific session
python3 audit/audit_viewer.py --session ai_intake_plan_20251120_102247
```

### Viewing Audit Logs

#### Basic Viewing

```bash
# View all logs
python3 audit/audit_viewer.py

# View last 20 entries
python3 audit/audit_viewer.py --tail 20

# View logs from specific date
python3 audit/audit_viewer.py --date 2025-11-20
```

#### Filtering

```bash
# Filter by component
python3 audit/audit_viewer.py --component edge_engine

# Filter by event type
python3 audit/audit_viewer.py --event-type edge_detection

# Filter by session ID
python3 audit/audit_viewer.py --session edge_engine_20251120_102247

# Combine filters
python3 audit/audit_viewer.py --component executor --event-type order --date 2025-11-20
```

#### Analysis

```bash
# Show statistics
python3 audit/audit_viewer.py --stats

# List all components
python3 audit/audit_viewer.py --list-components

# List all event types
python3 audit/audit_viewer.py --list-event-types

# Verbose output (full JSON)
python3 audit/audit_viewer.py --verbose --tail 5
```

## Log Storage

### Location

Audit logs are stored in one of the following locations (in order of preference):

1. `~/hands-off/audit/` (Termux production environment)
2. `<repo>/logs/audit/` (Development environment)

### File Naming

Logs are automatically rotated daily with the naming pattern:

```
audit_YYYY-MM-DD.jsonl
```

Example: `audit_2025-11-20.jsonl`

### Retention

- Logs are kept indefinitely by default
- Old logs can be manually archived or compressed
- Consider implementing automated retention policies for production

Recommended retention policy:
- Keep 30 days online
- Archive 1 year
- Delete after 1 year (or keep longer if needed for compliance)

## Integration Points

The audit system is currently integrated into:

1. **Core Components**:
   - `alpha/ho_alpha_polymarket.py` - Alpha calculations
   - `decider/ho_decider.py` - Decision making
   - `executor/ho_executor_plan.py` - Execution

2. **AI/Agent Systems**:
   - `ai/ai_intake_handler.py` - AI Intake command handling (logs all `/plan` commands, API calls, and responses)
   - `ai_nexus/` - AI Nexus multi-brain orchestration system (tracks all AI operations, costs, and financial outcomes)

## Best Practices

### What to Audit

Always audit:
- ✅ All trading decisions and orders (DRYRUN or LIVE)
- ✅ Edge/alpha calculations
- ✅ Risk assessments
- ✅ State changes (mode transitions, config changes)
- ✅ External data fetches
- ✅ Errors and exceptions
- ✅ System startup/shutdown

Optionally audit:
- Debug information for troubleshooting
- Performance metrics
- User interactions

### When to Audit

- **Before**: Log intent before performing critical operations
- **After**: Log results after operations complete
- **On Error**: Always log errors with context

### Session IDs

Use session IDs to group related events:

```python
# Good: All events in one run share a session ID
session_id = f"fetch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
audit.log_data_fetch(..., session_id=session_id)
audit.log_edge_detection(..., session_id=session_id)
audit.log_order(..., session_id=session_id)
```

### Error Handling

The audit system is designed to be resilient:

```python
# The audit logger handles its own errors
# If file write fails, it falls back to stderr
try:
    from audit import get_audit_logger
    audit = get_audit_logger(component="my_component")
except ImportError:
    # Gracefully handle if audit module is not available
    audit = None

# Always check if audit is available
if audit:
    audit.log_edge_detection(...)
```

## Security Considerations

1. **Sensitive Data**: Be careful not to log sensitive credentials or personal information
2. **File Permissions**: Audit logs should have appropriate file permissions (600 or 640)
3. **Log Rotation**: Implement proper rotation to prevent disk space issues
4. **Immutability**: Logs should not be modified after writing (append-only)

## Future Enhancements

Potential improvements:

1. **Automated Analysis**: Detect anomalies or patterns in audit logs
2. **Alerting**: Trigger alerts on critical events or errors
3. **Visualization**: Dashboard for audit log visualization
4. **Export**: Export to external monitoring/logging systems
5. **Compression**: Automatic compression of old logs
6. **Backup**: Automatic backup of audit logs to cloud storage

## Troubleshooting

### Logs Not Being Created

1. Check that the audit module is properly imported
2. Verify the log directory exists and is writable
3. Check for errors in stderr (fallback logging)

### Missing Events

1. Verify the component is using the audit logger
2. Check that the appropriate log methods are being called
3. Ensure session IDs are being passed correctly for filtering

### Performance Impact

The audit system is designed to be lightweight:
- Writes are append-only (fast)
- No blocking operations
- Minimal memory overhead
- Consider async logging for very high-throughput scenarios

## Related Documentation

- `README.md` - Project overview
- `AI_POLICY.md` - AI agent policies
- `ai_nexus/README.md` - AI Nexus documentation
- `audit/README.md` - Audit quick start
