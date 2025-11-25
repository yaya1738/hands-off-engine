#!/bin/bash
# Telegram Bot Setup - Interactive Script
# This will guide you through setting up the Telegram bot in 5 minutes

set -e

echo "=================================="
echo "🤖 TELEGRAM BOT SETUP"
echo "=================================="
echo ""
echo "This takes 5 minutes. I'll guide you through each step."
echo ""

# Check if already configured
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    echo "✅ Telegram is already configured!"
    echo ""
    echo "Your bot token: ${TELEGRAM_BOT_TOKEN:0:10}..."
    echo "Your chat ID: $TELEGRAM_CHAT_ID"
    echo ""
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [ "$reconfigure" != "y" ] && [ "$reconfigure" != "Y" ]; then
        echo "Keeping existing configuration."
        exit 0
    fi
fi

echo "=================================="
echo "STEP 1: Create Bot (2 minutes)"
echo "=================================="
echo ""
echo "1. Open Telegram on your phone"
echo "2. Search for: @BotFather"
echo "3. Send this message: /newbot"
echo "4. Follow prompts:"
echo "   - Bot name: Hands Off Engine Bot"
echo "   - Username: something like 'yourname_handsfoff_bot'"
echo "5. BotFather will give you a TOKEN"
echo "   (looks like: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)"
echo ""
read -p "Press ENTER when you have your token ready..."
echo ""
read -p "Paste your bot token here: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ No token provided. Exiting."
    exit 1
fi

echo ""
echo "✅ Bot token received"
echo ""

echo "=================================="
echo "STEP 2: Get Your Chat ID (1 minute)"
echo "=================================="
echo ""
echo "1. In Telegram, search for: @userinfobot"
echo "2. Send any message to it (like 'hi')"
echo "3. It will reply with your chat ID"
echo "   (looks like: 123456789)"
echo ""
read -p "Press ENTER when you have your chat ID ready..."
echo ""
read -p "Paste your chat ID here: " CHAT_ID

if [ -z "$CHAT_ID" ]; then
    echo "❌ No chat ID provided. Exiting."
    exit 1
fi

echo ""
echo "✅ Chat ID received"
echo ""

echo "=================================="
echo "STEP 3: Saving Configuration"
echo "=================================="
echo ""

# Save to .bashrc for persistence
if ! grep -q "TELEGRAM_BOT_TOKEN" ~/.bashrc; then
    echo "export TELEGRAM_BOT_TOKEN=\"$BOT_TOKEN\"" >> ~/.bashrc
    echo "✅ Added TELEGRAM_BOT_TOKEN to ~/.bashrc"
else
    # Update existing
    sed -i "s|export TELEGRAM_BOT_TOKEN=.*|export TELEGRAM_BOT_TOKEN=\"$BOT_TOKEN\"|" ~/.bashrc
    echo "✅ Updated TELEGRAM_BOT_TOKEN in ~/.bashrc"
fi

if ! grep -q "TELEGRAM_CHAT_ID" ~/.bashrc; then
    echo "export TELEGRAM_CHAT_ID=\"$CHAT_ID\"" >> ~/.bashrc
    echo "✅ Added TELEGRAM_CHAT_ID to ~/.bashrc"
else
    # Update existing
    sed -i "s|export TELEGRAM_CHAT_ID=.*|export TELEGRAM_CHAT_ID=\"$CHAT_ID\"|" ~/.bashrc
    echo "✅ Updated TELEGRAM_CHAT_ID in ~/.bashrc"
fi

# Export for current session
export TELEGRAM_BOT_TOKEN="$BOT_TOKEN"
export TELEGRAM_CHAT_ID="$CHAT_ID"

echo ""
echo "✅ Configuration saved permanently"
echo ""

echo "=================================="
echo "STEP 4: Testing Connection"
echo "=================================="
echo ""
echo "Testing if bot can send messages..."
echo ""

cd /root/hands-off-engine

# Test by sending a message
python3 << 'PYEOF'
import os
import sys
sys.path.insert(0, '/root/hands-off-engine')

from telegram.telegram_command_bot import TelegramCommandBot

try:
    bot = TelegramCommandBot()
    result = bot.send_message(
        "✅ **Telegram Bot Connected!**\n\n"
        "Your Hands-Off Engine bot is now active.\n\n"
        "Try these commands:\n"
        "• /status - System status\n"
        "• /metrics - Performance data\n"
        "• /health - Health check\n"
        "• /help - All commands"
    )
    if result:
        print("✅ Test message sent successfully!")
        print("   Check your Telegram - you should see a message from your bot")
    else:
        print("⚠️  Message may not have been sent")
        print("   Check your tokens are correct")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ SETUP COMPLETE!"
    echo "=================================="
    echo ""
    echo "Your bot is ready! Go to Telegram and:"
    echo ""
    echo "1. Find your bot (search for the name you gave it)"
    echo "2. Send: /status"
    echo "3. You should get a response!"
    echo ""
    echo "Available commands:"
    echo "  /status  - System status"
    echo "  /metrics - Performance metrics"
    echo "  /health  - Health check"
    echo "  /pending - Pending approvals"
    echo "  /help    - All commands"
    echo ""
    echo "You can now control everything from your phone!"
    echo ""
else
    echo ""
    echo "⚠️  Setup completed but test failed."
    echo "Your tokens are saved. Try running:"
    echo "  python3 telegram/telegram_command_bot.py"
    echo ""
fi
