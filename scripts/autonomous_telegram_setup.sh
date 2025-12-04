#!/bin/bash
# Autonomous Telegram Setup - Complete hands-off bot creation

set -e
cd /root/hands-off-engine

echo "═══════════════════════════════════════════════════════════"
echo "  AUTONOMOUS TELEGRAM BOT SETUP"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "This script will create a Telegram bot AUTONOMOUSLY."
echo ""
echo "Choose your method:"
echo ""
echo "1. WEB AUTOMATION (Recommended - simpler)"
echo "   - Opens browser"
echo "   - You scan QR code once"
echo "   - System does rest automatically"
echo "   - No API credentials needed"
echo ""
echo "2. CLIENT API (Advanced - fully headless)"
echo "   - Requires Telegram API credentials"
echo "   - Fully automated after setup"
echo "   - Can run without browser"
echo ""

read -p "Choose method (1 or 2): " METHOD

if [ "$METHOD" == "1" ]; then
    echo ""
    echo "Installing dependencies..."
    pip install playwright requests >/dev/null 2>&1 || true
    playwright install chromium >/dev/null 2>&1 || true

    echo ""
    echo "Starting web automation..."
    echo "A browser will open - scan QR code or login"
    echo ""

    python3 autonomous/telegram_bot_creator_web.py --create

elif [ "$METHOD" == "2" ]; then
    echo ""
    echo "You need Telegram API credentials."
    echo ""
    echo "Get them from: https://my.telegram.org"
    echo "  1. Login with your phone"
    echo "  2. Go to 'API development tools'"
    echo "  3. Create application"
    echo "  4. Copy API ID and Hash"
    echo ""

    read -p "API ID: " API_ID
    read -p "API Hash: " API_HASH
    read -p "Phone (+1234567890): " PHONE

    cat > .env.telegram_api << EOF
TELEGRAM_API_ID="$API_ID"
TELEGRAM_API_HASH="$API_HASH"
TELEGRAM_PHONE="$PHONE"
EOF

    echo ""
    echo "Installing dependencies..."
    pip install telethon requests >/dev/null 2>&1 || true

    echo ""
    echo "Creating bot..."
    echo "You may receive verification code via Telegram"
    echo ""

    python3 autonomous/telegram_bot_creator.py --setup

else
    echo "Invalid choice"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  SETUP COMPLETE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Your Telegram bot is now active!"
echo "Open Telegram and send /start to your bot"
echo ""
