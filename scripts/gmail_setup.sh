#!/bin/bash
# Gmail Setup - One Command Execution
# Usage: ./scripts/gmail_setup.sh YOUR_16_CHAR_APP_PASSWORD

set -e

cd /root/hands-off-engine

if [ -z "$1" ]; then
    echo "═══════════════════════════════════════════════════════════"
    echo "  GMAIL SETUP - EXECUTIVE MODE"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Get your app password:"
    echo "  1. Visit: https://myaccount.google.com/apppasswords"
    echo "  2. Sign in as: siegel.yaz@gmail.com"
    echo "  3. Create: Mail → Other → 'Hands-Off'"
    echo "  4. Copy the 16-character code (remove spaces)"
    echo ""
    echo "Then run:"
    echo "  ./scripts/gmail_setup.sh YOUR_PASSWORD_HERE"
    echo ""
    exit 1
fi

APP_PASSWORD="$1"

echo "Setting up Gmail automation..."
echo ""

# Update .env file
cat > .env.handsoff_email << EOF
HANDSOFF_EMAIL="siegel.yaz@gmail.com"
HANDSOFF_APP_PASSWORD="$APP_PASSWORD"
EOF

echo "✓ Credentials configured"
echo ""

# Test connection
echo "Testing Gmail connection..."
python3 autonomous/email_inbox_handler.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Connection successful!"
    echo "✓ Inbox processed"
    echo ""

    # Start continuous monitoring
    echo "Starting continuous monitoring..."
    pkill -f "email_inbox_handler.py --continuous" 2>/dev/null || true

    nohup python3 autonomous/email_inbox_handler.py --continuous > logs/email_handler.log 2>&1 &

    PID=$!
    echo "✓ Email handler running (PID: $PID)"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  GMAIL AUTOMATION: ACTIVE"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Your inbox is now fully automated."
    echo "All emails will be processed every 5 minutes."
    echo "You never need to check Gmail manually."
    echo ""
    echo "Monitor: tail -f logs/email_handler.log"
    echo ""
else
    echo ""
    echo "✗ Connection failed"
    echo "Check password and try again"
    exit 1
fi
