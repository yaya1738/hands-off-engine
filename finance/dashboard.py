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

from finance.truth import read_verified_polymarket_balance
from finance.private_state import private_finance_hub_path

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
    """Return only a recent, provenance-verified Polygon wallet balance."""
    hub_path = private_finance_hub_path()
    truth = read_verified_polymarket_balance(hub_path)
    return {
        "balance_usdc": truth["balance_usdc"],
        "balance_matic": None,
        "wallet": "configured" if truth["wallet_configured"] else "unknown",
        "last_updated": truth["observed_at"] or "unknown",
        "verified": truth["verified"],
        "source": truth["source"],
        "reason": truth["reason"] if not truth["verified"] else None,
    }


def get_credit_status():
    """Credit figures remain unknown until independently verified."""
    return {
        "score": None,
        "total_limit": None,
        "total_balance": None,
        "available": None,
        "utilization": None,
        "verified": False,
        "source": "manual_snapshot_not_reconciled",
    }


def get_runway_status():
    """Runway remains unknown until assets, debts, income and burn are reconciled."""
    return {
        "total_liquid": None,
        "monthly_burn": None,
        "runway_months": None,
        "deployable": None,
        "verified": False,
        "source": "manual_snapshot_not_reconciled",
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
    """Display verified balances and explicitly unknown unreconciled finances."""
    pm = get_polymarket_status()
    print("=" * 70)
    print("FINANCIAL DASHBOARD — EVIDENCE STATUS")
    print(f"Generated: {datetime.now().astimezone().isoformat()}")
    print("=" * 70)

    print("\nPOLYMARKET WALLET")
    if pm["verified"]:
        print("  Verified USDC: " + "$" + format(pm["balance_usdc"], ".2f"))
        print(f"  Verified at:   {pm['last_updated']}")
    else:
        print("  Verified USDC: UNKNOWN")
        print(f"  Reason: {pm['reason']}")

    print("\nOTHER FINANCES")
    print("  Cash, brokerage, debts, income, expenses: UNKNOWN / not reconciled")
    print("  Net worth: UNKNOWN")
    print("  Runway: UNKNOWN")
    print("  Spendable trading capital: DISABLED")

    signals = get_signals_status()
    print("\nRESEARCH SIGNALS (NOT VERIFIED PERFORMANCE)")
    print(f"  Active signals: {signals['count']}")
    print(f"  Average model edge: {signals['avg_edge']:.1f}% (unvalidated)")
    print("\nTRADING")
    print("  Live execution: DISABLED pending financial truth and governed authority")
    print()


if __name__ == "__main__":
    print_dashboard()
