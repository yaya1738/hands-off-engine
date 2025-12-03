#!/usr/bin/env python3
"""
Outcome Recorder - Closes the Learning Loop
Tracks trade outcomes and feeds them back to skill systems.

THE FEEDBACK LOOP (Yair's teaching: 'The 100 trade test'):
  TRADE → OUTCOME → MEASURE → LEARN → BETTER TRADE

What this does:
1. Monitors open positions
2. Detects when markets resolve
3. Records win/loss with actual vs predicted
4. Updates calibration buckets
5. Updates skill measurements
6. Generates learning insights

Serving: Yair Siegel
"""

import json
import os
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
OUTCOMES_FILE = STATE_DIR / "trade_outcomes.jsonl"
PENDING_FILE = STATE_DIR / "pending_trades.json"
LEARNING_FILE = STATE_DIR / "learning_insights.json"


class OutcomeRecorder:
    """
    Tracks outcomes to enable real learning.

    Yair's teaching: 'Edge is discovered through doing, not theorized'
    - This means we need actual outcomes, not just predictions
    """

    def __init__(self):
        self.pending = self._load_pending()
        self.learning = self._load_learning()

    def _load_pending(self) -> Dict:
        if PENDING_FILE.exists():
            with open(PENDING_FILE) as f:
                return json.load(f)
        return {"trades": {}}

    def _save_pending(self):
        with open(PENDING_FILE, 'w') as f:
            json.dump(self.pending, f, indent=2)

    def _load_learning(self) -> Dict:
        if LEARNING_FILE.exists():
            with open(LEARNING_FILE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_outcomes": 0,
            "wins": 0,
            "losses": 0,
            "calibration_data": {},  # bucket -> {predicted, actual, count}
            "category_performance": {},
            "insights": []
        }

    def _save_learning(self):
        self.learning["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(LEARNING_FILE, 'w') as f:
            json.dump(self.learning, f, indent=2)

    def _log_outcome(self, outcome: Dict):
        outcome["recorded_at"] = datetime.now(timezone.utc).isoformat()
        with open(OUTCOMES_FILE, 'a') as f:
            f.write(json.dumps(outcome) + "\n")

    def register_trade(self, trade: Dict) -> str:
        """
        Register a trade for outcome tracking.

        Returns trade_id for later outcome lookup.
        """
        trade_id = f"trade_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{len(self.pending['trades'])}"

        self.pending["trades"][trade_id] = {
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "market_id": trade.get("market_id"),
            "market_name": trade.get("market", "")[:80],
            "direction": trade.get("direction"),  # YES or NO
            "entry_price": trade.get("entry_price"),
            "our_estimate": trade.get("our_estimate"),
            "market_estimate": trade.get("market_estimate"),
            "category": trade.get("category"),
            "size": trade.get("size"),
            "edge_at_entry": trade.get("edge"),
            "status": "pending"
        }

        self._save_pending()
        return trade_id

    def check_resolutions(self) -> List[Dict]:
        """
        Check for resolved markets and record outcomes.
        """
        resolved = []

        for trade_id, trade in list(self.pending["trades"].items()):
            if trade["status"] != "pending":
                continue

            market_id = trade.get("market_id")
            if not market_id:
                continue

            # Check if market resolved
            resolution = self._check_market_resolution(market_id)

            if resolution.get("resolved"):
                outcome = self._process_resolution(trade_id, trade, resolution)
                resolved.append(outcome)

        return resolved

    def _check_market_resolution(self, market_id: str) -> Dict:
        """Check if a market has resolved."""
        try:
            # Try gamma API first
            response = requests.get(
                f"https://gamma-api.polymarket.com/markets/{market_id}",
                timeout=10
            )

            if response.status_code == 200:
                market = response.json()

                if market.get("closed"):
                    # Get outcome prices - $1 for winner, $0 for loser
                    prices = json.loads(market.get("outcomePrices", "[]"))

                    if len(prices) >= 2:
                        yes_price = float(prices[0])
                        no_price = float(prices[1])

                        # If one side is at 1.0 and other at 0.0, market resolved
                        if yes_price > 0.99 or no_price > 0.99:
                            return {
                                "resolved": True,
                                "outcome": 1 if yes_price > 0.99 else 0,  # 1=YES won, 0=NO won
                                "final_yes_price": yes_price,
                                "final_no_price": no_price,
                                "resolution_time": market.get("endDate")
                            }

            return {"resolved": False}

        except Exception as e:
            return {"resolved": False, "error": str(e)}

    def _process_resolution(self, trade_id: str, trade: Dict, resolution: Dict) -> Dict:
        """
        Process a resolved trade and update learning systems.
        """
        direction = trade.get("direction", "YES")
        outcome = resolution.get("outcome", 0)  # 1=YES won, 0=NO won

        # Did we win?
        won = (direction == "YES" and outcome == 1) or (direction == "NO" and outcome == 0)

        # Calculate P&L
        entry_price = trade.get("entry_price", 0.5)
        size = trade.get("size", 1)

        if won:
            # We bought at entry_price, paid out at $1
            pnl = (1 - entry_price) * size
        else:
            # We lost our stake
            pnl = -entry_price * size

        outcome_record = {
            "trade_id": trade_id,
            "market_name": trade.get("market_name"),
            "category": trade.get("category"),
            "direction": direction,
            "entry_price": entry_price,
            "our_estimate": trade.get("our_estimate"),
            "market_estimate": trade.get("market_estimate"),
            "actual_outcome": outcome,
            "won": won,
            "pnl": pnl,
            "edge_at_entry": trade.get("edge_at_entry"),
            "resolution": resolution
        }

        # Log outcome
        self._log_outcome(outcome_record)

        # Update learning systems
        self._update_learning(outcome_record)

        # Mark trade as resolved
        self.pending["trades"][trade_id]["status"] = "resolved"
        self.pending["trades"][trade_id]["outcome"] = outcome_record
        self._save_pending()

        return outcome_record

    def _update_learning(self, outcome: Dict):
        """
        Update all learning systems with this outcome.

        THE LEARNING LOOP:
        1. Update calibration (predicted vs actual)
        2. Update category performance
        3. Generate insights
        """
        self.learning["total_outcomes"] += 1

        if outcome["won"]:
            self.learning["wins"] += 1
        else:
            self.learning["losses"] += 1

        # Update calibration buckets
        our_estimate = outcome.get("our_estimate", 0.5)
        actual = outcome.get("actual_outcome", 0)

        # Bucket by 10% intervals
        bucket = str(int(our_estimate * 10) / 10)
        if bucket not in self.learning["calibration_data"]:
            self.learning["calibration_data"][bucket] = {
                "sum_predicted": 0,
                "sum_actual": 0,
                "count": 0
            }

        self.learning["calibration_data"][bucket]["sum_predicted"] += our_estimate
        self.learning["calibration_data"][bucket]["sum_actual"] += actual
        self.learning["calibration_data"][bucket]["count"] += 1

        # Update category performance
        category = outcome.get("category", "general")
        if category not in self.learning["category_performance"]:
            self.learning["category_performance"][category] = {
                "trades": 0,
                "wins": 0,
                "total_pnl": 0,
                "total_edge": 0
            }

        cat_data = self.learning["category_performance"][category]
        cat_data["trades"] += 1
        if outcome["won"]:
            cat_data["wins"] += 1
        cat_data["total_pnl"] += outcome.get("pnl", 0)
        cat_data["total_edge"] += outcome.get("edge_at_entry", 0)

        # Generate insights every 10 trades
        if self.learning["total_outcomes"] % 10 == 0:
            self._generate_insights()

        self._save_learning()

    def _generate_insights(self):
        """
        Generate learning insights from accumulated data.

        Yair's teaching: 'Look at what's working, do more of that'
        """
        insights = []

        # Calibration insights
        for bucket, data in self.learning["calibration_data"].items():
            if data["count"] >= 5:
                avg_predicted = data["sum_predicted"] / data["count"]
                avg_actual = data["sum_actual"] / data["count"]
                diff = avg_actual - avg_predicted

                if abs(diff) > 0.1:
                    if diff > 0:
                        insights.append({
                            "type": "calibration",
                            "message": f"Under-estimating in {bucket} bucket: actual {avg_actual:.0%} vs predicted {avg_predicted:.0%}",
                            "recommendation": "Increase estimates for similar markets"
                        })
                    else:
                        insights.append({
                            "type": "calibration",
                            "message": f"Over-estimating in {bucket} bucket: actual {avg_actual:.0%} vs predicted {avg_predicted:.0%}",
                            "recommendation": "Decrease estimates for similar markets"
                        })

        # Category insights
        for category, data in self.learning["category_performance"].items():
            if data["trades"] >= 5:
                win_rate = data["wins"] / data["trades"]

                if win_rate > 0.6:
                    insights.append({
                        "type": "category_edge",
                        "message": f"Strong in {category}: {win_rate:.0%} win rate over {data['trades']} trades",
                        "recommendation": f"Trade MORE in {category}"
                    })
                elif win_rate < 0.4:
                    insights.append({
                        "type": "category_weakness",
                        "message": f"Weak in {category}: {win_rate:.0%} win rate over {data['trades']} trades",
                        "recommendation": f"Trade LESS in {category} or improve analysis"
                    })

        # Store insights
        self.learning["insights"] = insights[-20:]  # Keep last 20 insights

    def get_calibration_report(self) -> Dict:
        """Get calibration statistics."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_outcomes": self.learning["total_outcomes"],
            "overall_win_rate": 0,
            "calibration_by_bucket": {},
            "brier_score": None
        }

        if self.learning["total_outcomes"] > 0:
            report["overall_win_rate"] = self.learning["wins"] / self.learning["total_outcomes"]

        # Calibration by bucket
        total_brier = 0
        total_count = 0

        for bucket, data in self.learning["calibration_data"].items():
            if data["count"] > 0:
                avg_predicted = data["sum_predicted"] / data["count"]
                avg_actual = data["sum_actual"] / data["count"]

                report["calibration_by_bucket"][bucket] = {
                    "avg_predicted": avg_predicted,
                    "avg_actual": avg_actual,
                    "count": data["count"],
                    "calibration_error": avg_actual - avg_predicted
                }

                # Accumulate for Brier score
                total_brier += data["count"] * (avg_predicted - avg_actual) ** 2
                total_count += data["count"]

        if total_count > 0:
            report["brier_score"] = total_brier / total_count

        return report

    def run_outcome_recording(self) -> Dict:
        """Run full outcome recording cycle."""
        print("=" * 70)
        print("OUTCOME RECORDER - Closing the Learning Loop")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[YAIR'S TEACHING]")
        print("  'The 100 trade test' - need real outcomes to learn")
        print("  'Edge is discovered through doing' - measure what happens")
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pending_trades": len([t for t in self.pending["trades"].values() if t["status"] == "pending"]),
            "newly_resolved": 0,
            "total_outcomes": self.learning["total_outcomes"]
        }

        # Check pending trades
        print(f"[CHECKING {results['pending_trades']} PENDING TRADES]")

        if results["pending_trades"] > 0:
            resolved = self.check_resolutions()
            results["newly_resolved"] = len(resolved)

            if resolved:
                print(f"\n[NEWLY RESOLVED: {len(resolved)}]")
                for outcome in resolved:
                    status = "WIN" if outcome["won"] else "LOSS"
                    print(f"  {status}: {outcome['market_name'][:50]}...")
                    print(f"    Entry: {outcome['entry_price']:.2f} | Direction: {outcome['direction']}")
                    print(f"    Our estimate: {outcome['our_estimate']:.2f} | Actual: {outcome['actual_outcome']}")
                    print(f"    P&L: ${outcome['pnl']:.2f}")
                    print()

        # Show calibration report
        calibration = self.get_calibration_report()
        results["calibration"] = calibration

        print("[CALIBRATION REPORT]")
        print(f"  Total outcomes: {calibration['total_outcomes']}")
        if calibration['total_outcomes'] > 0:
            print(f"  Overall win rate: {calibration['overall_win_rate']:.0%}")
            if calibration['brier_score'] is not None:
                print(f"  Brier score: {calibration['brier_score']:.4f}")

        if calibration["calibration_by_bucket"]:
            print("\n  Calibration by probability bucket:")
            for bucket, data in sorted(calibration["calibration_by_bucket"].items()):
                error = data['calibration_error']
                direction = "under" if error > 0 else "over"
                print(f"    {bucket}: predicted {data['avg_predicted']:.0%}, actual {data['avg_actual']:.0%} ({direction}-estimated)")
        print()

        # Show category performance
        print("[CATEGORY PERFORMANCE]")
        for category, data in self.learning.get("category_performance", {}).items():
            if data["trades"] > 0:
                win_rate = data["wins"] / data["trades"]
                print(f"  {category}: {win_rate:.0%} win rate ({data['trades']} trades, ${data['total_pnl']:.2f} P&L)")
        print()

        # Show insights
        if self.learning.get("insights"):
            print("[LEARNING INSIGHTS]")
            for insight in self.learning["insights"][-5:]:
                print(f"  {insight['type'].upper()}: {insight['message']}")
                print(f"    → {insight['recommendation']}")
            print()

        print("=" * 70)
        print("THE FEEDBACK LOOP")
        print("=" * 70)
        print("  TRADE → OUTCOME → MEASURE → LEARN → BETTER TRADE")
        print(f"  Currently: {results['pending_trades']} pending, {results['total_outcomes']} completed")
        print()

        return results


def main():
    recorder = OutcomeRecorder()
    return recorder.run_outcome_recording()


if __name__ == "__main__":
    main()
