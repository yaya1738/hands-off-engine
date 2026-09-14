#!/usr/bin/env python3
"""
REVENUE TRACKER - Track income and adjust strategy
====================================================

Tracks:
- Trading P&L
- Consulting income
- Position resolutions
- Any other income

Feeds back to strategy adjustment.

Master: Yair Siegel
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
REVENUE_STATE = STATE_DIR / "revenue_tracker.json"
REVENUE_HISTORY = STATE_DIR / "revenue_history.jsonl"


class RevenueTracker:
    """Track all income sources and learn what works."""

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if REVENUE_STATE.exists():
            return json.load(open(REVENUE_STATE))
        return {
            "total_revenue": 0,
            "total_costs": 0,
            "net": 0,
            "by_source": {},
            "best_performing": None,
            "worst_performing": None,
            "last_updated": None
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(REVENUE_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def record_income(self, source: str, amount: float, description: str = ""):
        """Record income from any source."""
        now = datetime.now(timezone.utc)

        self.state["total_revenue"] += amount
        self.state["net"] = self.state["total_revenue"] - self.state["total_costs"]

        if source not in self.state["by_source"]:
            self.state["by_source"][source] = {"total": 0, "count": 0, "avg": 0}

        self.state["by_source"][source]["total"] += amount
        self.state["by_source"][source]["count"] += 1
        self.state["by_source"][source]["avg"] = (
            self.state["by_source"][source]["total"] /
            self.state["by_source"][source]["count"]
        )

        # Update best/worst
        sources = self.state["by_source"]
        if sources:
            self.state["best_performing"] = max(sources, key=lambda s: sources[s]["total"])
            self.state["worst_performing"] = min(sources, key=lambda s: sources[s]["total"])

        self._save_state()

        # Log to history
        with open(REVENUE_HISTORY, 'a') as f:
            f.write(json.dumps({
                "timestamp": now.isoformat(),
                "type": "income",
                "source": source,
                "amount": amount,
                "description": description
            }) + '\n')

        return self.state["net"]

    def record_cost(self, category: str, amount: float, description: str = ""):
        """Record a cost."""
        now = datetime.now(timezone.utc)

        self.state["total_costs"] += amount
        self.state["net"] = self.state["total_revenue"] - self.state["total_costs"]

        self._save_state()

        with open(REVENUE_HISTORY, 'a') as f:
            f.write(json.dumps({
                "timestamp": now.isoformat(),
                "type": "cost",
                "category": category,
                "amount": amount,
                "description": description
            }) + '\n')

        return self.state["net"]

    def get_strategy_feedback(self) -> Dict:
        """Get feedback for strategy adjustment."""
        feedback = {
            "net_position": self.state["net"],
            "profitable": self.state["net"] > 0,
            "recommendations": []
        }

        # Recommend focusing on best performer
        if self.state["best_performing"]:
            best = self.state["best_performing"]
            feedback["recommendations"].append(
                f"Focus on {best} - best performer with ${self.state['by_source'][best]['total']:.2f}"
            )

        # Recommend cutting worst performer
        if self.state["worst_performing"] and self.state["by_source"].get(self.state["worst_performing"], {}).get("total", 0) < 0:
            worst = self.state["worst_performing"]
            feedback["recommendations"].append(
                f"Cut {worst} - losing ${abs(self.state['by_source'][worst]['total']):.2f}"
            )

        return feedback

    def get_status(self) -> Dict:
        """Get current revenue status."""
        return {
            "total_revenue": self.state["total_revenue"],
            "total_costs": self.state["total_costs"],
            "net": self.state["net"],
            "by_source": self.state["by_source"],
            "best": self.state["best_performing"],
            "worst": self.state["worst_performing"],
            "feedback": self.get_strategy_feedback()
        }


def get_revenue_tracker() -> RevenueTracker:
    return RevenueTracker()


if __name__ == "__main__":
    import sys
    tracker = get_revenue_tracker()

    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            print(json.dumps(tracker.get_status(), indent=2))
        elif sys.argv[1] == "income" and len(sys.argv) >= 4:
            source = sys.argv[2]
            amount = float(sys.argv[3])
            desc = sys.argv[4] if len(sys.argv) > 4 else ""
            tracker.record_income(source, amount, desc)
            print(f"Recorded ${amount} from {source}")
        elif sys.argv[1] == "cost" and len(sys.argv) >= 4:
            cat = sys.argv[2]
            amount = float(sys.argv[3])
            desc = sys.argv[4] if len(sys.argv) > 4 else ""
            tracker.record_cost(cat, amount, desc)
            print(f"Recorded ${amount} cost for {cat}")
    else:
        print("Usage: python revenue_tracker.py [status|income <source> <amount>|cost <category> <amount>]")
