#!/usr/bin/env python3
"""
INTEGRAFIX: Live Dashboard
==========================

Real-time monitoring of all system components.
Consolidates: P&L, trades, HFT metrics, system health.

Run: python3 integrafix/live_dashboard.py
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"


def get_hft_pnl() -> Dict[str, Any]:
    """Get P&L from HFT economics log."""
    hft_log = LOGS_DIR / "hft_economics.jsonl"
    if not hft_log.exists():
        return {"trades": 0, "pnl": 0, "wins": 0, "losses": 0}

    total = 0
    count = 0
    wins = 0
    losses = 0

    with open(hft_log) as f:
        for line in f:
            try:
                d = json.loads(line)
                if d.get("type") == "trade_close":
                    cost = d.get("cost", 0)
                    total += cost
                    count += 1
                    if cost > 0:
                        wins += 1
                    elif cost < 0:
                        losses += 1
            except:
                pass

    return {
        "trades": count,
        "pnl": total,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / count * 100 if count > 0 else 0
    }


def get_executor_status() -> Dict[str, Any]:
    """Get autonomous executor status."""
    exec_file = STATE_DIR / "autonomous_executor.json"
    if not exec_file.exists():
        return {"active": False}

    with open(exec_file) as f:
        data = json.load(f)

    return {
        "active": True,
        "live_mode": data.get("live_mode", False),
        "daily_trades": data.get("daily_trades", 0),
        "daily_limit": data.get("daily_trade_limit", 10),
        "exposure": data.get("current_exposure", 0),
        "max_exposure": data.get("max_exposure", 200),
        "last_run": data.get("last_execution_time", "Unknown")
    }


def get_process_status() -> Dict[str, bool]:
    """Check which autonomous processes are running."""
    import subprocess

    processes = {
        "backend_loop": False,
        "self_healer": False,
        "hardware_brain": False,
        "scaling_engine": False,
        "infra_manager": False
    }

    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout

        for proc in processes:
            if proc in output:
                processes[proc] = True
    except:
        pass

    return processes


def get_recent_trades(limit: int = 5) -> list:
    """Get recent trade executions."""
    log_file = STATE_DIR / "autonomous_executor.jsonl"
    if not log_file.exists():
        return []

    trades = []
    with open(log_file) as f:
        for line in f:
            try:
                data = json.loads(line)
                for t in data.get("trades", []):
                    trades.append({
                        "time": data.get("timestamp", "Unknown"),
                        "market": t.get("market", "Unknown")[:40],
                        "side": t.get("side", "?"),
                        "size": t.get("size", 0),
                        "expected_pnl": t.get("expected_pnl", 0)
                    })
            except:
                pass

    return trades[-limit:]


def render_dashboard() -> str:
    """Render full dashboard."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    hft = get_hft_pnl()
    executor = get_executor_status()
    processes = get_process_status()
    recent = get_recent_trades(5)

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║          INTEGRAFIX LIVE DASHBOARD                           ║",
        f"║          {now}                              ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  PERFORMANCE                                                 ║",
        f"║  Total P&L: ${hft['pnl']:>+10.2f}                                   ║",
        f"║  Trades: {hft['trades']:>4} | Win Rate: {hft['win_rate']:>5.1f}%                        ║",
        f"║  Wins: {hft['wins']:>4} | Losses: {hft['losses']:>4}                                 ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  EXECUTOR STATUS                                             ║",
    ]

    if executor["active"]:
        mode = "🟢 LIVE" if executor["live_mode"] else "🟡 DRY RUN"
        lines.extend([
            f"║  Mode: {mode}                                          ║",
            f"║  Daily Trades: {executor['daily_trades']}/{executor['daily_limit']}                                       ║",
            f"║  Exposure: ${executor['exposure']:.0f}/${executor['max_exposure']:.0f}                                     ║",
        ])
    else:
        lines.append("║  Executor: NOT ACTIVE                                        ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  PROCESSES                                                   ║",
    ])

    for name, running in processes.items():
        status = "🟢 Running" if running else "🔴 Stopped"
        lines.append(f"║  {name:<15} {status}                              ║")

    if recent:
        lines.extend([
            "╠══════════════════════════════════════════════════════════════╣",
            "║  RECENT TRADES                                               ║",
        ])
        for t in recent[-3:]:
            lines.append(f"║  {t['side']} ${t['size']:.2f} → {t['market'][:35]:<35} ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  SYSTEM: FULLY AUTONOMOUS                                    ║",
        "║  Next execution: Continuous (backend_loop)                   ║",
        "╚══════════════════════════════════════════════════════════════╝",
        ""
    ])

    return "\n".join(lines)


def watch(interval: int = 10):
    """Watch mode - refresh dashboard every N seconds."""
    import time

    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print(render_dashboard())
        time.sleep(interval)


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        watch(interval)
    else:
        print(render_dashboard())


if __name__ == "__main__":
    main()
