#!/bin/bash
# Hands-Off Engine: Complete Pipeline with Notifications
#
# This script runs the full trading pipeline and sends notifications:
# 1. Validate state files (fail-safe)
# 2. Sync Polymarket data → Alpha signals
# 3. Decider plans actions
# 4. Executor validates/executes
# 5. Notifications sent to Telegram/IFTTT
#
# Designed to be run via cron for automated trading signals.
# Includes retry logic and state file validation for autonomous operation.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Export flags for autonomous mode detection
export HANDS_OFF_AUTONOMOUS=1
export CRON_JOB=1

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY=30

log() {
    echo "[$(date -Iseconds)] $1"
}

# State file validation and recovery
validate_state_files() {
    log "Validating state files..."

    # Required state files with defaults
    declare -A STATE_FILES
    STATE_FILES["state/trading_mode.json"]='{"live_trading_enabled":false,"reason":"auto_created","auto_paused":false}'
    STATE_FILES["state/risk_profile.json"]='{"phase":"cautious","max_position_usd":50,"confidence_threshold":0.6}'

    for file in "${!STATE_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            log "WARN: Missing $file, creating with defaults"
            mkdir -p "$(dirname "$file")"
            echo "${STATE_FILES[$file]}" > "$file"
        else
            # Validate JSON is parseable
            if ! python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
                log "ERROR: Corrupted $file, restoring from backup or defaults"
                if [ -f "${file}.backup" ]; then
                    cp "${file}.backup" "$file"
                else
                    echo "${STATE_FILES[$file]}" > "$file"
                fi
            fi
        fi
    done

    log "✓ State files validated"
}

# Run with retry logic
run_with_retry() {
    local cmd="$1"
    local attempt=1

    while [ $attempt -le $MAX_RETRIES ]; do
        log "Attempt $attempt/$MAX_RETRIES: $cmd"

        if eval "$cmd"; then
            return 0
        fi

        local exit_code=$?
        log "WARN: Command failed with exit code $exit_code"

        if [ $attempt -lt $MAX_RETRIES ]; then
            log "Retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
        fi

        attempt=$((attempt + 1))
    done

    log "ERROR: All $MAX_RETRIES attempts failed"
    return 1
}

log "Starting Hands-Off Engine pipeline..."

# Step 0: Validate state files
validate_state_files

# Step 0.5: Get dynamic bankroll if not specified
get_bankroll() {
    # Check if --bankroll was provided in args
    if echo "$*" | grep -q "\-\-bankroll"; then
        return  # Use provided bankroll
    fi

    # Query from finance.json or risk_profile.json
    BANKROLL=$(python3 -c "
import json
from pathlib import Path
repo = Path('$REPO_ROOT')

# Try finance.json first (actual balance)
finance_file = repo / 'termux-hands-off' / 'state' / 'finance.json'
if finance_file.exists():
    data = json.load(open(finance_file))
    pm_balance = data.get('balances', {}).get('polymarket_usd', 0)
    if pm_balance > 0:
        print(int(pm_balance))
        exit(0)

# Fall back to risk profile scale factor
risk_file = repo / 'state' / 'risk_profile.json'
if risk_file.exists():
    profile = json.load(open(risk_file))
    # Base bankroll scaled by phase
    base = 500
    scale = profile.get('scale_factor', 1.0)
    print(int(base * scale))
    exit(0)

# Default fallback
print(500)
" 2>/dev/null || echo "500")

    log "Dynamic bankroll: \$${BANKROLL}"
    EXTRA_ARGS="--bankroll $BANKROLL"
}

get_bankroll "$@"

# Step 1: Run the full pipeline with retries
if ! run_with_retry "python3 scripts/run_pipeline.py $* $EXTRA_ARGS"; then
    log "ERROR: Pipeline failed after $MAX_RETRIES attempts"
    # Send failure notification
    python3 -c "
import sys
sys.path.insert(0, 'termux-hands-off/agent')
try:
    from notify import send_notification
    send_notification('❌ Pipeline failed after $MAX_RETRIES retries', 'hands-off')
except: pass
" 2>/dev/null || true
    exit 1
fi

# Check if execution plan was generated
if [ ! -f "executor/execution_plan.json" ]; then
    echo "[INFO] No execution plan generated (no actions passed safety checks)"
    exit 0
fi

# Send notification
echo "[$(date)] Sending notification..."
python3 termux-hands-off/agent/notify_execution_plan.py
NOTIFY_EXIT=$?

if [ $NOTIFY_EXIT -eq 0 ]; then
    echo "[$(date)] ✓ Pipeline completed and notification sent"
else
    echo "[$(date)] ✗ Pipeline completed but notification failed (exit code $NOTIFY_EXIT)"
    exit $NOTIFY_EXIT
fi

# Log performance metrics
python3 scripts/track_performance.py
echo "[$(date)] ✓ Performance metrics logged"

exit 0
