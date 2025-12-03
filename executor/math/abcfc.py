#!/usr/bin/env python3
"""
ABCFC - Absolute Bounds Continuous Fan Chart (Pure Implementation)

The fundamental mathematical structure for visualizing outcome distributions
with absolute bounds and 2D probability density.

CORE CONCEPT:
    Given any process with:
    - A best possible outcome (upper bound)
    - A worst possible outcome (lower bound)
    - An expected value
    - A time horizon

    The ABCFC visualizes the 2D probability density P(value, time) showing
    how probability mass evolves from a starting point toward final outcomes.

MATHEMATICAL FOUNDATION:
    - Bounds: [worst, best] define the absolute outcome space
    - Expected: E[X] = probability-weighted mean
    - Density: P(x,t) = probability of being at value x at time t
    - The density integrates to 1 at each time slice

USAGE:
    from executor.math.abcfc import ABCFC

    # Create pure ABCFC
    chart = ABCFC(
        best=1000,
        worst=-100,
        expected=50,
        duration=30
    )

    # Set probability model
    chart.set_density_model("gaussian")  # or "bimodal", "uniform", "custom"

    # Plot
    chart.plot()

    # Get probability at any point
    p = chart.density(value=100, time=15)

Created by: Yair Siegel
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime, timezone


@dataclass
class DensityModel:
    """
    Defines how probability density evolves over time.

    The model specifies P(value | time) for all (value, time) pairs.
    """
    name: str

    # Function: (value, time, params) -> probability density
    density_func: Callable[[float, float, Dict], float] = None

    # Parameters for the model
    params: Dict = field(default_factory=dict)


class ABCFC:
    """
    Absolute Bounds Continuous Fan Chart - Pure Mathematical Implementation

    A 2D probability density visualization bounded by absolute outcomes.

    Attributes:
        best: Upper bound (maximum possible outcome)
        worst: Lower bound (minimum possible outcome)
        expected: Expected value (probability-weighted mean)
        duration: Time horizon (arbitrary units)
        start: Starting value (default: 0)
    """

    def __init__(
        self,
        best: float,
        worst: float,
        expected: float = None,
        duration: float = 1.0,
        start: float = 0.0,
        prob_best: float = None
    ):
        """
        Initialize pure ABCFC.

        Args:
            best: Maximum possible outcome
            worst: Minimum possible outcome
            expected: Expected value (computed from prob_best if not given)
            duration: Time horizon
            start: Starting value
            prob_best: Probability of best outcome (for binary)
        """
        self.best = best
        self.worst = worst
        self.duration = duration
        self.start = start

        # Compute expected if not provided
        if expected is not None:
            self.expected = expected
            # Back-calculate prob_best
            if best != worst:
                self.prob_best = (expected - worst) / (best - worst)
            else:
                self.prob_best = 0.5
        elif prob_best is not None:
            self.prob_best = prob_best
            self.expected = prob_best * best + (1 - prob_best) * worst
        else:
            # Default: expected at midpoint
            self.expected = (best + worst) / 2
            self.prob_best = 0.5

        # Default density model
        self._density_model = self._default_density_model()

    # ==================== DENSITY MODELS ====================

    def _default_density_model(self) -> DensityModel:
        """Default: Gaussian that spreads then optionally splits."""
        return DensityModel(
            name="gaussian_evolving",
            params={
                "base_variance": 0.15,
                "split_at": 0.8,  # When to start bimodal split (0-1)
                "bimodal": True   # Whether to split at end
            }
        )

    def set_density_model(
        self,
        model: str = "gaussian",
        **params
    ):
        """
        Set the probability density model.

        Models:
            "gaussian": Single Gaussian, variance grows then shrinks
            "bimodal": Gaussian that splits into two modes at resolution
            "uniform": Uniform distribution within bounds
            "custom": Provide your own density function

        Args:
            model: Model name
            **params: Model-specific parameters
        """
        if model == "gaussian":
            self._density_model = DensityModel(
                name="gaussian",
                params={"base_variance": params.get("variance", 0.2), "bimodal": False}
            )
        elif model == "bimodal":
            self._density_model = DensityModel(
                name="bimodal",
                params={
                    "base_variance": params.get("variance", 0.15),
                    "split_at": params.get("split_at", 0.8),
                    "bimodal": True
                }
            )
        elif model == "uniform":
            self._density_model = DensityModel(name="uniform", params={})
        elif model == "custom":
            self._density_model = DensityModel(
                name="custom",
                density_func=params.get("func"),
                params=params
            )

    # ==================== CORE MATH ====================

    def density(self, value: float, time: float) -> float:
        """
        Calculate probability density at (value, time).

        Args:
            value: The outcome value
            time: Time point (0 to duration)

        Returns:
            Probability density (not probability - integrate for that)
        """
        if time <= 0:
            # At start: delta function at start value
            return 1.0 if abs(value - self.start) < 0.01 * (self.best - self.worst) else 0.0

        # Normalize time to [0, 1]
        t = min(time / self.duration, 1.0)

        # Normalize value to [0, 1] within bounds
        if self.best == self.worst:
            return 1.0 if value == self.best else 0.0

        # Value outside bounds
        if value < self.worst or value > self.best:
            return 0.0

        v = (value - self.worst) / (self.best - self.worst)  # 0 = worst, 1 = best

        model = self._density_model

        if model.name == "uniform":
            return 1.0 / (self.best - self.worst)

        elif model.name in ["gaussian", "gaussian_evolving", "bimodal"]:
            base_var = model.params.get("base_variance", 0.15)
            bimodal = model.params.get("bimodal", False)
            split_at = model.params.get("split_at", 0.8)

            # Variance peaks at t=0.5, zero at endpoints
            variance_time = 4 * t * (1 - t)

            # Expected position (normalized)
            exp_v = (self.expected - self.worst) / (self.best - self.worst)

            if not bimodal or t < split_at:
                # Single Gaussian mode
                std = base_var * math.sqrt(variance_time + 0.01)
                z = (v - exp_v) / (std + 0.001)
                return math.exp(-0.5 * z * z)

            else:
                # Bimodal: splitting toward best and worst
                split_progress = (t - split_at) / (1 - split_at)
                remaining_var = base_var * (1 - split_progress) * 0.3

                # Two modes at best (v=1) and worst (v=0)
                # Weighted by probabilities
                z_best = (v - 1.0) / (remaining_var + 0.01)
                z_worst = (v - 0.0) / (remaining_var + 0.01)

                p_best = self.prob_best * math.exp(-0.5 * z_best * z_best)
                p_worst = (1 - self.prob_best) * math.exp(-0.5 * z_worst * z_worst)

                return p_best + p_worst

        elif model.name == "custom" and model.density_func:
            return model.density_func(value, time, model.params)

        return 0.0

    def value_at_time(self, time: float, quantile: float = 0.5) -> float:
        """
        Get the value at a given quantile for a time point.

        Args:
            time: Time point
            quantile: 0.5 = median, 0.95 = 95th percentile, etc.

        Returns:
            Value at that quantile
        """
        # Simple linear interpolation for now
        # More accurate would integrate the density
        t = time / self.duration

        if quantile == 0.5:
            return self.start + t * (self.expected - self.start)
        elif quantile >= 0.99:
            return self.start + t * (self.best - self.start)
        elif quantile <= 0.01:
            return self.start + t * (self.worst - self.start)
        else:
            # Linear interpolation between bounds
            range_val = self.best - self.worst
            return self.worst + quantile * range_val * t

    def bounds_at_time(self, time: float) -> Tuple[float, float]:
        """Get (worst, best) bounds at a time point."""
        t = time / self.duration
        worst_t = self.start + t * (self.worst - self.start)
        best_t = self.start + t * (self.best - self.start)
        return (worst_t, best_t)

    def expected_at_time(self, time: float) -> float:
        """Get expected value at a time point."""
        t = time / self.duration
        return self.start + t * (self.expected - self.start)

    # ==================== VISUALIZATION ====================

    def plot(
        self,
        save_path: str = None,
        title: str = None,
        figsize: Tuple[int, int] = (12, 7),
        resolution: Tuple[int, int] = (300, 400),
        cmap: str = "Blues"
    ) -> Dict:
        """
        Generate ABCFC visualization with 2D probability density.

        Args:
            save_path: Where to save
            title: Chart title
            figsize: Figure size
            resolution: (time_points, value_points)
            cmap: Colormap name

        Returns:
            Dict with chart path and metadata
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy.ndimage import gaussian_filter
        except ImportError as e:
            return {"success": False, "error": f"Missing: {e}"}

        n_x, n_y = resolution

        # Build grid
        x = np.linspace(0, self.duration, n_x)

        # Y range with padding
        padding = 0.1 * (self.best - self.worst)
        y_min = self.worst - padding
        y_max = self.best + padding
        y = np.linspace(y_min, y_max, n_y)

        X, Y = np.meshgrid(x, y)
        density = np.zeros_like(X)

        # Calculate density at each point
        for i in range(n_x):
            for j in range(n_y):
                density[j, i] = self.density(y[j], x[i])

        # Smooth
        density = gaussian_filter(density, sigma=2)

        # Normalize columns
        for i in range(n_x):
            col_max = density[:, i].max()
            if col_max > 0:
                density[:, i] /= col_max

        # Global normalize
        if density.max() > 0:
            density = density / density.max()

        # Plot
        fig, ax = plt.subplots(figsize=figsize)

        pcm = ax.pcolormesh(X, Y, density, cmap=cmap, shading='gouraud', alpha=0.9)

        # Bound lines
        t_range = np.linspace(0, self.duration, 100)
        best_line = [self.start + (t/self.duration) * (self.best - self.start) for t in t_range]
        worst_line = [self.start + (t/self.duration) * (self.worst - self.start) for t in t_range]
        exp_line = [self.start + (t/self.duration) * (self.expected - self.start) for t in t_range]

        ax.plot(t_range, best_line, 'g-', lw=2, alpha=0.8, label=f'Best: {self.best:+.0f}')
        ax.plot(t_range, exp_line, 'b--', lw=1.5, alpha=0.8, label=f'Expected: {self.expected:+.0f}')
        ax.plot(t_range, worst_line, 'r-', lw=2, alpha=0.8, label=f'Worst: {self.worst:+.0f}')

        # Markers
        ax.scatter([0], [self.start], s=100, c='black', marker='o', zorder=5, label='Start')
        ax.scatter([self.duration], [self.best], s=80, c='green', marker='^', zorder=5)
        ax.scatter([self.duration], [self.worst], s=80, c='red', marker='v', zorder=5)

        ax.axhline(y=0, color='gray', ls='--', lw=1, alpha=0.5)

        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)

        if title is None:
            title = f'ABCFC: [{self.worst:+.0f}, {self.best:+.0f}] | E={self.expected:+.0f}'
        ax.set_title(title, fontsize=14)

        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.colorbar(pcm, ax=ax, label='Probability Density', shrink=0.8)
        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/abcfc_pure.png'

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "best": self.best,
            "worst": self.worst,
            "expected": self.expected,
            "duration": self.duration,
            "prob_best": self.prob_best,
            "model": self._density_model.name
        }

    # ==================== EXPORT ====================

    def to_dict(self) -> Dict:
        """Export ABCFC parameters."""
        return {
            "type": "abcfc",
            "best": self.best,
            "worst": self.worst,
            "expected": self.expected,
            "start": self.start,
            "duration": self.duration,
            "prob_best": round(self.prob_best, 4),
            "model": self._density_model.name
        }

    def __repr__(self) -> str:
        return f"ABCFC(best={self.best}, worst={self.worst}, exp={self.expected}, p={self.prob_best:.1%})"


# ==================== CONVENIENCE FUNCTIONS ====================

def abcfc(best: float, worst: float, expected: float = None, duration: float = 1.0) -> ABCFC:
    """Quick constructor."""
    return ABCFC(best=best, worst=worst, expected=expected, duration=duration)


def plot_abcfc(
    best: float,
    worst: float,
    expected: float = None,
    duration: float = 30,
    model: str = "bimodal",
    save_path: str = None
) -> Dict:
    """Quick plot function."""
    chart = ABCFC(best=best, worst=worst, expected=expected, duration=duration)
    chart.set_density_model(model)
    return chart.plot(save_path=save_path)


if __name__ == "__main__":
    print("=" * 60)
    print("ABCFC - Pure Implementation")
    print("=" * 60)

    # Example: Generic outcome space
    chart = ABCFC(
        best=1000,
        worst=-100,
        expected=50,
        duration=30
    )

    print(f"\n{chart}")
    print(f"  P(best): {chart.prob_best:.1%}")

    # Test density at various points
    print("\nDensity samples:")
    print(f"  (0, t=0):   {chart.density(0, 0):.4f}")
    print(f"  (50, t=15): {chart.density(50, 15):.4f}")
    print(f"  (500, t=15): {chart.density(500, 15):.4f}")
    print(f"  (1000, t=30): {chart.density(1000, 30):.4f}")

    # Plot with different models
    chart.set_density_model("bimodal")
    result = chart.plot(save_path="/tmp/abcfc_pure.png", title="Pure ABCFC (Bimodal)")
    print(f"\nChart: {result.get('chart_path')}")
