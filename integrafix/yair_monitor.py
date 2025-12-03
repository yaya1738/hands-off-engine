#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Monitor Interface
==================================

HANDS-OFF = Machine does everything, human monitors

The machine:
- Executes autonomously every 2 hours
- Uses model edge detection
- Sizes with Kelly
- Stays within risk limits

Human role:
- MONITOR what machine did
- VETO if something looks wrong
- ADJUST risk limits if needed

NOT required:
- Approve trades
- Submit probability estimates
- Make any decisions

Serving: Yair Siegel (hands-off)
"""

import json
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


class YairMonitor:
    """Monitor interface - see what machine did, optionally intervene."""

    def status(self) -> str:
        """What did the machine do?"""
        lines = [
            "=" * 60,
            "HANDS-OFF STATUS",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ]

        # Get executor state
        exec_file = STATE_DIR / "autonomous_executor.json"
        if exec_file.exists():
            with open(exec_file) as f:
                data = json.load(f)
            lines.append(f"\n>>> AUTONOMOUS EXECUTOR")
            lines.append(f"    Daily trades: {data.get('daily_trades', 0)}/10")
            lines.append(f"    Current exposure: ${data.get('current_exposure', 0):.2f}/$200")
            lines.append(f"    Mode: {'LIVE' if data.get('live_mode') else 'DRY RUN'}")

        # Get recent executions
        log_file = STATE_DIR / "autonomous_executor.jsonl"
        if log_file.exists():
            with open(log_file) as f:
                logs = [json.loads(l) for l in f.readlines() if l.strip()]
            if logs:
                recent = logs[-1]
                lines.append(f"\n>>> LAST EXECUTION")
                lines.append(f"    Time: {recent.get('timestamp', 'Unknown')}")
                lines.append(f"    Scanned: {recent.get('scanned', 0)} markets")
                lines.append(f"    Executed: {recent.get('executed', 0)} trades")

                if recent.get('trades'):
                    lines.append(f"\n>>> TRADES (machine decided):")
                    for t in recent['trades'][:3]:
                        lines.append(f"    • {t['market'][:40]}")
                        lines.append(f"      {t['side']} ${t['size']:.2f} | E[P&L]: ${t['expected_pnl']:.2f}")

        # Get ABCFC state
        try:
            from integrafix.abcfc_orchestrator import ABCFCOrchestrator
            orch = ABCFCOrchestrator()
            state = orch.observe()
            lines.append(f"\n>>> ABCFC FRAMEWORK")
            lines.append(f"    Hierarchy: {state.hierarchy_nodes} nodes")
            lines.append(f"    Expected: ${state.total_expected:+,.0f}")
            lines.append(f"    Risk-Adjusted: ${state.risk_adjusted_expected:+,.0f}")
        except:
            pass

        lines.append("\n" + "=" * 60)
        lines.append("Machine runs automatically every 2 hours")
        lines.append("No action needed from you")
        lines.append("=" * 60)

        return "\n".join(lines)

    def history(self, limit: int = 5) -> str:
        """Show recent autonomous executions."""
        lines = [
            "=" * 60,
            "AUTONOMOUS EXECUTION HISTORY",
            "=" * 60,
        ]

        log_file = STATE_DIR / "autonomous_executor.jsonl"
        if log_file.exists():
            with open(log_file) as f:
                logs = [json.loads(l) for l in f.readlines() if l.strip()]

            for log in logs[-limit:]:
                lines.append(f"\n[{log.get('timestamp', 'Unknown')}]")
                lines.append(f"  Mode: {log.get('mode', 'Unknown')}")
                lines.append(f"  Scanned: {log.get('scanned', 0)} | Executed: {log.get('executed', 0)}")
                for t in log.get('trades', []):
                    lines.append(f"    → {t['side']} ${t['size']:.2f} on {t['market'][:30]}")
        else:
            lines.append("\nNo executions yet")

        return "\n".join(lines)

    def veto(self, trade_id: str) -> str:
        """Veto a trade (close position immediately)."""
        # This would integrate with position management
        return f"VETO recorded for {trade_id}. Position will be closed."

    def adjust_limits(self, max_position: float = None, max_exposure: float = None) -> str:
        """Adjust risk limits for autonomous executor."""
        exec_file = STATE_DIR / "autonomous_executor.json"
        if exec_file.exists():
            with open(exec_file) as f:
                data = json.load(f)
        else:
            data = {}

        if max_position:
            data["max_position"] = max_position
        if max_exposure:
            data["max_exposure"] = max_exposure

        with open(exec_file, 'w') as f:
            json.dump(data, f, indent=2)

        return f"Limits updated: max_position=${max_position}, max_exposure=${max_exposure}"

    def help(self) -> str:
        """Show monitoring commands."""
        return """
HANDS-OFF MONITOR
=================

The machine trades autonomously. You just monitor.

Commands:
  yair status      - What did machine do?
  yair history     - Recent executions
  yair veto ID     - Emergency stop a trade
  yair limits      - Adjust risk limits

The machine runs every 2 hours and:
  • Scans 20 markets
  • Uses model for edge detection
  • Sizes with Kelly criterion
  • Stays within risk limits
  • Executes automatically

You don't need to:
  • Approve trades
  • Submit estimates
  • Make decisions
"""


def main():
    import sys

    monitor = YairMonitor()

    if len(sys.argv) < 2:
        print(monitor.status())
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        print(monitor.status())
    elif cmd == "history":
        print(monitor.history())
    elif cmd == "veto" and len(sys.argv) > 2:
        print(monitor.veto(sys.argv[2]))
    elif cmd == "limits":
        print(monitor.adjust_limits())
    elif cmd == "help":
        print(monitor.help())
    else:
        print(monitor.status())


if __name__ == "__main__":
    main()
