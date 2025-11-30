#!/bin/bash
# IMMEDIATE DOLLAR STACKING SCRIPT
# Gets the first dollars as fast as possible

set -e

WALLET="0x5258512505e13Bbb21c2f1738A32AEF2A5a6393e"
LOG="/root/hands-off-engine/state/dollar_stacking.log"

echo "💵 STACKING FIRST DOLLARS - IMMEDIATE EXECUTION"
echo "Wallet: $WALLET"
echo "Started: $(date)"
echo ""

# Function to log earnings
log_earnings() {
    echo "[$(date)] $1: $$2 from $3" >> "$LOG"
    echo "✓ Earned $$2 from $3"
}

# Phase 1: Faucets (IMMEDIATE - but manual)
echo "🚰 PHASE 1: Faucets (Manual - DO NOW)"
echo ""
echo "   Visit these URLs in your browser:"
echo "   1. https://faucet.polygon.technology/"
echo "   2. https://www.alchemy.com/faucets/polygon-mumbai"
echo "   3. https://faucet.quicknode.com/polygon"
echo ""
echo "   Connect wallet: $WALLET"
echo "   Expected: $0.50-0.80 in MATIC (instant)"
echo ""
read -p "   Press ENTER after claiming faucets..."

# Phase 2: Check balance
echo ""
echo "💰 Checking balance..."
python3 << 'PYEOF'
import requests
wallet = "0x5258512505e13Bbb21c2f1738A32AEF2A5a6393e"
try:
    # Check MATIC balance
    rpc = "https://polygon-rpc.com"
    payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [wallet, "latest"], "id": 1}
    r = requests.post(rpc, json=payload, timeout=5)
    if r.ok:
        result = r.json().get('result', '0x0')
        balance = int(result, 16) / 1e18
        print(f"   MATIC Balance: {balance:.4f} MATIC")
        if balance > 0:
            print(f"   💰 Worth: ~${balance * 0.80:.2f}")
        else:
            print("   ⚠️  Still $0 - claim faucets!")
except Exception as e:
    print(f"   Error checking balance: {e}")
PYEOF

echo ""
echo "🎯 PHASE 2: Instant Earn (No wallet needed)"
echo ""
echo "   Option A: Coinbase Earn"
echo "   → Go to https://www.coinbase.com/earn"
echo "   → Complete ANY lesson (5 min)"
echo "   → Earn $3-5 in crypto INSTANTLY"
echo ""
echo "   Option B: Binance Learn & Earn"
echo "   → https://www.binance.com/en/learn-and-earn"
echo "   → Complete quiz"
echo "   → Earn $1-3 in crypto"
echo ""
echo "   Option C: Crypto.com Missions"
echo "   → App-based, instant rewards"
echo ""
read -p "   Press ENTER after earning from ANY platform..."

# Phase 3: Track progress
echo ""
echo "📊 PROGRESS TRACKING"
echo "   Goal: First $1 → First $10 → First $100"
echo ""
echo "   Log your earnings:"
read -p "   How much did you earn? $" AMOUNT
read -p "   From which source? " SOURCE

if [ ! -z "$AMOUNT" ]; then
    echo "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"amount\": $AMOUNT, \"source\": \"$SOURCE\", \"wallet\": \"$WALLET\"}" >> /root/hands-off-engine/state/earnings.jsonl
    echo "   ✓ Logged $$AMOUNT from $SOURCE"

    # Calculate total
    TOTAL=$(python3 -c "import json; print(sum(json.loads(line)['amount'] for line in open('/root/hands-off-engine/state/earnings.jsonl')))")
    echo ""
    echo "   💰 TOTAL EARNED: $$TOTAL"
    echo "   🎯 Progress to $100: $(python3 -c "print(f'{$TOTAL/100:.1%}')")"

    if (( $(echo "$TOTAL >= 1" | bc -l) )); then
        echo ""
        echo "   🎉 FIRST DOLLAR ACHIEVED!"
    fi

    if (( $(echo "$TOTAL >= 10" | bc -l) )); then
        echo "   🎉 $10 MILESTONE!"
    fi

    if (( $(echo "$TOTAL >= 100" | bc -l) )); then
        echo "   🚀 $100 REACHED - READY TO TRADE!"
        # Send notification
        python3 /root/hands-off-engine/scripts/notify_trading_ready.py
    fi
fi

echo ""
echo "============================================================"
echo "NEXT: Keep stacking!"
echo "   - Repeat faucets (daily reset)"
echo "   - Complete more earn lessons"
echo "   - Refer friends (if available)"
echo "   - Stack every day until $100"
echo "============================================================"
echo ""
echo "Run this script again: ./scripts/stack_first_dollar.sh"
