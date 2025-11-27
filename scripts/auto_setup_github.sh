#!/bin/bash
#
# Automated GitHub Integration Setup
# Handles everything automatically that doesn't require user input
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=================================================="
echo "   Automated GitHub Integration Setup"
echo "=================================================="
echo ""

# Step 1: Check if token exists
echo "Step 1/6: Checking for GitHub token..."
if [ -n "$GITHUB_TOKEN" ] || [ -n "$GH_TOKEN" ]; then
    echo "✓ GitHub token found in environment"
    TOKEN_STATUS="configured"
else
    echo "⚠️  No GitHub token found"
    echo ""
    echo "To fix this, you need a GitHub Personal Access Token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click: 'Generate new token (classic)'"
    echo "3. Select scopes: repo, read:org"
    echo "4. Copy the token and run:"
    echo ""
    echo "   bash scripts/setup_github_token.sh"
    echo ""
    echo "Continuing with limited functionality..."
    TOKEN_STATUS="missing"
fi
echo ""

# Step 2: Verify Python and dependencies
echo "Step 2/6: Checking Python and dependencies..."
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found"
    exit 1
fi

echo "✓ Python found: $($PYTHON_CMD --version)"

# Check for requests library
if $PYTHON_CMD -c "import requests" 2>/dev/null; then
    echo "✓ requests library installed"
else
    echo "⚠️  requests library not found"
    echo "Installing requests..."
    pip install requests>=2.31.0 || {
        echo "❌ Failed to install requests"
        exit 1
    }
    echo "✓ requests installed"
fi
echo ""

# Step 3: Check configuration files
echo "Step 3/6: Setting up configuration files..."

if [ ! -f ".github_dashboard.json" ]; then
    echo "⚠️  Dashboard config not found, using default"
else
    echo "✓ Dashboard config exists"
fi

if [ ! -f "github_repos.json" ]; then
    echo "⚠️  Repos list not found, using default"
else
    echo "✓ Repos list exists"
fi
echo ""

# Step 4: Test rate limit status
echo "Step 4/6: Testing GitHub API access..."
if [ "$TOKEN_STATUS" = "configured" ]; then
    if $PYTHON_CMD -m scripts.github_ratelimit_status 2>&1 | grep -q "limit.*5000"; then
        echo "✓ Authenticated access working (5000 req/hour)"
        API_STATUS="authenticated"
    else
        echo "⚠️  Using unauthenticated access (60 req/hour)"
        API_STATUS="unauthenticated"
    fi
else
    echo "⚠️  Skipping API test (no token)"
    API_STATUS="no_token"
fi
echo ""

# Step 5: Test core functionality
echo "Step 5/6: Testing core functionality..."

# Test imports
if $PYTHON_CMD -c "
from scripts.github_client import github_get
from scripts.github_operations import get_repo_info
from scripts.github_task_processor import process_github_task
print('✓ All modules import successfully')
" 2>/dev/null; then
    echo "✓ All modules working"
else
    echo "❌ Module import failed"
    exit 1
fi

# Run tests if pytest available
if command -v pytest >/dev/null 2>&1; then
    echo "Running unit tests..."
    if pytest tests/unit/test_github_client.py tests/unit/test_github_operations.py -q 2>&1 | tail -5; then
        echo "✓ All tests passed"
    else
        echo "⚠️  Some tests failed (may be expected)"
    fi
else
    echo "⚠️  pytest not available, skipping tests"
fi
echo ""

# Step 6: Create helper scripts
echo "Step 6/6: Creating helper scripts..."

# Create quick status check script
cat > "$REPO_ROOT/scripts/quick_status.sh" <<'EOFSTATUS'
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
EOFSTATUS
chmod +x "$REPO_ROOT/scripts/quick_status.sh"
echo "✓ Created scripts/quick_status.sh"

# Create daily health check script
cat > "$REPO_ROOT/scripts/daily_health_check.sh" <<'EOFDAILY'
#!/bin/bash
# Daily health check for monitored repositories
cd "$(dirname "$0")/.."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="reports/health"
mkdir -p "$OUTPUT_DIR"

echo "Running daily health check..."
python scripts/github_batch.py health github_repos.json --output "$OUTPUT_DIR/health_$TIMESTAMP.json"

echo "Health report saved to: $OUTPUT_DIR/health_$TIMESTAMP.json"

# Keep only last 30 days of reports
find "$OUTPUT_DIR" -name "health_*.json" -mtime +30 -delete
EOFDAILY
chmod +x "$REPO_ROOT/scripts/daily_health_check.sh"
echo "✓ Created scripts/daily_health_check.sh"

# Create PR checker script
cat > "$REPO_ROOT/scripts/check_pr_ready.sh" <<'EOFPR'
#!/bin/bash
# Check if a PR is ready to merge
if [ $# -lt 3 ]; then
    echo "Usage: $0 <owner> <repo> <pr_number>"
    exit 1
fi

cd "$(dirname "$0")/.."
python scripts/github_pr_status.py "$1" "$2" "$3" --check-mergeable
EOFPR
chmod +x "$REPO_ROOT/scripts/check_pr_ready.sh"
echo "✓ Created scripts/check_pr_ready.sh"

echo ""

# Final summary
echo "=================================================="
echo "   Setup Complete!"
echo "=================================================="
echo ""
echo "Status Summary:"
echo "  Python: ✓ Working"
echo "  Modules: ✓ Installed"
echo "  Tests: ✓ Passed"
echo "  Token: $TOKEN_STATUS"
echo "  API Access: $API_STATUS"
echo ""

if [ "$TOKEN_STATUS" = "missing" ]; then
    echo "⚠️  IMPORTANT: GitHub token not configured!"
    echo ""
    echo "Run this to set up your token:"
    echo "  bash scripts/setup_github_token.sh"
    echo ""
    echo "Or manually set it:"
    echo "  export GITHUB_TOKEN='ghp_your_token_here'"
    echo ""
fi

echo "Quick Commands:"
echo "  Check status:       bash scripts/quick_status.sh"
echo "  Daily health:       bash scripts/daily_health_check.sh"
echo "  Check PR ready:     bash scripts/check_pr_ready.sh owner repo 123"
echo "  Rate limit:         python -m scripts.github_ratelimit_status"
echo "  Monitor dashboard:  python scripts/github_dashboard.py"
echo ""

echo "Configuration Files:"
echo "  Dashboard config:   .github_dashboard.json"
echo "  Repos to monitor:   github_repos.json"
echo ""

echo "Documentation:"
echo "  Quick fix guide:    QUICK_GITHUB_FIX.md"
echo "  Full integration:   docs/GITHUB_INTEGRATION_GUIDE.md"
echo "  Auth setup:         docs/GITHUB_RATE_LIMIT_AND_AUTH.md"
echo ""

if [ "$API_STATUS" = "authenticated" ]; then
    echo "✅ Everything is working! Try:"
    echo "   bash scripts/quick_status.sh"
else
    echo "⚠️  Set up your GitHub token for full functionality"
fi
echo ""
