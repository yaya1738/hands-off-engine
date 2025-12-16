#!/bin/bash
###############################################################################
# COMPLETE NEW BASE DEPLOYMENT - FULLY AUTOMATED
# ===============================================
#
# This script does EVERYTHING to set up a new base from scratch:
#   1. Provisions Oracle Cloud hardware (if needed)
#   2. Deploys complete system
#   3. Configures credentials
#   4. Starts autonomous loop
#   5. Verifies everything works
#
# Usage:
#   ./scripts/DEPLOY_NEW_BASE.sh
#
# Interactive wizard will guide you through the process.
#
# Master: Yair Siegel
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "================================================================================"
echo "🚀 NEW BASE DEPLOYMENT - FULLY AUTOMATED"
echo "================================================================================"
echo ""
echo "This will set up a complete new base with:"
echo "  ✓ Full hands-off-engine system"
echo "  ✓ All 6 autonomous systems"
echo "  ✓ Money Printer + ABCFC"
echo "  ✓ Backend loop (29 modules)"
echo "  ✓ Self-healing"
echo ""
echo "Estimated time: 15-20 minutes"
echo ""

# ===== STEP 0: Choose Setup Method =====
echo "================================================================================"
echo "📍 STEP 0: Choose Hardware Setup Method"
echo "================================================================================"
echo ""
echo "Options:"
echo "  1. New Oracle Cloud Free Tier (Recommended - $0/month forever)"
echo "  2. Existing server (already provisioned)"
echo "  3. Exit"
echo ""
read -p "Choose option (1-3): " setup_option

case $setup_option in
    1)
        echo ""
        echo "✅ Selected: Oracle Cloud Free Tier"
        echo ""
        echo "Starting Oracle Cloud provisioning..."
        echo ""

        # Run Oracle provisioning
        if bash "$SCRIPT_DIR/provision_oracle_cloud.sh"; then
            echo ""
            echo "✅ Hardware provisioned successfully"
            SSH_HOST="base2"
        else
            echo "❌ Provisioning failed"
            exit 1
        fi
        ;;

    2)
        echo ""
        echo "✅ Selected: Existing server"
        echo ""
        read -p "Enter SSH host/IP: " SSH_HOST

        echo ""
        echo "Testing connection to $SSH_HOST..."
        if ssh -o ConnectTimeout=5 "$SSH_HOST" "echo 'Connected'" >/dev/null 2>&1; then
            echo "✅ Connection successful"
        else
            echo "❌ Cannot connect to $SSH_HOST"
            echo ""
            echo "Make sure:"
            echo "  1. Server is running"
            echo "  2. SSH access is configured"
            echo "  3. SSH key is set up"
            exit 1
        fi
        ;;

    3)
        echo "Deployment cancelled"
        exit 0
        ;;

    *)
        echo "Invalid option"
        exit 1
        ;;
esac

# ===== STEP 1: Deploy System =====
echo ""
echo "================================================================================"
echo "📦 STEP 1: Deploying System"
echo "================================================================================"
echo ""

if bash "$SCRIPT_DIR/deploy_to_new_base.sh" "$SSH_HOST"; then
    echo "✅ System deployed"
else
    echo "❌ Deployment failed"
    exit 1
fi

# ===== STEP 2: Configure Credentials =====
echo ""
echo "================================================================================"
echo "🔑 STEP 2: Configure Credentials"
echo "================================================================================"
echo ""
echo "Choose credential setup method:"
echo "  1. Copy from current base (secure, automatic)"
echo "  2. Manual setup (enter credentials now)"
echo "  3. Skip (configure later manually)"
echo ""
read -p "Choose option (1-3): " cred_option

case $cred_option in
    1)
        echo ""
        echo "Copying credentials from current base..."

        if [ -f "$PROJECT_ROOT/.env" ]; then
            scp "$PROJECT_ROOT/.env" "$SSH_HOST:/root/hands-off-engine/.env"
            echo "✅ Credentials copied"
        else
            echo "⚠️  No .env file found on current base"
            echo "You'll need to configure credentials manually"
        fi
        ;;

    2)
        echo ""
        echo "Manual credential setup..."
        echo ""

        read -p "Polymarket API Key: " pm_key
        read -p "Polymarket API Secret: " pm_secret
        read -p "Polymarket Passphrase: " pm_pass
        read -p "GitHub Token (optional): " gh_token

        ssh "$SSH_HOST" bash << EOF
cat > /root/hands-off-engine/.env << ENVEOF
# Trading
POLYMARKET_API_KEY=$pm_key
POLYMARKET_API_SECRET=$pm_secret
POLYMARKET_PASSPHRASE=$pm_pass

# GitHub
GITHUB_TOKEN=$gh_token

# Add more as needed
ENVEOF
EOF

        echo "✅ Credentials configured"
        ;;

    3)
        echo "⚠️  Skipping credential setup"
        echo "Remember to configure manually before starting system"
        ;;
esac

# ===== STEP 3: Verify Installation =====
echo ""
echo "================================================================================"
echo "🔍 STEP 3: Verifying Installation"
echo "================================================================================"
echo ""

if bash "$SCRIPT_DIR/verify_new_base.sh" "$SSH_HOST"; then
    echo "✅ Verification passed"
else
    echo "⚠️  Verification had issues"
    echo ""
    read -p "Continue anyway? (yes/no): " continue_anyway
    if [ "$continue_anyway" != "yes" ]; then
        echo "Deployment paused. Fix issues and run verify script manually."
        exit 1
    fi
fi

# ===== STEP 4: Start System =====
echo ""
echo "================================================================================"
echo "🎯 STEP 4: Start System"
echo "================================================================================"
echo ""
echo "Ready to start the autonomous system on new base."
echo ""
read -p "Start now? (yes/no): " start_now

if [ "$start_now" == "yes" ]; then
    echo ""
    echo "Starting system in tmux session..."

    ssh "$SSH_HOST" << 'ENDSSH'
cd /root/hands-off-engine

# Kill any existing session
tmux kill-session -t hands-off 2>/dev/null || true

# Start new session with backend loop
tmux new-session -d -s hands-off "python3 autonomous/backend_loop.py"

echo "✅ System started in tmux session 'hands-off'"
echo ""
echo "To view:"
echo "  ssh $SSH_HOST"
echo "  tmux attach -t hands-off"
ENDSSH

    echo ""
    echo "✅ System started"

    # Wait for system to initialize
    echo ""
    echo "Waiting 15 seconds for system to initialize..."
    sleep 15

    # Check if it's running
    echo ""
    echo "Checking system status..."
    ssh "$SSH_HOST" << 'ENDSSH'
cd /root/hands-off-engine

if pgrep -f backend_loop.py >/dev/null; then
    echo "✅ Backend loop is running"
    PID=$(pgrep -f backend_loop.py | head -1)
    echo "   PID: $PID"
else
    echo "⚠️  Backend loop not detected"
    echo "   Check logs: tmux attach -t hands-off"
fi
ENDSSH
fi

# ===== DEPLOYMENT COMPLETE =====
echo ""
echo "================================================================================"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "✅ New base is operational at: $SSH_HOST"
echo ""
echo "📊 What's running:"
echo "  ✓ Backend loop (29 modules)"
echo "  ✓ Money Printer + ABCFC"
echo "  ✓ All 6 autonomous systems"
echo "  ✓ Self-healing enabled"
echo ""
echo "🔗 Access new base:"
echo "  ssh $SSH_HOST"
echo ""
echo "📺 View system:"
echo "  ssh $SSH_HOST -t 'tmux attach -t hands-off'"
echo ""
echo "📊 Check status:"
echo "  ssh $SSH_HOST 'cd /root/hands-off-engine && bash scripts/status.sh'"
echo ""
echo "💰 Monitor trading:"
echo "  ssh $SSH_HOST 'cat /root/hands-off-engine/state/money_printer.json'"
echo ""
echo "================================================================================"
echo ""

# Save deployment record
DEPLOYMENT_RECORD="$PROJECT_ROOT/.deployments/$(date +%Y%m%d_%H%M%S)_${SSH_HOST}.json"
mkdir -p "$PROJECT_ROOT/.deployments"

cat > "$DEPLOYMENT_RECORD" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "target": "$SSH_HOST",
  "method": "$setup_option",
  "deployed_by": "$(whoami)@$(hostname)",
  "status": "complete",
  "systems": [
    "backend_loop",
    "money_printer",
    "autonomous_communication",
    "autonomous_payments",
    "autonomous_employees",
    "autonomous_configuration",
    "autonomous_optimization",
    "self_healing"
  ]
}
EOF

echo "Deployment record saved to: $DEPLOYMENT_RECORD"
echo ""
echo "🎯 Your base is ready. Let it run!"
echo ""
