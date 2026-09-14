#!/bin/bash
# Quick Telegram token installer
# Usage: bash scripts/install_telegram_token.sh BOT_TOKEN CHAT_ID

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: bash scripts/install_telegram_token.sh BOT_TOKEN CHAT_ID"
    echo ""
    echo "Get these from:"
    echo "  1. Bot token: @BotFather → /mybots → API Token"
    echo "  2. Chat ID: @userinfobot → send any message → copy the ID"
    exit 1
fi

BOT_TOKEN="$1"
CHAT_ID="$2"

mkdir -p ~/.codex
cat > ~/.codex/telegram-bridge.json << JSON
{
    "botToken": "$BOT_TOKEN",
    "chatIds": [$CHAT_ID]
}
JSON

echo "✅ Telegram bridge configured"
echo "   Token: ${BOT_TOKEN:0:10}..."
echo "   Chat ID: $CHAT_ID"
echo ""
echo "Testing connection..."
cd /root/hands-off-engine
python3 scripts/telegram_bridge.py check
