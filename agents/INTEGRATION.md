# Self-Healing Agent Integration Guide

## Overview

This document describes how the self-healing agent system integrates with the existing Hands-Off Engine coordination system.

## Integration Points

### 1. Audit Logging

All self-healing actions are automatically logged to the audit system:

```python
from audit.audit_logger import AuditLogger

# Agents automatically create audit loggers
audit_logger = AuditLogger(component="health_monitor")
audit_logger.log(
    event_type="health_check",
    event_data=results
)
```

Audit logs are written to: `logs/audit/audit_YYYY-MM-DD.jsonl`

### 2. Telegram Alerts

Critical events are sent via Telegram using environment variables:
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Your chat ID

The alert system gracefully degrades to stderr if Telegram is not configured.

### 3. State Management

Agents use the existing `state/` directory:
- `state/self_healing_state.json` - Self-healer state
- `state/watchdog_state.json` - Watchdog state
- `state/backups/YYYY-MM-DD/` - Daily backups

### 4. Coordination System Integration

The agents can coordinate with other AI agents via the coordination system:

```python
# Register agent in coordination system
from pathlib import Path
import json

coordination_file = Path("ai/coordination/status.json")

# Read current status
with open(coordination_file) as f:
    status = json.load(f)

# Add self-healing agent
if "self-healing-agent" not in status.get("active_agents", []):
    status["active_agents"].append("self-healing-agent")

# Add task
status["pending_tasks"].append({
    "id": "system-health-monitoring",
    "assigned_to": "self-healing-agent",
    "status": "ongoing",
    "description": "Continuous health monitoring and self-healing"
})

# Save
with open(coordination_file, 'w') as f:
    json.dump(status, f, indent=2)
```

## Daily Summary Integration

To include self-healing metrics in daily summaries:

```python
from pathlib import Path
import json
from datetime import datetime

def get_healing_summary(date=None):
    """Get self-healing summary for a date"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Read audit log
    audit_file = Path(f"logs/audit/audit_{date}.jsonl")
    if not audit_file.exists():
        return None
    
    summary = {
        "health_checks": 0,
        "healing_actions": 0,
        "backups_created": 0,
        "alerts_sent": 0,
        "escalations": 0
    }
    
    with open(audit_file) as f:
        for line in f:
            event = json.loads(line)
            
            if event.get("component") == "health_monitor":
                summary["health_checks"] += 1
            elif event.get("component") == "self_healer":
                summary["healing_actions"] += 1
            elif event.get("component") == "backup":
                if event.get("event_type") == "backup_created":
                    summary["backups_created"] += 1
            elif event.get("component") == "alerts":
                summary["alerts_sent"] += 1
            elif event.get("component") == "watchdog":
                if event.get("event_type") == "escalation":
                    summary["escalations"] += 1
    
    return summary

# Example usage in daily summary script
summary = get_healing_summary()
if summary:
    print(f"\n## Self-Healing Summary")
    print(f"- Health checks: {summary['health_checks']}")
    print(f"- Healing actions: {summary['healing_actions']}")
    print(f"- Backups created: {summary['backups_created']}")
    print(f"- Alerts sent: {summary['alerts_sent']}")
    print(f"- Escalations: {summary['escalations']}")
```

## Autonomous Operation

The self-healing system can operate autonomously:

1. **Systemd Service** (recommended for servers):
   ```bash
   sudo systemctl enable hands-off-watchdog
   sudo systemctl start hands-off-watchdog
   ```

2. **Cron** (recommended for Termux):
   ```bash
   # Add to crontab
   */5 * * * * cd ~/hands-off-engine && python3 agents/run_watchdog.py --once
   0 3 * * * cd ~/hands-off-engine && python3 agents/run_backup.py
   ```

## Monitoring the Self-Healing System

### Check System Status

```bash
# View today's audit log
tail -f logs/audit/audit_$(date +%Y-%m-%d).jsonl | grep -E "health_monitor|self_healer|watchdog"

# Check watchdog state
cat state/watchdog_state.json | jq .

# Check self-healer state
cat state/self_healing_state.json | jq .

# List recent backups
ls -lt state/backups/
```

### Query Healing Events

```python
from pathlib import Path
import json

def get_recent_healing_events(hours=24):
    """Get recent healing events"""
    from datetime import datetime, timedelta
    
    events = []
    cutoff = datetime.now() - timedelta(hours=hours)
    
    # Check today and yesterday
    for days_ago in [0, 1]:
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        audit_file = Path(f"logs/audit/audit_{date}.jsonl")
        
        if not audit_file.exists():
            continue
        
        with open(audit_file) as f:
            for line in f:
                event = json.loads(line)
                
                if event.get("component") in ["self_healer", "watchdog"]:
                    event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                    if event_time > cutoff:
                        events.append(event)
    
    return sorted(events, key=lambda e: e["timestamp"])

# Get last 24 hours of healing
events = get_recent_healing_events()
print(f"Healing events in last 24h: {len(events)}")
for event in events[-5:]:  # Show last 5
    print(f"  {event['timestamp']}: {event['event_type']}")
```

## Alerting Channels

The system supports multiple alerting channels:

1. **Telegram** (primary): Immediate notifications
2. **Audit Log** (always): Permanent record
3. **Stderr** (fallback): When Telegram unavailable

To add custom alerting:

```python
from agents.alerts import AlertSystem, AlertLevel

class CustomAlertSystem(AlertSystem):
    def _send_custom_alert(self, message: str) -> bool:
        # Your custom alerting logic
        # e.g., send email, post to webhook, etc.
        pass
```

## Escalation Process

When self-healing fails after multiple attempts:

1. **Alert sent via Telegram** with `CRITICAL` level
2. **Audit log updated** with escalation event
3. **Human intervention required** flag set
4. **Watchdog continues monitoring** but stops auto-healing that issue

Human can resolve by:
- Investigating root cause
- Manually fixing issue
- Restarting watchdog to reset failure counts

## Configuration Updates

To update thresholds or rules:

1. Edit `config/health_thresholds.json` or `config/healing_rules.json`
2. No restart needed - agents reload config on each cycle
3. Changes take effect within 5 minutes (next health check)

## Best Practices

1. **Monitor audit logs** regularly for patterns
2. **Set appropriate thresholds** for your environment
3. **Test healing rules** before enabling in production
4. **Keep backups** for at least 7 days
5. **Review escalations** promptly
6. **Update contact info** in Telegram config

## Troubleshooting

### Watchdog not healing issues
- Check `state/self_healing_state.json` for failure counts
- Check cooldown periods in `config/healing_rules.json`
- Check audit logs for error messages

### Backups failing
- Check disk space: `df -h`
- Check permissions: `ls -la state/backups/`
- Check audit logs for specific errors

### Alerts not received
- Verify environment variables: `echo $TELEGRAM_BOT_TOKEN`
- Test manually: `python3 -c "from agents.alerts import AlertSystem; AlertSystem().send_alert('test')"`
- Check Telegram bot status with @BotFather

## Security Considerations

1. **Backup files excluded from git** via `.gitignore`
2. **Sensitive data not logged** to audit
3. **Rate limiting prevents spam**
4. **Cooldown periods prevent loops**
5. **Atomic file operations** prevent corruption
6. **Max attempts prevent infinite loops**

## Future Enhancements

- [ ] ML-based anomaly detection
- [ ] Predictive healing
- [ ] Multi-node coordination
- [ ] Performance metrics dashboard
- [ ] Custom healing plugins
- [ ] Advanced escalation workflows
