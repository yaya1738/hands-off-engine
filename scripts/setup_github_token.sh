#!/bin/bash
#
# Quick setup script for GitHub authentication
# Run this to configure GITHUB_TOKEN for the current environment
#

set -e

echo "=== GitHub Token Setup ==="
echo ""

# Detect environment
if [ -d "/data/data/com.termux" ]; then
    ENV_TYPE="termux"
    HOME_DIR="$HOME"
    SHELL_RC="$HOME/.bashrc"
elif [ "$(id -u)" = "0" ]; then
    ENV_TYPE="droplet"
    HOME_DIR="/root"
    SHELL_RC="/root/.bashrc"
else
    ENV_TYPE="unknown"
    HOME_DIR="$HOME"
    SHELL_RC="$HOME/.bashrc"
fi

echo "Detected environment: $ENV_TYPE"
echo "Home directory: $HOME_DIR"
echo ""

# Create config directory
CONFIG_DIR="$HOME_DIR/.config/github"
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"

# Check if token already exists
if [ -f "$CONFIG_DIR/env" ]; then
    echo "⚠️  Token configuration already exists at $CONFIG_DIR/env"
    echo ""
    read -p "Do you want to update it? (y/N): " UPDATE
    if [ "$UPDATE" != "y" ] && [ "$UPDATE" != "Y" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# Prompt for token
echo ""
echo "Please enter your GitHub Personal Access Token:"
echo "(You can create one at: https://github.com/settings/tokens)"
echo ""
read -s -p "Token (ghp_...): " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ No token provided. Aborted."
    exit 1
fi

# Validate token format
if [[ ! "$TOKEN" =~ ^(ghp_|github_pat_) ]]; then
    echo "⚠️  Warning: Token doesn't start with 'ghp_' or 'github_pat_'"
    echo "   Make sure you entered it correctly."
    echo ""
fi

# Write token to config file
cat > "$CONFIG_DIR/env" <<EOF
# GitHub Authentication
# Created: $(date)
# Environment: $ENV_TYPE
export GITHUB_TOKEN="$TOKEN"
EOF

chmod 600 "$CONFIG_DIR/env"

echo "✓ Token saved to $CONFIG_DIR/env"
echo ""

# Update shell RC if needed
if ! grep -q "source.*\.config/github/env" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# GitHub authentication (added by setup_github_token.sh)" >> "$SHELL_RC"
    echo "if [ -f \"$CONFIG_DIR/env\" ]; then" >> "$SHELL_RC"
    echo "    source \"$CONFIG_DIR/env\"" >> "$SHELL_RC"
    echo "fi" >> "$SHELL_RC"
    echo "✓ Added source command to $SHELL_RC"
else
    echo "✓ Shell RC already configured"
fi

# Source the token now
source "$CONFIG_DIR/env"

echo ""
echo "=== Testing token ==="

# Test the token
if command -v python3 >/dev/null 2>&1; then
    cd "$(dirname "$(dirname "$0")")" || exit 1

    echo "Checking rate limit..."
    python3 -m scripts.github_ratelimit_status

    echo ""
    echo "✓ Setup complete!"
    echo ""
    echo "Your GitHub token is now active with authenticated rate limits."
    echo "To use in new shells, run: source $SHELL_RC"
else
    echo "✓ Token configured, but Python not available for testing"
fi

echo ""
echo "=== Quick Reference ==="
echo "  Check rate limit: python -m scripts.github_ratelimit_status"
echo "  Token location: $CONFIG_DIR/env"
echo "  To update token: run this script again"
echo ""
