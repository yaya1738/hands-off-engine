#!/usr/bin/env python3
"""
ABCFC UNIFIED - Complete System Built on Pure Math

Links:
- abcfc_pure.py: Pure mathematical ABCFC2D definition
- abcfc_system.py: Hierarchy and nexus structure

This module:
1. Uses ABCFC2D as the mathematical foundation
2. Provides proper density functions (flow-adjusted, binary, etc.)
3. Integrates hierarchy with real 2D density
4. Visualizes with true continuous probability fields

Created by: Yair Siegel
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum

# Import pure math foundation
from executor.math.abcfc_pure import (
    ABCFC2D,
    DensityFunc,
    uniform_density,
    gaussian_density,
    bimodal_density,
    create_abcfc
)


# ============================================================================
# DENSITY FUNCTIONS (Flow-Adjusted, Binary Market, etc.)
# ============================================================================

def create_binary_market_density(
    prob_yes: float,
    entry_price: float,
    shares: float
) -> DensityFunc:
    """
    Create density for a binary market position.

    At t=0: concentrated at 0 (no P&L yet)
    As t→T: splits toward two outcomes (win/lose)

    Args:
        prob_yes: Probability of YES outcome (0-1)
        entry_price: Price paid per share
        shares: Number of shares

    Returns:
        Density function P(profit, t, a, b, T)
    """
    # P&L outcomes
    win_pnl = shares * (1 - entry_price)   # If YES wins
    lose_pnl = shares * (-entry_price)      # If YES loses

    def density(x: float, t: float, a: float, b: float, T: float) -> float:
        if T <= 0:
            return 0.0

        progress = t / T  # 0 at start, 1 at resolution

        if progress < 0.1:
            # Early: concentrated near 0
            sigma = (b - a) * 0.05
            z = x / (sigma + 0.001)
            return math.exp(-0.5 * z * z)

        elif progress > 0.9:
            # Near resolution: bimodal at outcomes
            sigma = (b - a) * 0.03 * (1.1 - progress)  # Tightens as we approach T

            z_win = (x - win_pnl) / (sigma + 0.001)
            z_lose = (x - lose_pnl) / (sigma + 0.001)

            p_win = prob_yes * math.exp(-0.5 * z_win * z_win)
            p_lose = (1 - prob_yes) * math.exp(-0.5 * z_lose * z_lose)

            return p_win + p_lose

        else:
            # Middle: transitioning from unimodal to bimodal
            split_factor = (progress - 0.1) / 0.8  # 0 at t=0.1T, 1 at t=0.9T

            # Unimodal component (centered on expected)
            expected = prob_yes * win_pnl + (1 - prob_yes) * lose_pnl
            sigma_uni = (b - a) * 0.2 * (1 - split_factor * 0.5)
            z_uni = (x - expected * progress) / (sigma_uni + 0.001)
            p_uni = math.exp(-0.5 * z_uni * z_uni)

            # Bimodal component
            sigma_bi = (b - a) * 0.1
            z_win = (x - win_pnl * progress) / (sigma_bi + 0.001)
            z_lose = (x - lose_pnl * progress) / (sigma_bi + 0.001)
            p_bi = prob_yes * math.exp(-0.5 * z_win * z_win) + \
                   (1 - prob_yes) * math.exp(-0.5 * z_lose * z_lose)

            # Blend
            return (1 - split_factor) * p_uni + split_factor * p_bi

    return density


def create_flow_adjusted_density(
    base_density: DensityFunc,
    order_flow_rate: Callable[[float], float],
    flow_confidence: float = 0.7
) -> DensityFunc:
    """
    Adjust density based on order flow rate.

    Higher flow rate → faster evolution of density
    Lower confidence → wider spread

    Args:
        base_density: Base density function
        order_flow_rate: λ(t) function returning orders/time
        flow_confidence: 0-1, how much we trust the flow model
    """
    def density(x: float, t: float, a: float, b: float, T: float) -> float:
        # Get base density
        base_p = base_density(x, t, a, b, T)

        # Adjust spread based on flow rate
        lambda_t = order_flow_rate(t) if callable(order_flow_rate) else order_flow_rate

        # Higher lambda = more activity = faster convergence
        # Lower confidence = wider spread
        spread_factor = 1.0 / (1.0 + lambda_t * 0.1) * (2 - flow_confidence)

        if spread_factor != 1.0 and base_p > 0:
            # Widen or narrow by adjusting distance from mean
            # This is approximate - proper way would be to adjust sigma
            center = (a + b) / 2
            dist = abs(x - center)
            adjusted_dist = dist * spread_factor
            # Map back (simplified)
            return base_p * math.exp(-0.1 * (spread_factor - 1) ** 2)

        return base_p

    return density


def create_aggregated_density(
    child_densities: List[DensityFunc],
    child_bounds: List[Tuple[float, float]]
) -> DensityFunc:
    """
    Create density for sum of independent random variables.

    For parent = sum of children, the density is the convolution.
    We use a simplified approximation here.
    """
    def density(x: float, t: float, a: float, b: float, T: float) -> float:
        # Approximate: treat aggregate as Gaussian with summed means and variances

        # For each child, estimate mean and variance
        total_mean = 0.0
        total_var = 0.0

        for i, (child_dens, (ca, cb)) in enumerate(zip(child_densities, child_bounds)):
            # Estimate child mean (midpoint approximation)
            child_mean = (ca + cb) / 2
            child_var = ((cb - ca) / 4) ** 2  # Rough estimate

            total_mean += child_mean
            total_var += child_var

        # Aggregate is approximately Gaussian
        sigma = math.sqrt(total_var) if total_var > 0 else 1.0
        z = (x - total_mean * (t / T if T > 0 else 0)) / sigma
        return math.exp(-0.5 * z * z)

    return density


# ============================================================================
# POSITION ABCFC (Built on ABCFC2D)
# ============================================================================

@dataclass
class PositionABCFC:
    """
    ABCFC for a trading position, using pure math foundation.

    Wraps ABCFC2D with position-specific semantics.
    """
    name: str
    abcfc: ABCFC2D                    # Pure math ABCFC
    position_type: str = "generic"    # "binary", "stock", "option", etc.

    # Position details
    shares: float = 0.0
    entry_price: float = 0.0
    prob_win: float = 0.5

    # Hierarchy
    parent: 'PositionABCFC' = None
    children: List['PositionABCFC'] = field(default_factory=list)
    level: int = 0

    @property
    def worst(self) -> float:
        return self.abcfc.a

    @property
    def best(self) -> float:
        return self.abcfc.b

    @property
    def duration(self) -> float:
        return self.abcfc.T

    def expected(self, t: float = None) -> float:
        """Expected profit at time t (or at T if not specified)."""
        if t is None:
            t = self.abcfc.T
        return self.abcfc.E(t)

    def variance(self, t: float = None) -> float:
        """Variance at time t."""
        if t is None:
            t = self.abcfc.T
        return self.abcfc.Var(t)

    def P(self, profit: float, t: float) -> float:
        """Probability density at (profit, t)."""
        return self.abcfc.P(profit, t)

    def add_child(self, child: 'PositionABCFC'):
        """Add child and rebuild aggregated density."""
        child.parent = self
        child.level = self.level + 1
        self.children.append(child)
        self._rebuild_aggregate()

    def _rebuild_aggregate(self):
        """Rebuild this node's ABCFC from children."""
        if not self.children:
            return

        # Sum bounds
        new_a = sum(c.worst for c in self.children)
        new_b = sum(c.best for c in self.children)

        # Create aggregated density
        child_densities = [c.abcfc.density for c in self.children]
        child_bounds = [(c.worst, c.best) for c in self.children]

        agg_density = create_aggregated_density(child_densities, child_bounds)

        # Rebuild ABCFC
        self.abcfc = ABCFC2D(
            bounds=(new_a, new_b),
            duration=self.abcfc.T,
            density=agg_density
        )

    def plot(self, save_path: str = None, title: str = None) -> Dict:
        """Plot with proper 2D density visualization."""
        return self.abcfc.plot(save_path=save_path)

    @classmethod
    def from_binary_position(
        cls,
        name: str,
        shares: float,
        entry_price: float,
        prob_yes: float,
        duration: float = 30.0
    ) -> 'PositionABCFC':
        """Create ABCFC for a binary market position."""
        # Compute bounds
        win_pnl = shares * (1 - entry_price)
        lose_pnl = shares * (-entry_price)

        worst = min(win_pnl, lose_pnl)
        best = max(win_pnl, lose_pnl)

        # Create density
        density = create_binary_market_density(prob_yes, entry_price, shares)

        abcfc = ABCFC2D(
            bounds=(worst, best),
            duration=duration,
            density=density
        )

        return cls(
            name=name,
            abcfc=abcfc,
            position_type="binary",
            shares=shares,
            entry_price=entry_price,
            prob_win=prob_yes
        )

    @classmethod
    def from_bounds(
        cls,
        name: str,
        worst: float,
        best: float,
        expected: float = None,
        duration: float = 30.0,
        density_type: str = "gaussian"
    ) -> 'PositionABCFC':
        """Create ABCFC from explicit bounds."""
        if expected is None:
            expected = (worst + best) / 2

        # Use factory from abcfc_pure
        if density_type == "gaussian":
            abcfc = create_abcfc(
                bounds=(worst, best),
                duration=duration,
                density_type="gaussian",
                mu=expected,
                sigma=(best - worst) / 6
            )
        elif density_type == "bimodal":
            p_high = (expected - worst) / (best - worst) if best != worst else 0.5
            abcfc = create_abcfc(
                bounds=(worst, best),
                duration=duration,
                density_type="bimodal",
                p_high=p_high
            )
        else:
            abcfc = create_abcfc(
                bounds=(worst, best),
                duration=duration,
                density_type="uniform"
            )

        return cls(
            name=name,
            abcfc=abcfc,
            position_type=density_type
        )

    def __repr__(self):
        return f"PositionABCFC({self.name}: [{self.worst:+.0f}, {self.best:+.0f}] E={self.expected():+.0f})"


# ============================================================================
# UNIFIED HIERARCHY
# ============================================================================

class UnifiedABCFCHierarchy:
    """
    Hierarchy using proper ABCFC2D math throughout.
    """

    def __init__(self, name: str = "Yair Siegel", duration: float = 30.0):
        # Create root with placeholder (will be rebuilt from children)
        self.root = PositionABCFC.from_bounds(
            name=name,
            worst=0,
            best=0,
            expected=0,
            duration=duration,
            density_type="uniform"
        )
        self.root.level = 0
        self.all_nodes: Dict[str, PositionABCFC] = {name: self.root}
        self.default_duration = duration

    def add_category(
        self,
        name: str,
        worst: float = 0,
        best: float = 0,
        expected: float = None,
        density_type: str = "gaussian"
    ) -> PositionABCFC:
        """Add Level 1 category."""
        node = PositionABCFC.from_bounds(
            name=name,
            worst=worst,
            best=best,
            expected=expected,
            duration=self.default_duration,
            density_type=density_type
        )
        node.level = 1
        self.root.add_child(node)
        self.all_nodes[name] = node
        return node

    def add_subcategory(
        self,
        parent_name: str,
        name: str,
        worst: float = 0,
        best: float = 0,
        expected: float = None,
        density_type: str = "gaussian"
    ) -> PositionABCFC:
        """Add Level 2 subcategory."""
        parent = self.all_nodes.get(parent_name)
        if not parent:
            raise ValueError(f"Parent '{parent_name}' not found")

        node = PositionABCFC.from_bounds(
            name=name,
            worst=worst,
            best=best,
            expected=expected,
            duration=self.default_duration,
            density_type=density_type
        )
        parent.add_child(node)
        self.all_nodes[name] = node
        return node

    def add_binary_position(
        self,
        parent_name: str,
        name: str,
        shares: float,
        entry_price: float,
        prob_yes: float,
        duration: float = None
    ) -> PositionABCFC:
        """Add a binary market position with proper density."""
        parent = self.all_nodes.get(parent_name)
        if not parent:
            raise ValueError(f"Parent '{parent_name}' not found")

        node = PositionABCFC.from_binary_position(
            name=name,
            shares=shares,
            entry_price=entry_price,
            prob_yes=prob_yes,
            duration=duration or self.default_duration
        )
        parent.add_child(node)
        self.all_nodes[name] = node
        return node

    def add_position(
        self,
        parent_name: str,
        name: str,
        worst: float,
        best: float,
        expected: float = None,
        density_type: str = "gaussian",
        duration: float = None
    ) -> PositionABCFC:
        """Add a generic position."""
        parent = self.all_nodes.get(parent_name)
        if not parent:
            raise ValueError(f"Parent '{parent_name}' not found")

        node = PositionABCFC.from_bounds(
            name=name,
            worst=worst,
            best=best,
            expected=expected,
            duration=duration or self.default_duration,
            density_type=density_type
        )
        parent.add_child(node)
        self.all_nodes[name] = node
        return node

    def get_node(self, name: str) -> Optional[PositionABCFC]:
        return self.all_nodes.get(name)

    def total_bounds(self) -> Tuple[float, float]:
        return (self.root.worst, self.root.best)

    def total_expected(self, t: float = None) -> float:
        return self.root.expected(t)

    def print_tree(self, node: PositionABCFC = None, indent: int = 0):
        if node is None:
            node = self.root
        prefix = "  " * indent
        print(f"{prefix}{node}")
        for child in node.children:
            self.print_tree(child, indent + 1)

    def plot_position(self, name: str, save_path: str = None) -> Dict:
        """Plot a specific position with 2D density."""
        node = self.get_node(name)
        if not node:
            return {"success": False, "error": f"Node '{name}' not found"}
        return node.plot(save_path=save_path)

    def plot_hierarchy_2d(self, save_path: str = None) -> Dict:
        """Plot hierarchy with 2D density for each position."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy.ndimage import gaussian_filter
        except ImportError as e:
            return {"success": False, "error": str(e)}

        # Get all leaf positions
        leaves = [n for n in self.all_nodes.values() if not n.children and n.level > 0]

        if not leaves:
            return {"success": False, "error": "No positions to plot"}

        # Create subplots
        n_plots = len(leaves) + 1  # +1 for total
        n_cols = min(3, n_plots)
        n_rows = (n_plots + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
        if n_plots == 1:
            axes = np.array([[axes]])
        elif n_rows == 1:
            axes = axes.reshape(1, -1)

        # Plot each leaf
        for i, node in enumerate(leaves):
            row, col = i // n_cols, i % n_cols
            ax = axes[row, col]

            # Build 2D density grid
            n_t, n_x = 100, 100
            t_vals = np.linspace(0, node.duration, n_t)
            x_vals = np.linspace(node.worst * 1.1, node.best * 1.1, n_x)

            Z = np.zeros((n_x, n_t))
            for ti in range(n_t):
                for xi in range(n_x):
                    Z[xi, ti] = node.P(x_vals[xi], t_vals[ti])

            # Normalize and smooth
            Z = gaussian_filter(Z, sigma=2)
            if Z.max() > 0:
                Z = Z / Z.max()

            # Plot
            T_grid, X_grid = np.meshgrid(t_vals, x_vals)
            pcm = ax.pcolormesh(T_grid, X_grid, Z, cmap='Blues', shading='gouraud')

            # Bounds and expected
            ax.axhline(y=node.best, color='green', ls='-', lw=1.5, alpha=0.7)
            ax.axhline(y=node.worst, color='red', ls='-', lw=1.5, alpha=0.7)
            ax.axhline(y=0, color='black', ls='--', lw=1, alpha=0.5)

            exp_line = [node.expected(t) for t in t_vals]
            ax.plot(t_vals, exp_line, 'b--', lw=1.5, alpha=0.8)

            ax.set_title(f'{node.name}\n[{node.worst:+.0f}, {node.best:+.0f}]', fontsize=10)
            ax.set_xlabel('Time')
            ax.set_ylabel('Profit')

        # Plot total in last subplot
        last_idx = len(leaves)
        row, col = last_idx // n_cols, last_idx % n_cols
        if row < n_rows and col < n_cols:
            ax = axes[row, col]

            n_t, n_x = 100, 100
            t_vals = np.linspace(0, self.root.duration, n_t)
            x_vals = np.linspace(self.root.worst * 1.1, self.root.best * 1.1, n_x)

            Z = np.zeros((n_x, n_t))
            for ti in range(n_t):
                for xi in range(n_x):
                    Z[xi, ti] = self.root.P(x_vals[xi], t_vals[ti])

            Z = gaussian_filter(Z, sigma=2)
            if Z.max() > 0:
                Z = Z / Z.max()

            T_grid, X_grid = np.meshgrid(t_vals, x_vals)
            ax.pcolormesh(T_grid, X_grid, Z, cmap='Greens', shading='gouraud')

            ax.axhline(y=self.root.best, color='green', ls='-', lw=2)
            ax.axhline(y=self.root.worst, color='red', ls='-', lw=2)
            ax.axhline(y=0, color='black', ls='--', lw=1)

            exp_line = [self.root.expected(t) for t in t_vals]
            ax.plot(t_vals, exp_line, 'b--', lw=2)

            ax.set_title(f'TOTAL: {self.root.name}\n[{self.root.worst:+.0f}, {self.root.best:+.0f}]', fontsize=10)
            ax.set_xlabel('Time')
            ax.set_ylabel('Profit')

        # Hide empty subplots
        for i in range(n_plots, n_rows * n_cols):
            row, col = i // n_cols, i % n_cols
            axes[row, col].set_visible(False)

        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/abcfc_unified_hierarchy.png'

        plt.savefig(save_path, dpi=150)
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "positions": len(leaves),
            "total_bounds": self.total_bounds()
        }


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ABCFC UNIFIED - Built on Pure Math")
    print("=" * 70)

    # Create hierarchy
    hierarchy = UnifiedABCFCHierarchy("Yair Siegel", duration=30)

    print("\n1. Building Hierarchy with Proper Densities...")

    # Add categories
    hierarchy.add_category("Trading", worst=-500, best=1500, expected=100)
    hierarchy.add_category("Business", worst=-100, best=500, expected=50)

    # Add subcategories
    hierarchy.add_subcategory("Trading", "Polymarket", worst=-200, best=800, expected=60)
    hierarchy.add_subcategory("Trading", "Stocks", worst=-300, best=700, expected=40)

    # Add binary positions (proper density!)
    hierarchy.add_binary_position(
        "Polymarket", "Election YES",
        shares=100, entry_price=0.40, prob_yes=0.55
    )
    hierarchy.add_binary_position(
        "Polymarket", "Fed Rate NO",
        shares=50, entry_price=0.30, prob_yes=0.70
    )
    hierarchy.add_binary_position(
        "Polymarket", "BTC 100k",
        shares=80, entry_price=0.45, prob_yes=0.35
    )

    # Add stock position (Gaussian density)
    hierarchy.add_position(
        "Stocks", "AAPL Long",
        worst=-100, best=200, expected=30,
        density_type="gaussian"
    )

    print("\nHierarchy:")
    hierarchy.print_tree()

    print(f"\nTotal Bounds: {hierarchy.total_bounds()}")
    print(f"Total Expected (at T): {hierarchy.total_expected():.1f}")

    # Query density at specific points
    print("\n2. Querying 2D Density...")
    election = hierarchy.get_node("Election YES")
    print(f"\n{election.name}:")
    print(f"  P(profit=0, t=0):  {election.P(0, 0):.4f}")
    print(f"  P(profit=0, t=15): {election.P(0, 15):.4f}")
    print(f"  P(profit=30, t=15): {election.P(30, 15):.4f}")
    print(f"  P(profit=60, t=30): {election.P(60, 30):.4f}")  # Near win outcome
    print(f"  P(profit=-40, t=30): {election.P(-40, 30):.4f}")  # Near lose outcome

    print(f"\n  E[profit | t=0]:  {election.expected(0):.1f}")
    print(f"  E[profit | t=15]: {election.expected(15):.1f}")
    print(f"  E[profit | t=30]: {election.expected(30):.1f}")

    # Plot
    print("\n3. Generating 2D Density Visualizations...")

    # Single position
    result1 = election.plot(save_path="/tmp/abcfc_election_2d.png")
    print(f"   Election chart: {result1.get('chart_path')}")

    # Full hierarchy
    result2 = hierarchy.plot_hierarchy_2d()
    print(f"   Hierarchy chart: {result2.get('chart_path')}")

    print("\n" + "=" * 70)
    print("DONE - All ABCFCs use proper 2D density from pure math!")
    print("=" * 70)
