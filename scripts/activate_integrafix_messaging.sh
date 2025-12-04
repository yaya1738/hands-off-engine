#!/bin/bash
# Activate INTEGRAFIX Messaging Integration

set -e
cd /root/hands-off-engine

echo "═══════════════════════════════════════════════════════════"
echo "  INTEGRAFIX MESSAGING ACTIVATION"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if Telegram is configured
if ! grep -q 'TELEGRAM_BOT_TOKEN="[^"]' .env.handsoff_telegram 2>/dev/null; then
    echo "⚠️  Telegram not configured yet"
    echo ""
    echo "Run this first:"
    echo "  ./scripts/autonomous_telegram_setup.sh"
    echo ""
    exit 1
fi

echo "✓ Telegram configured"
echo ""

# Start messaging bridge if not running
if ! pgrep -f "messaging_bridge.py --continuous" > /dev/null; then
    echo "Starting messaging bridge..."
    nohup python3 autonomous/messaging_bridge.py --continuous > logs/messaging_bridge.log 2>&1 &
    BRIDGE_PID=$!
    echo "✓ Messaging bridge started (PID: $BRIDGE_PID)"
else
    BRIDGE_PID=$(pgrep -f "messaging_bridge.py --continuous")
    echo "✓ Messaging bridge already running (PID: $BRIDGE_PID)"
fi

echo ""

# Start INTEGRAFIX hooks if not running
if ! pgrep -f "integrafix_messaging_hooks.py --continuous" > /dev/null; then
    echo "Starting INTEGRAFIX messaging hooks..."
    nohup python3 autonomous/integrafix_messaging_hooks.py --continuous > logs/integrafix_hooks.log 2>&1 &
    HOOKS_PID=$!
    echo "✓ INTEGRAFIX hooks started (PID: $HOOKS_PID)"
else
    HOOKS_PID=$(pgrep -f "integrafix_messaging_hooks.py --continuous")
    echo "✓ INTEGRAFIX hooks already running (PID: $HOOKS_PID)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  INTEGRAFIX MESSAGING: FULLY ACTIVE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Notifications enabled for:"
echo "  ✓ Trading decisions (Money Printer)"
echo "  ✓ Trade executions (INTEGRAFIX Executor)"
echo "  ✓ Trade wins (Outcome Tracker)"
echo "  ✓ PR status changes (Bounty Monitor)"
echo "  ✓ System health (Self Healer)"
echo "  ✓ Email processing (Gmail Handler)"
echo "  ✓ ABCFC decisions (Master ABCFC)"
echo ""
echo "Processes:"
echo "  Messaging Bridge: PID $BRIDGE_PID"
echo "  INTEGRAFIX Hooks: PID $HOOKS_PID"
echo ""
echo "Logs:"
echo "  tail -f logs/messaging_bridge.log"
echo "  tail -f logs/integrafix_hooks.log"
echo ""
echo "Send test notification:"
echo "  python3 integrafix/messaging_integration.py"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Your phone is now your INTEGRAFIX dashboard."
echo ""
