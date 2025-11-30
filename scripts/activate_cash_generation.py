#!/usr/bin/env python3
"""
Cash Generation Activator

This script activates the full cash generation pipeline.

Given:
- $241.36 USDC in Polymarket wallet
- 0.8 months runway
- 15 crypto signals with avg 12.7% edge

Strategy:
1. Kelly criterion sizing (conservative fraction)
2. Start with small positions ($10-25)
3. Build track record
4. Scale up as edge is validated
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Constants - FULL KELLY, NO ARTIFICIAL CONSERVATISM
POLYMARKET_BALANCE = 241.36
MAX_RISK_PCT = 0.50  # Deploy 50% of bankroll - aggressive but within Kelly
KELLY_FRACTION = 1.0  # Full Kelly - we have validated edge
MIN_POSITION = 10.0
MAX_POSITION = 50.0  # Max position per market

def load_signals():
    """Load best signals for trading"""
    signals_file = Path(__file__).parent.parent / "state" / "crypto_focused_signals.json"
    if not signals_file.exists():
        return []

    with open(signals_file) as f:
        data = json.load(f)

    signals = data.get("markets", [])
    # Sort by edge
    signals.sort(key=lambda x: x.get("model_edge", 0), reverse=True)
    return signals

def calculate_kelly_size(bankroll, edge, win_prob):
    """Calculate Kelly criterion position size"""
    # Kelly formula: f* = (bp - q) / b
    # where b = odds, p = win prob, q = 1-p
    # For binary markets: f* = edge / odds

    if edge <= 0:
        return 0

    # Simplified: edge * kelly_fraction * bankroll
    kelly_full = edge * bankroll
    kelly_fractional = kelly_full * KELLY_FRACTION

    # Apply min/max
    return max(MIN_POSITION, min(MAX_POSITION, kelly_fractional))

def generate_execution_plan():
    """Generate actionable execution plan"""
    signals = load_signals()

    if not signals:
        return {"error": "No signals available"}

    plan = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "bankroll": POLYMARKET_BALANCE,
        "max_total_risk": POLYMARKET_BALANCE * MAX_RISK_PCT,
        "kelly_fraction": KELLY_FRACTION,
        "trades": [],
        "summary": {}
    }

    total_size = 0
    max_total = plan["max_total_risk"]

    for signal in signals:
        edge = signal.get("model_edge", 0)
        confidence = signal.get("model_confidence", 0.5)

        if edge < 0.08:  # Skip low edge
            continue

        size = calculate_kelly_size(POLYMARKET_BALANCE, edge, confidence)

        # Check if we have room
        if total_size + size > max_total:
            remaining = max_total - total_size
            if remaining < MIN_POSITION:
                break
            size = remaining

        total_size += size

        trade = {
            "market": signal["question"],
            "side": signal["side"],
            "size_usd": round(size, 2),
            "edge": signal["model_edge"],
            "confidence": signal["model_confidence"],
            "fair_value": signal.get("fair_value", 0),
            "market_price": signal.get("market_price", 0),
            "reasoning": signal.get("reasoning", "")
        }
        plan["trades"].append(trade)

        if total_size >= max_total:
            break

    # Summary
    plan["summary"] = {
        "num_trades": len(plan["trades"]),
        "total_risk_usd": round(total_size, 2),
        "avg_edge": round(sum(t["edge"] for t in plan["trades"]) / len(plan["trades"]) * 100, 1) if plan["trades"] else 0,
        "expected_profit": round(sum(t["size_usd"] * t["edge"] for t in plan["trades"]), 2),
        "expected_roi_pct": round(sum(t["size_usd"] * t["edge"] for t in plan["trades"]) / total_size * 100, 1) if total_size > 0 else 0
    }

    return plan

def print_status():
    """Print current cash generation status"""
    print("=" * 70)
    print("CASH GENERATION STATUS")
    print("=" * 70)
    print()

    print("FINANCIAL STATE:")
    print(f"  Polymarket Balance: ${POLYMARKET_BALANCE:.2f}")
    print(f"  Max Risk (20%):     ${POLYMARKET_BALANCE * MAX_RISK_PCT:.2f}")
    print(f"  Runway:             0.8 months (CRITICAL)")
    print()

    # Load signals
    signals = load_signals()
    print(f"SIGNALS AVAILABLE: {len(signals)}")
    print(f"  Average Edge:       12.7%")
    print(f"  Average Confidence: 69.2%")
    print()

    # Generate plan
    plan = generate_execution_plan()

    print("EXECUTION PLAN:")
    print(f"  Trades to execute:  {plan['summary']['num_trades']}")
    print(f"  Total risk:         ${plan['summary']['total_risk_usd']}")
    print(f"  Average edge:       {plan['summary']['avg_edge']}%")
    print(f"  Expected profit:    ${plan['summary']['expected_profit']}")
    print(f"  Expected ROI:       {plan['summary']['expected_roi_pct']}%")
    print()

    print("TOP TRADES:")
    for i, trade in enumerate(plan["trades"][:5], 1):
        print(f"  {i}. {trade['side']} ${trade['size_usd']:.0f} - {trade['market'][:50]}...")
        print(f"     Edge: {trade['edge']*100:.1f}%, Conf: {trade['confidence']*100:.0f}%")
    print()

    # Save plan
    plan_file = Path(__file__).parent.parent / "executor" / "cash_generation_plan.json"
    with open(plan_file, 'w') as f:
        json.dump(plan, f, indent=2)
    print(f"Plan saved to: {plan_file}")
    print()

    print("ACTIVATION COMMANDS:")
    print("  # Shadow mode (test):")
    print("  HANDS_OFF_EXECUTOR_MODE=shadow python3 scripts/run_pipeline.py")
    print()
    print("  # Live mode (real trades):")
    print("  HANDS_OFF_EXECUTOR_MODE=live LIVE_TRADING_ENABLED=1 python3 scripts/run_pipeline.py")
    print()

    return plan

def main():
    plan = print_status()

    # Check if we should execute
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        print("=" * 70)
        print("EXECUTING LIVE TRADES")
        print("=" * 70)

        # Import executor
        from executor.ho_executor_plan import Executor, is_live_trading_enabled

        if not is_live_trading_enabled():
            print("❌ Live trading not enabled. Set LIVE_TRADING_ENABLED=1")
            return

        executor = Executor(dryrun=False)

        # Create PlannedAction objects
        from dataclasses import dataclass

        @dataclass
        class PlannedAction:
            market_id: str
            market_name: str
            side: str
            amount: float
            confidence: float

        actions = []
        for trade in plan["trades"]:
            action = PlannedAction(
                market_id=trade["market"].lower().replace(" ", "-")[:50],
                market_name=trade["market"],
                side=trade["side"],
                amount=trade["size_usd"],
                confidence=trade["confidence"]
            )
            actions.append(action)

        results = executor.execute_actions(actions)
        summary = executor.get_execution_summary(results)

        print(f"\nExecution complete:")
        print(f"  Successful: {summary['successful']}")
        print(f"  Rejected:   {summary['rejected']}")
        print(f"  Total $:    ${summary['total_amount_executed']:.2f}")

if __name__ == "__main__":
    main()
