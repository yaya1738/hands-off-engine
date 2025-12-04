#!/bin/bash
# IMMEDIATE GMAIL SETUP
# This script makes it as easy as possible to enable Gmail automation

echo "═══════════════════════════════════════════════════════════"
echo "  GMAIL AUTOMATION - IMMEDIATE SETUP"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Step 1: Opening Google App Passwords page..."
echo ""

# Try to open browser
if command -v xdg-open &> /dev/null; then
    xdg-open "https://myaccount.google.com/apppasswords" 2>/dev/null &
elif command -v open &> /dev/null; then
    open "https://myaccount.google.com/apppasswords" 2>/dev/null &
else
    echo "Visit: https://myaccount.google.com/apppasswords"
fi

echo "Step 2: Generate app password"
echo "  • Sign in as: siegel.yaz@gmail.com"
echo "  • Select app: Mail"
echo "  • Select device: Other (type 'Hands-Off')"
echo "  • Click Generate"
echo "  • Copy the 16-character code"
echo ""
echo "Step 3: Enter it below (paste with Ctrl+Shift+V or right-click)"
echo ""
read -p "Paste your app password here: " APP_PASSWORD

# Remove spaces if user pastes with spaces
APP_PASSWORD=$(echo "$APP_PASSWORD" | tr -d ' ')

if [ -z "$APP_PASSWORD" ]; then
    echo "Error: No password provided"
    exit 1
fi

# Execute setup
cd /root/hands-off-engine
./scripts/gmail_setup.sh "$APP_PASSWORD"
