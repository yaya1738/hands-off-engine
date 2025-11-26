#!/bin/bash
# Hands-Off Engine: Health Check & Alerting
# Monitors system health and sends alerts if issues detected

REPO_ROOT="/root/hands-off-engine"
cd "$REPO_ROOT"

ALERT_TELEGRAM=true  # Set to false to disable alerts
MAX_AGE_HOURS=2      # Alert if data is older than this

# Function to send alert via Telegram
send_alert() {
    local message="$1"
    if [ "$ALERT_TELEGRAM" = true ]; then
        echo "[$(date)] ALERT: $message"
        echo "$message" | python3 termux-hands-off/agent/notify.py 2>/dev/null || \
            echo "[$(date)] Failed to send alert"
    else
        echo "[$(date)] ALERT (not sent): $message"
    fi
}

echo "[$(date)] Running health checks..."

# Check 1: Execution plan exists and is recent
if [ ! -f "executor/execution_plan.json" ]; then
    send_alert "⚠️ No execution plan found. Pipeline may not be running."
    exit 1
fi

# Check 2: Execution plan age
AGE_MINS=$(python3 << 'PYEOF'
import json
from datetime import datetime, timezone
try:
    with open('executor/execution_plan.json') as f:
        plan = json.load(f)
    # Support both 'as_of' (new format) and 'timestamp' (old format)
    ts = plan.get('as_of') or plan.get('timestamp', '')
    if ts:
        # Handle both formats: with/without timezone
        ts_clean = ts.replace('Z', '+00:00')
        dt = datetime.fromisoformat(ts_clean)
        # If naive datetime, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_mins = (datetime.now(timezone.utc) - dt).total_seconds() / 60
        print(int(age_mins))
    else:
        print(999999)
except Exception as e:
    print(999999, file=__import__('sys').stderr)
    print(f"Error: {e}", file=__import__('sys').stderr)
PYEOF
)

MAX_AGE_MINS=$((MAX_AGE_HOURS * 60))
if [ "$AGE_MINS" -gt "$MAX_AGE_MINS" ]; then
    send_alert "⚠️ Execution plan is ${AGE_MINS} minutes old (max: ${MAX_AGE_MINS}). Pipeline may be stuck."
    exit 1
fi

# Check 3: Alpha signals exist
if [ ! -f "state/polymarket-model.json" ]; then
    send_alert "⚠️ No alpha signals found. Data sync may have failed."
    exit 1
fi

# Check 4: Cron is configured
if ! crontab -l 2>/dev/null | grep -q "run_and_notify"; then
    send_alert "⚠️ Cron job not configured. Automation is disabled."
    exit 1
fi

# Check 5: Log file writeable
if [ ! -w "/var/log/hands-off-engine.log" ]; then
    echo "[$(date)] WARNING: Cannot write to log file"
fi

# All checks passed
echo "[$(date)] ✓ All health checks passed"
echo "  Execution plan age: ${AGE_MINS} minutes"
echo "  Status: Healthy"

exit 0
