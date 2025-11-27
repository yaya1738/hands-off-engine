#!/bin/bash
# GitHub Token Setup Script
# 
# This script helps set up GitHub API authentication to avoid rate limiting.
# It stores the token in ~/.github_token and exports GITHUB_TOKEN.
#
# Usage:
#   ./scripts/setup_github_token.sh           # Interactive setup
#   ./scripts/setup_github_token.sh ghp_xxx   # Non-interactive with token
#   source scripts/setup_github_token.sh      # Also export to current shell

set -e

TOKEN_FILE="$HOME/.github_token"
SHELL_RC=""

# Detect shell config file
if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.profile" ]; then
    SHELL_RC="$HOME/.profile"
fi

echo ""
echo "=========================================="
echo "  GitHub Token Setup for Hands-Off Engine"
echo "=========================================="
echo ""

# Check if token already exists
if [ -f "$TOKEN_FILE" ]; then
    EXISTING=$(cat "$TOKEN_FILE" | head -c 4)
    echo "⚠️  Existing token found (${EXISTING}...)"
    echo ""
    read -p "Replace existing token? (y/N): " REPLACE
    if [ "$REPLACE" != "y" ] && [ "$REPLACE" != "Y" ]; then
        echo "Keeping existing token."
        if [ -z "$GITHUB_TOKEN" ]; then
            export GITHUB_TOKEN=$(cat "$TOKEN_FILE")
            echo "✅ Token exported to GITHUB_TOKEN"
        fi
        exit 0
    fi
fi

# Get token from argument or prompt
if [ -n "$1" ]; then
    TOKEN="$1"
else
    echo "To create a GitHub Personal Access Token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select scopes: repo, read:org (for private repos)"
    echo "4. Copy the generated token (starts with ghp_)"
    echo ""
    read -sp "Enter your GitHub token: " TOKEN
    echo ""
fi

# Validate token format
if [[ ! "$TOKEN" =~ ^(ghp_|github_pat_) ]]; then
    echo "⚠️  Warning: Token doesn't start with ghp_ or github_pat_"
    echo "    Make sure this is a valid Personal Access Token"
fi

# Validate token works
echo ""
echo "Testing token..."
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/rate_limit" 2>/dev/null || echo "FAILED")

if echo "$RESPONSE" | grep -q '"limit":5000'; then
    echo "✅ Token is valid! (5000 requests/hour)"
elif echo "$RESPONSE" | grep -q '"limit":'; then
    echo "⚠️  Token works but may have limited scopes"
else
    echo "❌ Token validation failed"
    echo "Response: $RESPONSE"
    exit 1
fi

# Save token securely
echo "$TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
echo "✅ Token saved to $TOKEN_FILE (chmod 600)"

# Export for current session
export GITHUB_TOKEN="$TOKEN"
echo "✅ GITHUB_TOKEN exported for current session"

# Add to shell config if not already there
if [ -n "$SHELL_RC" ]; then
    if ! grep -q "GITHUB_TOKEN" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# GitHub token for API access" >> "$SHELL_RC"
        echo "export GITHUB_TOKEN=\$(cat $TOKEN_FILE 2>/dev/null)" >> "$SHELL_RC"
        echo "✅ Added GITHUB_TOKEN to $SHELL_RC"
    else
        echo "ℹ️  GITHUB_TOKEN already in $SHELL_RC"
    fi
fi

# Create convenience alias
if [ -n "$SHELL_RC" ]; then
    if ! grep -q "alias gh-rate" "$SHELL_RC" 2>/dev/null; then
        echo "alias gh-rate='python3 scripts/github_ratelimit_status.py'" >> "$SHELL_RC"
    fi
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Your GitHub token is configured. To use in new terminals:"
echo "  source $SHELL_RC"
echo ""
echo "To check rate limit:"
echo "  python3 scripts/github_ratelimit_status.py"
echo ""
