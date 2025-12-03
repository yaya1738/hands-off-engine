#!/bin/bash
# fix_ssh.sh - Minimal effort SSH and safety setup for hands-off droplets
#
# Usage:
#   curl -s https://raw.githubusercontent.com/yaya1738/hands-off-engine/main/scripts/fix_ssh.sh | bash
#
# What this does:
#   1. Adds ho-cli-main SSH key to authorized_keys (for inter-droplet SSH)
#   2. Creates/updates .claudeignore blocklist (prevents AI from destructive operations)
#   3. Safe to run multiple times (idempotent)

set -e

echo "=== Hands-Off SSH & Safety Setup ==="
echo "Timestamp: $(date -Iseconds)"
echo ""

# 1. Setup SSH access from ho-cli-main and pm-helper
echo "[1/2] Setting up SSH access..."
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# Add ho-cli-main public key (primary CLI access)
HO_CLI_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN9leXKzmPHKpTLjwsynPjVSbtyyhk0HFynKlA6X1z6x root@ho-cli-main"

# Add pm-helper public key (original primary node)
PM_HELPER_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKUOlcMgjyYnAknQhzB/hHMZewPEx7XPLAd/Q2vLt1JD handsoff-do138"

# Add keys if not present
if [ -f /root/.ssh/authorized_keys ]; then
    if grep -q "root@ho-cli-main" /root/.ssh/authorized_keys 2>/dev/null; then
        echo "  ✓ ho-cli-main key already present"
    else
        echo "$HO_CLI_KEY" >> /root/.ssh/authorized_keys
        echo "  ✓ Added ho-cli-main key"
    fi
    
    if grep -q "handsoff-do138" /root/.ssh/authorized_keys 2>/dev/null; then
        echo "  ✓ pm-helper key already present"
    else
        echo "$PM_HELPER_KEY" >> /root/.ssh/authorized_keys
        echo "  ✓ Added pm-helper key"
    fi
else
    echo "$HO_CLI_KEY" > /root/.ssh/authorized_keys
    echo "$PM_HELPER_KEY" >> /root/.ssh/authorized_keys
    echo "  ✓ Created authorized_keys with both keys"
fi

chmod 600 /root/.ssh/authorized_keys
echo "  ✓ Set correct permissions"

# 2. Create blocklist (claudeignore) for AI safety
echo "[2/2] Creating AI safety blocklist..."

REPO_DIR="/root/hands-off-engine"
if [ ! -d "$REPO_DIR" ]; then
    echo "  ⚠ Repository not found at $REPO_DIR"
    echo "  ⚠ Skipping .claudeignore creation (run bootstrap_compute_node.sh first)"
else
    cat > "$REPO_DIR/.claudeignore" << 'EOF'
# Sensitive files - AI must not touch these
.env
.env.*
*.key
*.pem
*.cert
credentials.json
secrets.json
config.json

# API keys and tokens
**/api_keys.txt
**/tokens.txt
**/.anthropic

# SSH and authorized keys
.ssh/
authorized_keys

# Logs and temp files
logs/
*.log
*.tmp
*.temp
tmp/
temp/

# Git internals
.git/
.gitignore

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
ENV/

# Node
node_modules/
npm-debug.log
yarn-error.log

# Build artifacts
dist/
build/
*.egg-info/

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# CI/CD configs (careful with these)
.github/workflows/

# State files (managed by system)
state/
vault.json

# Critical execution scripts
executor/ho_executor.py
state/risk_profile.json
EOF
    echo "  ✓ Created .claudeignore blocklist"
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "✓ SSH access from ho-cli-main and pm-helper enabled"
echo "✓ AI safety blocklist in place"
echo ""
echo "You can now SSH from either node to this droplet:"
echo "  ssh root@$(curl -s ifconfig.me 2>/dev/null || echo '<this-droplet-ip>')"
echo ""
