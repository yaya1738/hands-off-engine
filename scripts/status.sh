#!/bin/bash
# High-Level Status - What You Need To Know
# Everything else is handled automatically

clear

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          HANDS-OFF SYSTEM - HIGH-LEVEL STATUS             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

# High-level alerts (interviews, offers)
if [ -f "state/high_level_alerts.json" ]; then
    python3 << 'EOF'
import json
alerts = json.load(open("state/high_level_alerts.json"))
pending = [a for a in alerts.get("pending", []) if a.get("status") == "pending"]

if pending:
    print("🚨 ACTION REQUIRED:")
    print("="*60)
    for alert in pending:
        print(f"\n[{alert['priority'].upper()}] {alert['title']}")
        for key, value in alert['details'].items():
            print(f"  {key}: {value}")
    print("\n" + "="*60)
else:
    print("✅ No action required - System handling everything")
    print("="*60)
EOF
else
    echo "✅ No action required - System handling everything"
    echo "="*60
fi

echo

# Quick stats
echo "📊 AUTONOMOUS OPERATIONS:"
echo "="*60

if [ -f "state/job_agent_state.json" ]; then
    python3 -c "import json; s=json.load(open('state/job_agent_state.json')); print(f'Applications sent: {s.get(\"applications_sent\", 0)}'); print(f'Responses received: {s.get(\"responses_received\", 0)}'); print(f'Interviews scheduled: {s.get(\"interviews_scheduled\", 0)}')"
fi

if [ -f "state/money_printer.json" ]; then
    python3 -c "import json; s=json.load(open('state/money_printer.json')); print(f'Trading: {s.get(\"mode\", \"inactive\")}')" 2>/dev/null || echo "Trading: checking..."
fi

echo "="*60
echo

# System health
echo "🔧 SYSTEM STATUS:"
echo "="*60

if pgrep -f "backend_loop.py" > /dev/null; then
    echo "✓ Backend Loop: RUNNING"
else
    echo "✗ Backend Loop: STOPPED"
fi

if [ -f ".env.handsoff_email" ]; then
    if grep -q "HANDSOFF_APP_PASSWORD=.\+" ".env.handsoff_email" 2>/dev/null; then
        echo "✓ Email System: CONFIGURED"
    else
        echo "⚠ Email System: NEEDS SETUP"
        echo "  → See: applications/EMAIL_SETUP_GUIDE.md"
    fi
else
    echo "⚠ Email System: NEEDS SETUP"
fi

echo "="*60
echo

# What's next
echo "💡 YOUR ROLE:"
echo "="*60
echo "1. Review offers when they come (we'll alert you)"
echo "2. Make final accept/reject decision"
echo
echo "NO INTERVIEWS - Portfolio does the talking ✓"
echo "Everything else: AUTOMATED ✓"
echo "="*60
echo

# Quick commands
echo "📋 COMMANDS:"
echo "  bash scripts/status.sh          # This screen"
echo "  cat state/high_level_alerts.json  # See all alerts"
echo "  cat state/job_agent_state.json    # Full job status"
echo
