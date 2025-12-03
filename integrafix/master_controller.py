#!/usr/bin/env python3
"""
INTEGRAFIX: Master Controller
=============================

Unified command center for the $5M/month trading system.

Integrates:
- Golden State tracking
- Edge Optimization
- System Hardening
- Auto-Scaling
- Live Dashboard
- Performance Analytics

Target: Solidify system to achieve $5,000,000/month through
progressive scaling and proven performance.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrafix.golden_state import GoldenState, SCALING_TIERS, status_report as golden_status
from integrafix.edge_optimizer import EdgeOptimizer, status_report as edge_status
from integrafix.system_hardening import SystemHardening, status_report as hardening_status
from integrafix.auto_scaler import AutoScaler, status_report as scaler_status
from integrafix.live_dashboard import render_dashboard


class MasterController:
    """Master controller for INTEGRAFIX system."""

    def __init__(self):
        self.golden = GoldenState.load()
        self.optimizer = EdgeOptimizer()
        self.hardening = SystemHardening()
        self.scaler = AutoScaler()

    def full_status(self) -> str:
        """Generate comprehensive system status."""
        health = self.hardening.check_system_health()
        tier = self.golden.get_tier_config()
        projection = self.golden.monthly_projection()

        lines = [
            "",
            "╔══════════════════════════════════════════════════════════════════════════╗",
            "║                    INTEGRAFIX MASTER CONTROL                             ║",
            "║                    Target: $5,000,000/month                              ║",
            "╠══════════════════════════════════════════════════════════════════════════╣",
        ]

        # Golden state status
        if self.golden.golden_achieved:
            lines.append("║  🏆 GOLDEN STATE ACHIEVED                                                ║")
        else:
            progress = (self.golden.tier_trades / tier.required_trades) * 100
            lines.append(f"║  Progress: Tier {self.golden.current_tier} ({tier.name}) - {progress:.0f}% to next tier                 ║")

        lines.extend([
            "╠══════════════════════════════════════════════════════════════════════════╣",
            "║  PERFORMANCE METRICS                                                     ║",
            f"║    Total Trades: {self.golden.total_trades:>8,}                                              ║",
            f"║    Total P&L: ${self.golden.total_pnl:>+12,.2f}                                          ║",
            f"║    Win Rate: {self.golden.win_rate*100:>8.1f}%                                               ║",
            f"║    Monthly Projection: ${projection:>12,.0f}                                     ║",
            "╠══════════════════════════════════════════════════════════════════════════╣",
            "║  CURRENT LIMITS                                                          ║",
            f"║    Max Exposure: ${tier.max_exposure:>12,.0f}                                          ║",
            f"║    Max Position: ${tier.max_position:>12,.0f}                                          ║",
            f"║    Daily Trades: {tier.daily_trade_limit:>8}                                              ║",
            f"║    Kelly Fraction: {tier.kelly_fraction*100:>6.0f}%                                             ║",
            "╠══════════════════════════════════════════════════════════════════════════╣",
            "║  SYSTEM HEALTH                                                           ║",
        ])

        health_emoji = {"healthy": "🟢", "degraded": "🟡", "critical": "🔴"}
        lines.append(f"║    Status: {health_emoji.get(health.status, '?')} {health.status.upper():<56} ║")
        lines.append(f"║    Processes: {health.processes_running}/{health.processes_total} running                                           ║")

        # Gap analysis
        target = 5_000_000
        gap = target - projection
        gap_pct = (projection / target) * 100 if target > 0 else 0

        lines.extend([
            "╠══════════════════════════════════════════════════════════════════════════╣",
            "║  GAP TO TARGET                                                           ║",
            f"║    Target: ${target:>12,}/month                                        ║",
            f"║    Current Projection: ${projection:>12,.0f}/month                               ║",
            f"║    Gap: ${gap:>+14,.0f} ({gap_pct:.2f}% achieved)                          ║",
        ])

        # Path forward
        path = self.scaler.project_to_golden()
        lines.extend([
            "╠══════════════════════════════════════════════════════════════════════════╣",
            "║  PATH FORWARD                                                            ║",
            f"║    Trades to golden: {path['total_trades_to_golden']:>8,}                                          ║",
            f"║    Estimated time: {path['projected_time_days']:.0f} days                                            ║",
        ])

        lines.extend([
            "╠══════════════════════════════════════════════════════════════════════════╣",
            "║  COMMANDS                                                                ║",
            "║    integrafix status     - This overview                                 ║",
            "║    integrafix dashboard  - Live trading dashboard                        ║",
            "║    integrafix golden     - Golden state details                          ║",
            "║    integrafix edge       - Edge optimizer status                         ║",
            "║    integrafix health     - System health details                         ║",
            "║    integrafix scale      - Auto-scaler status                            ║",
            "║    integrafix run        - Run continuous operation                      ║",
            "╚══════════════════════════════════════════════════════════════════════════╝",
        ])

        return "\n".join(lines)

    def run_continuous(self, check_interval: int = 60):
        """Run continuous INTEGRAFIX operation."""
        print("[INTEGRAFIX] Starting continuous operation")
        print(f"[INTEGRAFIX] Target: $5,000,000/month")
        print(f"[INTEGRAFIX] Current tier: {self.golden.current_tier}")

        import time

        iteration = 0
        while True:
            try:
                iteration += 1

                # 1. Check system health
                health = self.hardening.check_system_health()
                if health.status == "critical":
                    print(f"[INTEGRAFIX] CRITICAL: System unhealthy, enforcing health")
                    self.hardening.enforce_health()

                # 2. Check for scaling
                result = self.scaler.run_check()
                if result["action"]:
                    print(f"[INTEGRAFIX] SCALING: {result['action']} from tier {result['from_tier']} to {result['to_tier']}")
                    print(f"[INTEGRAFIX] Reason: {result['reason']}")

                # 3. Log status every 10 iterations
                if iteration % 10 == 0:
                    projection = self.golden.monthly_projection()
                    print(f"[INTEGRAFIX] Status: Tier {self.golden.current_tier} | "
                          f"Trades: {self.golden.total_trades} | "
                          f"P&L: ${self.golden.total_pnl:.2f} | "
                          f"WR: {self.golden.win_rate*100:.1f}% | "
                          f"Proj: ${projection:,.0f}/mo")

                time.sleep(check_interval)

            except KeyboardInterrupt:
                print("[INTEGRAFIX] Stopped by user")
                break
            except Exception as e:
                print(f"[INTEGRAFIX] Error: {e}")
                time.sleep(check_interval)


def main():
    controller = MasterController()

    if len(sys.argv) < 2:
        print(controller.full_status())
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        print(controller.full_status())
    elif cmd == "dashboard":
        print(render_dashboard())
    elif cmd == "golden":
        print(golden_status())
    elif cmd == "edge":
        print(edge_status())
    elif cmd == "health":
        print(hardening_status())
    elif cmd == "scale":
        print(scaler_status())
    elif cmd == "run":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        controller.run_continuous(interval)
    elif cmd == "all":
        # Print all status reports
        print(controller.full_status())
        print("\n" + "=" * 78 + "\n")
        print(golden_status())
        print("\n" + "=" * 78 + "\n")
        print(edge_status())
        print("\n" + "=" * 78 + "\n")
        print(hardening_status())
        print("\n" + "=" * 78 + "\n")
        print(scaler_status())
    else:
        print(controller.full_status())


if __name__ == "__main__":
    main()
