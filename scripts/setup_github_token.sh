#!/bin/bash
# GitHub Token Setup Script for Hands-Off Engine
# 
# Configures GITHUB_TOKEN for authenticated API access.
# Increases rate limit from 60/hour to 5000/hour.
#
# Usage:
#   ./scripts/setup_github_token.sh [token]
#
# If token is not provided, prompts interactively.
# Token is stored in ~/.bashrc for persistence.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if already configured
if [ -n "$GITHUB_TOKEN" ]; then
    # Validate existing token
    response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit 2>/dev/null)
    limit=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('resources',{}).get('core',{}).get('limit',0))" 2>/dev/null || echo "0")
    
    if [ "$limit" = "5000" ]; then
        print_status "GitHub token already configured and working!"
        echo "Rate limit: 5000/hour (authenticated)"
        exit 0
    else
        print_warning "GITHUB_TOKEN is set but may not be valid"
    fi
fi

# Get token from argument or prompt
if [ -n "$1" ]; then
    TOKEN="$1"
else
    echo "GitHub Personal Access Token Setup"
    echo "==================================="
    echo ""
    echo "You need a GitHub Personal Access Token (PAT) with 'repo' scope."
    echo ""
    echo "To create one:"
    echo "1. Go to: https://github.com/settings/tokens/new"
    echo "2. Set expiration (recommend: 90 days)"
    echo "3. Select scope: 'repo' (Full control of private repositories)"
    echo "4. Click 'Generate token'"
    echo "5. Copy the token (starts with ghp_)"
    echo ""
    read -sp "Paste your GitHub token: " TOKEN
    echo ""
fi

# Validate token format
if [[ ! "$TOKEN" =~ ^ghp_[a-zA-Z0-9_]+$ ]] && [[ ! "$TOKEN" =~ ^github_pat_[a-zA-Z0-9_]+$ ]]; then
    print_warning "Token format looks unusual (expected ghp_... or github_pat_...)"
    echo "Proceeding anyway..."
fi

# Test the token
echo "Testing token..."
response=$(curl -s -H "Authorization: token $TOKEN" https://api.github.com/rate_limit 2>/dev/null)

if [ -z "$response" ]; then
    print_error "Failed to connect to GitHub API"
    exit 1
fi

limit=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('resources',{}).get('core',{}).get('limit',0))" 2>/dev/null || echo "0")

if [ "$limit" != "5000" ]; then
    print_error "Token validation failed"
    echo "Expected rate limit 5000, got $limit"
    echo "Check that your token has the correct scopes."
    exit 1
fi

print_status "Token validated successfully!"

# Detect shell config file
if [ -n "$TERMUX_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
    print_status "Detected Termux environment"
elif [ -f "$HOME/.zshrc" ] && [ "$SHELL" = "/bin/zsh" ]; then
    SHELL_RC="$HOME/.zshrc"
else
    SHELL_RC="$HOME/.bashrc"
fi

# Add to shell config
if grep -q "export GITHUB_TOKEN=" "$SHELL_RC" 2>/dev/null; then
    # Update existing - safer approach: remove old line and add new one
    grep -v "^export GITHUB_TOKEN=" "$SHELL_RC" > "${SHELL_RC}.tmp"
    mv "${SHELL_RC}.tmp" "$SHELL_RC"
    echo "export GITHUB_TOKEN=\"$TOKEN\"" >> "$SHELL_RC"
    print_status "Updated GITHUB_TOKEN in $SHELL_RC"
else
    # Add new
    echo "" >> "$SHELL_RC"
    echo "# GitHub token for hands-off-engine" >> "$SHELL_RC"
    echo "export GITHUB_TOKEN=\"$TOKEN\"" >> "$SHELL_RC"
    print_status "Added GITHUB_TOKEN to $SHELL_RC"
fi

# Export for current session
export GITHUB_TOKEN="$TOKEN"

# Verify final setup
echo ""
echo "Setup complete!"
echo "==============="
echo "Rate limit: 5000 requests/hour (authenticated)"
echo ""
echo "To apply in current terminal, run:"
echo "  source $SHELL_RC"
echo ""
echo "Or just open a new terminal."
