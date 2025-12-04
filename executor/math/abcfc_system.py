#!/usr/bin/env python3
"""
ABCFC SYSTEM - Complete Hierarchy + Nexus Cloud

The full ABCFC implementation:
- Hierarchical profit ABCFCs (Yair → Categories → Positions)
- Nexus cloud for decision space
- Order flow models (3 levels of predictability)

Created by: Yair Siegel
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta


# ============================================================================
# CORE ABCFC (Profit over Time)
# ============================================================================

@dataclass
class ABCFC:
    """
    Absolute Bounds Continuous Fan Chart - Profit over Time

    The fundamental unit: a bounded probability density over profit × time.
    """
    name: str
    worst: float                    # Lower bound (worst P&L)
    best: float                     # Upper bound (best P&L)
    expected: float = None          # Expected value
    duration: float = 30.0          # Time horizon (days)

    # Density function P(profit, t) - if None, uses default
    density_func: Callable[[float, float], float] = None

    # Metadata
    level: int = 0                  # Hierarchy level
    parent: 'ABCFC' = None
    children: List['ABCFC'] = field(default_factory=list)

    # Order flow model
    flow_model: 'OrderFlowModel' = None

    def __post_init__(self):
        if self.expected is None:
            self.expected = (self.best + self.worst) / 2
        if self.density_func is None:
            self.density_func = self._default_density

    def _default_density(self, profit: float, t: float) -> float:
        """Default: Gaussian centered on expected, widening over time."""
        if profit < self.worst or profit > self.best:
            return 0.0

        # Normalize
        progress = t / self.duration if self.duration > 0 else 0
        spread = (self.best - self.worst) / 2

        # Variance peaks mid-duration
        variance_factor = 4 * progress * (1 - progress) + 0.1
        sigma = spread * 0.3 * math.sqrt(variance_factor)

        # Center moves from 0 toward expected
        center = progress * self.expected

        z = (profit - center) / (sigma + 0.001)
        return math.exp(-0.5 * z * z)

    def P(self, profit: float, t: float) -> float:
        """Probability density at (profit, t)."""
        return self.density_func(profit, t)

    def E(self, t: float) -> float:
        """Expected profit at time t."""
        progress = t / self.duration if self.duration > 0 else 0
        return progress * self.expected

    @property
    def range(self) -> float:
        return self.best - self.worst

    @property
    def upside(self) -> float:
        return self.best

    @property
    def downside(self) -> float:
        return self.worst

    def add_child(self, child: 'ABCFC'):
        """Add child ABCFC and update parent reference."""
        child.parent = self
        child.level = self.level + 1
        self.children.append(child)

    def aggregate_from_children(self):
        """Recompute bounds from children."""
        if not self.children:
            return
        self.worst = sum(c.worst for c in self.children)
        self.best = sum(c.best for c in self.children)
        self.expected = sum(c.expected for c in self.children)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "level": self.level,
            "worst": self.worst,
            "best": self.best,
            "expected": self.expected,
            "duration": self.duration,
            "children": [c.name for c in self.children]
        }

    def __repr__(self):
        return f"ABCFC({self.name}: [{self.worst:+.0f}, {self.best:+.0f}] E={self.expected:+.0f})"


# ============================================================================
# HIERARCHY
# ============================================================================

class ABCFCHierarchy:
    """
    Complete hierarchical ABCFC structure.

    Level 0: Yair Siegel Total Profit
    Level 1: Categories (Trading, Business, Employment, etc.)
    Level 2: Sub-categories (Polymarket, Stocks, etc.)
    Level 3: Individual positions
    """

    def __init__(self, name: str = "Yair Siegel"):
        self.root = ABCFC(
            name=name,
            worst=0,
            best=0,
            expected=0,
            level=0
        )
        self.all_nodes: Dict[str, ABCFC] = {name: self.root}

    def add_category(self, name: str, worst: float = 0, best: float = 0, expected: float = None) -> ABCFC:
        """Add Level 1 category."""
        cat = ABCFC(name=name, worst=worst, best=best, expected=expected, level=1)
        self.root.add_child(cat)
        self.all_nodes[name] = cat
        self._propagate_up(cat)
        return cat

    def add_subcategory(self, parent_name: str, name: str,
                        worst: float = 0, best: float = 0, expected: float = None) -> ABCFC:
        """Add Level 2 sub-category."""
        parent = self.all_nodes.get(parent_name)
        if not parent:
            raise ValueError(f"Parent '{parent_name}' not found")

        sub = ABCFC(name=name, worst=worst, best=best, expected=expected, level=2)
        parent.add_child(sub)
        self.all_nodes[name] = sub
        self._propagate_up(sub)
        return sub

    def add_position(self, parent_name: str, name: str,
                     worst: float, best: float, expected: float = None,
                     duration: float = 30.0) -> ABCFC:
        """Add Level 3 position."""
        parent = self.all_nodes.get(parent_name)
        if not parent:
            raise ValueError(f"Parent '{parent_name}' not found")

        pos = ABCFC(name=name, worst=worst, best=best, expected=expected,
                    duration=duration, level=3)
        parent.add_child(pos)
        self.all_nodes[name] = pos
        self._propagate_up(pos)
        return pos

    def _propagate_up(self, node: ABCFC):
        """Propagate changes up the hierarchy."""
        current = node.parent
        while current:
            current.aggregate_from_children()
            current = current.parent

    def get_node(self, name: str) -> Optional[ABCFC]:
        return self.all_nodes.get(name)

    def total_bounds(self) -> Tuple[float, float]:
        return (self.root.worst, self.root.best)

    def total_expected(self) -> float:
        return self.root.expected

    def print_tree(self, node: ABCFC = None, indent: int = 0):
        """Print hierarchy tree."""
        if node is None:
            node = self.root

        prefix = "  " * indent
        print(f"{prefix}{node}")
        for child in node.children:
            self.print_tree(child, indent + 1)

    def to_dict(self) -> Dict:
        def node_to_dict(node: ABCFC) -> Dict:
            d = node.to_dict()
            d["children"] = [node_to_dict(c) for c in node.children]
            return d
        return node_to_dict(self.root)


# ============================================================================
# ORDER FLOW MODELS (3 Levels)
# ============================================================================

class FlowPredictability(Enum):
    """Level of order flow predictability."""
    PERFECT_DISCRETE = 1    # Know exact orders
    CONTINUOUS_RATE = 2     # Know rate λ(t)
    UNKNOWN_CHAOTIC = 3     # Don't even know rate


@dataclass
class OrderFlowModel:
    """
    Order flow model for ABCFC density evolution.

    Level 1: Perfect discrete - know exact orders coming
    Level 2: Continuous rate - know λ(t) arrival rate
    Level 3: Unknown/chaotic - model uncertainty of the rate itself
    """
    level: FlowPredictability

    # Level 1: Known orders
    known_orders: List[Tuple[float, str, float]] = None  # (time, side, size)

    # Level 2: Rate function
    rate_func: Callable[[float], float] = None  # λ(t)

    # Level 3: Rate uncertainty
    rate_mean: float = 1.0          # Expected rate
    rate_variance: float = 0.5      # Uncertainty in rate
    regularity_score: float = 0.5   # 0 = chaotic, 1 = regular

    def get_rate(self, t: float) -> float:
        """Get order arrival rate at time t."""
        if self.level == FlowPredictability.PERFECT_DISCRETE:
            # Count known orders near t
            if not self.known_orders:
                return 0
            window = 1.0
            count = sum(1 for (ot, _, _) in self.known_orders if abs(ot - t) < window)
            return count / window

        elif self.level == FlowPredictability.CONTINUOUS_RATE:
            if self.rate_func:
                return self.rate_func(t)
            return self.rate_mean

        else:  # UNKNOWN_CHAOTIC
            return self.rate_mean

    def get_confidence(self) -> float:
        """How confident are we in this model?"""
        if self.level == FlowPredictability.PERFECT_DISCRETE:
            return 1.0
        elif self.level == FlowPredictability.CONTINUOUS_RATE:
            return 0.7
        else:
            return self.regularity_score * 0.5

    @classmethod
    def from_order_history(cls, timestamps: List[float]) -> 'OrderFlowModel':
        """Infer model from historical order timestamps."""
        if len(timestamps) < 2:
            return cls(level=FlowPredictability.UNKNOWN_CHAOTIC)

        # Calculate inter-arrival times
        gaps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]

        mean_gap = sum(gaps) / len(gaps)
        variance = sum((g - mean_gap)**2 for g in gaps) / len(gaps)
        cv = math.sqrt(variance) / mean_gap if mean_gap > 0 else float('inf')

        # Coefficient of variation determines regularity
        # CV ≈ 1 = Poisson (regular), CV >> 1 = bursty (irregular)

        if cv < 1.2:
            # Regular enough for continuous rate model
            regularity = 1.0 - (cv - 0.5) / 1.5
            return cls(
                level=FlowPredictability.CONTINUOUS_RATE,
                rate_mean=1.0 / mean_gap if mean_gap > 0 else 0,
                regularity_score=max(0, min(1, regularity))
            )
        else:
            # Too irregular
            regularity = max(0, 1.0 - (cv - 1.2) / 2)
            return cls(
                level=FlowPredictability.UNKNOWN_CHAOTIC,
                rate_mean=1.0 / mean_gap if mean_gap > 0 else 0,
                rate_variance=variance / (mean_gap ** 2) if mean_gap > 0 else 1,
                regularity_score=regularity
            )


# ============================================================================
# NEXUS CLOUD (Decision Space)
# ============================================================================

@dataclass
class Action:
    """A possible action in the nexus."""
    name: str
    action_type: str                # "buy", "sell", "hold", "hedge", etc.
    params: Dict = field(default_factory=dict)  # size, price, etc.

    def __repr__(self):
        return f"Action({self.name}: {self.action_type})"


@dataclass
class NexusNode:
    """A node in the decision tree - an ABCFC resulting from an action."""
    abcfc: ABCFC
    action: Action                  # Action that led here
    parent: 'NexusNode' = None
    children: List['NexusNode'] = field(default_factory=list)
    score: float = 0.0              # Decision score

    def __repr__(self):
        return f"NexusNode({self.action.name} → {self.abcfc})"


class ABCFCNexus:
    """
    ABCFC Nexus Cloud - Decision Space

    Models all possible future ABCFCs based on available actions.
    Enables optimal decision making.
    """

    def __init__(self, current_abcfc: ABCFC, risk_aversion: float = 0.5):
        """
        Initialize nexus from current state.

        Args:
            current_abcfc: Current ABCFC (steady state)
            risk_aversion: 0 = risk-seeking, 1 = risk-averse
        """
        self.current = current_abcfc
        self.risk_aversion = risk_aversion

        # Root of decision tree
        self.root = NexusNode(
            abcfc=current_abcfc,
            action=Action("current", "hold")
        )

        # All possible futures
        self.futures: List[NexusNode] = []

    def add_action(self, action: Action,
                   resulting_abcfc: ABCFC,
                   parent: NexusNode = None) -> NexusNode:
        """Add a possible action and its resulting ABCFC."""
        if parent is None:
            parent = self.root

        node = NexusNode(
            abcfc=resulting_abcfc,
            action=action,
            parent=parent
        )
        node.score = self._score_abcfc(resulting_abcfc)

        parent.children.append(node)
        self.futures.append(node)

        return node

    def _score_abcfc(self, abcfc: ABCFC) -> float:
        """
        Score an ABCFC for decision making.

        Balances expected value with risk (downside).
        """
        # Normalize values
        range_val = max(abs(abcfc.best), abs(abcfc.worst), 1)

        expected_norm = abcfc.expected / range_val
        downside_norm = abcfc.worst / range_val  # Negative number
        upside_norm = abcfc.best / range_val

        # Risk-adjusted score
        # Higher expected = better
        # More negative downside = worse (scaled by risk aversion)
        # Wider range = more uncertain

        score = expected_norm
        score += self.risk_aversion * downside_norm  # Penalize downside
        score += (1 - self.risk_aversion) * upside_norm * 0.2  # Small bonus for upside

        return score

    def get_best_action(self) -> Tuple[Action, NexusNode]:
        """Find the best action based on scores."""
        if not self.futures:
            return (self.root.action, self.root)

        best = max(self.futures, key=lambda n: n.score)
        return (best.action, best)

    def get_ranked_actions(self) -> List[Tuple[Action, NexusNode, float]]:
        """Get all actions ranked by score."""
        ranked = sorted(self.futures, key=lambda n: n.score, reverse=True)
        return [(n.action, n, n.score) for n in ranked]

    def simulate_action(self, action: Action,
                        current: ABCFC,
                        order_book: Dict = None) -> ABCFC:
        """
        Simulate an action and return resulting ABCFC.

        Args:
            action: Action to simulate
            current: Current ABCFC
            order_book: Optional order book for realistic simulation
        """
        if action.action_type == "hold":
            return current

        elif action.action_type == "buy":
            size = action.params.get("size", 10)
            price = action.params.get("price", 0.5)
            # INTEGRAFIX: Use actual probability/edge if provided, not hardcoded 50%
            prob = action.params.get("probability", action.params.get("prob", 0.5))
            edge = action.params.get("edge", 0)
            if edge > 0:
                # If edge provided, derive probability from price + edge
                prob = min(price + edge, 0.95)

            # Buying increases both upside and downside
            new_worst = current.worst - size * price
            new_best = current.best + size * (1 - price)
            # INTEGRAFIX: Use actual probability for expected value
            new_expected = current.expected + size * (prob - price)

            return ABCFC(
                name=f"{current.name}+buy",
                worst=new_worst,
                best=new_best,
                expected=new_expected,
                duration=current.duration
            )

        elif action.action_type == "sell":
            size = action.params.get("size", 10)
            price = action.params.get("price", 0.5)

            # Selling reduces exposure
            reduction = min(size / 100, 1.0)  # Assuming 100 shares max
            new_worst = current.worst * (1 - reduction)
            new_best = current.best * (1 - reduction)
            new_expected = current.expected * (1 - reduction)

            # Add realized profit
            realized = size * price
            new_worst += realized * 0.9  # Slippage
            new_best += realized
            new_expected += realized * 0.95

            return ABCFC(
                name=f"{current.name}+sell",
                worst=new_worst,
                best=new_best,
                expected=new_expected,
                duration=current.duration
            )

        elif action.action_type == "hedge":
            # Hedging narrows the bounds toward expected
            hedge_ratio = action.params.get("ratio", 0.5)

            new_range = current.range * (1 - hedge_ratio)
            new_worst = current.expected - new_range / 2
            new_best = current.expected + new_range / 2

            # Hedging has a cost
            hedge_cost = current.range * hedge_ratio * 0.05
            new_expected = current.expected - hedge_cost

            return ABCFC(
                name=f"{current.name}+hedge",
                worst=new_worst,
                best=new_best,
                expected=new_expected,
                duration=current.duration
            )

        return current

    def explore_actions(self, actions: List[Action], depth: int = 1):
        """
        Explore multiple actions and build decision tree.

        Args:
            actions: List of possible actions
            depth: How many steps ahead to simulate
        """
        def explore_node(node: NexusNode, remaining_depth: int):
            if remaining_depth <= 0:
                return

            for action in actions:
                resulting = self.simulate_action(action, node.abcfc)
                child = self.add_action(action, resulting, parent=node)
                explore_node(child, remaining_depth - 1)

        explore_node(self.root, depth)

    def get_cloud_bounds(self) -> Tuple[float, float, float, float]:
        """Get the overall bounds of the nexus cloud."""
        if not self.futures:
            return (self.current.worst, self.current.best,
                    self.current.expected, self.current.expected)

        all_worst = min(n.abcfc.worst for n in self.futures)
        all_best = max(n.abcfc.best for n in self.futures)
        all_exp_min = min(n.abcfc.expected for n in self.futures)
        all_exp_max = max(n.abcfc.expected for n in self.futures)

        return (all_worst, all_best, all_exp_min, all_exp_max)

    def print_tree(self, node: NexusNode = None, indent: int = 0):
        """Print decision tree."""
        if node is None:
            node = self.root

        prefix = "  " * indent
        score_str = f" (score={node.score:.2f})" if node.score else ""
        print(f"{prefix}{node.action.name}: {node.abcfc}{score_str}")

        for child in node.children:
            self.print_tree(child, indent + 1)

    def plot(self, save_path: str = None) -> Dict:
        """Visualize the nexus cloud."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError as e:
            return {"success": False, "error": str(e)}

        fig, ax = plt.subplots(figsize=(12, 8))

        t = np.linspace(0, self.current.duration, 100)

        # Plot current ABCFC
        current_best = [self.current.best * (ti/self.current.duration) for ti in t]
        current_worst = [self.current.worst * (ti/self.current.duration) for ti in t]
        current_exp = [self.current.expected * (ti/self.current.duration) for ti in t]

        ax.fill_between(t, current_worst, current_best, alpha=0.2, color='gray', label='Current (hold)')
        ax.plot(t, current_exp, '--', color='gray', lw=2)

        # Plot each future
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(self.futures)))

        for i, node in enumerate(self.futures):
            abcfc = node.abcfc
            best_line = [abcfc.best * (ti/abcfc.duration) for ti in t]
            worst_line = [abcfc.worst * (ti/abcfc.duration) for ti in t]
            exp_line = [abcfc.expected * (ti/abcfc.duration) for ti in t]

            ax.fill_between(t, worst_line, best_line, alpha=0.15, color=colors[i])
            ax.plot(t, exp_line, '-', color=colors[i], lw=1.5,
                   label=f'{node.action.name} (E={abcfc.expected:+.0f})')

        ax.axhline(y=0, color='black', ls='-', lw=1)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Profit', fontsize=12)
        ax.set_title('ABCFC Nexus Cloud - Decision Space', fontsize=14)
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/abcfc_nexus.png'

        plt.savefig(save_path, dpi=150)
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "num_futures": len(self.futures),
            "best_action": self.get_best_action()[0].name if self.futures else "hold"
        }


# ============================================================================
# COMPLETE SYSTEM
# ============================================================================

class ABCFCSystem:
    """
    Complete ABCFC System combining hierarchy and nexus.

    INTEGRATED: Actions at any level propagate up to top-line.

    Usage:
        system = ABCFCSystem("Yair Siegel")

        # Build hierarchy
        system.add_category("Trading")
        system.add_subcategory("Trading", "Polymarket")
        system.add_position("Polymarket", "Market A", worst=-40, best=60)

        # Evaluate action on any node - see top-line impact
        impact = system.evaluate_action("Market A", Action("sell", "sell", {"size": 50}))
        print(impact["top_line_change"])  # How Yair Siegel ABCFC changes

        # Find best action across all nodes
        best = system.find_best_action()
    """

    def __init__(self, name: str = "Yair Siegel"):
        self.hierarchy = ABCFCHierarchy(name)
        self.nexuses: Dict[str, ABCFCNexus] = {}
        self.risk_aversion = 0.5

    # Hierarchy methods
    def add_category(self, *args, **kwargs) -> ABCFC:
        return self.hierarchy.add_category(*args, **kwargs)

    def add_subcategory(self, *args, **kwargs) -> ABCFC:
        return self.hierarchy.add_subcategory(*args, **kwargs)

    def add_position(self, *args, **kwargs) -> ABCFC:
        return self.hierarchy.add_position(*args, **kwargs)

    def get_node(self, name: str) -> Optional[ABCFC]:
        return self.hierarchy.get_node(name)

    def total_bounds(self) -> Tuple[float, float]:
        return self.hierarchy.total_bounds()

    def total_expected(self) -> float:
        return self.hierarchy.total_expected()

    def print_hierarchy(self):
        self.hierarchy.print_tree()

    # ==================== INTEGRATED NEXUS ====================

    def evaluate_action(self, node_name: str, action: Action) -> Dict:
        """
        Evaluate an action on any node and see top-line impact.

        Returns:
            Dict with:
            - node_before: ABCFC before action
            - node_after: ABCFC after action
            - top_line_before: Root ABCFC before
            - top_line_after: Root ABCFC after (simulated)
            - delta: Change in expected, worst, best
        """
        node = self.get_node(node_name)
        if not node:
            raise ValueError(f"Node '{node_name}' not found")

        # Current state
        root_before = self._copy_abcfc(self.hierarchy.root)

        # Simulate action
        nexus = ABCFCNexus(node, self.risk_aversion)
        node_after = nexus.simulate_action(action, node)

        # Calculate delta
        delta_worst = node_after.worst - node.worst
        delta_best = node_after.best - node.best
        delta_expected = node_after.expected - node.expected

        # Propagate to top line
        top_line_after_worst = root_before.worst + delta_worst
        top_line_after_best = root_before.best + delta_best
        top_line_after_expected = root_before.expected + delta_expected

        return {
            "node_name": node_name,
            "action": action.name,
            "node_before": {"worst": node.worst, "best": node.best, "expected": node.expected},
            "node_after": {"worst": node_after.worst, "best": node_after.best, "expected": node_after.expected},
            "top_line_before": {"worst": root_before.worst, "best": root_before.best, "expected": root_before.expected},
            "top_line_after": {"worst": top_line_after_worst, "best": top_line_after_best, "expected": top_line_after_expected},
            "delta": {"worst": delta_worst, "best": delta_best, "expected": delta_expected},
            "score": self._score_delta(delta_expected, delta_worst, delta_best)
        }

    def _copy_abcfc(self, abcfc: ABCFC) -> ABCFC:
        """Create a copy of ABCFC for simulation."""
        return ABCFC(
            name=abcfc.name + "_copy",
            worst=abcfc.worst,
            best=abcfc.best,
            expected=abcfc.expected,
            duration=abcfc.duration,
            level=abcfc.level
        )

    def _score_delta(self, delta_exp: float, delta_worst: float, delta_best: float) -> float:
        """Score a change in ABCFC."""
        # Higher expected = good
        # Better worst (less negative) = good (weighted by risk aversion)
        # Higher best = good (small weight)
        score = delta_exp
        score += self.risk_aversion * delta_worst  # If worst improves (less negative), this helps
        score += (1 - self.risk_aversion) * delta_best * 0.1
        return score

    def evaluate_all_actions(self, node_name: str, actions: List[Action]) -> List[Dict]:
        """Evaluate multiple actions on a node."""
        results = []
        for action in actions:
            result = self.evaluate_action(node_name, action)
            results.append(result)
        return sorted(results, key=lambda r: r["score"], reverse=True)

    def find_best_action_on_node(self, node_name: str, actions: List[Action]) -> Dict:
        """Find best action for a specific node."""
        results = self.evaluate_all_actions(node_name, actions)
        return results[0] if results else None

    def find_best_action_global(self, actions: List[Action], node_filter: Callable = None) -> Dict:
        """
        Find the best action across ALL nodes in hierarchy.

        Args:
            actions: List of possible actions
            node_filter: Optional function to filter which nodes to consider

        Returns:
            Best (node, action, impact) tuple
        """
        all_results = []

        for node_name, node in self.hierarchy.all_nodes.items():
            # Skip root
            if node.level == 0:
                continue

            # Apply filter if provided
            if node_filter and not node_filter(node):
                continue

            for action in actions:
                try:
                    result = self.evaluate_action(node_name, action)
                    all_results.append(result)
                except Exception:
                    continue

        if not all_results:
            return None

        return max(all_results, key=lambda r: r["score"])

    def get_top_line_nexus_cloud(self, actions: List[Action]) -> Dict:
        """
        Get the nexus cloud at top-line level.

        Shows how different actions on different nodes affect Yair Siegel total.
        """
        cloud = {
            "current": {
                "worst": self.hierarchy.root.worst,
                "best": self.hierarchy.root.best,
                "expected": self.hierarchy.root.expected
            },
            "futures": []
        }

        for node_name, node in self.hierarchy.all_nodes.items():
            if node.level == 0:
                continue

            for action in actions:
                try:
                    result = self.evaluate_action(node_name, action)
                    cloud["futures"].append({
                        "node": node_name,
                        "action": action.name,
                        "top_line": result["top_line_after"],
                        "delta": result["delta"],
                        "score": result["score"]
                    })
                except Exception:
                    continue

        # Sort by score
        cloud["futures"].sort(key=lambda f: f["score"], reverse=True)

        # Cloud bounds
        if cloud["futures"]:
            cloud["cloud_bounds"] = {
                "worst_possible": min(f["top_line"]["worst"] for f in cloud["futures"]),
                "best_possible": max(f["top_line"]["best"] for f in cloud["futures"]),
                "best_expected": max(f["top_line"]["expected"] for f in cloud["futures"]),
                "worst_expected": min(f["top_line"]["expected"] for f in cloud["futures"])
            }

        return cloud

    # Legacy nexus methods (still available)
    def create_nexus(self, node_name: str, risk_aversion: float = 0.5) -> ABCFCNexus:
        """Create a nexus for decision making on a specific node."""
        node = self.get_node(node_name)
        if not node:
            raise ValueError(f"Node '{node_name}' not found")

        nexus = ABCFCNexus(node, risk_aversion)
        self.nexuses[node_name] = nexus
        return nexus

    def get_nexus(self, node_name: str) -> Optional[ABCFCNexus]:
        return self.nexuses.get(node_name)

    # ==================== VISUALIZATION ====================

    def plot_top_line_nexus(self, actions: List[Action], save_path: str = None) -> Dict:
        """Visualize how actions across hierarchy affect top-line."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError as e:
            return {"success": False, "error": str(e)}

        cloud = self.get_top_line_nexus_cloud(actions)

        fig, ax = plt.subplots(figsize=(14, 8))

        duration = self.hierarchy.root.duration
        t = np.linspace(0, duration, 100)

        # Plot current state
        current = cloud["current"]
        curr_worst = [current["worst"] * (ti/duration) for ti in t]
        curr_best = [current["best"] * (ti/duration) for ti in t]
        curr_exp = [current["expected"] * (ti/duration) for ti in t]

        ax.fill_between(t, curr_worst, curr_best, alpha=0.15, color='gray', label='Current (no action)')
        ax.plot(t, curr_exp, '--', color='gray', lw=2)

        # Plot top futures (limit to avoid clutter)
        top_futures = cloud["futures"][:8]
        colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(top_futures)))

        for i, future in enumerate(top_futures):
            tl = future["top_line"]
            worst_line = [tl["worst"] * (ti/duration) for ti in t]
            best_line = [tl["best"] * (ti/duration) for ti in t]
            exp_line = [tl["expected"] * (ti/duration) for ti in t]

            label = f'{future["node"]}: {future["action"]} (E={tl["expected"]:+.0f})'
            ax.fill_between(t, worst_line, best_line, alpha=0.1, color=colors[i])
            ax.plot(t, exp_line, '-', color=colors[i], lw=1.5, label=label)

        ax.axhline(y=0, color='black', ls='-', lw=1)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Profit', fontsize=12)
        ax.set_title(f'{self.hierarchy.root.name} - Top-Line Nexus Cloud', fontsize=14)
        ax.legend(loc='upper left', fontsize=8, ncol=2)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/abcfc_topline_nexus.png'

        plt.savefig(save_path, dpi=150)
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "cloud": cloud
        }

    def plot_hierarchy(self, save_path: str = None) -> Dict:
        """Plot the hierarchy as stacked ABCFCs."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError as e:
            return {"success": False, "error": str(e)}

        # Collect all level 3 nodes (positions)
        positions = [n for n in self.hierarchy.all_nodes.values() if n.level == 3]

        if not positions:
            return {"success": False, "error": "No positions to plot"}

        fig, ax = plt.subplots(figsize=(14, 8))

        duration = max(p.duration for p in positions)
        t = np.linspace(0, duration, 100)

        # Stack positions
        cumulative_worst = np.zeros_like(t)
        cumulative_best = np.zeros_like(t)

        colors = plt.cm.tab10(np.linspace(0, 1, len(positions)))

        for i, pos in enumerate(positions):
            worst_line = np.array([pos.worst * (ti/pos.duration) for ti in t])
            best_line = np.array([pos.best * (ti/pos.duration) for ti in t])

            ax.fill_between(t, cumulative_worst + worst_line,
                          cumulative_best + best_line,
                          alpha=0.4, color=colors[i],
                          label=f'{pos.name} [{pos.worst:+.0f}, {pos.best:+.0f}]')

            cumulative_worst += worst_line
            cumulative_best += best_line

        # Plot total bounds
        root = self.hierarchy.root
        total_worst = [root.worst * (ti/duration) for ti in t]
        total_best = [root.best * (ti/duration) for ti in t]
        total_exp = [root.expected * (ti/duration) for ti in t]

        ax.plot(t, total_best, 'g-', lw=2, label=f'Total Best: {root.best:+.0f}')
        ax.plot(t, total_exp, 'b--', lw=2, label=f'Total Expected: {root.expected:+.0f}')
        ax.plot(t, total_worst, 'r-', lw=2, label=f'Total Worst: {root.worst:+.0f}')

        ax.axhline(y=0, color='black', ls='-', lw=1)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Profit', fontsize=12)
        ax.set_title(f'{root.name} - ABCFC Hierarchy', fontsize=14)
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/abcfc_hierarchy.png'

        plt.savefig(save_path, dpi=150)
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "total_bounds": (root.worst, root.best),
            "total_expected": root.expected
        }


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ABCFC SYSTEM - Integrated Hierarchy + Nexus")
    print("=" * 70)

    # Create system
    system = ABCFCSystem("Yair Siegel")
    system.risk_aversion = 0.6

    # Build hierarchy
    print("\n1. Building Hierarchy...")

    system.add_category("Trading", worst=-500, best=2000, expected=200)
    system.add_category("Business", worst=-100, best=500, expected=50)
    system.add_category("Employment", worst=0, best=0, expected=0)

    system.add_subcategory("Trading", "Polymarket", worst=-200, best=1000, expected=100)
    system.add_subcategory("Trading", "Stocks", worst=-300, best=800, expected=80)
    system.add_subcategory("Trading", "Crypto", worst=0, best=200, expected=20)

    system.add_position("Polymarket", "Election YES", worst=-40, best=60, expected=15)
    system.add_position("Polymarket", "Fed Rate NO", worst=-30, best=70, expected=25)
    system.add_position("Polymarket", "BTC 100k YES", worst=-50, best=100, expected=10)

    system.add_position("Stocks", "AAPL Long", worst=-100, best=200, expected=30)
    system.add_position("Stocks", "TSLA Put", worst=-50, best=150, expected=20)

    print("\nHierarchy:")
    system.print_hierarchy()

    print(f"\nTotal Bounds: {system.total_bounds()}")
    print(f"Total Expected: {system.total_expected()}")

    # Define possible actions
    actions = [
        Action("Buy More", "buy", {"size": 50, "price": 0.45}),
        Action("Sell Half", "sell", {"size": 25, "price": 0.55}),
        Action("Hedge 50%", "hedge", {"ratio": 0.5}),
        Action("Hold", "hold", {}),
    ]

    # ==================== INTEGRATED NEXUS ====================
    print("\n2. Integrated Nexus - Actions affect Top-Line...")

    # Evaluate specific action on specific node
    print("\n   a) Single action evaluation:")
    result = system.evaluate_action("Election YES", actions[0])  # Buy More
    print(f"      Action: {result['action']} on {result['node_name']}")
    print(f"      Node change: [{result['node_before']['worst']:+.0f}, {result['node_before']['best']:+.0f}] → [{result['node_after']['worst']:+.0f}, {result['node_after']['best']:+.0f}]")
    print(f"      Top-line change: E={result['top_line_before']['expected']:+.0f} → E={result['top_line_after']['expected']:+.0f}")
    print(f"      Delta: worst={result['delta']['worst']:+.0f}, best={result['delta']['best']:+.0f}, expected={result['delta']['expected']:+.0f}")

    # Find best action on a node
    print("\n   b) Best action on 'Election YES':")
    best = system.find_best_action_on_node("Election YES", actions)
    print(f"      → {best['action']} (score={best['score']:.2f})")

    # Find best action GLOBALLY
    print("\n   c) Best action across ENTIRE hierarchy:")
    global_best = system.find_best_action_global(actions)
    print(f"      → {global_best['action']} on {global_best['node_name']}")
    print(f"      Score: {global_best['score']:.2f}")
    print(f"      Top-line impact: E goes from {global_best['top_line_before']['expected']:+.0f} to {global_best['top_line_after']['expected']:+.0f}")

    # Get full nexus cloud
    print("\n   d) Top-Line Nexus Cloud (top 5):")
    cloud = system.get_top_line_nexus_cloud(actions)
    for i, future in enumerate(cloud["futures"][:5]):
        print(f"      {i+1}. {future['node']}: {future['action']} → E={future['top_line']['expected']:+.0f} (score={future['score']:.2f})")

    if "cloud_bounds" in cloud:
        cb = cloud["cloud_bounds"]
        print(f"\n   Cloud bounds:")
        print(f"      Worst possible: {cb['worst_possible']:+.0f}")
        print(f"      Best possible: {cb['best_possible']:+.0f}")
        print(f"      Expected range: [{cb['worst_expected']:+.0f}, {cb['best_expected']:+.0f}]")

    # ==================== VISUALIZATION ====================
    print("\n3. Generating Visualizations...")

    result1 = system.plot_hierarchy()
    print(f"   Hierarchy chart: {result1.get('chart_path')}")

    result2 = system.plot_top_line_nexus(actions)
    print(f"   Top-line nexus chart: {result2.get('chart_path')}")

    # ==================== ORDER FLOW ====================
    print("\n4. Order Flow Model...")

    import random
    regular_timestamps = [i * 10 + random.uniform(-2, 2) for i in range(20)]
    chaotic_timestamps = sorted([random.uniform(0, 100) for _ in range(20)])

    regular_flow = OrderFlowModel.from_order_history(regular_timestamps)
    chaotic_flow = OrderFlowModel.from_order_history(chaotic_timestamps)

    print(f"   Regular market: level={regular_flow.level.name}, confidence={regular_flow.get_confidence():.2f}")
    print(f"   Chaotic market: level={chaotic_flow.level.name}, confidence={chaotic_flow.get_confidence():.2f}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
Yair Siegel Total:
  Current: [{system.total_bounds()[0]:+.0f}, {system.total_bounds()[1]:+.0f}] E={system.total_expected():+.0f}

Best Move (global):
  {global_best['action']} on {global_best['node_name']}
  Impact: E {global_best['top_line_before']['expected']:+.0f} → {global_best['top_line_after']['expected']:+.0f}

Decision Space:
  {len(cloud['futures'])} possible actions across {len(system.hierarchy.all_nodes)-1} nodes
    """)
    print("=" * 70)
