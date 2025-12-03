#!/usr/bin/env python3
"""
Compound Improvement Tracker - Track Cumulative Impact of Improvements

Created by autonomous self-modification on 2025-12-02.
This module tracks the compound effect of small improvements over time,
which is essential for achieving escape velocity.

Serving: Yair Siegel
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import math

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
COMPOUND_STATE = STATE_DIR / "compound_tracker.json"
IMPROVEMENTS_LOG = STATE_DIR / "moonshot_improvements.jsonl"


@dataclass
class ImprovementMetric:
    """A single improvement and its measured impact."""
    timestamp: str
    category: str  # capital, automation, income, efficiency
    description: str
    base_value: float  # Value before improvement
    new_value: float   # Value after improvement
    improvement_pct: float  # Percentage improvement
    compound_contribution: float  # Contribution to overall compound effect


class CompoundTracker:
    """Track and visualize compound improvement effects."""

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load compound tracking state."""
        if COMPOUND_STATE.exists():
            with open(COMPOUND_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_improvements": 0,
            "compound_multiplier": 1.0,
            "improvements": [],
            "category_multipliers": {
                "capital": 1.0,
                "automation": 1.0,
                "income": 1.0,
                "efficiency": 1.0,
                "protection": 1.0
            },
            "escape_velocity_contribution": 0.0,
            "projections": {}
        }

    def _save_state(self):
        """Save compound tracking state."""
        with open(COMPOUND_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def record_improvement(
        self,
        category: str,
        description: str,
        base_value: float,
        new_value: float
    ) -> Dict:
        """Record a new improvement and calculate its compound effect."""

        # Calculate improvement percentage
        if base_value > 0:
            improvement_pct = ((new_value - base_value) / base_value) * 100
        else:
            improvement_pct = 100 if new_value > 0 else 0

        # Calculate compound contribution (using continuous compounding)
        # Each 1% improvement adds ~1% to the compound multiplier
        improvement_factor = 1 + (improvement_pct / 100)

        # Update category multiplier
        old_category_mult = self.state["category_multipliers"].get(category, 1.0)
        new_category_mult = old_category_mult * improvement_factor
        self.state["category_multipliers"][category] = new_category_mult

        # Update overall compound multiplier (geometric mean of categories)
        category_values = list(self.state["category_multipliers"].values())
        self.state["compound_multiplier"] = math.prod(category_values) ** (1/len(category_values))

        # Calculate escape velocity contribution
        # Higher compound multiplier = faster path to escape velocity
        ev_contribution = (self.state["compound_multiplier"] - 1) * 100
        self.state["escape_velocity_contribution"] = ev_contribution

        # Create improvement record
        improvement = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "description": description,
            "base_value": base_value,
            "new_value": new_value,
            "improvement_pct": round(improvement_pct, 2),
            "compound_contribution": round(improvement_factor - 1, 4),
            "cumulative_multiplier": round(self.state["compound_multiplier"], 4)
        }

        self.state["improvements"].append(improvement)
        self.state["total_improvements"] += 1

        # Generate projections
        self._update_projections()

        self._save_state()

        return {
            "recorded": True,
            "improvement": improvement,
            "overall_compound_multiplier": self.state["compound_multiplier"],
            "escape_velocity_contribution": ev_contribution
        }

    def _update_projections(self):
        """Update compound growth projections."""
        current_mult = self.state["compound_multiplier"]

        # Project future values at current compound rate
        self.state["projections"] = {
            "7_days": round(current_mult ** 7, 2),
            "30_days": round(current_mult ** 30, 2),
            "90_days": round(current_mult ** 90, 2),
            "365_days": round(current_mult ** 365, 2),
            "days_to_2x": self._days_to_multiple(2.0),
            "days_to_10x": self._days_to_multiple(10.0),
            "days_to_100x": self._days_to_multiple(100.0)
        }

    def _days_to_multiple(self, target: float) -> Optional[int]:
        """Calculate days to reach a target multiple."""
        mult = self.state["compound_multiplier"]
        if mult <= 1:
            return None
        daily_growth = mult - 1  # Daily improvement rate
        if daily_growth <= 0:
            return None
        # Using continuous compounding formula: days = ln(target) / ln(1 + rate)
        try:
            days = math.log(target) / math.log(1 + daily_growth)
            return int(math.ceil(days))
        except (ValueError, ZeroDivisionError):
            return None

    def analyze_improvements(self) -> Dict:
        """Analyze historical improvements for patterns."""
        improvements = self.state["improvements"]

        if not improvements:
            return {"status": "no_data", "message": "No improvements recorded yet"}

        # Category breakdown
        by_category = {}
        for imp in improvements:
            cat = imp["category"]
            if cat not in by_category:
                by_category[cat] = {"count": 0, "total_improvement_pct": 0}
            by_category[cat]["count"] += 1
            by_category[cat]["total_improvement_pct"] += imp["improvement_pct"]

        for cat in by_category:
            by_category[cat]["avg_improvement_pct"] = (
                by_category[cat]["total_improvement_pct"] / by_category[cat]["count"]
            )

        # Most impactful categories
        sorted_cats = sorted(
            self.state["category_multipliers"].items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "total_improvements": self.state["total_improvements"],
            "compound_multiplier": self.state["compound_multiplier"],
            "escape_velocity_contribution": self.state["escape_velocity_contribution"],
            "by_category": by_category,
            "category_rankings": sorted_cats,
            "projections": self.state["projections"],
            "recommendation": self._generate_recommendation(sorted_cats)
        }

    def _generate_recommendation(self, rankings: List) -> str:
        """Generate improvement recommendation based on analysis."""
        if not rankings:
            return "Start making improvements in any category to build compound momentum"

        # Find weakest category
        weakest = min(rankings, key=lambda x: x[1])

        if weakest[1] < 1.01:
            return f"Focus on {weakest[0]} improvements - this category has the most room for compound growth"

        return "Maintain balanced improvements across all categories for optimal compound effect"

    def get_escape_velocity_impact(self) -> Dict:
        """Calculate how compound improvements affect escape velocity."""
        ev_file = STATE_DIR / "escape_velocity.json"

        if ev_file.exists():
            with open(ev_file) as f:
                ev_data = json.load(f)
        else:
            ev_data = {
                "current_velocity": 0,
                "compound_multiplier": 1.0
            }

        base_velocity = ev_data.get("current_velocity", 0)
        current_mult = self.state["compound_multiplier"]

        # Compound improvements accelerate escape velocity
        accelerated_velocity = base_velocity * current_mult
        velocity_gain = accelerated_velocity - base_velocity

        return {
            "base_velocity": base_velocity,
            "compound_multiplier": current_mult,
            "accelerated_velocity": accelerated_velocity,
            "velocity_gain": velocity_gain,
            "escape_velocity_contribution": self.state["escape_velocity_contribution"],
            "projections": self.state["projections"]
        }

    def visualize_compound_growth(self) -> str:
        """Create ASCII visualization of compound growth."""
        mult = self.state["compound_multiplier"]
        proj = self.state["projections"]

        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║            COMPOUND IMPROVEMENT TRACKER                       ║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║  Current Compound Multiplier: {mult:.4f}x                       ║",
            "╠══════════════════════════════════════════════════════════════╣",
            "║  CATEGORY MULTIPLIERS:                                        ║"
        ]

        for cat, val in self.state["category_multipliers"].items():
            bar_len = int(min(val - 1, 0.5) * 40)  # Scale bar
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"║  {cat:12}: {val:.4f}x [{bar}] ║")

        lines.extend([
            "╠══════════════════════════════════════════════════════════════╣",
            "║  PROJECTIONS:                                                 ║",
            f"║  7 days:   {proj.get('7_days', 'N/A')}x                                            ║",
            f"║  30 days:  {proj.get('30_days', 'N/A')}x                                            ║",
            f"║  90 days:  {proj.get('90_days', 'N/A')}x                                            ║",
            "╠══════════════════════════════════════════════════════════════╣"
        ])

        days_2x = proj.get('days_to_2x')
        if days_2x:
            lines.append(f"║  Days to 2x:  {days_2x}                                            ║")

        days_10x = proj.get('days_to_10x')
        if days_10x:
            lines.append(f"║  Days to 10x: {days_10x}                                           ║")

        lines.append("╚══════════════════════════════════════════════════════════════╝")

        return "\n".join(lines)


def record_improvement(category: str, description: str, base: float, new: float) -> Dict:
    """Record an improvement from command line."""
    tracker = CompoundTracker()
    return tracker.record_improvement(category, description, base, new)


def analyze() -> Dict:
    """Analyze compound improvements."""
    tracker = CompoundTracker()
    return tracker.analyze_improvements()


def visualize() -> str:
    """Get visualization of compound growth."""
    tracker = CompoundTracker()
    return tracker.visualize_compound_growth()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "analyze":
            result = analyze()
            print(json.dumps(result, indent=2))

        elif cmd == "visualize":
            print(visualize())

        elif cmd == "record" and len(sys.argv) >= 6:
            # record <category> <description> <base> <new>
            result = record_improvement(
                sys.argv[2],
                sys.argv[3],
                float(sys.argv[4]),
                float(sys.argv[5])
            )
            print(json.dumps(result, indent=2))

        else:
            print("Usage:")
            print("  python compound_tracker.py analyze")
            print("  python compound_tracker.py visualize")
            print("  python compound_tracker.py record <category> <description> <base> <new>")
    else:
        # Default: show analysis
        result = analyze()
        print(json.dumps(result, indent=2))
