#!/usr/bin/env python3
"""
ABCFC NEXUS - Dynamic Decision Space for Hierarchical Finance

The Nexus connects:
1. STEADY STATE - Current ABCFC hierarchy (what we have now)
2. ACTION SPACE - All possible actions the system can take
3. FUTURE STATES - Projected ABCFC hierarchies for each action
4. DECISION ENGINE - Chooses actions that maximize steady state

CONCEPT:
    The "nexus cloud" is the space of all possible ABCFC hierarchies
    reachable from the current state via available actions.

    Current State ──┬── Action A ──► Future State A (ABCFC)
                    ├── Action B ──► Future State B (ABCFC)
                    ├── Action C ──► Future State C (ABCFC)
                    └── ...

    The system evaluates each future state and selects the action
    that leads to the best expected outcome.

USAGE:
    from executor.math.abcfc_nexus import ABCFCNexus, get_nexus

    nexus = get_nexus()

    # Set current state
    nexus.set_steady_state(current_layers)

    # Add possible actions
    nexus.add_action("buy_weed", action_type="buy", market="weed-2025", size=100, price=0.10)
    nexus.add_action("sell_btc", action_type="sell", market="btc-100k", size=50)
    nexus.add_action("hold", action_type="hold")

    # Evaluate all actions
    evaluation = nexus.evaluate()

    # Get best action
    best = nexus.best_action()
    print(f"Recommended: {best.name} → Expected +${best.expected_improvement}")

    # Execute best action
    nexus.execute_best()

Created by: Yair Siegel
"""

import copy
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from pathlib import Path

from executor.math.abcfc_layers import ABCFCLayers, ABCFCNode, get_layers


@dataclass
class Action:
    """A possible action the system can take."""
    name: str
    action_type: str  # buy, sell, hold, adjust, hedge, etc.

    # Action parameters
    market: Optional[str] = None
    side: str = "YES"
    size: float = 0.0
    price: float = 0.0

    # For complex actions
    params: Dict = field(default_factory=dict)

    # Computed after simulation
    future_state: Optional[Dict] = None
    expected_improvement: float = 0.0
    best_improvement: float = 0.0
    worst_improvement: float = 0.0
    risk_adjusted_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "action_type": self.action_type,
            "market": self.market,
            "side": self.side,
            "size": self.size,
            "price": self.price,
            "params": self.params,
            "expected_improvement": round(self.expected_improvement, 2),
            "best_improvement": round(self.best_improvement, 2),
            "worst_improvement": round(self.worst_improvement, 2),
            "risk_adjusted_score": round(self.risk_adjusted_score, 4)
        }


@dataclass
class NexusState:
    """A point in the nexus cloud - a possible ABCFC hierarchy."""
    action: Action
    layers: ABCFCLayers

    # Aggregate metrics
    total_best: float = 0.0
    total_expected: float = 0.0
    total_worst: float = 0.0

    # Comparison to current state
    delta_best: float = 0.0
    delta_expected: float = 0.0
    delta_worst: float = 0.0


class ABCFCNexus:
    """
    Dynamic decision space for ABCFC hierarchy optimization.

    The Nexus maintains:
    1. Steady State - Current ABCFC hierarchy
    2. Action Space - All possible actions
    3. Nexus Cloud - Future states for each action
    4. Decision Engine - Optimal action selection
    """

    def __init__(self):
        self._steady_state: Optional[ABCFCLayers] = None
        self._actions: Dict[str, Action] = {}
        self._nexus_cloud: Dict[str, NexusState] = {}
        self._last_evaluation: Optional[str] = None
        self._history: List[Dict] = []

    # ==================== STEADY STATE ====================

    def set_steady_state(self, layers: ABCFCLayers = None):
        """Set the current steady state ABCFC hierarchy."""
        if layers is None:
            layers = get_layers()
        self._steady_state = layers

    @property
    def steady_state(self) -> ABCFCLayers:
        """Get current steady state."""
        if self._steady_state is None:
            self._steady_state = get_layers()
        return self._steady_state

    @property
    def current_expected(self) -> float:
        """Current total expected value."""
        return self.steady_state.total_finance.expected

    @property
    def current_best(self) -> float:
        """Current total best case."""
        return self.steady_state.total_finance.best_case

    @property
    def current_worst(self) -> float:
        """Current total worst case."""
        return self.steady_state.total_finance.worst_case

    # ==================== ACTION SPACE ====================

    def add_action(
        self,
        name: str,
        action_type: str,
        market: str = None,
        side: str = "YES",
        size: float = 0.0,
        price: float = 0.0,
        **params
    ) -> Action:
        """
        Add a possible action to the action space.

        Action types:
        - buy: Buy position (requires market, size, price, side)
        - sell: Sell/close position (requires market, size)
        - hold: Do nothing
        - adjust: Modify existing position
        - hedge: Add hedging position
        - compound: Reinvest profits

        Example:
            nexus.add_action("buy_weed", "buy", market="weed-2025", size=100, price=0.10)
            nexus.add_action("sell_btc", "sell", market="btc-100k", size=50)
            nexus.add_action("hold", "hold")
        """
        action = Action(
            name=name,
            action_type=action_type,
            market=market,
            side=side.upper() if side else "YES",
            size=size,
            price=price,
            params=params
        )
        self._actions[name] = action
        return action

    def add_buy_action(self, name: str, market: str, size: float, price: float, side: str = "YES"):
        """Convenience: Add a buy action."""
        return self.add_action(name, "buy", market=market, size=size, price=price, side=side)

    def add_sell_action(self, name: str, market: str, size: float):
        """Convenience: Add a sell action."""
        return self.add_action(name, "sell", market=market, size=size)

    def add_hold_action(self, name: str = "hold"):
        """Convenience: Add a hold (do nothing) action."""
        return self.add_action(name, "hold")

    def clear_actions(self):
        """Clear all actions from action space."""
        self._actions.clear()
        self._nexus_cloud.clear()

    @property
    def actions(self) -> List[Action]:
        """Get all actions."""
        return list(self._actions.values())

    # ==================== SIMULATION ====================

    def _simulate_action(self, action: Action) -> NexusState:
        """
        Simulate an action and return the resulting ABCFC hierarchy.

        Creates a deep copy of steady state and applies the action.
        """
        # Deep copy current state
        future_layers = ABCFCLayers()

        # Copy existing nodes
        for node_id, node in self.steady_state.nodes.items():
            future_layers.nodes[node_id] = ABCFCNode(
                name=node.name,
                layer=node.layer,
                parent=node.parent,
                entry_price=node.entry_price,
                position_size=node.position_size,
                prob_yes=node.prob_yes,
                side=node.side,
                days=node.days,
                best_case=node.best_case,
                worst_case=node.worst_case,
                expected=node.expected,
                children=node.children.copy(),
                metadata=node.metadata.copy()
            )

        # Apply action
        if action.action_type == "buy":
            # Add new position
            future_layers.add_polymarket_position(
                market_slug=action.market,
                entry_price=action.price,
                size=action.size,
                side=action.side
            )

        elif action.action_type == "sell":
            # Remove position (find and remove from hierarchy)
            node_id = f"market:{action.market}"
            if node_id in future_layers.nodes:
                node = future_layers.nodes[node_id]
                # Remove from parent's children
                if node.parent and node.parent in future_layers.nodes:
                    parent = future_layers.nodes[node.parent]
                    if node_id in parent.children:
                        parent.children.remove(node_id)
                # Delete node
                del future_layers.nodes[node_id]
                # Recalculate
                future_layers._recalculate_aggregates()

        elif action.action_type == "hold":
            # No change
            pass

        elif action.action_type == "adjust":
            # Modify existing position
            node_id = f"market:{action.market}"
            if node_id in future_layers.nodes:
                # Recalculate with new parameters
                from executor.math.resolution_cone import ResolutionCone
                node = future_layers.nodes[node_id]
                new_size = action.params.get("new_size", node.position_size)
                new_price = action.params.get("new_price", node.entry_price)

                cone = ResolutionCone(new_price, new_size, node.prob_yes, node.days, node.side)
                node.best_case = cone.best_case
                node.worst_case = cone.worst_case
                node.expected = cone.expected
                node.position_size = new_size
                node.entry_price = new_price

                future_layers._recalculate_aggregates()

        elif action.action_type == "hedge":
            # Add hedging position (opposite side)
            hedge_side = "NO" if action.side == "YES" else "YES"
            future_layers.add_polymarket_position(
                market_slug=f"{action.market}_hedge",
                entry_price=1 - action.price,  # Complement price
                size=action.size * action.params.get("hedge_ratio", 0.5),
                side=hedge_side
            )

        # Build nexus state
        state = NexusState(
            action=action,
            layers=future_layers,
            total_best=future_layers.total_finance.best_case,
            total_expected=future_layers.total_finance.expected,
            total_worst=future_layers.total_finance.worst_case,
            delta_best=future_layers.total_finance.best_case - self.current_best,
            delta_expected=future_layers.total_finance.expected - self.current_expected,
            delta_worst=future_layers.total_finance.worst_case - self.current_worst
        )

        return state

    # ==================== EVALUATION ====================

    def evaluate(self, risk_aversion: float = 0.5) -> Dict:
        """
        Evaluate all actions in the action space.

        Args:
            risk_aversion: 0 = pure expected value, 1 = focus on worst case

        Returns:
            Evaluation results with rankings
        """
        self._nexus_cloud.clear()
        results = []

        for name, action in self._actions.items():
            # Simulate action
            state = self._simulate_action(action)
            self._nexus_cloud[name] = state

            # Update action with results
            action.future_state = {
                "best": state.total_best,
                "expected": state.total_expected,
                "worst": state.total_worst
            }
            action.expected_improvement = state.delta_expected
            action.best_improvement = state.delta_best
            action.worst_improvement = state.delta_worst

            # Risk-adjusted score
            # Combines expected improvement with worst-case protection
            action.risk_adjusted_score = (
                (1 - risk_aversion) * state.delta_expected +
                risk_aversion * state.delta_worst
            )

            results.append(action.to_dict())

        # Sort by risk-adjusted score
        results.sort(key=lambda x: x["risk_adjusted_score"], reverse=True)

        self._last_evaluation = datetime.now(timezone.utc).isoformat()

        return {
            "timestamp": self._last_evaluation,
            "current_state": {
                "best": self.current_best,
                "expected": self.current_expected,
                "worst": self.current_worst
            },
            "risk_aversion": risk_aversion,
            "actions_evaluated": len(results),
            "rankings": results,
            "best_action": results[0] if results else None
        }

    def best_action(self) -> Optional[Action]:
        """Get the best action from last evaluation."""
        if not self._nexus_cloud:
            self.evaluate()

        best_score = float('-inf')
        best_action = None

        for name, state in self._nexus_cloud.items():
            if state.action.risk_adjusted_score > best_score:
                best_score = state.action.risk_adjusted_score
                best_action = state.action

        return best_action

    def get_action_comparison(self) -> str:
        """Get text comparison of all evaluated actions."""
        if not self._nexus_cloud:
            self.evaluate()

        lines = [
            "=" * 60,
            "ABCFC NEXUS - Action Comparison",
            "=" * 60,
            f"Current State: Best +${self.current_best:,.0f} / Exp ${self.current_expected:+,.0f} / Worst ${self.current_worst:,.0f}",
            "",
            "Possible Actions (ranked by risk-adjusted score):",
            "-" * 60
        ]

        # Sort actions by score
        sorted_actions = sorted(
            self._actions.values(),
            key=lambda a: a.risk_adjusted_score,
            reverse=True
        )

        for i, action in enumerate(sorted_actions, 1):
            marker = "★" if i == 1 else " "
            lines.append(
                f"{marker} {i}. {action.name} ({action.action_type})"
            )
            lines.append(
                f"     Δ Expected: ${action.expected_improvement:+,.0f} | "
                f"Δ Best: ${action.best_improvement:+,.0f} | "
                f"Δ Worst: ${action.worst_improvement:+,.0f}"
            )
            lines.append(
                f"     Score: {action.risk_adjusted_score:.2f}"
            )
            lines.append("")

        return "\n".join(lines)

    # ==================== EXECUTION ====================

    def execute_best(self) -> Dict:
        """
        Execute the best action.

        Updates the steady state with the result.
        """
        best = self.best_action()
        if not best:
            return {"success": False, "error": "No actions to execute"}

        # Get the future state for this action
        future_state = self._nexus_cloud.get(best.name)
        if not future_state:
            return {"success": False, "error": "Action not evaluated"}

        # Record in history
        self._history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": best.to_dict(),
            "before": {
                "best": self.current_best,
                "expected": self.current_expected,
                "worst": self.current_worst
            },
            "after": {
                "best": future_state.total_best,
                "expected": future_state.total_expected,
                "worst": future_state.total_worst
            }
        })

        # Update steady state
        self._steady_state = future_state.layers

        # Clear actions (need new evaluation)
        self.clear_actions()

        return {
            "success": True,
            "action": best.name,
            "improvement": {
                "expected": best.expected_improvement,
                "best": best.best_improvement,
                "worst": best.worst_improvement
            },
            "new_state": {
                "best": future_state.total_best,
                "expected": future_state.total_expected,
                "worst": future_state.total_worst
            }
        }

    # ==================== NEXUS CLOUD VISUALIZATION ====================

    def plot_nexus_cloud(self, save_path: str = None) -> Dict:
        """
        Visualize the nexus cloud - all possible future states.

        Shows current state and arrows to each possible future state.
        """
        if not self._nexus_cloud:
            self.evaluate()

        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError as e:
            return {"success": False, "error": f"Missing dependency: {e}"}

        fig, ax = plt.subplots(figsize=(14, 10))

        # Plot current state as center point
        current = (self.current_expected, self.current_worst)
        ax.scatter([current[0]], [current[1]], s=300, c='blue', marker='o',
                   zorder=5, label='Current State', edgecolors='black', linewidths=2)
        ax.annotate('CURRENT', current, textcoords="offset points",
                    xytext=(0, 15), ha='center', fontsize=10, fontweight='bold')

        # Plot each future state
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(self._nexus_cloud)))

        for i, (name, state) in enumerate(self._nexus_cloud.items()):
            future = (state.total_expected, state.total_worst)

            # Color based on improvement
            color = 'green' if state.delta_expected > 0 else 'red'

            # Draw arrow from current to future
            ax.annotate('', xy=future, xytext=current,
                       arrowprops=dict(arrowstyle='->', color=color, alpha=0.6, lw=2))

            # Plot future state point
            ax.scatter([future[0]], [future[1]], s=200, c=color, marker='s',
                      alpha=0.7, edgecolors='black', linewidths=1)

            # Label
            ax.annotate(f'{name}\nΔ${state.delta_expected:+,.0f}',
                       future, textcoords="offset points",
                       xytext=(10, 0), ha='left', fontsize=8)

        ax.set_xlabel('Expected Value ($)', fontsize=12)
        ax.set_ylabel('Worst Case ($)', fontsize=12)
        ax.set_title('ABCFC Nexus Cloud\nPossible Future States', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)

        # Quadrant labels
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.text(xlim[1]*0.9, ylim[1]*0.9, 'BEST\n(+EV, +Worst)', ha='right', fontsize=9, color='green')
        ax.text(xlim[0]*0.9, ylim[0]*0.9, 'WORST\n(-EV, -Worst)', ha='left', fontsize=9, color='red')

        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/abcfc_nexus_cloud.png'

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "states_plotted": len(self._nexus_cloud)
        }

    # ==================== PERSISTENCE ====================

    def save(self, path: str = None):
        """Save nexus state."""
        if path is None:
            path = Path(__file__).parent.parent.parent / "state" / "abcfc_nexus.json"

        data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "steady_state": self.steady_state.to_dict() if self._steady_state else None,
            "history": self._history[-100:]  # Keep last 100 decisions
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def to_dict(self) -> Dict:
        """Export full nexus state."""
        return {
            "steady_state": {
                "best": self.current_best,
                "expected": self.current_expected,
                "worst": self.current_worst
            },
            "actions": [a.to_dict() for a in self._actions.values()],
            "nexus_cloud_size": len(self._nexus_cloud),
            "last_evaluation": self._last_evaluation,
            "history_length": len(self._history)
        }


# Singleton
_nexus = None

def get_nexus() -> ABCFCNexus:
    """Get or create the ABCFC Nexus singleton."""
    global _nexus
    if _nexus is None:
        _nexus = ABCFCNexus()
    return _nexus


# Convenience alias
nexus = get_nexus


if __name__ == "__main__":
    print("=" * 60)
    print("ABCFC NEXUS - Dynamic Decision Space")
    print("=" * 60)

    # Get nexus and set up steady state
    n = get_nexus()

    # Add some positions to steady state
    layers = get_layers()
    layers.add_polymarket_position("weed-2025", 0.10, 100)
    layers.add_polymarket_position("btc-100k", 0.45, 200)
    n.set_steady_state(layers)

    print(f"\nCurrent State:")
    print(f"  Best:     +${n.current_best:,.0f}")
    print(f"  Expected: ${n.current_expected:+,.0f}")
    print(f"  Worst:    ${n.current_worst:,.0f}")

    # Add possible actions
    n.add_buy_action("buy_trump", "trump-pardons", size=100, price=0.02)
    n.add_buy_action("buy_more_weed", "weed-2025", size=50, price=0.10)
    n.add_sell_action("sell_btc", "btc-100k", size=200)
    n.add_hold_action("hold")

    # Evaluate
    print("\nEvaluating action space...")
    result = n.evaluate(risk_aversion=0.3)

    print("\n" + n.get_action_comparison())

    # Best action
    best = n.best_action()
    print(f"\n★ RECOMMENDED: {best.name}")
    print(f"  Expected improvement: ${best.expected_improvement:+,.0f}")
