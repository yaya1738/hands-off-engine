#!/usr/bin/env python3
"""
INTEGRAFIX: State Synchronizer
==============================

Keeps Golden State in sync with actual trading data.

Problem: Golden State and HFT logs can drift apart.
Solution: Periodic reconciliation from source of truth (HFT logs).

Also provides:
- Win rate recalculation from actual outcomes
- P&L reconciliation
- Tier adjustment recommendations
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"

# Import golden state
from integrafix.golden_state import GoldenState, SCALING_TIERS


def get_hft_truth() -> Dict:
    """Get ground truth from HFT economics log."""
    hft_log = LOGS_DIR / "hft_economics.jsonl"

    total_trades = 0
    total_pnl = 0.0
    wins = 0
    losses = 0

    if hft_log.exists():
        with open(hft_log) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if d.get("type") == "trade_close":
                        total_trades += 1
                        pnl = d.get("cost", 0)
                        total_pnl += pnl
                        if pnl > 0:
                            wins += 1
                        elif pnl < 0:
                            losses += 1
                except:
                    pass

    win_rate = wins / total_trades if total_trades > 0 else 0.5

    return {
        "total_trades": total_trades,
        "total_pnl": total_pnl,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate
    }


def get_executor_truth() -> Dict:
    """Get truth from autonomous executor log."""
    exec_log = STATE_DIR / "autonomous_executor.jsonl"

    total_trades = 0
    total_pnl = 0.0

    if exec_log.exists():
        with open(exec_log) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    for trade in d.get("trades", []):
                        total_trades += 1
                        total_pnl += trade.get("expected_pnl", 0)
                except:
                    pass

    return {
        "total_trades": total_trades,
        "total_pnl": total_pnl
    }


def sync_golden_state() -> Dict:
    """
    Synchronize Golden State with actual data.

    Returns sync report.
    """
    golden = GoldenState.load()
    hft = get_hft_truth()
    executor = get_executor_truth()

    old_state = {
        "trades": golden.total_trades,
        "pnl": golden.total_pnl,
        "win_rate": golden.win_rate,
        "tier": golden.current_tier
    }

    # Use HFT as source of truth (actual executed trades)
    golden.total_trades = hft["total_trades"]
    golden.total_pnl = hft["total_pnl"]
    golden.win_rate = hft["win_rate"]

    # Update tier trades (assume all are current tier for now)
    golden.tier_trades = hft["total_trades"]
    golden.tier_pnl = hft["total_pnl"]

    # Check for tier advancement
    tier = golden.get_tier_config()
    can_advance = (
        golden.tier_trades >= tier.required_trades and
        golden.win_rate >= tier.required_win_rate and
        golden.tier_pnl > 0
    )

    if can_advance and golden.current_tier < 4:
        golden.current_tier += 1
        golden.tier_trades = 0
        golden.tier_pnl = 0
        golden.tier_started = datetime.now(timezone.utc).isoformat()
        if golden.current_tier == 4:
            golden.golden_achieved = True
            golden.golden_achieved_at = datetime.now(timezone.utc).isoformat()

    golden.last_updated = datetime.now(timezone.utc).isoformat()
    golden.save()

    new_state = {
        "trades": golden.total_trades,
        "pnl": golden.total_pnl,
        "win_rate": golden.win_rate,
        "tier": golden.current_tier
    }

    return {
        "synced": True,
        "old_state": old_state,
        "new_state": new_state,
        "hft_truth": hft,
        "executor_truth": executor,
        "tier_advanced": new_state["tier"] > old_state["tier"],
        "changes": {
            "trades_delta": new_state["trades"] - old_state["trades"],
            "pnl_delta": new_state["pnl"] - old_state["pnl"],
            "wr_delta": new_state["win_rate"] - old_state["win_rate"]
        }
    }


def check_tier_requirements() -> Dict:
    """Check current tier requirements and gaps."""
    golden = GoldenState.load()
    tier = golden.get_tier_config()

    trades_gap = max(0, tier.required_trades - golden.tier_trades)
    wr_gap = max(0, tier.required_win_rate - golden.win_rate)
    pnl_ok = golden.tier_pnl > 0

    return {
        "current_tier": golden.current_tier,
        "tier_name": tier.name,
        "trades": {
            "current": golden.tier_trades,
            "required": tier.required_trades,
            "gap": trades_gap,
            "met": trades_gap == 0
        },
        "win_rate": {
            "current": golden.win_rate,
            "required": tier.required_win_rate,
            "gap": wr_gap,
            "met": wr_gap <= 0
        },
        "pnl": {
            "current": golden.tier_pnl,
            "required": "> $0",
            "met": pnl_ok
        },
        "ready_to_advance": trades_gap == 0 and wr_gap <= 0 and pnl_ok
    }


def status_report() -> str:
    """Generate sync status report."""
    hft = get_hft_truth()
    golden = GoldenState.load()
    reqs = check_tier_requirements()

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║             STATE SYNCHRONIZER                               ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  GROUND TRUTH (HFT Logs):                                    ║",
        f"║    Trades: {hft['total_trades']:>6}                                          ║",
        f"║    P&L: ${hft['total_pnl']:>+10.2f}                                     ║",
        f"║    Win Rate: {hft['win_rate']*100:>6.1f}%                                     ║",
        f"║    Wins: {hft['wins']:>4} | Losses: {hft['losses']:>4}                             ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  GOLDEN STATE:                                               ║",
        f"║    Trades: {golden.total_trades:>6}                                          ║",
        f"║    P&L: ${golden.total_pnl:>+10.2f}                                     ║",
        f"║    Win Rate: {golden.win_rate*100:>6.1f}%                                     ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  TIER ADVANCEMENT CHECK:                                     ║",
    ]

    # Trades check
    t = reqs["trades"]
    status = "✓" if t["met"] else f"Need {t['gap']} more"
    lines.append(f"║    Trades: {t['current']}/{t['required']} {status:<25} ║")

    # Win rate check
    w = reqs["win_rate"]
    status = "✓" if w["met"] else f"Need +{w['gap']*100:.1f}%"
    lines.append(f"║    Win Rate: {w['current']*100:.1f}%/{w['required']*100:.0f}% {status:<22} ║")

    # P&L check
    p = reqs["pnl"]
    status = "✓" if p["met"] else "Need positive"
    lines.append(f"║    P&L: ${p['current']:.2f} {status:<29} ║")

    # Ready status
    if reqs["ready_to_advance"]:
        lines.append("║    🟢 READY TO ADVANCE TO NEXT TIER                          ║")
    else:
        lines.append("║    🟡 Not yet ready to advance                               ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  Run: python3 integrafix/state_sync.py sync                  ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines)


def main():
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "sync":
            result = sync_golden_state()
            print(f"Synced: {result['old_state']} → {result['new_state']}")
            if result["tier_advanced"]:
                print("🎉 TIER ADVANCED!")
            print(json.dumps(result, indent=2))
        elif cmd == "check":
            reqs = check_tier_requirements()
            print(json.dumps(reqs, indent=2))
        else:
            print(status_report())
    else:
        print(status_report())


if __name__ == "__main__":
    main()
