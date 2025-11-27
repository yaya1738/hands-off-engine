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

# Check 6: GitHub API rate limit status
GH_STATUS=$(python3 << 'PYEOF'
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from scripts.github_client import GitHubClient
    client = GitHubClient()
    status = client.get_auth_status()
    if status["remaining"] == 0:
        print("RATE_LIMITED")
    elif not status["authenticated"]:
        print("UNAUTHENTICATED")
    elif status["remaining"] < 500:
        print("LOW")
    else:
        print("OK")
except Exception as e:
    print("ERROR", file=sys.stderr)
    print(f"GitHub check failed: {e}", file=sys.stderr)
PYEOF
)

case "$GH_STATUS" in
    "RATE_LIMITED")
        send_alert "🔴 GitHub API rate limited! Configure GITHUB_TOKEN."
        ;;
    "UNAUTHENTICATED")
        echo "[$(date)] WARNING: GitHub API unauthenticated (60 req/hour limit)"
        ;;
    "LOW")
        echo "[$(date)] WARNING: GitHub API rate limit running low (<500 remaining)"
        ;;
    "OK")
        echo "[$(date)] ✓ GitHub API: Authenticated with sufficient rate limit"
        ;;
    *)
        echo "[$(date)] WARNING: Could not check GitHub API status"
        ;;
esac

# All checks passed
echo "[$(date)] ✓ All health checks passed"
echo "  Execution plan age: ${AGE_MINS} minutes"
echo "  Status: Healthy"

exit 0
