#!/usr/bin/env python3
"""
ABCFC LAYERS - Hierarchical Absolute Bounds Continuous Fan Charts

Multi-layer ABCFC system for Yair's finance visualization:

HIERARCHY:
    Total Finance
    ├── Trading
    │   ├── Polymarket
    │   │   ├── Market 1
    │   │   │   ├── Order 1
    │   │   │   └── Order 2
    │   │   └── Market 2
    │   └── Other Trading
    ├── Hands-off System
    │   ├── Revenue Stream 1
    │   └── Revenue Stream 2
    └── Other Finance

Each layer aggregates best/worst/expected from its children.

USAGE:
    from executor.math.abcfc_layers import ABCFCLayers, get_layers

    layers = get_layers()

    # View hierarchy
    layers.total_finance.summary()
    layers.polymarket.summary()

    # Add a position
    layers.add_position("polymarket", "weed-2025", entry=0.10, size=100)

    # Plot any layer
    layers.plot("trading")
    layers.plot("total_finance")

Created by: Yair Siegel
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path

# Import the base ABCFC
from executor.math.resolution_cone import ResolutionCone


@dataclass
class ABCFCNode:
    """
    A single node in the ABCFC hierarchy.

    Can be a leaf (single position) or aggregate (sum of children).
    """
    name: str
    layer: str  # total_finance, trading, polymarket, market, order
    parent: Optional[str] = None

    # For leaf nodes (actual positions)
    entry_price: Optional[float] = None
    position_size: Optional[float] = None
    prob_yes: Optional[float] = None
    side: str = "YES"
    days: int = 30

    # Computed values (set by _calculate)
    best_case: float = 0.0
    worst_case: float = 0.0
    expected: float = 0.0

    # Children for aggregate nodes
    children: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict = field(default_factory=dict)

    def is_leaf(self) -> bool:
        """True if this is a position, not an aggregate."""
        return self.entry_price is not None and len(self.children) == 0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "layer": self.layer,
            "parent": self.parent,
            "best_case": round(self.best_case, 2),
            "worst_case": round(self.worst_case, 2),
            "expected": round(self.expected, 2),
            "is_leaf": self.is_leaf(),
            "children": self.children,
            "metadata": self.metadata
        }


class ABCFCLayers:
    """
    Hierarchical ABCFC system for multi-layer finance visualization.

    Layers (from macro to micro):
    1. total_finance - Everything
    2. trading - All trading activities
    3. polymarket - Polymarket positions
    4. handsoff - Hands-off system revenue
    5. market - Individual market
    6. order - Individual order
    """

    LAYER_HIERARCHY = {
        "total_finance": None,  # Root
        "trading": "total_finance",
        "polymarket": "trading",
        "handsoff": "total_finance",
        "other_finance": "total_finance",
        "market": "polymarket",  # Dynamic parent
        "order": "market"  # Dynamic parent
    }

    def __init__(self):
        self.nodes: Dict[str, ABCFCNode] = {}
        self._init_structure()

    def _init_structure(self):
        """Initialize the base hierarchy."""
        # Root layers
        self.nodes["total_finance"] = ABCFCNode(
            name="Total Finance",
            layer="total_finance"
        )

        self.nodes["trading"] = ABCFCNode(
            name="Trading",
            layer="trading",
            parent="total_finance"
        )
        self.nodes["total_finance"].children.append("trading")

        self.nodes["polymarket"] = ABCFCNode(
            name="Polymarket",
            layer="polymarket",
            parent="trading"
        )
        self.nodes["trading"].children.append("polymarket")

        self.nodes["handsoff"] = ABCFCNode(
            name="Hands-off System",
            layer="handsoff",
            parent="total_finance"
        )
        self.nodes["total_finance"].children.append("handsoff")

        self.nodes["other_finance"] = ABCFCNode(
            name="Other Finance",
            layer="other_finance",
            parent="total_finance"
        )
        self.nodes["total_finance"].children.append("other_finance")

    # ==================== ADD POSITIONS ====================

    def add_position(
        self,
        layer: str,
        name: str,
        entry_price: float,
        size: float,
        prob_yes: float = None,
        side: str = "YES",
        days: int = 30,
        parent: str = None,
        metadata: Dict = None
    ) -> ABCFCNode:
        """
        Add a position to the hierarchy.

        Args:
            layer: "polymarket", "market", "order", "handsoff", etc.
            name: Position identifier
            entry_price: Entry price
            size: Position size in USDC
            prob_yes: Probability estimate
            side: "YES" or "NO"
            days: Days to resolution
            parent: Parent node (auto-detected if not specified)
            metadata: Additional info (market slug, order id, etc.)

        Returns:
            The created ABCFCNode
        """
        # Determine parent
        if parent is None:
            parent = self.LAYER_HIERARCHY.get(layer, "total_finance")

        # Create node
        node_id = f"{layer}:{name}"
        node = ABCFCNode(
            name=name,
            layer=layer,
            parent=parent,
            entry_price=entry_price,
            position_size=size,
            prob_yes=prob_yes if prob_yes else entry_price,
            side=side.upper(),
            days=days,
            metadata=metadata or {}
        )

        # Calculate outcomes using ResolutionCone
        cone = ResolutionCone(
            entry_price=entry_price,
            position_size=size,
            prob_yes=node.prob_yes,
            days=days,
            side=side
        )
        node.best_case = cone.best_case
        node.worst_case = cone.worst_case
        node.expected = cone.expected

        # Store node
        self.nodes[node_id] = node

        # Add to parent's children
        if parent in self.nodes:
            if node_id not in self.nodes[parent].children:
                self.nodes[parent].children.append(node_id)

        # Recalculate aggregates up the chain
        self._recalculate_aggregates()

        return node

    def add_polymarket_position(
        self,
        market_slug: str,
        entry_price: float,
        size: float,
        prob_yes: float = None,
        side: str = "YES",
        days: int = 30
    ) -> ABCFCNode:
        """Convenience method for adding Polymarket positions."""
        return self.add_position(
            layer="market",
            name=market_slug,
            entry_price=entry_price,
            size=size,
            prob_yes=prob_yes,
            side=side,
            days=days,
            parent="polymarket",
            metadata={"source": "polymarket", "slug": market_slug}
        )

    def add_handsoff_stream(
        self,
        name: str,
        expected_daily: float,
        variance_pct: float = 0.2,
        days: int = 30
    ) -> ABCFCNode:
        """
        Add a hands-off system revenue stream.

        Args:
            name: Stream name (e.g., "liquidity_rewards", "trading_profits")
            expected_daily: Expected daily revenue
            variance_pct: Variance as percentage (0.2 = 20%)
            days: Projection period
        """
        node_id = f"handsoff:{name}"

        expected = expected_daily * days
        best = expected * (1 + variance_pct * 2)  # 2 sigma up
        worst = expected * (1 - variance_pct * 2)  # 2 sigma down (can go negative)

        node = ABCFCNode(
            name=name,
            layer="handsoff",
            parent="handsoff",
            days=days,
            best_case=best,
            worst_case=worst,
            expected=expected,
            metadata={"expected_daily": expected_daily, "variance_pct": variance_pct}
        )

        self.nodes[node_id] = node

        if node_id not in self.nodes["handsoff"].children:
            self.nodes["handsoff"].children.append(node_id)

        self._recalculate_aggregates()
        return node

    # ==================== CALCULATIONS ====================

    def _recalculate_aggregates(self):
        """Recalculate all aggregate nodes from leaves up."""
        # Process in reverse order (leaves first, then parents)
        processed = set()

        def process_node(node_id: str):
            if node_id in processed:
                return

            node = self.nodes.get(node_id)
            if not node:
                return

            # Process children first
            for child_id in node.children:
                process_node(child_id)

            # If has children, aggregate
            if node.children:
                node.best_case = sum(
                    self.nodes[c].best_case for c in node.children if c in self.nodes
                )
                node.worst_case = sum(
                    self.nodes[c].worst_case for c in node.children if c in self.nodes
                )
                node.expected = sum(
                    self.nodes[c].expected for c in node.children if c in self.nodes
                )

            processed.add(node_id)

        # Start from root
        process_node("total_finance")

    # ==================== ACCESS ====================

    def get(self, node_id: str) -> Optional[ABCFCNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_layer(self, layer: str) -> List[ABCFCNode]:
        """Get all nodes in a layer."""
        return [n for n in self.nodes.values() if n.layer == layer]

    @property
    def total_finance(self) -> ABCFCNode:
        return self.nodes["total_finance"]

    @property
    def trading(self) -> ABCFCNode:
        return self.nodes["trading"]

    @property
    def polymarket(self) -> ABCFCNode:
        return self.nodes["polymarket"]

    @property
    def handsoff(self) -> ABCFCNode:
        return self.nodes["handsoff"]

    # ==================== VISUALIZATION ====================

    def summary(self, node_id: str = "total_finance", indent: int = 0) -> str:
        """Get hierarchical summary as text."""
        node = self.nodes.get(node_id)
        if not node:
            return f"Node not found: {node_id}"

        prefix = "  " * indent
        lines = []

        # Node info
        if node.is_leaf():
            lines.append(
                f"{prefix}├── {node.name}: "
                f"Best +${node.best_case:.0f} / "
                f"Exp ${node.expected:+.0f} / "
                f"Worst ${node.worst_case:.0f}"
            )
        else:
            lines.append(
                f"{prefix}{'└── ' if indent > 0 else ''}{node.name.upper()}: "
                f"Best +${node.best_case:.0f} / "
                f"Exp ${node.expected:+.0f} / "
                f"Worst ${node.worst_case:.0f}"
            )

        # Children
        for child_id in node.children:
            lines.append(self.summary(child_id, indent + 1))

        return "\n".join(lines)

    def plot(
        self,
        node_id: str = "total_finance",
        save_path: str = None,
        days: int = None
    ) -> Dict:
        """
        Plot ABCFC for any node in the hierarchy.

        Args:
            node_id: Node to plot (e.g., "total_finance", "polymarket", "market:weed-2025")
            save_path: Where to save
            days: Override days (default: use node's days)
        """
        node = self.nodes.get(node_id)
        if not node:
            return {"success": False, "error": f"Node not found: {node_id}"}

        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy.ndimage import gaussian_filter
        except ImportError as e:
            return {"success": False, "error": f"Missing dependency: {e}"}

        if days is None:
            days = node.days if node.days else 30

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))

        # Build trajectory lines
        days_range = np.linspace(0, days, days + 1)
        best_line = (days_range / days) * node.best_case
        worst_line = (days_range / days) * node.worst_case
        expected_line = (days_range / days) * node.expected

        # Create gradient mesh
        n_x, n_y = 200, 400
        y_min = node.worst_case * 1.05 if node.worst_case < 0 else -abs(node.best_case) * 0.1
        y_max = node.best_case * 1.05 if node.best_case > 0 else abs(node.worst_case) * 0.1

        x = np.linspace(0, days, n_x)
        y = np.linspace(y_min, y_max, n_y)
        X, Y = np.meshgrid(x, y)
        density = np.zeros_like(X)

        for i in range(n_x):
            day = x[i]
            if day == 0:
                continue

            day_best = (day / days) * node.best_case
            day_worst = (day / days) * node.worst_case
            day_expected = (day / days) * node.expected
            day_range = day_best - day_worst

            for j in range(n_y):
                y_val = y[j]
                if day_range > 0 and day_worst <= y_val <= day_best:
                    t = (y_val - day_worst) / day_range
                    exp_t = (day_expected - day_worst) / day_range if day_range > 0 else 0.5
                    sigma = 0.35
                    dist = abs(t - exp_t)
                    density[j, i] = np.exp(-(dist ** 2) / (2 * sigma ** 2))

        density = gaussian_filter(density, sigma=3)
        if density.max() > 0:
            density = density / density.max()

        ax.pcolormesh(X, Y, density, cmap='Blues', shading='gouraud', alpha=0.85)

        # Plot lines
        ax.plot(days_range, best_line, 'g-', linewidth=2,
                label=f'Best: +${node.best_case:,.0f}')
        ax.plot(days_range, expected_line, 'b-', linewidth=2.5,
                label=f'Expected: ${node.expected:+,.0f}')
        ax.plot(days_range, worst_line, 'r-', linewidth=2,
                label=f'Worst: ${node.worst_case:,.0f}')

        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax.axhspan(0, ax.get_ylim()[1], alpha=0.05, color='green')
        ax.axhspan(ax.get_ylim()[0], 0, alpha=0.05, color='red')

        ax.set_xlabel('Days', fontsize=12)
        ax.set_ylabel('Profit/Loss ($)', fontsize=12)
        ax.set_title(f'ABCFC: {node.name}\n{len(node.children)} positions', fontsize=14)
        ax.legend(loc='upper left' if node.expected > 0 else 'lower left', fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path is None:
            safe_name = node_id.replace(":", "_").replace("/", "_")
            save_path = f'/tmp/abcfc_{safe_name}.png'

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "node": node.to_dict()
        }

    # ==================== PERSISTENCE ====================

    def save(self, path: str = None):
        """Save state to JSON."""
        if path is None:
            path = Path(__file__).parent.parent.parent / "state" / "abcfc_layers.json"

        data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()}
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, path: str = None):
        """Load state from JSON."""
        if path is None:
            path = Path(__file__).parent.parent.parent / "state" / "abcfc_layers.json"

        if not Path(path).exists():
            return

        with open(path) as f:
            data = json.load(f)

        # Reconstruct nodes
        for node_id, node_data in data.get("nodes", {}).items():
            self.nodes[node_id] = ABCFCNode(
                name=node_data["name"],
                layer=node_data["layer"],
                parent=node_data.get("parent"),
                best_case=node_data.get("best_case", 0),
                worst_case=node_data.get("worst_case", 0),
                expected=node_data.get("expected", 0),
                children=node_data.get("children", []),
                metadata=node_data.get("metadata", {})
            )

    def to_dict(self) -> Dict:
        """Export full state."""
        return {
            "total_finance": self.total_finance.to_dict(),
            "layers": {
                "trading": self.trading.to_dict(),
                "polymarket": self.polymarket.to_dict(),
                "handsoff": self.handsoff.to_dict()
            },
            "all_nodes": {k: v.to_dict() for k, v in self.nodes.items()}
        }


# Singleton
_layers = None

def get_layers() -> ABCFCLayers:
    """
    Get or create the ABCFC layers singleton.

    INTEGRAFIX: Loads positions from abcfc_unified_state.json for real data.
    """
    global _layers
    if _layers is None:
        _layers = ABCFCLayers()
        _load_from_unified_state(_layers)
    return _layers


def _load_from_unified_state(layers: ABCFCLayers):
    """
    INTEGRAFIX: Load positions from unified state into layers hierarchy.
    """
    try:
        import json
        from pathlib import Path

        PROJECT_ROOT = Path(__file__).parent.parent.parent
        unified_file = PROJECT_ROOT / "state" / "abcfc_unified_state.json"

        if not unified_file.exists():
            return

        with open(unified_file) as f:
            data = json.load(f)

        positions = data.get("positions", [])

        for pos in positions[:100]:  # Top 100 positions
            try:
                name = pos.get("name", "unknown")[:30]
                category = pos.get("category", "Trading")
                worst = float(pos.get("worst", 0))
                best = float(pos.get("best", 0))
                expected = float(pos.get("expected", 0))

                # Determine parent based on category
                if category == "Trading" or "trade" in name.lower() or "polymarket" in name.lower():
                    parent = "polymarket"
                    layer = "market"
                else:
                    parent = "handsoff"
                    layer = "stream"

                # Create node with ABCFC values directly
                node_id = f"{parent}_{name}"
                node = ABCFCNode(
                    name=name,
                    layer=layer,
                    parent=parent,
                    best_case=best,
                    worst_case=worst,
                    expected=expected,
                    metadata={"source": "unified_state", "category": category}
                )

                # Store and link
                layers.nodes[node_id] = node
                if parent in layers.nodes:
                    if node_id not in layers.nodes[parent].children:
                        layers.nodes[parent].children.append(node_id)

            except Exception:
                continue

        # Recalculate aggregates
        layers._recalculate_aggregates()

    except Exception:
        pass  # Silent fail - layers work without positions


# Convenience aliases
layers = get_layers


if __name__ == "__main__":
    print("=" * 60)
    print("ABCFC LAYERS - Hierarchical Finance Visualization")
    print("=" * 60)

    l = get_layers()

    # Add some test positions
    l.add_polymarket_position("weed-rescheduled-2025", 0.10, 100)
    l.add_polymarket_position("btc-100k-2025", 0.45, 200)
    l.add_handsoff_stream("liquidity_rewards", expected_daily=2.0)
    l.add_handsoff_stream("trading_profits", expected_daily=5.0, variance_pct=0.5)

    print("\n" + l.summary())

    print("\n" + "=" * 60)
    print("Layer Summaries:")
    print(f"  Total Finance: Best +${l.total_finance.best_case:,.0f} / Worst ${l.total_finance.worst_case:,.0f}")
    print(f"  Polymarket:    Best +${l.polymarket.best_case:,.0f} / Worst ${l.polymarket.worst_case:,.0f}")
    print(f"  Hands-off:     Best +${l.handsoff.best_case:,.0f} / Worst ${l.handsoff.worst_case:,.0f}")
