#!/usr/bin/env python3
"""
ABCFC STATE HARMONIZATION

The unified state representation where:
- All state is ABCFC (Polymarket, Claude, Business, Meta)
- All actions modify the ABCFC hierarchy
- All decisions query the nexus cloud

This is THE state. Everything else is a view into it.

Created by: Yair Siegel
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from executor.math.abcfc_system import ABCFCSystem, Action as ABCFCAction, ABCFC

STATE_FILE = PROJECT_ROOT / "state" / "abcfc_unified_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


class UnifiedABCFCState:
    """
    THE unified state representation.

    Everything is ABCFC:
    - Yair Siegel (root)
      - Trading (Polymarket positions)
      - Claude (value delivery)
      - Business (revenue streams)
      - Meta (system design decisions)

    Query nexus cloud for any decision.
    Update hierarchy after any action.
    """

    def __init__(self):
        self.system = ABCFCSystem("Yair Siegel")
        self.system.risk_aversion = 0.5
        self.last_updated = None
        self._load_or_init()

    def _load_or_init(self):
        """Load from file or initialize fresh."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    data = json.load(f)
                self._from_dict(data)
                return
            except Exception as e:
                print(f"Could not load state: {e}, initializing fresh")

        self._init_fresh()

    def _init_fresh(self):
        """Initialize with base categories."""
        # Level 1 categories
        self.system.add_category("Trading")
        self.system.add_category("Claude")
        self.system.add_category("Business")
        self.system.add_category("Meta")

        # Level 2 subcategories
        self.system.add_subcategory("Trading", "Polymarket")
        self.system.add_subcategory("Claude", "ValueDelivery")
        self.system.add_subcategory("Business", "Revenue")
        self.system.add_subcategory("Meta", "SystemDesign")

        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.save()

    def _from_dict(self, data: Dict):
        """Rebuild system from saved dict."""
        self.system = ABCFCSystem("Yair Siegel")
        self.system.risk_aversion = data.get("risk_aversion", 0.5)
        self.last_updated = data.get("last_updated")

        # Rebuild hierarchy from positions
        for pos in data.get("positions", []):
            cat = pos.get("category")
            subcat = pos.get("subcategory")
            name = pos.get("name")

            # Ensure category exists
            if cat and cat not in self.system.hierarchy.all_nodes:
                self.system.add_category(cat)

            # Ensure subcategory exists
            if subcat and subcat not in self.system.hierarchy.all_nodes:
                self.system.add_subcategory(cat, subcat)

            # Add position
            if name and name not in self.system.hierarchy.all_nodes:
                self.system.add_position(
                    parent_name=subcat or cat,
                    name=name,
                    worst=pos.get("worst", 0),
                    best=pos.get("best", 0),
                    expected=pos.get("expected", 0)
                )

    def _to_dict(self) -> Dict:
        """Convert to saveable dict."""
        positions = []

        def extract_positions(node: ABCFC, category: str = None, subcategory: str = None):
            if node.level == 1:
                category = node.name
            elif node.level == 2:
                subcategory = node.name
            elif node.level >= 3:
                positions.append({
                    "category": category,
                    "subcategory": subcategory,
                    "name": node.name,
                    "worst": node.worst,
                    "best": node.best,
                    "expected": node.expected
                })

            for child in node.children:
                extract_positions(child, category, subcategory)

        extract_positions(self.system.hierarchy.root)

        return {
            "root": "Yair Siegel",
            "risk_aversion": self.system.risk_aversion,
            "last_updated": self.last_updated,
            "total_expected": self.system.total_expected(),
            "total_bounds": self.system.total_bounds(),
            "positions": positions
        }

    def save(self):
        """Save state to file."""
        self.last_updated = datetime.now(timezone.utc).isoformat()
        with open(STATE_FILE, 'w') as f:
            json.dump(self._to_dict(), f, indent=2)

    # ==================== QUERY ====================

    def decide(self, actions: List[ABCFCAction] = None) -> Dict:
        """
        THE decision function.

        Query nexus cloud, return best action.
        """
        if actions is None:
            actions = self.default_actions()

        cloud = self.system.get_top_line_nexus_cloud(actions)

        best = cloud["futures"][0] if cloud["futures"] else None

        return {
            "decision": best["action"] if best else "hold",
            "target": best["node"] if best else None,
            "score": best["score"] if best else 0,
            "current_expected": cloud["current"]["expected"],
            "new_expected": best["top_line"]["expected"] if best else cloud["current"]["expected"],
            "n_futures": len(cloud["futures"]),
            "cloud": cloud
        }

    def default_actions(self) -> List[ABCFCAction]:
        """Default action set."""
        return [
            ABCFCAction("hold", "hold", {}),
            ABCFCAction("hedge_50", "hedge", {"ratio": 0.5}),
            ABCFCAction("hedge_25", "hedge", {"ratio": 0.25}),
            ABCFCAction("buy", "buy", {"size": 25, "price": 0.4}),
            ABCFCAction("sell", "sell", {"size": 25, "price": 0.6}),
        ]

    # ==================== UPDATE ====================

    def update_trading(self, positions: List[Dict]):
        """Update trading positions from Polymarket."""
        # Clear existing trading positions
        polymarket = self.system.get_node("Polymarket")
        if polymarket:
            polymarket.children = []

        # Add new positions
        for pos in positions:
            name = pos.get("name", f"pos_{len(polymarket.children) if polymarket else 0}")
            self.system.add_position(
                parent_name="Polymarket",
                name=name,
                worst=pos.get("worst", 0),
                best=pos.get("best", 0),
                expected=pos.get("expected", 0)
            )

        self.save()

    def update_claude(self, action_taken: str, value_added: float,
                      worst: float = 0, best: float = None):
        """Update Claude value delivery after taking action."""
        if best is None:
            best = value_added * 1.2

        name = f"claude_{action_taken}_{datetime.now().strftime('%H%M%S')}"

        self.system.add_position(
            parent_name="ValueDelivery",
            name=name,
            worst=worst,
            best=best,
            expected=value_added
        )

        self.save()

    def update_business(self, stream: str, worst: float, best: float, expected: float):
        """Update business revenue stream."""
        self.system.add_position(
            parent_name="Revenue",
            name=stream,
            worst=worst,
            best=best,
            expected=expected
        )
        self.save()

    def update_meta(self, decision: str, worst: float, best: float, expected: float):
        """Update meta system design decision."""
        self.system.add_position(
            parent_name="SystemDesign",
            name=decision,
            worst=worst,
            best=best,
            expected=expected
        )
        self.save()

    # ==================== VIEW ====================

    def status(self) -> Dict:
        """Current state summary."""
        return {
            "total_expected": self.system.total_expected(),
            "total_bounds": self.system.total_bounds(),
            "last_updated": self.last_updated,
            "n_positions": len([n for n in self.system.hierarchy.all_nodes.values() if n.level >= 3])
        }

    def print_state(self):
        """Print full hierarchy."""
        print("=" * 70)
        print("UNIFIED ABCFC STATE")
        print("=" * 70)
        self.system.print_hierarchy()
        print(f"\nTotal: E=${self.system.total_expected():.0f} | Bounds: {self.system.total_bounds()}")
        print(f"Last updated: {self.last_updated}")
        print("=" * 70)


# Singleton instance
_state = None

def get_state() -> UnifiedABCFCState:
    """Get the unified state singleton."""
    global _state
    if _state is None:
        _state = UnifiedABCFCState()
    return _state


def decide(actions: List[ABCFCAction] = None) -> Dict:
    """Query the nexus cloud for a decision."""
    return get_state().decide(actions)


def update_after_action(domain: str, **kwargs):
    """Update state after taking an action."""
    state = get_state()
    if domain == "trading":
        state.update_trading(kwargs.get("positions", []))
    elif domain == "claude":
        state.update_claude(
            kwargs.get("action", "unknown"),
            kwargs.get("value", 0),
            kwargs.get("worst", 0),
            kwargs.get("best")
        )
    elif domain == "business":
        state.update_business(
            kwargs.get("stream", "unknown"),
            kwargs.get("worst", 0),
            kwargs.get("best", 0),
            kwargs.get("expected", 0)
        )
    elif domain == "meta":
        state.update_meta(
            kwargs.get("decision", "unknown"),
            kwargs.get("worst", 0),
            kwargs.get("best", 0),
            kwargs.get("expected", 0)
        )


# ==================== CLI ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Unified ABCFC State")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--decide", action="store_true", help="Get decision from nexus cloud")
    parser.add_argument("--print", action="store_true", help="Print full hierarchy")
    parser.add_argument("--reset", action="store_true", help="Reset to fresh state")
    args = parser.parse_args()

    state = get_state()

    if args.reset:
        STATE_FILE.unlink(missing_ok=True)
        state = UnifiedABCFCState()
        print("State reset.")

    if args.status:
        import pprint
        pprint.pprint(state.status())

    if args.decide:
        decision = state.decide()
        print(f"\nDECISION: {decision['decision']} on {decision['target']}")
        print(f"Score: {decision['score']:.2f}")
        print(f"E: ${decision['current_expected']:.0f} -> ${decision['new_expected']:.0f}")

    if args.print or (not args.status and not args.decide and not args.reset):
        state.print_state()
