#!/bin/bash
# AUTO-EXECUTE GMAIL PROCESSING
# Runs immediately when password is detected

cd /root/hands-off-engine

echo "═══════════════════════════════════════════════════════════"
echo "  GMAIL INBOX PROCESSING - EXECUTING NOW"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if password is set
if grep -q 'HANDSOFF_APP_PASSWORD=""' .env.handsoff_email 2>/dev/null; then
    echo "⚠️  Password not set yet"
    echo ""
    echo "Provide password via:"
    echo "  ./scripts/gmail_setup.sh YOUR_PASSWORD"
    echo ""
    exit 1
fi

echo "✓ Password detected"
echo ""
echo "Connecting to Gmail and processing ALL emails..."
echo ""

# Process inbox once
python3 autonomous/email_inbox_handler.py

echo ""
echo "Starting continuous monitoring..."
echo ""

# Kill any existing instance
pkill -f "email_inbox_handler.py --continuous" 2>/dev/null || true

# Start continuous
nohup python3 autonomous/email_inbox_handler.py --continuous > logs/email_handler.log 2>&1 &

PID=$!

echo "═══════════════════════════════════════════════════════════"
echo "  GMAIL AUTOMATION: ACTIVE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Process ID: $PID"
echo "Log file: logs/email_handler.log"
echo ""
echo "Your inbox is now fully automated."
echo "System checks every 5 minutes."
echo "You never need to open Gmail."
echo ""
echo "Monitor: tail -f logs/email_handler.log"
echo ""
