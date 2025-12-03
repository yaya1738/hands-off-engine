#!/usr/bin/env bash
# aider-start.sh - Convenient launcher for aider in Termux
# Usage: ./aider-start.sh [additional aider args]

set -euo pipefail

REPO_ROOT="$HOME/hands-off-engine"
LOG_DIR="$HOME/hands-off/logs"

# Ensure we're in the repo
if [ ! -d "$REPO_ROOT/.git" ]; then
  echo "❌ Error: $REPO_ROOT is not a git repo"
  exit 1
fi

cd "$REPO_ROOT"

# Create logs directory
mkdir -p "$LOG_DIR"

# Check for API key
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
  echo "To set it permanently, add to ~/.bashrc:"
  echo '  export ANTHROPIC_API_KEY="your-key-here"'
  echo ""
  read -p "Continue anyway? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Check if aider is installed
if ! command -v aider >/dev/null 2>&1; then
  echo "❌ aider not found. Install it with:"
  echo "  pip install aider-chat"
  exit 1
fi

# Show current status
echo "🚀 Starting aider in: $REPO_ROOT"
echo "📊 Git status:"
git status --short

echo ""
echo "💡 Tip: aider will auto-commit changes with attribution"
echo "💡 Type /help for aider commands, /exit to quit"
echo ""

# Launch aider with config from .aider.conf.yml
# Pass through any additional args
exec aider "$@"
