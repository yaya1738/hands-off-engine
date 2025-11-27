#!/usr/bin/env python3
"""
Cash Explosion Runner - Autonomous Trading Pipeline Executor
============================================================

This script orchestrates the complete cash explosion operation:
1. Fetches fresh market data from Polymarket
2. Runs alpha signal generation
3. Executes decider and executor pipeline
4. Logs results and sends notifications
5. Updates system state for monitoring

Designed to be run via cron or called by autonomous agents.
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.fetch_live_markets import fetch_live_markets, save_market_data
from scripts.run_pipeline import run_pipeline

# Configuration
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs" / "cash_explosion"


class CashExplosionRunner:
    """Orchestrates the complete cash explosion operation."""

    def __init__(self, bankroll: float = 1500.0, dryrun: bool = True):
        self.bankroll = bankroll
        self.dryrun = dryrun
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.results = {
            "run_id": self.run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "bankroll": bankroll,
            "mode": "DRYRUN" if dryrun else "LIVE",
            "steps": {},
            "success": False
        }

    def run(self) -> Dict:
        """Execute the complete cash explosion operation."""
        print("=" * 60)
        print("  CASH EXPLOSION OPERATION")
        print("=" * 60)
        print(f"  Run ID: {self.run_id}")
        print(f"  Bankroll: ${self.bankroll:.2f}")
        print(f"  Mode: {'DRYRUN (safe)' if self.dryrun else 'LIVE (real money!)'}")
        print("=" * 60)
        print()

        try:
            # Step 1: Fetch fresh market data
            self._step_fetch_markets()

            # Step 2: Run trading pipeline
            self._step_run_pipeline()

            # Step 3: Generate status report
            self._step_generate_report()

            # Step 4: Send notifications
            self._step_send_notifications()

            self.results["success"] = True
            self.results["completed_at"] = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            self.results["success"] = False
            self.results["error"] = str(e)
            self.results["completed_at"] = datetime.now(timezone.utc).isoformat()
            print(f"\nCASH EXPLOSION FAILED: {e}")

        # Save run log
        self._save_run_log()

        return self.results

    def _step_fetch_markets(self):
        """Step 1: Fetch fresh market data."""
        print("\n[1/4] Fetching fresh market data...")

        try:
            # Fetch live data
            data = fetch_live_markets(
                categories=["bitcoin", "ethereum", "trump", "politics", "crypto"],
                markets_per_category=12
            )

            # Save to compact file
            output_path = REPO_ROOT / "termux-hands-off" / "out" / "polymarket-compact.json"
            save_market_data(data, output_path)

            total_markets = sum(data["counts"].values())
            self.results["steps"]["fetch"] = {
                "success": True,
                "markets_fetched": total_markets,
                "categories": data["counts"],
                "timestamp": data["timestamp"]
            }

            print(f"  Fetched {total_markets} markets")
            print(f"  Categories: {data['counts']}")

        except Exception as e:
            self.results["steps"]["fetch"] = {
                "success": False,
                "error": str(e)
            }
            raise Exception(f"Market fetch failed: {e}")

    def _step_run_pipeline(self):
        """Step 2: Run the trading pipeline."""
        print("\n[2/4] Running trading pipeline...")

        try:
            pipeline_results = run_pipeline(
                bankroll=self.bankroll,
                dryrun=self.dryrun,
                verbose=True
            )

            self.results["steps"]["pipeline"] = pipeline_results["steps"]
            self.results["pipeline_success"] = pipeline_results["success"]

            # Extract key metrics
            exec_step = pipeline_results["steps"].get("execute", {})
            self.results["trades_executed"] = exec_step.get("successful", 0)
            self.results["trades_rejected"] = exec_step.get("rejected", 0)
            self.results["total_deployed"] = exec_step.get("total_amount", 0)

        except Exception as e:
            self.results["steps"]["pipeline"] = {
                "success": False,
                "error": str(e)
            }
            raise Exception(f"Pipeline failed: {e}")

    def _step_generate_report(self):
        """Step 3: Generate cash explosion status report."""
        print("\n[3/4] Generating status report...")

        try:
            # Read execution plan
            exec_plan_path = REPO_ROOT / "executor" / "execution_plan.json"
            if exec_plan_path.exists():
                with open(exec_plan_path) as f:
                    exec_plan = json.load(f)
            else:
                exec_plan = {}

            # Generate report
            report = {
                "run_id": self.run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": "DRYRUN" if self.dryrun else "LIVE",
                "bankroll": self.bankroll,
                "deployment": {
                    "total_usd": self.results.get("total_deployed", 0),
                    "percentage": (self.results.get("total_deployed", 0) / self.bankroll) * 100,
                    "trades": self.results.get("trades_executed", 0)
                },
                "orders": exec_plan.get("orders", []),
                "metrics": {
                    "markets_analyzed": self.results["steps"].get("fetch", {}).get("markets_fetched", 0),
                    "signals_generated": self.results["steps"].get("pipeline", {}).get("sync", {}).get("markets_selected", 0),
                    "trades_planned": self.results["steps"].get("pipeline", {}).get("decide", {}).get("actions_planned", 0),
                    "trades_executed": self.results.get("trades_executed", 0),
                    "trades_rejected": self.results.get("trades_rejected", 0)
                }
            }

            # Save report
            report_path = STATE_DIR / "cash_explosion_status.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            self.results["steps"]["report"] = {"success": True, "path": str(report_path)}
            print(f"  Report saved: {report_path}")

        except Exception as e:
            self.results["steps"]["report"] = {"success": False, "error": str(e)}
            print(f"  Warning: Report generation failed: {e}")

    def _step_send_notifications(self):
        """Step 4: Send notifications."""
        print("\n[4/4] Sending notifications...")

        try:
            # Build notification message
            total = self.results.get("total_deployed", 0)
            trades = self.results.get("trades_executed", 0)
            mode = "DRYRUN" if self.dryrun else "LIVE"

            message = f"""Cash Explosion Complete

Mode: {mode}
Trades: {trades}
Deployed: ${total:.2f} ({total/self.bankroll*100:.1f}% of bankroll)

Run ID: {self.run_id}"""

            # Try to send Telegram notification
            self._send_telegram(message)

            self.results["steps"]["notify"] = {"success": True}
            print(f"  Notification sent")

        except Exception as e:
            self.results["steps"]["notify"] = {"success": False, "error": str(e)}
            print(f"  Warning: Notification failed: {e}")

    def _send_telegram(self, message: str):
        """Send notification via Telegram."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            print("  Telegram not configured - skipping notification")
            return

        try:
            import urllib.request
            import urllib.parse

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": message
            }).encode()

            req = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req, timeout=10)

        except Exception as e:
            print(f"  Telegram error: {e}")

    def _save_run_log(self):
        """Save run log for history."""
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_path = LOGS_DIR / f"run_{self.run_id}.json"

            with open(log_path, "w") as f:
                json.dump(self.results, f, indent=2)

            print(f"\nRun log saved: {log_path}")

        except Exception as e:
            print(f"Warning: Could not save run log: {e}")


def get_cash_explosion_status() -> Dict:
    """Get current cash explosion status for monitoring."""
    status_path = STATE_DIR / "cash_explosion_status.json"

    if not status_path.exists():
        return {"status": "not_run", "message": "Cash explosion has not been run yet"}

    with open(status_path) as f:
        return json.load(f)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run cash explosion operation")
    parser.add_argument(
        "--bankroll",
        type=float,
        default=1500.0,
        help="Trading bankroll (default: 1500.0)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in LIVE mode (real money!)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current status instead of running"
    )

    args = parser.parse_args()

    if args.status:
        status = get_cash_explosion_status()
        print(json.dumps(status, indent=2))
        return 0

    # Safety check for live mode
    if args.live:
        print("\nWARNING: LIVE mode will use REAL MONEY!")
        print("Type 'YES' to confirm: ", end="")
        if input().strip() != "YES":
            print("Aborted.")
            return 1

    runner = CashExplosionRunner(
        bankroll=args.bankroll,
        dryrun=not args.live
    )

    results = runner.run()

    # Summary
    print("\n" + "=" * 60)
    print("  CASH EXPLOSION SUMMARY")
    print("=" * 60)
    print(f"  Status: {'SUCCESS' if results['success'] else 'FAILED'}")
    print(f"  Trades Executed: {results.get('trades_executed', 0)}")
    print(f"  Total Deployed: ${results.get('total_deployed', 0):.2f}")
    print("=" * 60)

    return 0 if results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
