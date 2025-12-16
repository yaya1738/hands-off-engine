#!/bin/bash
###############################################################################
# New Hardware Base Setup
# =======================
#
# Sets up a fresh hands-off-engine instance on new hardware.
# Does NOT migrate data or touch the existing base.
#
# Run this on the NEW hardware base ONLY.
#
# Master: Yair Siegel
###############################################################################

set -e  # Exit on error

echo "================================================================================"
echo "🚀 HANDS-OFF-ENGINE - NEW BASE SETUP"
echo "================================================================================"
echo ""

# Check if we're on the right system
read -p "⚠️  Are you on the NEW hardware base (not the current one)? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Setup cancelled. Run this on the NEW base only."
    exit 1
fi

echo ""
echo "📋 SETUP CHECKLIST:"
echo "  1. Install system dependencies"
echo "  2. Clone repository"
echo "  3. Install Python packages"
echo "  4. Set up environment variables"
echo "  5. Create directory structure"
echo "  6. Verify installation"
echo ""

# ===== STEP 1: System Dependencies =====
echo "================================================================================"
echo "📦 STEP 1/6: Installing system dependencies..."
echo "================================================================================"

# Update package lists
echo "Updating package lists..."
sudo apt-get update -qq

# Install required packages
echo "Installing required packages..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    jq \
    tree \
    htop

echo "✅ System dependencies installed"

# ===== STEP 2: Clone Repository =====
echo ""
echo "================================================================================"
echo "📥 STEP 2/6: Cloning repository..."
echo "================================================================================"

# Ask for repository location
read -p "Enter repository URL or path (default: https://github.com/yaya1738/hands-off-engine.git): " repo_url
repo_url=${repo_url:-"https://github.com/yaya1738/hands-off-engine.git"}

# Ask for installation directory
read -p "Enter installation directory (default: /root/hands-off-engine): " install_dir
install_dir=${install_dir:-"/root/hands-off-engine"}

# Clone if directory doesn't exist
if [ -d "$install_dir" ]; then
    echo "⚠️  Directory $install_dir already exists"
    read -p "Pull latest changes? (yes/no): " pull_confirm
    if [ "$pull_confirm" = "yes" ]; then
        cd "$install_dir"
        git pull origin local-sync
        echo "✅ Repository updated"
    fi
else
    echo "Cloning repository to $install_dir..."
    git clone "$repo_url" "$install_dir"
    cd "$install_dir"
    git checkout local-sync
    echo "✅ Repository cloned"
fi

# ===== STEP 3: Python Packages =====
echo ""
echo "================================================================================"
echo "🐍 STEP 3/6: Installing Python packages..."
echo "================================================================================"

cd "$install_dir"

# Check if requirements.txt exists, if not create it
if [ ! -f "requirements.txt" ]; then
    echo "Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
requests>=2.31.0
python-dotenv>=1.0.0
pydantic>=2.0.0
web3>=6.0.0
eth-account>=0.10.0
py-clob-client>=0.20.0
EOF
fi

# Install packages
echo "Installing Python packages..."
pip3 install -r requirements.txt

echo "✅ Python packages installed"

# ===== STEP 4: Environment Variables =====
echo ""
echo "================================================================================"
echo "🔑 STEP 4/6: Setting up environment variables..."
echo "================================================================================"

# Create .env file if it doesn't exist
if [ ! -f "$install_dir/.env" ]; then
    echo "Creating .env file..."
    cat > "$install_dir/.env" << 'EOF'
# GitHub API Token
GITHUB_TOKEN=

# Polymarket API Credentials
POLYMARKET_API_KEY=
POLYMARKET_API_SECRET=
POLYMARKET_PASSPHRASE=

# HackerOne API Token
HACKERONE_API_TOKEN=

# AWS Credentials (for S3 backups)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Etherscan/Polygonscan API Keys
ETHERSCAN_API_KEY=
POLYGONSCAN_API_KEY=

# Email Configuration (optional)
EMAIL_APP_PASSWORD=

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF
    echo "✅ .env file created at $install_dir/.env"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your API keys:"
    echo "   nano $install_dir/.env"
    echo ""
else
    echo "✅ .env file already exists"
fi

# ===== STEP 5: Directory Structure =====
echo ""
echo "================================================================================"
echo "📁 STEP 5/6: Creating directory structure..."
echo "================================================================================"

cd "$install_dir"

# Create required directories
mkdir -p state
mkdir -p logs
mkdir -p backups
mkdir -p config
mkdir -p bounties
mkdir -p bug_bounties

echo "✅ Directory structure created"

# ===== STEP 6: Verification =====
echo ""
echo "================================================================================"
echo "✅ STEP 6/6: Verifying installation..."
echo "================================================================================"

# Check Python
python3_version=$(python3 --version 2>&1)
echo "✅ Python: $python3_version"

# Check Git
git_version=$(git --version 2>&1)
echo "✅ Git: $git_version"

# Check repository
if [ -d "$install_dir/.git" ]; then
    current_branch=$(cd "$install_dir" && git branch --show-current)
    echo "✅ Repository: $install_dir (branch: $current_branch)"
else
    echo "⚠️  Not a git repository"
fi

# Check Python packages
echo "✅ Python packages:"
pip3 list | grep -E "requests|pydantic|web3"

# Check directory structure
echo ""
echo "✅ Directory structure:"
tree -L 1 -d "$install_dir" 2>/dev/null || ls -la "$install_dir"

# ===== SETUP COMPLETE =====
echo ""
echo "================================================================================"
echo "🎉 SETUP COMPLETE!"
echo "================================================================================"
echo ""
echo "📍 Installation Directory: $install_dir"
echo ""
echo "🔑 NEXT STEPS:"
echo ""
echo "1. Configure API keys:"
echo "   nano $install_dir/.env"
echo ""
echo "2. Test the system:"
echo "   cd $install_dir"
echo "   python3 autonomous/full_autonomous_loop.py"
echo ""
echo "3. Run in background:"
echo "   cd $install_dir"
echo "   python3 autonomous/full_autonomous_loop.py --daemon &"
echo ""
echo "4. Check status:"
echo "   cd $install_dir"
echo "   python3 integrafix/api_dashboard.py"
echo ""
echo "================================================================================"
echo "⚠️  REMEMBER: This is the NEW base. The old base is still running separately."
echo "================================================================================"
echo ""

# Save setup info
cat > "$install_dir/.setup_info.json" << EOF
{
  "setup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "install_dir": "$install_dir",
  "hostname": "$(hostname)",
  "python_version": "$(python3 --version 2>&1)",
  "git_branch": "$(cd $install_dir && git branch --show-current 2>/dev/null || echo 'unknown')",
  "setup_complete": true
}
EOF

echo "Setup info saved to $install_dir/.setup_info.json"
echo ""
echo "✅ New base ready!"
