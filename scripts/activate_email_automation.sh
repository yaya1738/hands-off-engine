#!/bin/bash
# Auto-Activate Email Automation
# Run this after adding Gmail app password to .env.handsoff_email

cd /root/hands-off-engine

echo "Checking Gmail credentials..."

# Check if app password is set
if grep -q 'HANDSOFF_APP_PASSWORD=""' .env.handsoff_email; then
    echo ""
    echo "❌ Gmail app password not set yet!"
    echo ""
    echo "Quick setup (2 minutes):"
    echo "1. Visit: https://myaccount.google.com/apppasswords"
    echo "2. Sign in as siegel.yaz@gmail.com"
    echo "3. Create app password for 'Mail'"
    echo "4. Copy the 16-character code"
    echo "5. Run: nano .env.handsoff_email"
    echo "6. Paste code in HANDSOFF_APP_PASSWORD="
    echo "7. Save and run this script again"
    echo ""
    exit 1
fi

echo "✓ Credentials configured"
echo ""

# Test connection
echo "Testing Gmail connection..."
python3 autonomous/email_inbox_handler.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Connection successful!"
    echo ""
    echo "Starting continuous monitoring..."

    # Kill any existing instance
    pkill -f "email_inbox_handler.py --continuous"

    # Start in background
    nohup python3 autonomous/email_inbox_handler.py --continuous > logs/email_handler.log 2>&1 &

    NEW_PID=$!
    echo "✓ Email handler started (PID: $NEW_PID)"
    echo ""
    echo "Your Gmail is now FULLY AUTOMATED"
    echo "You never need to check email manually"
    echo ""
    echo "Check status: tail -f logs/email_handler.log"
else
    echo ""
    echo "✗ Connection failed"
    echo "Check credentials in .env.handsoff_email"
    exit 1
fi
