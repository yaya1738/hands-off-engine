#!/bin/bash
# Quick GitHub status check
cd "$(dirname "$0")/.."
echo "=== GitHub Integration Status ==="
echo ""
echo "Rate Limit:"
python -m scripts.github_ratelimit_status 2>&1 | grep -E "(core|search)" || echo "Error checking rate limit"
echo ""
echo "Repository Health (hands-off-engine):"
python scripts/github_repo_health.py yaya1738 hands-off-engine 2>/dev/null | head -20 || echo "Error: Set GITHUB_TOKEN first"
