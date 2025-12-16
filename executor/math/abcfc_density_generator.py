#!/usr/bin/env python3
"""
ABCFC 2D Density Generator
===========================

Generates full P(x,t) probability density functions for ABCFC positions
using Monte Carlo simulation.

Instead of just W/E/B point estimates, this creates continuous probability
distributions showing likelihood of each outcome at each time point.

Author: Claude + Yair
Created: 2025-12-16
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PositionDensity:
    """2D probability density for a single position."""
    name: str
    worst: float
    expected: float
    best: float

    # Density grid
    x_grid: np.ndarray  # Outcome values
    t_grid: np.ndarray  # Time points
    density: np.ndarray  # P(x, t) - shape (len(t_grid), len(x_grid))


class ABCFCDensityGenerator:
    """
    Generate 2D probability densities from W/E/B bounds.

    Uses Monte Carlo sampling with assumed distribution shape.
    """

    def __init__(self, n_samples: int = 10000, n_time_points: int = 50):
        self.n_samples = n_samples
        self.n_time_points = n_time_points

    def generate_position_density(
        self,
        position: Dict,
        duration_days: int = 30
    ) -> PositionDensity:
        """
        Generate P(x,t) density for a single position.

        Assumes:
        - Distribution shape: Beta distribution (flexible, bounded)
        - Time evolution: Variance decreases as t → T (resolves to outcome)
        """
        w = position.get('worst', 0)
        e = position.get('expected', 0)
        b = position.get('best', 0)
        name = position.get('name', 'Unknown')

        # Create grids
        x_grid = np.linspace(w, b, 100)  # 100 outcome points
        t_grid = np.linspace(0, duration_days, self.n_time_points)

        # Generate density matrix
        density = np.zeros((self.n_time_points, len(x_grid)))

        for i, t in enumerate(t_grid):
            # Time factor: variance shrinks as resolution approaches
            time_factor = 1 - (t / duration_days)  # 1 at t=0, 0 at t=T

            # Generate samples for this time point
            samples = self._sample_outcome_at_time(w, e, b, time_factor)

            # Convert samples to density using histogram
            hist, _ = np.histogram(samples, bins=x_grid, density=True)

            # Pad to match x_grid length
            if len(hist) < len(x_grid):
                hist = np.pad(hist, (0, len(x_grid) - len(hist)))

            density[i, :len(hist)] = hist

        return PositionDensity(
            name=name,
            worst=w,
            expected=e,
            best=b,
            x_grid=x_grid,
            t_grid=t_grid,
            density=density
        )

    def _sample_outcome_at_time(
        self,
        worst: float,
        expected: float,
        best: float,
        time_factor: float
    ) -> np.ndarray:
        """
        Sample outcomes at a specific time point.

        time_factor = 1 → maximum uncertainty (wide distribution)
        time_factor = 0 → resolution (converges to actual outcome)
        """
        # Fit beta distribution to match expected value
        # Beta distribution is bounded [0, 1], we'll scale to [worst, best]

        # Convert expected to beta parameters
        # For simplicity, use symmetric beta centered on expected
        range_val = best - worst
        if range_val == 0:
            return np.full(self.n_samples, expected)

        # Normalized expected value [0, 1]
        p = (expected - worst) / range_val
        p = np.clip(p, 0.01, 0.99)  # Avoid edge cases

        # Beta parameters (higher alpha/beta = more concentrated)
        # Concentration increases as time_factor → 0
        concentration = 2 + (1 - time_factor) * 20  # 2 to 22

        alpha = concentration * p
        beta_param = concentration * (1 - p)

        # Sample from beta, scale to [worst, best]
        samples = np.random.beta(alpha, beta_param, self.n_samples)
        samples = worst + samples * range_val

        return samples

    def generate_portfolio_density(
        self,
        positions: List[Dict],
        duration_days: int = 30
    ) -> PositionDensity:
        """
        Generate combined P(x,t) density for entire portfolio.

        This is the sum of all position outcomes.
        """
        print(f"Generating portfolio density from {len(positions)} positions...")

        # Generate density for each position
        position_densities = []
        for i, pos in enumerate(positions):
            if i % 50 == 0:
                print(f"  Processing position {i+1}/{len(positions)}...")

            pd = self.generate_position_density(pos, duration_days)
            position_densities.append(pd)

        # Combine via Monte Carlo simulation
        print("Combining position densities...")

        # Time grid (use first position's grid)
        t_grid = position_densities[0].t_grid

        # Portfolio outcome range
        total_worst = sum(p.worst for p in position_densities)
        total_best = sum(p.best for p in position_densities)
        total_expected = sum(p.expected for p in position_densities)

        x_grid = np.linspace(total_worst, total_best, 200)  # More points for portfolio
        density = np.zeros((self.n_time_points, len(x_grid)))

        # For each time point, sum sampled outcomes from all positions
        for i, t in enumerate(t_grid):
            if i % 10 == 0:
                print(f"  Time point {i+1}/{self.n_time_points}...")

            time_factor = 1 - (t / duration_days)

            # Sample from each position and sum
            portfolio_samples = np.zeros(self.n_samples)
            for pd in position_densities:
                samples = self._sample_outcome_at_time(
                    pd.worst, pd.expected, pd.best, time_factor
                )
                portfolio_samples += samples

            # Convert to density
            hist, _ = np.histogram(portfolio_samples, bins=x_grid, density=True)

            if len(hist) < len(x_grid):
                hist = np.pad(hist, (0, len(x_grid) - len(hist)))

            density[i, :len(hist)] = hist

        print("✓ Portfolio density generated")

        return PositionDensity(
            name="Portfolio Total",
            worst=total_worst,
            expected=total_expected,
            best=total_best,
            x_grid=x_grid,
            t_grid=t_grid,
            density=density
        )

    def save_density(self, density: PositionDensity, output_path: Path):
        """Save density to file."""
        data = {
            "name": density.name,
            "bounds": {
                "worst": float(density.worst),
                "expected": float(density.expected),
                "best": float(density.best)
            },
            "x_grid": density.x_grid.tolist(),
            "t_grid": density.t_grid.tolist(),
            "density": density.density.tolist(),
            "metadata": {
                "n_time_points": len(density.t_grid),
                "n_outcome_points": len(density.x_grid),
                "generated_at": str(Path().resolve())
            }
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved density to {output_path}")


def generate_from_unified_state(
    state_path: Path = Path("state/abcfc_unified_state.json"),
    output_path: Path = Path("state/abcfc_2d_density.json"),
    n_samples: int = 10000
):
    """Generate 2D density from unified ABCFC state."""

    print("ABCFC 2D DENSITY GENERATION")
    print("=" * 70)
    print("")

    # Load positions
    with open(state_path) as f:
        state = json.load(f)

    positions = state.get("positions", [])
    print(f"Loaded {len(positions)} positions")
    print("")

    # Generate density
    generator = ABCFCDensityGenerator(n_samples=n_samples)
    portfolio_density = generator.generate_portfolio_density(positions)

    # Save
    generator.save_density(portfolio_density, output_path)

    print("")
    print("DENSITY SUMMARY:")
    print("-" * 70)
    print(f"Time points: {len(portfolio_density.t_grid)}")
    print(f"Outcome points: {len(portfolio_density.x_grid)}")
    print(f"Total density matrix: {portfolio_density.density.shape}")
    print(f"Bounds: [${portfolio_density.worst:,.2f}, ${portfolio_density.best:,.2f}]")
    print(f"Expected: ${portfolio_density.expected:,.2f}")

    return portfolio_density


if __name__ == "__main__":
    generate_from_unified_state()
