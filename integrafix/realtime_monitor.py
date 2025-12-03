#!/usr/bin/env python3
"""
INTEGRAFIX: Real-Time Monitor
=============================

Live monitoring of system performance:
- Win rate tracking
- P&L updates
- Tier progress
- Trade flow
- Alert on important events

Run: python3 integrafix/realtime_monitor.py
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"


def get_live_metrics() -> Dict:
    """Get current live metrics."""
    hft_log = LOGS_DIR / "hft_economics.jsonl"

    total = 0
    wins = 0
    pnl = 0.0
    recent_trades = []

    if hft_log.exists():
        with open(hft_log) as f:
            lines = f.readlines()

        for line in lines:
            try:
                d = json.loads(line)
                if d.get("type") == "trade_close":
                    total += 1
                    cost = d.get("cost", 0)
                    pnl += cost
                    if cost > 0:
                        wins += 1
                    recent_trades.append({
                        "ts": d.get("ts_us", 0),
                        "pnl": cost,
                        "won": cost > 0
                    })
            except:
                pass

    win_rate = wins / total if total > 0 else 0

    # Get last 10 trades
    recent = recent_trades[-10:] if recent_trades else []

    # Calculate recent win rate (last 20 trades)
    last_20 = recent_trades[-20:] if len(recent_trades) >= 20 else recent_trades
    recent_wr = sum(1 for t in last_20 if t["won"]) / len(last_20) if last_20 else 0

    return {
        "total_trades": total,
        "wins": wins,
        "losses": total - wins,
        "pnl": pnl,
        "win_rate": win_rate,
        "recent_win_rate": recent_wr,
        "recent_trades": recent,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_tier_status() -> Dict:
    """Get current tier status."""
    try:
        from integrafix.golden_state import GoldenState
        golden = GoldenState.load()
        tier = golden.get_tier_config()

        return {
            "tier": golden.current_tier,
            "tier_name": tier.name,
            "trades": golden.tier_trades,
            "required_trades": tier.required_trades,
            "win_rate": golden.win_rate,
            "required_wr": tier.required_win_rate,
            "trades_progress": golden.tier_trades / tier.required_trades,
            "wr_gap": tier.required_win_rate - golden.win_rate,
            "ready": golden.tier_trades >= tier.required_trades and golden.win_rate >= tier.required_win_rate
        }
    except:
        return {"tier": 0, "tier_name": "Unknown"}


def get_booster_status() -> Dict:
    """Get win rate booster status."""
    try:
        from integrafix.win_rate_booster import get_booster
        booster = get_booster()
        return booster.get_status()
    except:
        return {"mode": "Unknown"}


def render_monitor() -> str:
    """Render real-time monitor display."""
    metrics = get_live_metrics()
    tier = get_tier_status()
    booster = get_booster_status()

    # Determine indicators
    wr = metrics["win_rate"]
    wr_color = "🟢" if wr >= 0.55 else "🟡" if wr >= 0.52 else "🔴"

    recent_wr = metrics["recent_win_rate"]
    trend = "↑" if recent_wr > wr else "↓" if recent_wr < wr else "→"

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║          INTEGRAFIX REAL-TIME MONITOR                        ║",
        f"║          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                              ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  {wr_color} WIN RATE: {wr*100:>6.2f}% {trend} (Recent: {recent_wr*100:.1f}%)                ║",
        f"║  P&L: ${metrics['pnl']:>+10.2f}                                       ║",
        f"║  Trades: {metrics['total_trades']:>5} (W:{metrics['wins']} L:{metrics['losses']})                          ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  TIER: {tier['tier']} ({tier['tier_name']})                                       ║",
        f"║  Progress: {tier.get('trades_progress', 0)*100:>5.0f}% trades | WR gap: {tier.get('wr_gap', 0)*100:>+5.1f}%         ║",
    ]

    if tier.get("ready"):
        lines.append("║  🎉 READY TO ADVANCE!                                        ║")
    else:
        if tier.get("wr_gap", 0) > 0:
            lines.append(f"║  Need: WR +{tier.get('wr_gap', 0)*100:.1f}% to advance                              ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  BOOSTER: {booster.get('mode', 'Off'):<48} ║",
        f"║  Filtered: {booster.get('signals_filtered', 0):>5} | Passed: {booster.get('signals_passed', 0):>5}                    ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  RECENT TRADES:                                              ║",
    ])

    # Show recent trades
    for trade in metrics["recent_trades"][-5:]:
        icon = "✓" if trade["won"] else "✗"
        lines.append(f"║    {icon} ${trade['pnl']:>+6.2f}                                           ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  Target: 55% WR → Tier 1 → $5M/month                         ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines)


def watch(interval: int = 5):
    """Watch mode - refresh every N seconds."""
    while True:
        try:
            os.system('clear' if os.name == 'posix' else 'cls')
            print(render_monitor())
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            break


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        watch(interval)
    else:
        print(render_monitor())


if __name__ == "__main__":
    main()
