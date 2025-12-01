#!/bin/bash
# Enable Automated Trading for Hands-Off Engine
#
# This script sets up automated trading with:
# 1. Actual balance-based position sizing
# 2. Intelligent alpha engine (LLM-based)
# 3. Cron automation
# 4. Safety checks and monitoring
#
# Run this script when ready to enable automated money generation.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "=" "======================================================================"
echo "  Hands-Off Engine: Enable Automated Trading"
echo "======================================================================"
echo

# Step 1: Check current balance
echo "Step 1: Checking current balance..."
BALANCE=$(python3 -c "
import json
from pathlib import Path

financial_state = Path('state/financial_state.json')
if financial_state.exists():
    with open(financial_state) as f:
        state = json.load(f)
    print(state.get('balance', 0))
else:
    print(0)
" 2>/dev/null || echo "0")

echo "  Current balance: \$${BALANCE}"

if (( $(echo "$BALANCE < 1.0" | bc -l) )); then
    echo "  ⚠️  Balance too low for trading (< \$1.00)"
    echo "  Recommendation: Wait for positions to resolve or add funds"
    exit 1
fi

# Step 2: Check LIVE_TRADING_ENABLED setting
echo
echo "Step 2: Checking trading mode configuration..."

if grep -q "^LIVE_TRADING_ENABLED=1" .env.polymarket 2>/dev/null; then
    echo "  ✓ LIVE_TRADING_ENABLED=1 in .env.polymarket"
    LIVE_MODE="--live"
else
    echo "  ℹ️  LIVE_TRADING_ENABLED not set to 1"
    echo "  Running in DRYRUN mode (no real trades)"
    LIVE_MODE=""
fi

# Step 3: Create trading mode state file for autonomous operation
echo
echo "Step 3: Creating trading mode state file..."

mkdir -p state

cat > state/trading_mode.json <<EOF
{
  "live_trading_enabled": $([ -n "$LIVE_MODE" ] && echo "true" || echo "false"),
  "reason": "automated_trading_enabled_$(date +%Y%m%d_%H%M%S)",
  "auto_paused": false,
  "enabled_at": "$(date -Iseconds)",
  "min_balance": 1.0,
  "max_position_usd": 50.0
}
EOF

echo "  ✓ Created state/trading_mode.json"

# Step 4: Test pipeline execution
echo
echo "Step 4: Testing pipeline execution..."

python3 scripts/run_pipeline.py \
    --intelligent \
    $LIVE_MODE \
    --save-log

if [ $? -ne 0 ]; then
    echo "  ✗ Pipeline test failed"
    echo "  Please check errors above and fix before enabling cron"
    exit 1
fi

echo "  ✓ Pipeline test successful"

# Step 5: Set up cron job
echo
echo "Step 5: Setting up cron automation..."

# Generate cron command
CRON_CMD="*/30 * * * * cd $REPO_ROOT && bash scripts/run_and_notify.sh --intelligent $LIVE_MODE >> logs/cron.log 2>&1"

echo "  Proposed cron job (runs every 30 minutes):"
echo "  $CRON_CMD"
echo

read -p "  Add this cron job? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "  Skipping cron setup"
    echo "  You can manually add it later with:"
    echo "  crontab -e"
    echo "  Then add: $CRON_CMD"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "  ✓ Cron job added"
    echo "  Trading will run every 30 minutes"
fi

# Step 6: Summary
echo
echo "======================================================================"
echo "  Setup Complete!"
echo "======================================================================"
echo
echo "Configuration Summary:"
echo "  Balance: \$${BALANCE}"
echo "  Mode: $([ -n "$LIVE_MODE" ] && echo "LIVE (real trades)" || echo "DRYRUN (simulated)")"
echo "  Alpha: Intelligent (LLM-based)"
echo "  Max position: \$50"
echo "  Frequency: Every 30 minutes"
echo
echo "Next steps:"
echo "  1. Monitor logs: tail -f logs/cron.log"
echo "  2. Check execution plans: cat executor/execution_plan.json"
echo "  3. View balance: cat state/financial_state.json"
echo
echo "To disable automated trading:"
echo "  crontab -e  # Remove the line"
echo "  rm state/trading_mode.json"
echo
echo "======================================================================"
