#!/bin/bash
# Setup Autonomous Job Application System
# Wires everything into the backend loop for full autonomy

set -e

echo "================================"
echo "AUTONOMOUS JOB SYSTEM SETUP"
echo "================================"
echo

# 1. Check if backend loop is running
if pgrep -f "backend_loop.py" > /dev/null; then
    echo "✓ Backend loop is running"
else
    echo "✗ Backend loop not running"
    echo "  Start with: nohup python3 autonomous/backend_loop.py &"
fi

# 2. Check email credentials
if [ -f ".env.handsoff_email" ]; then
    if grep -q "HANDSOFF_EMAIL=" ".env.handsoff_email" && \
       grep -q "HANDSOFF_APP_PASSWORD=" ".env.handsoff_email"; then
        echo "✓ Email credentials configured"
    else
        echo "✗ Email credentials not complete"
        echo "  Edit: .env.handsoff_email"
        echo "  See: applications/EMAIL_SETUP_GUIDE.md"
    fi
else
    echo "✗ Email credentials not found"
    echo "  Create: .env.handsoff_email"
    echo "  See: applications/EMAIL_SETUP_GUIDE.md"
fi

# 3. Check applications queue
if [ -f "applications/queue.json" ]; then
    count=$(python3 -c "import json; print(len(json.load(open('applications/queue.json'))['applications']))")
    echo "✓ Application queue ready ($count applications)"
else
    echo "✗ Application queue not found"
fi

# 4. Test email system
echo
echo "Testing email system..."
cd autonomous
if python3 email_sender.py 2>&1 | grep -q "Email system ready"; then
    echo "✓ Email system ready"
else
    echo "✗ Email system needs setup"
    echo "  See: applications/EMAIL_SETUP_GUIDE.md"
fi
cd ..

# 5. Run job agent once to test
echo
echo "Running job agent test..."
python3 autonomous/job_application_agent.py --once

echo
echo "================================"
echo "AUTONOMOUS JOB SYSTEM STATUS"
echo "================================"
echo
echo "To make fully autonomous:"
echo "1. Complete email setup (see EMAIL_SETUP_GUIDE.md)"
echo "2. Backend loop will automatically run job agent every hour"
echo "3. Applications sent once per day maximum"
echo "4. Responses monitored automatically"
echo
echo "Manual testing:"
echo "  python3 autonomous/job_application_agent.py --once"
echo
echo "View state:"
echo "  cat state/job_agent_state.json"
echo
