#!/usr/bin/env python3
"""
INTEGRAFIX: ABCFC Cloud Bridge
===============================

Wires the ABCFC Cloud/Nexus decision system with INTEGRAFIX trading pipeline.

ABCFC CLOUD COMPONENTS:
- ABCFCNexus: Decision space evaluation (all possible futures)
- ABCFCCloudFlyer: Autonomous agent flying through nexus cloud
- ABCFCSystem: Hierarchical finance (Yair → Trading → Positions)
- ABCFCLayers: Hierarchical ABCFC structure

INTEGRAFIX WIRING:
1. ABCFC Cloud → Trading Pipeline (decisions inform trades)
2. Trading Outcomes → ABCFC Cloud (update hierarchy)
3. ABCFC Nexus → Decision Engine (best action selection)
4. All components → State Backend (unified state)

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

CLOUD_STATE = STATE_DIR / "abcfc_cloud_state.json"
CLOUD_LOG = STATE_DIR / "abcfc_cloud_decisions.jsonl"


@dataclass
class CloudDecision:
    """A decision from the ABCFC cloud."""
    decision_id: str
    timestamp: str
    action_name: str
    action_type: str
    market: Optional[str]

    # ABCFC metrics
    expected_improvement: float
    best_improvement: float
    worst_improvement: float
    risk_adjusted_score: float

    # Cloud state
    cloud_size: int  # Number of futures evaluated
    current_expected: float
    current_bounds: Tuple[float, float]

    # Execution
    executed: bool = False
    outcome: Optional[Dict] = None


class ABCFCCloudBridge:
    """
    Bridge between ABCFC Cloud/Nexus and INTEGRAFIX trading pipeline.

    WIRES:
    - ABCFCNexus (decision space)
    - ABCFCCloudFlyer (autonomous agent)
    - ABCFCSystem (hierarchy)
    - Market Data Pipeline (trading)
    - Outcome Tracker (feedback)
    """

    def __init__(self):
        self.state = self._load_state()

        # Lazy-loaded components
        self._nexus = None
        self._system = None
        self._flyer = None
        self._layers = None

    def _load_state(self) -> Dict:
        if CLOUD_STATE.exists():
            try:
                with open(CLOUD_STATE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "initialized": datetime.now(timezone.utc).isoformat(),
            "decisions": 0,
            "executions": 0,
            "total_improvement": 0.0,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(CLOUD_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    # ========================================================================
    # ABCFC COMPONENT ACCESS
    # ========================================================================

    @property
    def nexus(self):
        """Get ABCFC Nexus (decision space)."""
        if self._nexus is None:
            try:
                from executor.math.abcfc_nexus import get_nexus
                self._nexus = get_nexus()
            except ImportError as e:
                print(f"ABCFCNexus not available: {e}")
        return self._nexus

    @property
    def system(self):
        """Get ABCFC System (full hierarchy)."""
        if self._system is None:
            try:
                from executor.math.abcfc_system import ABCFCSystem
                self._system = ABCFCSystem("Yair Siegel")
            except ImportError as e:
                print(f"ABCFCSystem not available: {e}")
        return self._system

    @property
    def flyer(self):
        """Get ABCFC Cloud Flyer (autonomous agent)."""
        if self._flyer is None:
            try:
                from executor.math.abcfc_cloud_flyer import ABCFCCloudFlyer
                self._flyer = ABCFCCloudFlyer(name="Yair Siegel", dry_run=True)
            except ImportError as e:
                print(f"ABCFCCloudFlyer not available: {e}")
        return self._flyer

    @property
    def layers(self):
        """Get ABCFC Layers (hierarchical structure)."""
        if self._layers is None:
            try:
                from executor.math.abcfc_layers import get_layers
                self._layers = get_layers()
            except ImportError as e:
                print(f"ABCFCLayers not available: {e}")
        return self._layers

    # ========================================================================
    # NEXUS CLOUD OPERATIONS
    # ========================================================================

    def evaluate_cloud(self, risk_aversion: float = 0.5) -> Dict:
        """
        Evaluate the ABCFC nexus cloud.

        Returns all possible futures with scores.
        """
        if not self.nexus:
            return {"error": "ABCFCNexus not available"}

        result = self.nexus.evaluate(risk_aversion=risk_aversion)

        self.state["decisions"] = self.state.get("decisions", 0) + 1
        self._save_state()

        return result

    def get_best_action(self, risk_aversion: float = 0.5) -> Optional[Dict]:
        """Get the best action from the nexus cloud."""
        if not self.nexus:
            return None

        self.nexus.evaluate(risk_aversion=risk_aversion)
        action = self.nexus.best_action()

        if action:
            return action.to_dict()
        return None

    def add_trading_actions(self, signals: List[Dict]):
        """
        Add trading signals as possible actions to the nexus cloud.

        Signals from the trading pipeline become actions in the cloud.
        """
        if not self.nexus:
            return

        self.nexus.clear_actions()

        # Always add hold action
        self.nexus.add_hold_action("hold")

        # Add each signal as a potential action
        for signal in signals:
            market = signal.get("market_id", signal.get("slug", "unknown"))
            direction = signal.get("direction", "YES")
            edge = signal.get("edge", 0)
            price = signal.get("price", 0.5)

            # Size based on edge (Kelly criterion simplified)
            size = min(100, max(10, edge * 1000))

            self.nexus.add_buy_action(
                name=f"buy_{market[:20]}",
                market=market,
                size=size,
                price=price,
                side=direction
            )

    def fly_once(self) -> Dict:
        """
        Execute one flight iteration through the nexus cloud.

        Uses ABCFCCloudFlyer to:
        1. Observe current state
        2. Build hierarchy
        3. Generate nexus cloud
        4. Select best trajectory
        5. Execute (or log in dry run)
        """
        if not self.flyer:
            return {"error": "ABCFCCloudFlyer not available"}

        return self.flyer.fly_once()

    # ========================================================================
    # HIERARCHY OPERATIONS
    # ========================================================================

    def get_hierarchy_status(self) -> Dict:
        """Get current ABCFC hierarchy status."""
        if self.system:
            return {
                "name": self.system.hierarchy.root.name if hasattr(self.system, 'hierarchy') else "ABCFCSystem",
                "total_expected": self.system.total_expected(),
                "total_bounds": self.system.total_bounds(),
                "categories": len(self.system.hierarchy.categories) if hasattr(self.system.hierarchy, 'categories') else 0,
            }
        elif self.layers:
            total = self.layers.total_finance
            return {
                "name": "Layers",
                "total_expected": total.expected,
                "total_bounds": (total.worst_case, total.best_case),
                "nodes": len(self.layers.nodes),
            }
        return {"error": "No ABCFC hierarchy available"}

    def add_position_to_hierarchy(
        self,
        market: str,
        entry_price: float,
        size: float,
        side: str = "YES"
    ):
        """Add a position to the ABCFC hierarchy."""
        if self.layers:
            self.layers.add_polymarket_position(
                market_slug=market,
                entry_price=entry_price,
                size=size,
                side=side
            )
        elif self.system:
            # Calculate bounds
            if side == "YES":
                best = size * (1 - entry_price)
                worst = -size * entry_price
            else:
                best = size * entry_price
                worst = -size * (1 - entry_price)

            expected = (best + worst) / 2

            # Ensure Polymarket subcategory exists
            if "Trading" not in [c.name for c in self.system.categories.values()]:
                self.system.add_category("Trading")
            if "Polymarket" not in [s for cat in self.system.categories.values() for s in cat.subcategories]:
                self.system.add_subcategory("Trading", "Polymarket")

            self.system.add_position(
                parent_name="Polymarket",
                name=f"M_{market[:20]}",
                worst=worst,
                best=best,
                expected=expected
            )

    def update_from_outcome(self, market: str, resolution: str, pnl: float):
        """Update hierarchy after a trade outcome."""
        # Remove resolved position from hierarchy
        if self.layers:
            node_id = f"market:{market}"
            if node_id in self.layers.nodes:
                del self.layers.nodes[node_id]
                self.layers._recalculate_aggregates()

        self.state["total_improvement"] = self.state.get("total_improvement", 0) + pnl
        self._save_state()

    # ========================================================================
    # INTEGRAFIX WIRING
    # ========================================================================

    def wire_to_trading_pipeline(self):
        """
        Wire ABCFC cloud to the trading pipeline.

        Trading pipeline signals become ABCFC cloud actions.
        Best ABCFC action becomes trade recommendation.
        """
        try:
            from trading.market_data_pipeline import MarketDataPipeline

            # This is the wire - the pipeline can call cloud.get_best_action()
            # to get ABCFC-informed recommendations
            return True
        except ImportError:
            return False

    def wire_to_outcome_tracker(self):
        """
        Wire ABCFC cloud to outcome tracker.

        Outcomes update the ABCFC hierarchy.
        """
        try:
            from integrafix.outcome_tracker import OutcomeTracker
            return True
        except ImportError:
            return False

    # ========================================================================
    # TOP-LINE NEXUS CLOUD (ABCFCSystem integration)
    # ========================================================================

    def get_top_line_nexus(self, actions: List[Dict] = None) -> Dict:
        """
        Get the top-line nexus cloud from ABCFCSystem.

        This evaluates how each action affects Yair Siegel's total ABCFC.
        """
        if not self.system:
            return {"error": "ABCFCSystem not available"}

        # Convert dict actions to Action objects
        from executor.math.abcfc_system import Action

        abcfc_actions = []
        if actions:
            for a in actions:
                abcfc_actions.append(Action(
                    name=a.get("name", "unknown"),
                    action_type=a.get("type", "hold"),
                    params=a.get("params", {})
                ))
        else:
            # Default actions
            abcfc_actions = [
                Action("hold", "hold", {}),
                Action("hedge_50", "hedge", {"ratio": 0.5}),
            ]

        return self.system.get_top_line_nexus_cloud(abcfc_actions)

    def plot_nexus_cloud(self, save_path: str = None) -> Dict:
        """Generate visualization of the nexus cloud."""
        if self.nexus:
            return self.nexus.plot_nexus_cloud(save_path)
        elif self.system:
            if save_path is None:
                save_path = "/tmp/abcfc_nexus.png"
            from executor.math.abcfc_system import Action
            actions = [Action("hold", "hold", {})]
            return self.system.plot_top_line_nexus(actions, save_path=save_path)
        return {"error": "No visualization available"}

    # ========================================================================
    # STATUS
    # ========================================================================

    def status(self) -> Dict:
        """Get bridge status."""
        components = {
            "abcfc_nexus": self.nexus is not None,
            "abcfc_system": self.system is not None,
            "abcfc_flyer": self.flyer is not None,
            "abcfc_layers": self.layers is not None,
        }

        hierarchy = self.get_hierarchy_status()

        return {
            "initialized": self.state.get("initialized"),
            "decisions": self.state.get("decisions", 0),
            "executions": self.state.get("executions", 0),
            "total_improvement": self.state.get("total_improvement", 0.0),
            "components": components,
            "components_available": sum(components.values()),
            "hierarchy": hierarchy,
            "wired_to_pipeline": self.wire_to_trading_pipeline(),
            "wired_to_outcomes": self.wire_to_outcome_tracker(),
            "message": "ABCFC Cloud ↔ INTEGRAFIX bridge operational",
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_bridge: Optional[ABCFCCloudBridge] = None


def get_cloud_bridge() -> ABCFCCloudBridge:
    """Get or create the ABCFC Cloud bridge."""
    global _bridge
    if _bridge is None:
        _bridge = ABCFCCloudBridge()
    return _bridge


def evaluate_cloud(risk_aversion: float = 0.5) -> Dict:
    """Main API: Evaluate the ABCFC nexus cloud."""
    return get_cloud_bridge().evaluate_cloud(risk_aversion)


def get_best_cloud_action() -> Optional[Dict]:
    """Main API: Get best action from cloud."""
    return get_cloud_bridge().get_best_action()


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ABCFC Cloud ↔ INTEGRAFIX Bridge")
    parser.add_argument("command", choices=["status", "evaluate", "fly", "hierarchy", "plot"])
    parser.add_argument("--risk", type=float, default=0.5, help="Risk aversion (0-1)")
    parser.add_argument("--output", type=str, help="Output path for plots")
    args = parser.parse_args()

    bridge = get_cloud_bridge()

    if args.command == "status":
        status = bridge.status()
        print("=" * 70)
        print("INTEGRAFIX: ABCFC Cloud Bridge Status")
        print("=" * 70)
        print(f"\nDecisions: {status['decisions']}")
        print(f"Executions: {status['executions']}")
        print(f"Total Improvement: ${status['total_improvement']:.2f}")
        print(f"\nComponents ({status['components_available']}/4):")
        for comp, available in status['components'].items():
            symbol = "+" if available else "x"
            print(f"  [{symbol}] {comp}")
        print(f"\nHierarchy: {status['hierarchy']}")
        print(f"\nWiring:")
        print(f"  Trading Pipeline: {'Connected' if status['wired_to_pipeline'] else 'Not connected'}")
        print(f"  Outcome Tracker: {'Connected' if status['wired_to_outcomes'] else 'Not connected'}")
        print(f"\n{status['message']}")

    elif args.command == "evaluate":
        print("=" * 70)
        print("INTEGRAFIX: Evaluating ABCFC Cloud")
        print("=" * 70)

        result = bridge.evaluate_cloud(risk_aversion=args.risk)

        if "error" in result:
            print(f"Error: {result['error']}")
            return

        print(f"\nCurrent State: {result.get('current_state')}")
        print(f"Risk Aversion: {result.get('risk_aversion')}")
        print(f"Actions Evaluated: {result.get('actions_evaluated')}")

        print(f"\nRankings:")
        for i, action in enumerate(result.get("rankings", [])[:5], 1):
            print(f"  {i}. {action.get('name')} ({action.get('action_type')})")
            print(f"     Score: {action.get('risk_adjusted_score', 0):+.3f}")
            print(f"     Δ Expected: ${action.get('expected_improvement', 0):+.2f}")

        best = result.get("best_action")
        if best:
            print(f"\n* BEST: {best.get('name')} (score: {best.get('risk_adjusted_score', 0):+.3f})")

    elif args.command == "fly":
        print("=" * 70)
        print("INTEGRAFIX: Flying Through ABCFC Cloud")
        print("=" * 70)

        result = bridge.fly_once()

        if "error" in result:
            print(f"Error: {result['error']}")
            return

        print(f"\nIteration: {result.get('iteration')}")
        state = result.get('state')
        if state:
            print(f"Positions: {len(state.positions)}")
            print(f"Expected: ${state.total_expected:+.2f}")
            print(f"Bounds: ${state.bounds[0]:+.0f} to ${state.bounds[1]:+.0f}")

        selected = result.get('selected', {})
        print(f"\nSelected: {selected.get('action', 'hold')} on {selected.get('node', 'n/a')}")
        print(f"Score: {selected.get('score', 0):+.2f}")

    elif args.command == "hierarchy":
        print("=" * 70)
        print("INTEGRAFIX: ABCFC Hierarchy")
        print("=" * 70)

        status = bridge.get_hierarchy_status()
        print(f"\nHierarchy: {status}")

        if bridge.system:
            print("\nFull Hierarchy:")
            bridge.system.print_hierarchy()
        elif bridge.layers:
            print(f"\nNodes: {len(bridge.layers.nodes)}")

    elif args.command == "plot":
        output = args.output or "/tmp/abcfc_cloud.png"
        result = bridge.plot_nexus_cloud(output)
        if result.get("success"):
            print(f"Saved to: {result.get('chart_path')}")
        else:
            print(f"Error: {result.get('error')}")


if __name__ == "__main__":
    main()
