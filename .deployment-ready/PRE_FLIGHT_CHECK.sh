#!/bin/bash
###############################################################################
# Pre-Flight Check - Verify Deployment Readiness
# ==============================================
#
# Run this before deploying a new base to ensure everything is ready.
#
# Usage: bash .deployment-ready/PRE_FLIGHT_CHECK.sh
###############################################################################

echo "================================================================================"
echo "✈️  PRE-FLIGHT CHECK - Deployment Readiness"
echo "================================================================================"
echo ""

ISSUES=0
WARNINGS=0

# Check 1: Current base is operational
echo "1. Checking current base status..."
if pgrep -f backend_loop.py >/dev/null; then
    echo "   ✅ Backend loop running"
else
    echo "   ❌ Backend loop NOT running on current base"
    ISSUES=$((ISSUES + 1))
fi

# Check 2: Money Printer status
echo ""
echo "2. Checking Money Printer..."
if [ -f "state/money_printer.json" ]; then
    active=$(cat state/money_printer.json | python3 -c "import sys, json; print(json.load(sys.stdin)['active'])" 2>/dev/null)
    if [ "$active" == "True" ]; then
        echo "   ✅ Money Printer active"
    else
        echo "   ⚠️  Money Printer not active"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ⚠️  Money Printer state file not found"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 3: Credentials available
echo ""
echo "3. Checking credentials..."
if [ -f ".env" ]; then
    configured=$(grep -v '^#' .env | grep '=' | grep -v '=$' | wc -l)
    if [ $configured -gt 0 ]; then
        echo "   ✅ .env file exists with $configured credentials"
    else
        echo "   ⚠️  .env file exists but no credentials configured"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ⚠️  No .env file (will need to configure manually)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 4: Deployment scripts present
echo ""
echo "4. Checking deployment scripts..."
scripts=(
    "scripts/DEPLOY_NEW_BASE.sh"
    "scripts/provision_oracle_cloud.sh"
    "scripts/deploy_to_new_base.sh"
    "scripts/verify_new_base.sh"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "   ✅ $script"
    else
        echo "   ❌ $script NOT FOUND"
        ISSUES=$((ISSUES + 1))
    fi
done

# Check 5: Git repository status
echo ""
echo "5. Checking git repository..."
if [ -d ".git" ]; then
    echo "   ✅ Git repository initialized"

    # Check for uncommitted changes
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        echo "   ✅ No uncommitted changes"
    else
        echo "   ⚠️  Uncommitted changes present"
        echo "      Consider committing before deployment"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ❌ Not a git repository"
    ISSUES=$((ISSUES + 1))
fi

# Check 6: SSH configuration
echo ""
echo "6. Checking SSH setup..."
if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ]; then
    echo "   ✅ SSH keys present"
else
    echo "   ⚠️  No SSH keys found"
    echo "      May need to generate keys for Oracle Cloud"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 7: System resources
echo ""
echo "7. Checking system resources..."
disk_usage=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
if [ $disk_usage -lt 80 ]; then
    echo "   ✅ Disk usage: ${disk_usage}%"
else
    echo "   ⚠️  Disk usage: ${disk_usage}% (high)"
    WARNINGS=$((WARNINGS + 1))
fi

mem_available=$(free -m | grep Mem | awk '{print $7}')
if [ $mem_available -gt 500 ]; then
    echo "   ✅ Available memory: ${mem_available}MB"
else
    echo "   ⚠️  Available memory: ${mem_available}MB (low)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 8: Network connectivity
echo ""
echo "8. Checking network..."
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "   ✅ Internet connectivity"
else
    echo "   ❌ No internet connection"
    ISSUES=$((ISSUES + 1))
fi

if ping -c 1 github.com >/dev/null 2>&1; then
    echo "   ✅ GitHub reachable"
else
    echo "   ⚠️  Cannot reach GitHub"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "================================================================================"
echo "📊 PRE-FLIGHT SUMMARY"
echo "================================================================================"
echo ""

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo ""
    echo "🎉 You're ready to deploy a new base!"
    echo ""
    echo "Run: bash scripts/DEPLOY_NEW_BASE.sh"
    exit 0
elif [ $ISSUES -eq 0 ]; then
    echo "⚠️  WARNINGS: $WARNINGS"
    echo ""
    echo "Deployment is possible but with warnings."
    echo "Review warnings above and proceed if acceptable."
    echo ""
    echo "Run: bash scripts/DEPLOY_NEW_BASE.sh"
    exit 0
else
    echo "❌ ISSUES FOUND: $ISSUES"
    echo "⚠️  WARNINGS: $WARNINGS"
    echo ""
    echo "Fix issues above before deploying."
    echo ""
    echo "Critical issues must be resolved."
    exit 1
fi
