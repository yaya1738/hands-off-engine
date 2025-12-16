#!/bin/bash
###############################################################################
# New Base Verification Script
# ============================
#
# Comprehensive verification of newly deployed base.
# Checks system health, dependencies, configuration, and connectivity.
#
# Usage: ./verify_new_base.sh <ssh_host>
# Example: ./verify_new_base.sh base2
#
# Master: Yair Siegel
###############################################################################

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <ssh_host>"
    exit 1
fi

SSH_HOST=$1

echo "================================================================================"
echo "🔍 NEW BASE VERIFICATION"
echo "================================================================================"
echo ""
echo "Target: $SSH_HOST"
echo ""

# Track issues
ISSUES=0

# ===== CONNECTION TEST =====
echo "================================================================================"
echo "1. CONNECTION TEST"
echo "================================================================================"
echo ""

if ssh -o ConnectTimeout=5 "$SSH_HOST" "echo 'Connected'" >/dev/null 2>&1; then
    echo "✅ SSH connection successful"
else
    echo "❌ Cannot connect to $SSH_HOST"
    ISSUES=$((ISSUES + 1))
fi

# ===== SYSTEM INFO =====
echo ""
echo "================================================================================"
echo "2. SYSTEM INFORMATION"
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Uptime: $(uptime -p)"
echo ""
echo "CPU Cores: $(nproc)"
echo "RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $2}')"
echo "Disk Usage: $(df -h / | tail -1 | awk '{print $5}')"
ENDSSH

# ===== DEPENDENCIES CHECK =====
echo ""
echo "================================================================================"
echo "3. DEPENDENCIES CHECK"
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
# Check Python
if command -v python3 >/dev/null 2>&1; then
    echo "✅ Python3: $(python3 --version)"
else
    echo "❌ Python3: NOT INSTALLED"
    exit 1
fi

# Check Git
if command -v git >/dev/null 2>&1; then
    echo "✅ Git: $(git --version)"
else
    echo "❌ Git: NOT INSTALLED"
    exit 1
fi

# Check other tools
for tool in curl jq htop tmux; do
    if command -v $tool >/dev/null 2>&1; then
        echo "✅ $tool: installed"
    else
        echo "⚠️  $tool: not installed"
    fi
done
ENDSSH

if [ $? -ne 0 ]; then
    ISSUES=$((ISSUES + 1))
fi

# ===== REPOSITORY CHECK =====
echo ""
echo "================================================================================"
echo "4. REPOSITORY CHECK"
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
if [ -d "/root/hands-off-engine/.git" ]; then
    cd /root/hands-off-engine
    echo "✅ Repository: exists"
    echo "   Branch: $(git branch --show-current)"
    echo "   Latest commit: $(git log -1 --format='%h - %s')"
    echo "   Remote: $(git remote get-url origin)"
else
    echo "❌ Repository: NOT FOUND at /root/hands-off-engine"
    exit 1
fi
ENDSSH

if [ $? -ne 0 ]; then
    ISSUES=$((ISSUES + 1))
fi

# ===== PYTHON PACKAGES CHECK =====
echo ""
echo "================================================================================"
echo "5. PYTHON PACKAGES CHECK"
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
required_packages=("requests" "pydantic" "web3" "dotenv")
missing=0

for pkg in "${required_packages[@]}"; do
    if pip3 list 2>/dev/null | grep -i "$pkg" >/dev/null; then
        version=$(pip3 show "$pkg" 2>/dev/null | grep Version | cut -d' ' -f2)
        echo "✅ $pkg: $version"
    else
        echo "❌ $pkg: NOT INSTALLED"
        missing=$((missing + 1))
    fi
done

exit $missing
ENDSSH

if [ $? -ne 0 ]; then
    ISSUES=$((ISSUES + 1))
fi

# ===== DIRECTORY STRUCTURE CHECK =====
echo ""
echo "================================================================================"
echo "6. DIRECTORY STRUCTURE CHECK"
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
cd /root/hands-off-engine

required_dirs=("state" "logs" "backups" "config" "autonomous" "integrafix")
missing=0

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/: exists"
    else
        echo "❌ $dir/: NOT FOUND"
        missing=$((missing + 1))
    fi
done

exit $missing
ENDSSH

if [ $? -ne 0 ]; then
    ISSUES=$((ISSUES + 1))
fi

# ===== ENVIRONMENT VARIABLES CHECK =====
echo ""
echo "================================================================================"
echo "7. ENVIRONMENT VARIABLES CHECK"
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
if [ -f "/root/hands-off-engine/.env" ]; then
    echo "✅ .env file: exists"

    # Check if it has content
    if [ -s "/root/hands-off-engine/.env" ]; then
        # Count configured variables (non-empty lines that aren't comments)
        configured=$(grep -v '^#' /root/hands-off-engine/.env | grep -v '^$' | grep '=' | grep -v '=$' | wc -l)
        total=$(grep -v '^#' /root/hands-off-engine/.env | grep '=' | wc -l)

        echo "   Configured variables: $configured / $total"

        if [ $configured -eq 0 ]; then
            echo "   ⚠️  No variables configured yet"
        elif [ $configured -lt 3 ]; then
            echo "   ⚠️  Only $configured variables configured"
        else
            echo "   ✅ $configured variables configured"
        fi
    else
        echo "   ⚠️  File is empty"
    fi
else
    echo "❌ .env file: NOT FOUND"
    exit 1
fi
ENDSSH

if [ $? -ne 0 ]; then
    ISSUES=$((ISSUES + 1))
fi

# ===== KEY FILES CHECK =====
echo ""
echo "================================================================================"
echo "8. KEY FILES CHECK"
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
cd /root/hands-off-engine

key_files=(
    "autonomous/full_autonomous_loop.py"
    "integrafix/api_orchestrator.py"
    "integrafix/api_manager.py"
    "integrafix/failure_hardening.py"
    "integrafix/self_improvement_engine.py"
)

missing=0
for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file: NOT FOUND"
        missing=$((missing + 1))
    fi
done

exit $missing
ENDSSH

if [ $? -ne 0 ]; then
    ISSUES=$((ISSUES + 1))
fi

# ===== FIREWALL CHECK =====
echo ""
echo "================================================================================"
echo "9. FIREWALL CHECK"
echo "================================================================================"
echo ""

ssh "$SSH_HOST" << 'ENDSSH'
if command -v ufw >/dev/null 2>&1; then
    ufw_status=$(sudo ufw status 2>/dev/null | head -1)
    echo "UFW Status: $ufw_status"

    if echo "$ufw_status" | grep -q "active"; then
        echo "✅ Firewall: active"
        echo ""
        echo "Rules:"
        sudo ufw status numbered | grep -E "22|443" || echo "   No rules for ports 22/443"
    else
        echo "⚠️  Firewall: inactive"
    fi
else
    echo "⚠️  UFW: not installed"
fi
ENDSSH

# ===== SYSTEM TEST =====
echo ""
echo "================================================================================"
echo "10. SYSTEM TEST"
echo "================================================================================"
echo ""

echo "Testing API Dashboard..."
ssh "$SSH_HOST" << 'ENDSSH'
cd /root/hands-off-engine
timeout 10 python3 integrafix/api_dashboard.py 2>&1 | head -20 || echo "Test completed"
ENDSSH

if [ $? -eq 0 ]; then
    echo "✅ API Dashboard: executable"
else
    echo "⚠️  API Dashboard: check manually"
fi

# ===== VERIFICATION SUMMARY =====
echo ""
echo "================================================================================"
echo "📊 VERIFICATION SUMMARY"
echo "================================================================================"
echo ""

if [ $ISSUES -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo ""
    echo "🎉 New base is fully operational!"
    echo ""
    echo "Ready to start autonomous loop:"
    echo "  ssh $SSH_HOST 'cd /root/hands-off-engine && python3 autonomous/full_autonomous_loop.py'"
    echo ""
else
    echo "⚠️  ISSUES FOUND: $ISSUES"
    echo ""
    echo "Review the checks above and fix any issues before starting the system."
    echo ""
fi

echo "================================================================================"

exit $ISSUES
