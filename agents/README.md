# Self-Healing Agent System

Autonomous health monitoring and self-repair capabilities for Hands-Off Engine.

## Components

### 1. Health Monitor (`health_monitor.py`)

Monitors system health every 5 minutes:
- API connectivity (Polymarket, etc.)
- State file integrity
- Cron job status
- System resources (disk, memory)
- Process status

**Usage:**
```python
from agents.health_monitor import HealthMonitor

monitor = HealthMonitor()
results = monitor.run_health_check()
print(results['overall_status'])
```

### 2. Self-Healing Agent (`self_healer.py`)

Automatically fixes common issues:
- Restart failed processes
- Restore corrupted state files from backups
- Clear stale locks
- Reset rate limit counters
- Retry failed operations
- Cleanup temporary files

**Usage:**
```python
from agents.self_healer import SelfHealer

healer = SelfHealer()
success = healer.auto_heal({
    "type": "process_not_running",
    "details": {"process_name": "crond"}
})
```

### 3. Backup System (`backup.py`)

Manages state file backups:
- Daily backups to `state/backups/YYYY-MM-DD/`
- Keeps 7 days of backups (configurable)
- Verifies backup integrity
- Restores from backup on demand

**Usage:**
```python
from agents.backup import BackupSystem

backup = BackupSystem()
backup.create_daily_backup()
backup.cleanup_old_backups()

# Restore file
backup.restore_from_backup("polymarket-model.json")
```

### 4. Alert System (`alerts.py`)

Sends alerts via Telegram:
- Critical errors
- Extended downtime
- Unusual activity
- Health check failures

**Usage:**
```python
from agents.alerts import AlertSystem, AlertLevel

alerts = AlertSystem()
alerts.send_alert(
    "Service restarted",
    level=AlertLevel.INFO
)
```

### 5. Watchdog (`watchdog.py`)

Orchestrates all monitoring and healing:
- Monitors agent heartbeats
- Runs health checks
- Triggers self-healing
- Restarts dead agents
- Escalates persistent issues

**Usage:**
```bash
# Run once (for cron)
python3 agents/run_watchdog.py --once

# Run continuously (for systemd)
python3 agents/run_watchdog.py --interval 300
```

## Configuration

### `config/health_thresholds.json`

Define thresholds for health checks:
```json
{
  "health_check_interval_seconds": 300,
  "api_timeout_seconds": 30,
  "max_consecutive_failures": 3,
  "disk_usage_warning_percent": 80,
  "disk_usage_critical_percent": 90,
  "monitored_state_files": [
    "state/polymarket-model.json",
    "state/knowledge.json"
  ]
}
```

### `config/healing_rules.json`

Define auto-healing rules:
```json
{
  "auto_healing_enabled": true,
  "rules": [
    {
      "id": "restart_process",
      "enabled": true,
      "condition": "process_not_running",
      "action": "restart",
      "max_attempts": 3
    }
  ]
}
```

## Installation

### Dependencies
```bash
pip3 install -r agents/requirements.txt
```

### Systemd Service (Linux)
```bash
# Copy service file
sudo cp agents/hands-off-watchdog.service /etc/systemd/system/

# Edit paths in service file
sudo nano /etc/systemd/system/hands-off-watchdog.service

# Enable and start
sudo systemctl enable hands-off-watchdog
sudo systemctl start hands-off-watchdog

# Check status
sudo systemctl status hands-off-watchdog
```

### Cron (Termux or Linux)
```bash
# Add to crontab
crontab -e

# Run watchdog every 5 minutes
*/5 * * * * cd /path/to/hands-off-engine && python3 agents/run_watchdog.py --once

# Daily backup at 3 AM
0 3 * * * cd /path/to/hands-off-engine && python3 agents/run_backup.py
```

## Integration with Coordination System

The agents automatically integrate with the existing coordination system:

1. **Audit Logging**: All healing actions are logged to audit logs
2. **Telegram Alerts**: Critical events sent via Telegram
3. **State Management**: Uses existing state directory structure

### Coordination System Integration

The agents can register with the coordination system:

```python
from agents.watchdog import Watchdog

watchdog = Watchdog()

# Register heartbeat
watchdog.register_heartbeat("my_agent")

# Run watch cycle
results = watchdog.run_watch_cycle()
```

## Daily Summary Reporting

To add self-healing info to daily summaries, query the audit logs:

```python
from pathlib import Path
import json
from datetime import datetime, timedelta

# Read today's healing events
audit_dir = Path("logs/audit")
today = datetime.now().strftime("%Y-%m-%d")
audit_file = audit_dir / f"audit_{today}.jsonl"

healing_events = []
if audit_file.exists():
    with open(audit_file) as f:
        for line in f:
            event = json.loads(line)
            if event.get("component") in ["health_monitor", "self_healer", "watchdog"]:
                healing_events.append(event)

print(f"Self-healing interventions today: {len(healing_events)}")
```

## Testing

### Manual Testing

```bash
# Test health monitor
python3 -c "from agents.health_monitor import HealthMonitor; import json; print(json.dumps(HealthMonitor().run_health_check(), indent=2))"

# Test backup system
python3 agents/run_backup.py

# Test watchdog (single cycle)
python3 agents/run_watchdog.py --once
```

### Unit Tests

```bash
# Run unit tests (if pytest is available)
pytest tests/agents/
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       Watchdog                          │
│  - Orchestrates monitoring and healing                  │
│  - Monitors agent heartbeats                            │
│  - Escalates persistent issues                          │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┬──────────────┐
        │                   │              │
        ▼                   ▼              ▼
┌───────────────┐   ┌──────────────┐   ┌─────────────┐
│ Health        │   │ Self-Healer  │   │ Backup      │
│ Monitor       │──▶│              │──▶│ System      │
│               │   │              │   │             │
└───────┬───────┘   └──────┬───────┘   └─────────────┘
        │                  │
        └──────────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │ Alert System  │
           │ (Telegram)    │
           └───────────────┘
```

## Security Considerations

1. **Rate Limiting**: Alerts are rate-limited to prevent spam
2. **Cooldown Periods**: Healing actions have cooldown periods
3. **Max Attempts**: Limited attempts before escalation
4. **Audit Trail**: All actions logged to audit
5. **Backup Integrity**: Backups verified before use
6. **Atomic Operations**: State files updated atomically

## Troubleshooting

### Watchdog not running
```bash
# Check logs
journalctl -u hands-off-watchdog -f

# Or check cron logs
tail -f /tmp/watchdog.log
```

### Alerts not being sent
1. Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables
2. Check network connectivity
3. Alerts fallback to stderr if Telegram unavailable

### Backup failures
1. Check disk space
2. Check permissions on `state/backups/` directory
3. Check audit logs for details

## Future Enhancements

- [ ] Machine learning-based anomaly detection
- [ ] Predictive healing (heal before failure)
- [ ] Multi-node coordination
- [ ] Performance metrics collection
- [ ] Advanced escalation rules
- [ ] Integration with external monitoring systems
