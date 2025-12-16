#!/bin/bash
###############################################################################
# Automated Deployment to New Base
# =================================
#
# Deploys hands-off-engine to newly provisioned hardware.
# Run this AFTER provisioning is complete.
#
# Usage: ./deploy_to_new_base.sh <ssh_host>
# Example: ./deploy_to_new_base.sh base2
#
# Master: Yair Siegel
###############################################################################

set -e

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <ssh_host>"
    echo "Example: $0 base2"
    exit 1
fi

SSH_HOST=$1

echo "================================================================================"
echo "🚀 AUTOMATED DEPLOYMENT TO NEW BASE"
echo "================================================================================"
echo ""
echo "Target: $SSH_HOST"
echo ""

# ===== STEP 1: Verify Connection =====
echo "================================================================================"
echo "🔌 STEP 1/8: Verifying connection..."
echo "================================================================================"
echo ""

if ssh -o ConnectTimeout=5 "$SSH_HOST" "echo '✅ Connected'" 2>/dev/null; then
    echo "✅ Connection successful"
else
    echo "❌ Cannot connect to $SSH_HOST"
    echo "   Make sure provisioning is complete and SSH is configured"
    exit 1
fi

# ===== STEP 2: System Update =====
echo ""
echo "================================================================================"
echo "📦 STEP 2/8: Updating system..."
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
echo "Updating package lists..."
sudo apt-get update -qq
echo "Upgrading packages..."
sudo apt-get upgrade -y -qq
echo "✅ System updated"
ENDSSH

# ===== STEP 3: Install Dependencies =====
echo ""
echo "================================================================================"
echo "🔧 STEP 3/8: Installing dependencies..."
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
echo "Installing system packages..."
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    jq \
    tree \
    htop \
    tmux \
    vim

echo "✅ Dependencies installed"
ENDSSH

# ===== STEP 4: Clone Repository =====
echo ""
echo "================================================================================"
echo "📥 STEP 4/8: Cloning repository..."
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
if [ -d "/root/hands-off-engine" ]; then
    echo "Repository already exists, pulling latest..."
    cd /root/hands-off-engine
    git pull origin local-sync
else
    echo "Cloning repository..."
    git clone https://github.com/yaya1738/hands-off-engine.git /root/hands-off-engine
    cd /root/hands-off-engine
    git checkout local-sync
fi
echo "✅ Repository ready"
ENDSSH

# ===== STEP 5: Install Python Packages =====
echo ""
echo "================================================================================"
echo "🐍 STEP 5/8: Installing Python packages..."
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
cd /root/hands-off-engine

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
requests>=2.31.0
python-dotenv>=1.0.0
pydantic>=2.0.0
web3>=6.0.0
eth-account>=0.10.0
py-clob-client>=0.20.0
EOF
fi

echo "Installing Python packages..."
pip3 install -q -r requirements.txt

echo "✅ Python packages installed"
ENDSSH

# ===== STEP 6: Create Directory Structure =====
echo ""
echo "================================================================================"
echo "📁 STEP 6/8: Creating directory structure..."
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
cd /root/hands-off-engine

mkdir -p state
mkdir -p logs
mkdir -p backups
mkdir -p config
mkdir -p bounties
mkdir -p bug_bounties
mkdir -p analysis

echo "✅ Directory structure created"
ENDSSH

# ===== STEP 7: Copy Environment Variables =====
echo ""
echo "================================================================================"
echo "🔑 STEP 7/8: Setting up environment..."
echo "================================================================================"
echo ""

# Check if local .env exists
if [ -f "/root/hands-off-engine/.env" ]; then
    echo "Copying .env file from current base..."
    scp /root/hands-off-engine/.env "$SSH_HOST:/root/hands-off-engine/.env"
    echo "✅ Environment variables copied"
else
    echo "Creating blank .env file..."
    ssh "$SSH_HOST" << 'ENDSSH'
cat > /root/hands-off-engine/.env << 'EOF'
# GitHub API Token
GITHUB_TOKEN=

# Polymarket API Credentials
POLYMARKET_API_KEY=
POLYMARKET_API_SECRET=
POLYMARKET_PASSPHRASE=

# HackerOne API Token
HACKERONE_API_TOKEN=

# AWS Credentials
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Etherscan/Polygonscan API Keys
ETHERSCAN_API_KEY=
POLYGONSCAN_API_KEY=

# Email Configuration
EMAIL_APP_PASSWORD=

# Telegram Bot
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF
ENDSSH
    echo "⚠️  .env file created but empty - you'll need to add credentials"
fi

# ===== STEP 8: Verify Installation =====
echo ""
echo "================================================================================"
echo "✅ STEP 8/8: Verifying installation..."
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
cd /root/hands-off-engine

echo "Checking Python..."
python3 --version

echo ""
echo "Checking Git..."
git --version

echo ""
echo "Checking repository..."
git branch --show-current

echo ""
echo "Checking Python packages..."
pip3 list | grep -E "requests|pydantic|web3" || true

echo ""
echo "Checking directory structure..."
ls -la | grep -E "state|logs|backups|config" || true

echo ""
echo "✅ Installation verified"
ENDSSH

# ===== DEPLOYMENT COMPLETE =====
echo ""
echo "================================================================================"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "✅ New base is ready at: $SSH_HOST"
echo ""
echo "📍 Installation: /root/hands-off-engine"
echo ""
echo "🔑 NEXT STEPS:"
echo ""
echo "1. Verify .env has credentials:"
echo "   ssh $SSH_HOST 'cat /root/hands-off-engine/.env'"
echo ""
echo "2. Test the system:"
echo "   ssh $SSH_HOST 'cd /root/hands-off-engine && python3 integrafix/api_dashboard.py'"
echo ""
echo "3. Start autonomous loop:"
echo "   ssh $SSH_HOST 'cd /root/hands-off-engine && python3 autonomous/full_autonomous_loop.py'"
echo ""
echo "4. Monitor with tmux:"
echo "   ssh $SSH_HOST"
echo "   tmux new -s hands-off"
echo "   cd /root/hands-off-engine"
echo "   python3 autonomous/full_autonomous_loop.py"
echo ""
echo "================================================================================"
echo ""

# Save deployment info
cat > /root/hands-off-engine/.deployment_info.json << EOF
{
  "deployed_to": "$SSH_HOST",
  "deployment_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "deployed_from": "$(hostname)",
  "status": "deployed"
}
EOF

echo "Deployment info saved to .deployment_info.json"
echo ""
echo "✅ New base deployment complete!"
