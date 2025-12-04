#!/bin/bash
# Quick Telegram Setup

set -e
cd /root/hands-off-engine

echo "═══════════════════════════════════════════════════════════"
echo "  TELEGRAM BOT SETUP"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./scripts/setup_telegram.sh BOT_TOKEN CHAT_ID"
    echo ""
    echo "Quick Start:"
    echo "1. Open Telegram"
    echo "2. Search: @BotFather"
    echo "3. Send: /newbot"
    echo "4. Copy bot token"
    echo ""
    echo "5. Search: @userinfobot"
    echo "6. Send: /start"
    echo "7. Copy your chat ID"
    echo ""
    echo "Then run:"
    echo "  ./scripts/setup_telegram.sh YOUR_BOT_TOKEN YOUR_CHAT_ID"
    echo ""
    exit 1
fi

BOT_TOKEN="$1"
CHAT_ID="$2"

echo "Configuring Telegram bot..."

cat > .env.handsoff_telegram << EOF
TELEGRAM_BOT_TOKEN="$BOT_TOKEN"
TELEGRAM_CHAT_ID="$CHAT_ID"
EOF

echo "✓ Configuration saved"
echo ""

echo "Testing connection..."
python3 autonomous/telegram_notifier.py --test

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Telegram configured successfully!"
    echo ""
    echo "Check your Telegram - you should have received a test message"
    echo ""

    echo "Starting messaging bridge..."
    pkill -f messaging_bridge.py 2>/dev/null || true

    nohup python3 autonomous/messaging_bridge.py --continuous > logs/messaging_bridge.log 2>&1 &

    PID=$!
    echo "✓ Messaging bridge started (PID: $PID)"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  TELEGRAM: ACTIVE"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "You'll now receive notifications about:"
    echo "  • Trading wins/losses"
    echo "  • Bounty updates"
    echo "  • System health"
    echo ""
    echo "Send /status to your bot to test commands"
    echo ""
    echo "Monitor: tail -f logs/messaging_bridge.log"
    echo ""
else
    echo ""
    echo "✗ Setup failed"
    echo "Check your bot token and chat ID"
    exit 1
fi
