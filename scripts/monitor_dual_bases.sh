#!/bin/bash
###############################################################################
# Dual Base Monitoring
# ====================
#
# Monitors both hardware bases and compares their status.
# Useful for redundancy verification and performance comparison.
#
# Usage: ./monitor_dual_bases.sh <base1_host> <base2_host>
# Example: ./monitor_dual_bases.sh localhost base2
#
# Master: Yair Siegel
###############################################################################

BASE1=${1:-"localhost"}
BASE2=${2:-"base2"}

echo "================================================================================"
echo "📡 DUAL BASE MONITORING"
echo "================================================================================"
echo ""
echo "Base 1: $BASE1"
echo "Base 2: $BASE2"
echo ""
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Function to get base info
get_base_info() {
    local host=$1
    local label=$2

    echo "================================================================================"
    echo "$label ($host)"
    echo "================================================================================"
    echo ""

    # Check if accessible
    if [ "$host" = "localhost" ]; then
        # Local check
        if [ -f "/root/hands-off-engine/state/api_manager.json" ]; then
            echo "✅ Status: ONLINE"

            # System info
            echo ""
            echo "SYSTEM INFO:"
            echo "  Hostname: $(hostname)"
            echo "  Uptime: $(uptime -p)"
            echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
            echo "  Memory: $(free -h | grep Mem | awk '{print $3 " / " $2}')"
            echo "  Disk: $(df -h / | tail -1 | awk '{print $5 " used"}')"

            # API Manager stats
            if [ -f "/root/hands-off-engine/state/api_manager.json" ]; then
                echo ""
                echo "API MANAGER:"
                cd /root/hands-off-engine
                python3 << 'PYEOF'
import json
from pathlib import Path

state = json.loads(Path("state/api_manager.json").read_text())
print(f"  Total Calls: {state['total_calls']}")
print(f"  Successful: {state['successful_calls']}")
print(f"  Failed: {state['failed_calls']}")
if state['total_calls'] > 0:
    success_rate = state['successful_calls'] / state['total_calls']
    print(f"  Success Rate: {success_rate:.1%}")
print(f"  Total Cost: ${state['total_cost']:.4f}")
print(f"  Value Generated: ${state['total_value_generated']:.2f}")
PYEOF
            fi

            # Failure Hardening stats
            if [ -f "/root/hands-off-engine/state/failure_hardening.json" ]; then
                echo ""
                echo "FAILURE HARDENING:"
                python3 << 'PYEOF'
import json
from pathlib import Path

state = json.loads(Path("state/failure_hardening.json").read_text())
print(f"  Total Failures: {state['total_failures']}")
print(f"  Recovered: {state['failures_recovered']}")
if state['total_failures'] > 0:
    recovery_rate = state['failures_recovered'] / state['total_failures']
    print(f"  Recovery Rate: {recovery_rate:.1%}")
print(f"  Health: {state['health_status'].upper()}")
PYEOF
            fi

            # Check if autonomous loop is running
            echo ""
            echo "PROCESSES:"
            if pgrep -f "full_autonomous_loop.py" >/dev/null; then
                echo "  ✅ Autonomous loop: RUNNING"
                pid=$(pgrep -f "full_autonomous_loop.py")
                echo "     PID: $pid"
                echo "     Runtime: $(ps -p $pid -o etime= | tr -d ' ')"
            else
                echo "  ⚠️  Autonomous loop: NOT RUNNING"
            fi

        else
            echo "⚠️  Status: INSTALLED BUT NOT INITIALIZED"
        fi
    else
        # Remote check
        if ssh -o ConnectTimeout=5 "$host" "echo 'ok'" >/dev/null 2>&1; then
            echo "✅ Status: ONLINE"

            # Get remote info
            ssh "$host" << 'ENDSSH'
# System info
echo ""
echo "SYSTEM INFO:"
echo "  Hostname: $(hostname)"
echo "  Uptime: $(uptime -p)"
echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "  Memory: $(free -h | grep Mem | awk '{print $3 " / " $2}')"
echo "  Disk: $(df -h / | tail -1 | awk '{print $5 " used"}')"

# API Manager stats
if [ -f "/root/hands-off-engine/state/api_manager.json" ]; then
    echo ""
    echo "API MANAGER:"
    cd /root/hands-off-engine
    python3 << 'PYEOF'
import json
from pathlib import Path

try:
    state = json.loads(Path("state/api_manager.json").read_text())
    print(f"  Total Calls: {state['total_calls']}")
    print(f"  Successful: {state['successful_calls']}")
    print(f"  Failed: {state['failed_calls']}")
    if state['total_calls'] > 0:
        success_rate = state['successful_calls'] / state['total_calls']
        print(f"  Success Rate: {success_rate:.1%}")
    print(f"  Total Cost: ${state['total_cost']:.4f}")
    print(f"  Value Generated: ${state['total_value_generated']:.2f}")
except Exception as e:
    print(f"  ⚠️  Error reading state: {e}")
PYEOF
else
    echo ""
    echo "API MANAGER: Not initialized"
fi

# Failure Hardening stats
if [ -f "/root/hands-off-engine/state/failure_hardening.json" ]; then
    echo ""
    echo "FAILURE HARDENING:"
    python3 << 'PYEOF'
import json
from pathlib import Path

try:
    state = json.loads(Path("state/failure_hardening.json").read_text())
    print(f"  Total Failures: {state['total_failures']}")
    print(f"  Recovered: {state['failures_recovered']}")
    if state['total_failures'] > 0:
        recovery_rate = state['failures_recovered'] / state['total_failures']
        print(f"  Recovery Rate: {recovery_rate:.1%}")
    print(f"  Health: {state['health_status'].upper()}")
except Exception as e:
    print(f"  ⚠️  Error reading state: {e}")
PYEOF
else
    echo ""
    echo "FAILURE HARDENING: Not initialized"
fi

# Check processes
echo ""
echo "PROCESSES:"
if pgrep -f "full_autonomous_loop.py" >/dev/null; then
    echo "  ✅ Autonomous loop: RUNNING"
    pid=$(pgrep -f "full_autonomous_loop.py")
    echo "     PID: $pid"
    echo "     Runtime: $(ps -p $pid -o etime= | tr -d ' ')"
else
    echo "  ⚠️  Autonomous loop: NOT RUNNING"
fi
ENDSSH
        else
            echo "❌ Status: OFFLINE (cannot connect)"
        fi
    fi

    echo ""
}

# Monitor both bases
get_base_info "$BASE1" "BASE 1 (PRIMARY)"
get_base_info "$BASE2" "BASE 2 (BACKUP)"

# Summary
echo "================================================================================"
echo "📊 REDUNDANCY STATUS"
echo "================================================================================"
echo ""

# Check both bases
base1_online=false
base2_online=false

if [ "$BASE1" = "localhost" ]; then
    [ -f "/root/hands-off-engine/state/api_manager.json" ] && base1_online=true
else
    ssh -o ConnectTimeout=5 "$BASE1" "test -f /root/hands-off-engine/state/api_manager.json" 2>/dev/null && base1_online=true
fi

if [ "$BASE2" = "localhost" ]; then
    [ -f "/root/hands-off-engine/state/api_manager.json" ] && base2_online=true
else
    ssh -o ConnectTimeout=5 "$BASE2" "test -f /root/hands-off-engine/state/api_manager.json" 2>/dev/null && base2_online=true
fi

if $base1_online && $base2_online; then
    echo "✅ FULL REDUNDANCY"
    echo "   Both bases operational"
    echo "   System is antifragile"
elif $base1_online; then
    echo "⚠️  PARTIAL REDUNDANCY"
    echo "   Base 1 operational, Base 2 not ready"
    echo "   Single point of failure"
elif $base2_online; then
    echo "⚠️  PARTIAL REDUNDANCY"
    echo "   Base 2 operational, Base 1 not ready"
    echo "   Single point of failure"
else
    echo "❌ NO REDUNDANCY"
    echo "   Both bases offline"
    echo "   CRITICAL: System down"
fi

echo ""
echo "================================================================================"
