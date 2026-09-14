#!/bin/bash
# Autonomous Trading Monitor - Starts trading immediately when funded

set -e

WALLET="0x5258512505e13Bbb21c2f1738A32AEF2A5a6393e"
USDC_CONTRACT="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
POLYGONSCAN_API="https://api.polygonscan.com/api"
MIN_USDC=10  # Minimum USDC to start trading

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Checking wallet balance..."

# Check USDC balance on Polygon
response=$(curl -s "${POLYGONSCAN_API}?module=account&action=tokenbalance&contractaddress=${USDC_CONTRACT}&address=${WALLET}&tag=latest" || echo '{"result":"0"}')
balance_raw=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('result', '0'))" 2>/dev/null || echo "0")

if [[ "$balance_raw" =~ ^[0-9]+$ ]]; then
    balance_usdc=$(python3 -c "print(round(int('$balance_raw')/1_000_000, 2))")
    echo "💰 Balance: $balance_usdc USDC"

    if (( $(echo "$balance_usdc >= $MIN_USDC" | bc -l) )); then
        echo "✅ Sufficient funds detected! Starting live trading..."

        # Execute live trading cycle
        cd /root/hands-off-engine
        HANDS_OFF_EXECUTOR_MODE=live ./scripts/run_and_notify.sh --bankroll $(echo "$balance_usdc * 10" | bc)

        echo "✅ Trading cycle complete"
        exit 0
    else
        echo "⏳ Waiting for funding... Need $MIN_USDC USDC minimum"
        echo "   Send USDC to: $WALLET (Polygon network)"
        exit 1
    fi
else
    echo "❌ Could not check balance"
    exit 1
fi
