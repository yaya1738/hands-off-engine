# Audit Package

Comprehensive audit logging for the Hands-Off Engine.

## Quick Start

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
    action="BUY YES"
)

# Log an order
audit.log_order(
    order_type="limit",
    market="btc_100k_eoy",
    side="YES",
    size=37.5,
    dryrun=True
)
```

## Viewing Logs

```bash
# List all agent sessions
python3 audit/audit_viewer.py --list-sessions

# Show summary for all sessions
python3 audit/audit_viewer.py --all-sessions

# Show summary for specific session
python3 audit/audit_viewer.py --session <session-id> --summary

# View recent events
python3 audit/audit_viewer.py --limit 20

# Filter by component
python3 audit/audit_viewer.py --component trading.polymarket

# View events with metadata
python3 audit/audit_viewer.py --metadata --limit 10
```

## Documentation

See [docs/AUDIT_SYSTEM.md](../docs/AUDIT_SYSTEM.md) for complete documentation.

## Features

- 📝 Structured JSON-based logging
- 🔄 Automatic daily log rotation
- 🔍 Powerful filtering and querying
- 📊 Built-in statistics and analysis
- 🎯 Session-based event grouping
- ⚡ Lightweight and performant
- 🛡️ Graceful error handling
