#!/bin/bash
# Hands-Off Engine: Live Monitoring Dashboard
# Shows real-time status of the automated trading system

REPO_ROOT="/root/hands-off-engine"
cd "$REPO_ROOT"

# Colors for terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

while true; do
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         HANDS-OFF ENGINE - LIVE MONITORING                 ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${GREEN}📊 System Status${NC}"
    echo "─────────────────────────────────────────────────────────────"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "Mode: DRYRUN (safe)"
    echo

    # Check execution plan
    if [ -f "executor/execution_plan.json" ]; then
        echo -e "${GREEN}📋 Latest Execution Plan${NC}"
        echo "─────────────────────────────────────────────────────────────"
        python3 << 'PYEOF'
import json
from datetime import datetime

try:
    with open('executor/execution_plan.json') as f:
        plan = json.load(f)

    ts = plan.get('timestamp', 'unknown')
    if ts != 'unknown':
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        age_mins = (datetime.now().astimezone() - dt).total_seconds() / 60
        print(f"  Generated: {dt.strftime('%Y-%m-%d %H:%M:%S')} ({age_mins:.0f} min ago)")
    else:
        print(f"  Generated: {ts}")

    print(f"  Orders: {plan.get('total_orders', 0)}")
    print(f"  Total size: ${plan.get('total_size_usd', 0):.2f}")
    print(f"  DRYRUN: {'Yes' if plan.get('dryrun', True) else 'NO (LIVE!)'}")

    if age_mins > 120:
        print(f"\n  ⚠️  Warning: Plan is {age_mins/60:.1f} hours old")
except Exception as e:
    print(f"  Error reading plan: {e}")
PYEOF
    else
        echo "  No execution plan generated yet"
    fi
    echo

    # Check alpha signals
    if [ -f "state/polymarket-model.json" ]; then
        echo -e "${GREEN}🎯 Alpha Signals${NC}"
        echo "─────────────────────────────────────────────────────────────"
        python3 << 'PYEOF'
import json
from datetime import datetime

try:
    with open('state/polymarket-model.json') as f:
        model = json.load(f)

    gen_at = model.get('generated_at', 'unknown')
    if gen_at != 'unknown':
        dt = datetime.fromisoformat(gen_at.replace('Z', '+00:00'))
        age_mins = (datetime.now().astimezone() - dt).total_seconds() / 60
        print(f"  Generated: {dt.strftime('%Y-%m-%d %H:%M:%S')} ({age_mins:.0f} min ago)")
    else:
        print(f"  Generated: {gen_at}")

    print(f"  Markets analyzed: {model.get('total_markets_analyzed', 0)}")
    print(f"  Markets selected: {model.get('markets_selected', 0)}")

    # Show top 3 opportunities
    markets = model.get('markets', [])[:3]
    if markets:
        print("\n  Top opportunities:")
        for i, m in enumerate(markets, 1):
            edge = m.get('model_edge', 0) * 100
            conf = m.get('model_confidence', 0) * 100
            q = m.get('question', 'Unknown')[:45]
            print(f"    {i}. {q}...")
            print(f"       Edge: {edge:.1f}%, Confidence: {conf:.0f}%")
except Exception as e:
    print(f"  Error reading signals: {e}")
PYEOF
    else
        echo "  No alpha signals generated yet"
    fi
    echo

    # Check recent logs
    if [ -f "/var/log/hands-off-engine.log" ]; then
        echo -e "${GREEN}📝 Recent Activity${NC}"
        echo "─────────────────────────────────────────────────────────────"
        tail -5 /var/log/hands-off-engine.log 2>/dev/null || echo "  No logs yet"
    fi
    echo

    # Check cron status
    echo -e "${GREEN}⏰ Automation Status${NC}"
    echo "─────────────────────────────────────────────────────────────"
    if crontab -l 2>/dev/null | grep -q "run_and_notify"; then
        echo -e "  Cron: ${GREEN}✓ Active${NC}"
        crontab -l | grep run_and_notify | head -1 | sed 's/^/  Schedule: /'
    else
        echo -e "  Cron: ${RED}✗ Not configured${NC}"
    fi
    echo

    # Next update countdown
    echo -e "${YELLOW}Updating in 10 seconds... (Ctrl+C to exit)${NC}"
    sleep 10
done
