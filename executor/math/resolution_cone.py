#!/usr/bin/env python3
"""
ABSOLUTE BOUNDS CONTINUOUS FAN CHART (ABCFC)
Also known as: Resolution Cone

A novel chart type for binary prediction markets that shows:
- Absolute best case outcome (upper bound)
- Absolute worst case outcome (lower bound)
- Expected value trajectory
- Continuous probability gradient between bounds

Created by: Yair Siegel
Inspired by: Bank of England Fan Charts (1996)

NOMENCLATURE:
- "Absolute Bounds" = Uses actual min/max outcomes, not percentiles
- "Continuous" = Smooth probability gradient, not discrete bands
- "Fan Chart" = Uncertainty expands over time (cone shape)

WHAT MAKES IT UNIQUE:
1. Absolute bounds - Uses actual min/max outcomes, not percentiles
2. Continuous gradient - Smooth probability shading, not discrete bands
3. Binary outcome space - Designed for YES/NO markets that resolve to 0 or 1
4. Time-expanding cone - Uncertainty fans out toward resolution date

USAGE:
    from executor.math.resolution_cone import ResolutionCone, plot_resolution_cone

    # Quick plot
    result = plot_resolution_cone(
        entry_price=0.10,      # Bought YES at 10 cents
        position_size=100,     # $100 position
        prob_yes=0.10,         # 10% implied probability
        days_to_resolution=30
    )

    # Or use the class for more control
    cone = ResolutionCone(
        entry_price=0.10,
        position_size=100,
        prob_yes=0.10,
        days=30
    )

    # Get projections
    print(cone.best_case)    # +$900
    print(cone.worst_case)   # -$100
    print(cone.expected)     # $0

    # Generate chart
    cone.plot(save_path="/tmp/cone.png")
"""

import math
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List


@dataclass
class ConeProjection:
    """Holds the core projection values for a resolution cone."""
    entry_price: float
    position_size: float
    prob_yes: float
    days: int

    # Computed outcomes
    best_case: float      # If YES wins
    worst_case: float     # If NO wins
    expected: float       # Probability-weighted EV

    # Derived metrics
    risk_reward_ratio: float
    breakeven_prob: float
    edge: float           # Your prob estimate - market prob


class ResolutionCone:
    """
    Resolution Cone analysis for binary prediction markets.

    The "cone" represents the expanding range of possible outcomes
    as time progresses toward resolution, when uncertainty collapses
    to one of two states: YES (price = 1) or NO (price = 0).
    """

    def __init__(
        self,
        entry_price: float,
        position_size: float,
        prob_yes: float = None,
        days: int = 30,
        side: str = "YES"
    ):
        """
        Initialize resolution cone.

        Args:
            entry_price: Price paid for position (0.01 to 0.99)
            position_size: Total USDC invested
            prob_yes: Probability of YES (default: use entry_price as implied prob)
            days: Days until resolution
            side: "YES" or "NO" - which token was purchased
        """
        self.entry_price = entry_price
        self.position_size = position_size
        self.prob_yes = prob_yes if prob_yes is not None else entry_price
        self.days = days
        self.side = side.upper()

        # Calculate outcomes
        self._calculate()

    def _calculate(self):
        """Calculate all cone projections."""
        if self.side == "YES":
            # Bought YES tokens
            # Number of shares = position_size / entry_price
            shares = self.position_size / self.entry_price

            # Best case: YES wins, each share worth $1
            self.best_case = shares * 1.0 - self.position_size  # Profit

            # Worst case: NO wins, shares worth $0
            self.worst_case = -self.position_size  # Total loss

        else:  # NO
            # Bought NO tokens
            shares = self.position_size / (1 - self.entry_price)

            # Best case: NO wins, each share worth $1
            self.best_case = shares * 1.0 - self.position_size

            # Worst case: YES wins, NO shares worth $0
            self.worst_case = -self.position_size

        # Expected value (probability-weighted)
        if self.side == "YES":
            self.expected = (self.prob_yes * self.best_case) + \
                           ((1 - self.prob_yes) * self.worst_case)
        else:
            self.expected = ((1 - self.prob_yes) * self.best_case) + \
                           (self.prob_yes * self.worst_case)

        # Risk/reward ratio
        potential_gain = abs(self.best_case)
        potential_loss = abs(self.worst_case)
        self.risk_reward_ratio = potential_gain / potential_loss if potential_loss > 0 else float('inf')

        # Breakeven probability
        # At what probability would EV = 0?
        # For YES: p * best + (1-p) * worst = 0
        # p = -worst / (best - worst)
        total_range = self.best_case - self.worst_case
        if total_range != 0:
            self.breakeven_prob = -self.worst_case / total_range
        else:
            self.breakeven_prob = 0.5

        # Edge: how much better than market do you think you are?
        if self.side == "YES":
            self.edge = self.prob_yes - self.entry_price
        else:
            self.edge = (1 - self.prob_yes) - (1 - self.entry_price)

    def get_projection(self) -> ConeProjection:
        """Get projection data as structured object."""
        return ConeProjection(
            entry_price=self.entry_price,
            position_size=self.position_size,
            prob_yes=self.prob_yes,
            days=self.days,
            best_case=round(self.best_case, 2),
            worst_case=round(self.worst_case, 2),
            expected=round(self.expected, 2),
            risk_reward_ratio=round(self.risk_reward_ratio, 2),
            breakeven_prob=round(self.breakeven_prob, 4),
            edge=round(self.edge, 4)
        )

    def get_daily_bounds(self, day: int) -> Tuple[float, float, float]:
        """
        Get the outcome bounds for a specific day.

        Returns (worst, expected, best) for that day,
        linearly interpolated from 0 to final values.
        """
        if day <= 0:
            return (0.0, 0.0, 0.0)

        progress = min(day / self.days, 1.0)

        return (
            self.worst_case * progress,
            self.expected * progress,
            self.best_case * progress
        )

    def probability_at_outcome(self, outcome: float, day: int) -> float:
        """
        Calculate probability density at a specific outcome value.

        Uses Gaussian-like distribution centered on expected value.
        """
        worst, expected, best = self.get_daily_bounds(day)

        if outcome < worst or outcome > best:
            return 0.0

        if best == worst:
            return 1.0 if outcome == expected else 0.0

        # Normalize position
        t = (outcome - worst) / (best - worst)
        exp_t = (expected - worst) / (best - worst)

        # Gaussian density
        sigma = 0.35
        dist = abs(t - exp_t)
        return math.exp(-(dist ** 2) / (2 * sigma ** 2))

    def to_dict(self) -> Dict:
        """Export cone analysis as dictionary."""
        return {
            "type": "resolution_cone",
            "side": self.side,
            "entry_price": self.entry_price,
            "position_size": self.position_size,
            "prob_yes": self.prob_yes,
            "days": self.days,
            "outcomes": {
                "best_case": round(self.best_case, 2),
                "expected": round(self.expected, 2),
                "worst_case": round(self.worst_case, 2)
            },
            "metrics": {
                "risk_reward_ratio": round(self.risk_reward_ratio, 2),
                "breakeven_prob": round(self.breakeven_prob, 4),
                "edge": round(self.edge, 4)
            }
        }

    def plot(
        self,
        save_path: str = None,
        title: str = None,
        figsize: Tuple[int, int] = (12, 7),
        density_mode: str = "2d"
    ) -> Dict:
        """
        Generate ABCFC visualization with proper 2D probability density.

        The 2D density models:
        - Price follows stochastic process (random walk with drift toward resolution)
        - Early: tight distribution around entry
        - Middle: wider distribution (price fluctuates)
        - Resolution: bimodal split toward binary outcomes

        Args:
            save_path: Where to save the chart
            title: Custom title
            figsize: Figure dimensions
            density_mode: "2d" (full), "1d" (vertical only), "binary" (endpoints only)

        Returns:
            Dict with chart path and projection data
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy.ndimage import gaussian_filter
        except ImportError as e:
            return {"success": False, "error": f"Missing dependency: {e}"}

        fig, ax = plt.subplots(figsize=figsize)

        # Grid for density
        n_x = 300  # time resolution
        n_y = 400  # P&L resolution

        y_min = self.worst_case * 1.1
        y_max = self.best_case * 1.1

        x = np.linspace(0, self.days, n_x)
        y = np.linspace(y_min, y_max, n_y)
        X, Y = np.meshgrid(x, y)

        density = np.zeros_like(X)

        # Convert P&L bounds to price bounds
        # shares = position_size / entry_price
        shares = self.position_size / self.entry_price

        for i in range(n_x):
            t = x[i]
            if t == 0:
                # At entry: all probability mass at P&L = 0
                zero_idx = np.argmin(np.abs(y - 0))
                density[zero_idx, i] = 1.0
                continue

            # Time progress: 0 at entry, 1 at resolution
            progress = t / self.days

            # === 2D PROBABILITY MODEL ===
            # Price follows bounded random walk converging to binary outcome
            #
            # Early (progress~0): Gaussian centered on entry price, small variance
            # Middle (progress~0.5): Wider Gaussian, price can fluctuate
            # Late (progress~1): Bimodal - splitting toward 0 and 1

            # Variance grows then shrinks (peaks mid-way, collapses at resolution)
            # This models: early uncertainty grows, then resolves to binary
            variance_time = 4 * progress * (1 - progress)  # peaks at 0.5

            # Base variance in price space
            base_price_variance = 0.15  # How much price can move

            # Current price distribution parameters
            # Mean drifts toward resolution based on prob_yes
            if self.side == "YES":
                # Price drifts toward prob_yes over time
                mean_price = self.entry_price + progress * (self.prob_yes - self.entry_price)
            else:
                mean_price = (1 - self.entry_price) + progress * ((1 - self.prob_yes) - (1 - self.entry_price))

            # Variance: grows early, then splits into bimodal at resolution
            if progress < 0.8:
                # Single mode with growing variance
                price_std = base_price_variance * np.sqrt(variance_time + 0.01)

                for j in range(n_y):
                    pnl = y[j]
                    # Convert P&L back to implied price
                    # pnl = shares * (price - entry_price) for YES
                    if self.side == "YES":
                        implied_price = self.entry_price + pnl / shares
                    else:
                        implied_price = (1 - self.entry_price) + pnl / shares

                    # Clamp to valid price range
                    if 0 <= implied_price <= 1:
                        # Gaussian probability at this price
                        z = (implied_price - mean_price) / (price_std + 0.001)
                        density[j, i] = np.exp(-0.5 * z * z)

            else:
                # Bimodal: splitting toward binary outcomes
                # Weight toward best/worst based on prob_yes
                split_progress = (progress - 0.8) / 0.2  # 0 at 0.8, 1 at 1.0

                # Two modes: one at best, one at worst
                best_weight = self.prob_yes
                worst_weight = 1 - self.prob_yes

                # Shrinking variance as we approach resolution
                remaining_var = base_price_variance * (1 - split_progress) * 0.3

                for j in range(n_y):
                    pnl = y[j]

                    # Distance to best outcome
                    best_pnl = self.best_case * progress
                    worst_pnl = self.worst_case * progress

                    # Bimodal Gaussian mixture
                    z_best = (pnl - best_pnl) / (remaining_var * abs(self.best_case) + 1)
                    z_worst = (pnl - worst_pnl) / (remaining_var * abs(self.worst_case) + 1)

                    prob_best = best_weight * np.exp(-0.5 * z_best * z_best)
                    prob_worst = worst_weight * np.exp(-0.5 * z_worst * z_worst)

                    density[j, i] = prob_best + prob_worst

        # Smooth for visual continuity
        density = gaussian_filter(density, sigma=2)

        # Normalize each column (time slice) to show relative probability
        for i in range(n_x):
            col_max = density[:, i].max()
            if col_max > 0:
                density[:, i] /= col_max

        # Global normalization for color mapping
        if density.max() > 0:
            density = density / density.max()

        # Plot density
        pcm = ax.pcolormesh(X, Y, density, cmap='Blues', shading='gouraud', alpha=0.9)

        # Plot outcome lines (for reference, not as "predictions")
        days_range = np.linspace(0, self.days, self.days + 1)
        best_line = (days_range / self.days) * self.best_case
        worst_line = (days_range / self.days) * self.worst_case
        expected_line = (days_range / self.days) * self.expected

        ax.plot(days_range, best_line, 'g-', linewidth=2, alpha=0.7,
                label=f'Best: +${self.best_case:.0f} ({self.prob_yes:.0%})')
        ax.plot(days_range, expected_line, 'b--', linewidth=1.5, alpha=0.7,
                label=f'Expected: ${self.expected:+.0f}')
        ax.plot(days_range, worst_line, 'r-', linewidth=2, alpha=0.7,
                label=f'Worst: ${self.worst_case:.0f} ({1-self.prob_yes:.0%})')

        # Mark entry and resolution points
        ax.scatter([0], [0], s=100, c='black', marker='o', zorder=5, label='Entry')
        ax.scatter([self.days], [self.best_case], s=80, c='green', marker='^', zorder=5)
        ax.scatter([self.days], [self.worst_case], s=80, c='red', marker='v', zorder=5)

        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

        ax.set_xlabel('Days to Resolution', fontsize=12)
        ax.set_ylabel('Profit/Loss ($)', fontsize=12)

        if title is None:
            title = f'ABCFC: ${self.position_size:.0f} {self.side} @ ${self.entry_price:.2f}\n' \
                   f'P({self.side})={self.prob_yes:.1%} | 2D Probability Density'

        ax.set_title(title, fontsize=14)
        ax.legend(loc='upper left' if self.expected > 0 else 'lower left', fontsize=9)
        ax.grid(True, alpha=0.3)

        # Add colorbar
        cbar = plt.colorbar(pcm, ax=ax, label='Probability Density', shrink=0.8)

        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/resolution_cone.png'

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "density_mode": density_mode,
            **self.to_dict()
        }


def plot_resolution_cone(
    entry_price: float,
    position_size: float,
    prob_yes: float = None,
    days_to_resolution: int = 30,
    side: str = "YES",
    save_path: str = None,
    title: str = None
) -> Dict:
    """
    Quick function to generate a resolution cone chart.

    Args:
        entry_price: Price paid (0.01-0.99)
        position_size: USDC invested
        prob_yes: Your probability estimate (default: market price)
        days_to_resolution: Days until market resolves
        side: "YES" or "NO"
        save_path: Where to save chart
        title: Custom title

    Returns:
        Dict with chart path and analysis

    Example:
        >>> result = plot_resolution_cone(0.10, 100, prob_yes=0.15, days_to_resolution=30)
        >>> print(f"Best: ${result['outcomes']['best_case']}")
        >>> print(f"Chart: {result['chart_path']}")
    """
    cone = ResolutionCone(
        entry_price=entry_price,
        position_size=position_size,
        prob_yes=prob_yes,
        days=days_to_resolution,
        side=side
    )

    return cone.plot(save_path=save_path, title=title)


def analyze_position(
    entry_price: float,
    position_size: float,
    prob_yes: float = None,
    side: str = "YES"
) -> Dict:
    """
    Analyze a binary market position without generating a chart.

    Returns complete analysis including:
    - Best/worst/expected outcomes
    - Risk/reward ratio
    - Breakeven probability
    - Edge calculation

    Example:
        >>> analysis = analyze_position(0.10, 100, prob_yes=0.15)
        >>> print(f"Expected: ${analysis['outcomes']['expected']}")
        >>> print(f"R:R = {analysis['metrics']['risk_reward_ratio']}")
    """
    cone = ResolutionCone(
        entry_price=entry_price,
        position_size=position_size,
        prob_yes=prob_yes,
        days=30,
        side=side
    )

    return cone.to_dict()


# Module-level quick access
def cone(entry: float, size: float, prob: float = None, days: int = 30, side: str = "YES"):
    """Quick constructor for resolution cone."""
    return ResolutionCone(entry, size, prob, days, side)


if __name__ == "__main__":
    # Demo
    print("=" * 60)
    print("RESOLUTION CONE - Binary Outcome Probability Chart")
    print("=" * 60)

    # Create example cone
    c = ResolutionCone(
        entry_price=0.10,
        position_size=100,
        prob_yes=0.10,
        days=30,
        side="YES"
    )

    print(f"\nPosition: $100 YES @ $0.10")
    print(f"  Best case:  +${c.best_case:.2f}")
    print(f"  Expected:   ${c.expected:+.2f}")
    print(f"  Worst case: ${c.worst_case:.2f}")
    print(f"\nMetrics:")
    print(f"  Risk/Reward: {c.risk_reward_ratio:.1f}:1")
    print(f"  Breakeven:   {c.breakeven_prob:.1%}")
    print(f"  Edge:        {c.edge:+.1%}")

    # Generate chart
    result = c.plot(save_path="/tmp/resolution_cone_demo.png")
    print(f"\nChart saved: {result.get('chart_path')}")
