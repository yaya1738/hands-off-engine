#!/usr/bin/env bash
# Deploy Improvements to Droplet
# Run this when SSH connectivity is restored

set -euo pipefail

REMOTE="do138"
REMOTE_PATH="/root/hands-off-engine"

echo "🚀 DEPLOYING IMPROVEMENTS TO DROPLET"
echo "===================================="
echo ""

# Check SSH connectivity
echo "📡 Checking SSH connectivity..."
if ! ssh -o ConnectTimeout=5 "$REMOTE" "echo 'SSH OK'" 2>/dev/null; then
    echo "❌ Cannot connect to $REMOTE"
    echo "   Check network/VPN and try again"
    exit 1
fi
echo "✅ SSH connected"
echo ""

# Backup existing files
echo "💾 Backing up existing files..."
ssh "$REMOTE" "
    cd $REMOTE_PATH
    mkdir -p backups
    cp -f decider/ho_decider.py backups/ho_decider.py.backup.\$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    cp -f executor/ho_executor_plan.py backups/ho_executor_plan.py.backup.\$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
"
echo "✅ Backup complete"
echo ""

# Deploy decider improvements
echo "📦 Deploying decider improvements..."
scp decider/ho_decider.py "$REMOTE:$REMOTE_PATH/decider/"
echo "✅ Decider deployed"
echo ""

# Deploy executor improvements
echo "📦 Deploying executor improvements..."
scp executor/ho_executor_plan.py "$REMOTE:$REMOTE_PATH/executor/"
echo "✅ Executor deployed"
echo ""

# Deploy dashboard
echo "📦 Deploying trading dashboard..."
ssh "$REMOTE" "mkdir -p $REMOTE_PATH/tools"
scp tools/trading_dashboard.py "$REMOTE:$REMOTE_PATH/tools/"
ssh "$REMOTE" "chmod +x $REMOTE_PATH/tools/trading_dashboard.py"
echo "✅ Dashboard deployed"
echo ""

# Verify deployment
echo "🔍 Verifying deployment..."
ssh "$REMOTE" "
    cd $REMOTE_PATH
    grep -q 'MIN_CONFIDENCE_THRESHOLD = 0.60' executor/ho_executor_plan.py && echo '✅ Executor threshold: 0.60'
    grep -q 'filter_expired: bool = True' decider/ho_decider.py && echo '✅ Decider filtering: enabled'
    grep -q 'apply_time_decay: bool = True' decider/ho_decider.py && echo '✅ Time decay: enabled'
"
echo ""

# Test on remote
echo "🧪 Testing on remote..."
ssh "$REMOTE" "
    cd $REMOTE_PATH
    python3 -c '
from decider.ho_decider import Decider
from pathlib import Path

d = Decider()
signals = d.load_model_signals(Path(\"state/polymarket-model.json\"))
print(f\"✅ Loaded {len(signals)} markets after filtering\")
'
"
echo ""

echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "Next steps:"
echo "1. Run: ssh $REMOTE 'cd $REMOTE_PATH && python3 tools/trading_dashboard.py'"
echo "2. Regenerate plan: ssh $REMOTE '/usr/local/bin/ho_executor_plan.sh'"
echo "3. Enable LIVE mode (see .claude/LIVE_TRADING_OPERATIONS_GUIDE.md)"
echo ""
echo "🚀 Ready to make money!"
