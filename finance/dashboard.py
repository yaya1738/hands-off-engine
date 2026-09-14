#!/usr/bin/env python3
"""
Financial Dashboard - Complete View of Yair's Financial State

Integrates:
- Polymarket trading account
- Credit card optimizer
- AI cost tracking
- Cash generation pipeline
"""

import json
from datetime import datetime
from pathlib import Path

FINANCE_DIR = Path(__file__).parent
STATE_DIR = FINANCE_DIR.parent / "state"
LOGS_DIR = FINANCE_DIR.parent / "logs"

def load_json(filepath):
    """Safely load JSON file"""
    try:
        with open(filepath) as f:
            return json.load(f)
    except:
        return {}

def get_polymarket_status():
    """Get Polymarket account status"""
    hub = load_json(FINANCE_DIR / "yair_finance_hub.json")
    pm = hub.get("accounts", {}).get("polymarket", {})

    return {
        "balance_usdc": pm.get("balance_usdc", 0),
        "balance_matic": pm.get("balance_matic", 0),
        "wallet": pm.get("wallet_address", "unknown"),
        "last_updated": pm.get("last_updated", "never")
    }

def get_credit_status():
    """Get credit card status"""
    hub = load_json(FINANCE_DIR / "yair_finance_hub.json")
    credit = hub.get("credit", {})

    return {
        "score": credit.get("score", 0),
        "total_limit": credit.get("total_limit", 0),
        "total_balance": credit.get("total_balance", 0),
        "available": credit.get("total_available", 0),
        "utilization": credit.get("utilization_pct", 0)
    }

def get_runway_status():
    """Get runway status"""
    hub = load_json(FINANCE_DIR / "yair_finance_hub.json")
    summary = hub.get("summary", {})
    burn = hub.get("monthly_burn", {})

    return {
        "total_liquid": summary.get("total_liquid_usd", 0),
        "monthly_burn": burn.get("total_usd", 0),
        "runway_months": summary.get("runway_months", 0),
        "deployable": summary.get("deployable_to_trading", 0)
    }

def get_trading_status():
    """Get trading status from shadow trades"""
    trades_file = STATE_DIR / "shadow_trades.jsonl"
    if not trades_file.exists():
        return {"total_shadow": 0, "today": 0}

    total = 0
    today = 0
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    with open(trades_file) as f:
        for line in f:
            try:
                trade = json.loads(line)
                total += 1
                if trade.get("timestamp", "").startswith(today_str):
                    today += 1
            except:
                continue

    return {"total_shadow": total, "today": today}

def get_signals_status():
    """Get signals status"""
    signals = load_json(STATE_DIR / "crypto_focused_signals.json")
    markets = signals.get("markets", [])

    if not markets:
        return {"count": 0, "avg_edge": 0, "avg_conf": 0}

    return {
        "count": len(markets),
        "avg_edge": sum(m.get("model_edge", 0) for m in markets) / len(markets) * 100,
        "avg_conf": sum(m.get("model_confidence", 0) for m in markets) / len(markets) * 100
    }

def get_ai_cost_status():
    """Get AI cost status"""
    from ai_cost_optimizer import AICostOptimizer

    try:
        optimizer = AICostOptimizer()
        status = optimizer.budget_status()
        return status
    except:
        return {
            "monthly_budget": 250,
            "spent": 0,
            "roi_pct": 0
        }

def print_dashboard():
    """Print complete financial dashboard"""
    print("=" * 70)
    print("FINANCIAL DASHBOARD - YAIR SIEGEL SYSTEM")
    print(f"Generated: {datetime.utcnow().isoformat()}Z")
    print("=" * 70)
    print()

    # Polymarket
    pm = get_polymarket_status()
    print("POLYMARKET TRADING ACCOUNT:")
    print(f"  USDC Balance:   ${pm['balance_usdc']:.2f}")
    print(f"  MATIC (gas):    {pm['balance_matic']:.4f}")
    print(f"  Last Updated:   {pm['last_updated']}")
    print()

    # Runway
    runway = get_runway_status()
    print("RUNWAY STATUS:")
    runway_status = "🔴 CRITICAL" if runway['runway_months'] < 1 else "🟡 WARNING" if runway['runway_months'] < 3 else "🟢 OK"
    print(f"  Total Liquid:   ${runway['total_liquid']:,.0f}")
    print(f"  Monthly Burn:   ${runway['monthly_burn']:,.0f}")
    print(f"  Runway:         {runway['runway_months']:.1f} months {runway_status}")
    print(f"  Deployable:     ${runway['deployable']:.0f}")
    print()

    # Credit
    credit = get_credit_status()
    util_status = "🔴 HIGH" if credit['utilization'] > 50 else "🟡 ELEVATED" if credit['utilization'] > 30 else "🟢 GOOD"
    print("CREDIT STATUS:")
    print(f"  Score:          {credit['score']}")
    print(f"  Total Limit:    ${credit['total_limit']:,}")
    print(f"  Balance:        ${credit['total_balance']:,}")
    print(f"  Available:      ${credit['available']:,}")
    print(f"  Utilization:    {credit['utilization']}% {util_status}")
    print()

    # Signals
    signals = get_signals_status()
    print("TRADING SIGNALS:")
    print(f"  Active Signals: {signals['count']}")
    print(f"  Average Edge:   {signals['avg_edge']:.1f}%")
    print(f"  Avg Confidence: {signals['avg_conf']:.1f}%")
    print()

    # Shadow trades
    trading = get_trading_status()
    print("TRADING ACTIVITY:")
    print(f"  Shadow Trades:  {trading['total_shadow']} total")
    print(f"  Today:          {trading['today']} trades")
    print()

    # AI Costs
    print("AI API COSTS:")
    print(f"  Monthly Budget: $250")
    print(f"  Strategy:       Reserve API for trading signals")
    print(f"  Subs (fixed):   $50/mo (Claude Max + ChatGPT + Copilot)")
    print(f"  Variable:       $200/mo for signal generation")
    print()

    # Key Actions
    print("=" * 70)
    print("KEY ACTIONS:")
    print("=" * 70)

    actions = []

    if runway['runway_months'] < 1:
        actions.append("🔴 CRITICAL: Execute cash generation trades IMMEDIATELY")
        actions.append("   Run: HANDS_OFF_EXECUTOR_MODE=live LIVE_TRADING_ENABLED=1 python3 scripts/run_pipeline.py")

    if credit['utilization'] > 50:
        actions.append("🟡 Pay down credit cards to reduce utilization (CC optimizer)")
        actions.append("   Run: python3 finance/cc_optimizer.py")

    if signals['count'] > 10 and signals['avg_edge'] > 10:
        actions.append("🟢 Good signals available - consider increasing trade frequency")

    if trading['today'] == 0:
        actions.append("⚠️  No trades today - pipeline may need activation")

    if not actions:
        actions.append("✅ System healthy - continue monitoring")

    for action in actions:
        print(f"  {action}")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY:")
    print("=" * 70)
    print(f"  Net Position:    ${pm['balance_usdc'] + runway['total_liquid']:,.2f} liquid")
    print(f"  Net Worth:       ${pm['balance_usdc'] + runway['total_liquid'] - credit['total_balance']:,.2f} (liquid - debt)")
    print(f"  Time to Crisis:  {runway['runway_months']:.1f} months")
    print()

    if signals['avg_edge'] > 10:
        expected_monthly = pm['balance_usdc'] * 0.2 * (signals['avg_edge'] / 100) * 4  # 4 rounds per month
        print(f"  Expected Monthly Profit (with trading): ${expected_monthly:.2f}")
        print(f"  Months until break-even (vs burn):     {runway['monthly_burn'] / expected_monthly:.1f}" if expected_monthly > 0 else "  Need larger bankroll")

if __name__ == "__main__":
    print_dashboard()
