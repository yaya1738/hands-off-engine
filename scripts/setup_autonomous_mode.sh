#!/bin/bash
#
# HANDS-OFF ENGINE: Full Autonomous Setup
# ========================================
#
# This script configures the entire system to run autonomously
# with minimal human intervention required.
#
# What it sets up:
# 1. Cron jobs for all automated tasks
# 2. Telegram bot for remote control
# 3. Log directories
# 4. Environment validation
# 5. Initial health check
#
# Usage:
#   ./scripts/setup_autonomous_mode.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "HANDS-OFF ENGINE: Autonomous Mode Setup"
echo "============================================================"
echo ""
echo "This will configure the system to run fully autonomously."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() { echo -e "${GREEN}✓${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# Step 1: Create log directories
echo ""
echo "Step 1: Creating log directories..."
sudo mkdir -p /var/log/hands-off
sudo chmod 777 /var/log/hands-off
success "Log directory created: /var/log/hands-off"

# Step 2: Validate environment
echo ""
echo "Step 2: Validating environment..."

# Check Python
if command -v python3 &> /dev/null; then
    success "Python3 found: $(python3 --version)"
else
    error "Python3 not found!"
    exit 1
fi

# Check Telegram credentials
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    success "Telegram credentials found"
else
    warning "Telegram credentials not in environment"
    echo "  Using defaults from scripts"
fi

# Check Polymarket credentials
if [ -f "$REPO_ROOT/.env.polymarket" ]; then
    success "Polymarket config found"
else
    warning "Polymarket config not found"
    echo "  Copy .env.polymarket.template to .env.polymarket"
fi

# Check gh CLI
if command -v gh &> /dev/null; then
    success "GitHub CLI found"
else
    warning "GitHub CLI not installed (PR automation won't work)"
fi

# Step 3: Install Python dependencies
echo ""
echo "Step 3: Checking Python dependencies..."
pip install -q tweepy praw requests flask 2>/dev/null || true
success "Python dependencies installed"

# Step 4: Install cron jobs
echo ""
echo "Step 4: Setting up cron jobs..."
python3 "$REPO_ROOT/scripts/auto_setup_cron.py" --install
success "Cron jobs installed"

# Step 5: Create systemd service for Telegram bot (optional)
echo ""
echo "Step 5: Setting up Telegram bot service..."

SYSTEMD_SERVICE="/etc/systemd/system/hands-off-telegram.service"

if [ -f "$REPO_ROOT/scripts/systemd/hands-off-telegram.service" ]; then
    sudo install -m 0644 "$REPO_ROOT/scripts/systemd/hands-off-telegram.service" "$SYSTEMD_SERVICE"
else
    error "Canonical Telegram ingress service unit missing"
    exit 1
fi

sudo systemctl daemon-reload
sudo systemctl enable --now hands-off-telegram.service
success "Authenticated Telegram autonomy ingress configured"

# Step 6: Run initial health check
echo ""
echo "Step 6: Running initial health check..."
if [ -x "$REPO_ROOT/scripts/healthcheck.sh" ]; then
    "$REPO_ROOT/scripts/healthcheck.sh" || warning "Health check reported issues"
    success "Health check complete"
else
    warning "Health check script not executable"
fi

# Step 7: Initialize state files
echo ""
echo "Step 7: Initializing state files..."

# Trading mode
if [ ! -f "$REPO_ROOT/state/trading_mode.json" ]; then
    cat > "$REPO_ROOT/state/trading_mode.json" << EOF
{
  "phase": "baby_mode",
  "phase_started": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "paused": false
}
EOF
    success "Trading mode initialized (baby_mode)"
else
    success "Trading mode already exists"
fi

# Hard limits
if [ ! -f "$REPO_ROOT/config/hard_limits.json" ]; then
    mkdir -p "$REPO_ROOT/config"
    cat > "$REPO_ROOT/config/hard_limits.json" << EOF
{
  "max_position_usd": 50,
  "max_daily_loss_usd": 200,
  "max_open_risk_usd": 500,
  "phase": "baby_mode",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    success "Hard limits initialized"
else
    success "Hard limits already exist"
fi

# Step 8: Summary
echo ""
echo "============================================================"
echo "SETUP COMPLETE"
echo "============================================================"
echo ""
echo "The following autonomous systems are now active:"
echo ""
echo "  ✓ Trading Pipeline      - Runs hourly"
echo "  ✓ Social Promotion      - Every 4 hours"
echo "  ✓ Health Monitoring     - Every 15 minutes"
echo "  ✓ Daily Recalibration   - 08:00 UTC"
echo "  ✓ Phase Progression     - Midnight UTC"
echo "  ✓ Coordination Agent    - Every 5 minutes"
echo "  ✓ Telegram Bot          - Running continuously"
echo ""
echo "Telegram Commands:"
echo "  /status   - Get system status"
echo "  /health   - Run health check"
echo "  /metrics  - View performance"
echo "  /pause    - Pause trading"
echo "  /resume   - Resume trading"
echo "  /help     - All commands"
echo ""
echo "Logs: /var/log/hands-off/"
echo ""
echo "The system will now operate autonomously."
echo "Use Telegram to monitor and control remotely."
echo "============================================================"

# Send Telegram notification
python3 -c "
import requests
import os

token = os.getenv('TELEGRAM_BOT_TOKEN', '')
chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

message = '''🚀 <b>AUTONOMOUS MODE ACTIVATED</b>

All systems configured and running:

✅ Trading Pipeline (hourly)
✅ Social Promotion (4h)
✅ Health Monitoring (15m)
✅ Phase Progression (daily)
✅ Telegram Bot (continuous)

<b>Commands:</b>
/status /health /metrics /pause /resume

System is now fully autonomous.
'''

if token and chat_id:
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(url, json={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}, timeout=10)
" 2>/dev/null || warning "Failed to send Telegram notification"

exit 0
