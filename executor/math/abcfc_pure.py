#!/usr/bin/env python3
"""
ABCFC PURE - Absolute Bounds Continuous Fan Chart (Pure Mathematical Definition)

THE THEOREM:

    An ABCFC is a 2-dimensional probability density function P(x, t) where:

    1. BOUNDS: x ∈ [a, b] for all t (absolute bounds)
    2. TIME: t ∈ [0, T] (duration)
    3. DENSITY: P(x, t) ≥ 0 for all (x, t)
    4. NORMALIZATION: ∫ P(x, t) dx = 1 for all t (integrates to 1 at each time slice)

    That's it. No assumptions about:
    - Shape of distribution (Gaussian, uniform, bimodal, etc.)
    - How it evolves over time
    - Starting or ending conditions
    - Expected value location

MATHEMATICAL PROPERTIES:

    Given an ABCFC with bounds [a, b] and duration T:

    1. Expected Value at time t:
       E[X|t] = ∫ x · P(x, t) dx

    2. Variance at time t:
       Var[X|t] = ∫ (x - E[X|t])² · P(x, t) dx

    3. Cumulative Probability:
       F(x, t) = ∫_{a}^{x} P(u, t) du

    4. Marginal over time:
       P(x) = (1/T) ∫ P(x, t) dt

USAGE:

    from executor.math.abcfc_pure import ABCFC2D

    # Define your density function
    def my_density(x, t, a, b, T):
        '''Your custom 2D probability density.'''
        # Must satisfy: integrates to 1 over [a,b] for any t
        return ...

    # Create ABCFC
    chart = ABCFC2D(
        bounds=(0, 100),
        duration=30,
        density=my_density
    )

    # Query
    p = chart.P(x=50, t=15)  # Density at point
    e = chart.E(t=15)         # Expected value at time
    v = chart.Var(t=15)       # Variance at time

    # Visualize
    chart.plot()

Created by: Yair Siegel
"""

import math
from typing import Callable, Tuple, Dict, Optional
from dataclasses import dataclass


# Type for density function: (x, t, a, b, T) -> probability density
DensityFunc = Callable[[float, float, float, float, float], float]


@dataclass
class ABCFC2D:
    """
    Pure 2D Absolute Bounds Continuous Fan Chart.

    The minimal mathematical structure:
    - Bounds [a, b]
    - Duration T
    - Density function P(x, t)
    """

    bounds: Tuple[float, float]  # (a, b) = (lower, upper)
    duration: float              # T
    density: DensityFunc         # P(x, t) -> density value

    @property
    def a(self) -> float:
        """Lower bound."""
        return self.bounds[0]

    @property
    def b(self) -> float:
        """Upper bound."""
        return self.bounds[1]

    @property
    def T(self) -> float:
        """Duration."""
        return self.duration

    def P(self, x: float, t: float) -> float:
        """
        Probability density at point (x, t).

        P(x, t) ≥ 0
        ∫ P(x, t) dx = 1 for all t
        """
        if x < self.a or x > self.b:
            return 0.0
        if t < 0 or t > self.T:
            return 0.0
        return self.density(x, t, self.a, self.b, self.T)

    def E(self, t: float, n: int = 1000) -> float:
        """
        Expected value at time t.

        E[X|t] = ∫ x · P(x, t) dx
        """
        dx = (self.b - self.a) / n
        total = 0.0
        norm = 0.0

        for i in range(n):
            x = self.a + (i + 0.5) * dx
            p = self.P(x, t)
            total += x * p * dx
            norm += p * dx

        return total / norm if norm > 0 else (self.a + self.b) / 2

    def Var(self, t: float, n: int = 1000) -> float:
        """
        Variance at time t.

        Var[X|t] = ∫ (x - E[X|t])² · P(x, t) dx
        """
        mean = self.E(t, n)
        dx = (self.b - self.a) / n
        total = 0.0
        norm = 0.0

        for i in range(n):
            x = self.a + (i + 0.5) * dx
            p = self.P(x, t)
            total += (x - mean) ** 2 * p * dx
            norm += p * dx

        return total / norm if norm > 0 else 0.0

    def std(self, t: float, n: int = 1000) -> float:
        """Standard deviation at time t."""
        return math.sqrt(self.Var(t, n))

    def CDF(self, x: float, t: float, n: int = 1000) -> float:
        """
        Cumulative distribution at (x, t).

        F(x, t) = ∫_{a}^{x} P(u, t) du / ∫_{a}^{b} P(u, t) du

        INTEGRAFIX: Must normalize since density may be unnormalized.
        """
        if x <= self.a:
            return 0.0
        if x >= self.b:
            return 1.0

        # First compute total integral for normalization (THE AREA)
        full_dx = (self.b - self.a) / n
        total_area = 0.0
        for i in range(n):
            u = self.a + (i + 0.5) * full_dx
            total_area += self.P(u, t) * full_dx

        if total_area <= 0:
            return 0.5  # Fallback

        # Now compute partial integral up to x
        partial_n = max(100, int(n * (x - self.a) / (self.b - self.a)))
        dx = (x - self.a) / partial_n
        partial_area = 0.0

        for i in range(partial_n):
            u = self.a + (i + 0.5) * dx
            partial_area += self.P(u, t) * dx

        # Normalized CDF = partial area / total area
        return min(1.0, max(0.0, partial_area / total_area))

    def quantile(self, p: float, t: float, n: int = 1000) -> float:
        """
        Inverse CDF: find x where CDF(x, t) = p.
        """
        # Binary search
        lo, hi = self.a, self.b

        for _ in range(50):  # 50 iterations = very precise
            mid = (lo + hi) / 2
            if self.CDF(mid, t, n) < p:
                lo = mid
            else:
                hi = mid

        return (lo + hi) / 2

    def median(self, t: float) -> float:
        """Median at time t."""
        return self.quantile(0.5, t)

    def plot(
        self,
        save_path: str = None,
        resolution: Tuple[int, int] = (200, 200),
        cmap: str = "Blues"
    ) -> Dict:
        """Visualize the 2D density."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError as e:
            return {"success": False, "error": str(e)}

        n_t, n_x = resolution

        t_vals = np.linspace(0, self.T, n_t)
        x_vals = np.linspace(self.a, self.b, n_x)

        T_grid, X_grid = np.meshgrid(t_vals, x_vals)
        Z = np.zeros_like(T_grid)

        for i in range(n_t):
            for j in range(n_x):
                Z[j, i] = self.P(x_vals[j], t_vals[i])

        # Normalize columns
        for i in range(n_t):
            col_max = Z[:, i].max()
            if col_max > 0:
                Z[:, i] /= col_max

        fig, ax = plt.subplots(figsize=(10, 6))

        pcm = ax.pcolormesh(T_grid, X_grid, Z, cmap=cmap, shading='gouraud')

        ax.axhline(y=self.a, color='red', ls='-', lw=2, alpha=0.7, label=f'Lower bound: {self.a}')
        ax.axhline(y=self.b, color='green', ls='-', lw=2, alpha=0.7, label=f'Upper bound: {self.b}')

        # Plot expected value line
        e_vals = [self.E(t, n=100) for t in t_vals[::10]]
        ax.plot(t_vals[::10], e_vals, 'b--', lw=2, alpha=0.8, label='E[X|t]')

        ax.set_xlabel('Time (t)', fontsize=12)
        ax.set_ylabel('Value (x)', fontsize=12)
        ax.set_title('ABCFC: P(x, t)', fontsize=14)
        ax.legend(loc='best')

        plt.colorbar(pcm, ax=ax, label='Density')
        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/abcfc_pure.png'

        plt.savefig(save_path, dpi=150)
        plt.close()

        return {"success": True, "chart_path": save_path}


# ==================== COMMON DENSITY FUNCTIONS ====================
# These are EXAMPLES, not requirements. User can define any density.

def uniform_density(x: float, t: float, a: float, b: float, T: float) -> float:
    """
    Uniform distribution - equal probability everywhere in bounds.

    P(x, t) = 1 / (b - a)  for all t
    """
    return 1.0 / (b - a) if a < b else 0.0


def gaussian_density(x: float, t: float, a: float, b: float, T: float,
                     mu: float = None, sigma: float = None) -> float:
    """
    Gaussian (normal) distribution centered at mu with std sigma.

    If mu not specified, uses midpoint.
    If sigma not specified, uses (b-a)/6 (99.7% within bounds).
    """
    if mu is None:
        mu = (a + b) / 2
    if sigma is None:
        sigma = (b - a) / 6

    z = (x - mu) / sigma
    return math.exp(-0.5 * z * z)


def beta_density(x: float, t: float, a: float, b: float, T: float,
                 alpha: float = 2, beta: float = 2) -> float:
    """
    Beta distribution - flexible shape within bounds.

    alpha = beta = 1: uniform
    alpha = beta = 2: symmetric bell
    alpha < beta: skewed left
    alpha > beta: skewed right
    """
    # Normalize x to [0, 1]
    if b == a:
        return 0.0
    u = (x - a) / (b - a)

    if u <= 0 or u >= 1:
        return 0.0

    # Beta PDF (unnormalized)
    return (u ** (alpha - 1)) * ((1 - u) ** (beta - 1))


def bimodal_density(x: float, t: float, a: float, b: float, T: float,
                    p_high: float = 0.5, width: float = 0.1) -> float:
    """
    Bimodal distribution - two peaks at bounds.

    p_high: probability weight on upper bound
    width: relative width of each mode
    """
    range_val = b - a
    sigma = width * range_val

    # Two Gaussians at a and b
    z_low = (x - a) / sigma
    z_high = (x - b) / sigma

    p_low = (1 - p_high) * math.exp(-0.5 * z_low * z_low)
    p_hi = p_high * math.exp(-0.5 * z_high * z_high)

    return p_low + p_hi


def time_evolving_density(x: float, t: float, a: float, b: float, T: float,
                          start_density: DensityFunc,
                          end_density: DensityFunc) -> float:
    """
    Density that interpolates between start and end distributions.

    P(x, t) = (1 - t/T) * start(x) + (t/T) * end(x)
    """
    progress = t / T if T > 0 else 0

    p_start = start_density(x, t, a, b, T)
    p_end = end_density(x, t, a, b, T)

    return (1 - progress) * p_start + progress * p_end


# ==================== FACTORY FUNCTIONS ====================

def create_abcfc(
    bounds: Tuple[float, float],
    duration: float,
    density_type: str = "uniform",
    **params
) -> ABCFC2D:
    """
    Factory to create ABCFC with common density types.

    density_type:
        "uniform": Flat distribution
        "gaussian": Bell curve (params: mu, sigma)
        "beta": Flexible shape (params: alpha, beta)
        "bimodal": Two peaks at bounds (params: p_high, width)
        "custom": Provide your own function (params: func)
    """
    a, b = bounds

    if density_type == "uniform":
        return ABCFC2D(bounds, duration, uniform_density)

    elif density_type == "gaussian":
        mu = params.get("mu", (a + b) / 2)
        sigma = params.get("sigma", (b - a) / 6)
        return ABCFC2D(bounds, duration,
                       lambda x, t, a, b, T: gaussian_density(x, t, a, b, T, mu, sigma))

    elif density_type == "beta":
        alpha = params.get("alpha", 2)
        beta_param = params.get("beta", 2)
        return ABCFC2D(bounds, duration,
                       lambda x, t, a, b, T: beta_density(x, t, a, b, T, alpha, beta_param))

    elif density_type == "bimodal":
        p_high = params.get("p_high", 0.5)
        width = params.get("width", 0.1)
        return ABCFC2D(bounds, duration,
                       lambda x, t, a, b, T: bimodal_density(x, t, a, b, T, p_high, width))

    elif density_type == "custom":
        func = params.get("func")
        if func is None:
            raise ValueError("Must provide 'func' for custom density")
        return ABCFC2D(bounds, duration, func)

    else:
        raise ValueError(f"Unknown density type: {density_type}")


# ==================== ABCFC PURE MATHEMATICS ====================

ABCFC_DEFINITION = """
╔══════════════════════════════════════════════════════════════════════════╗
║                         ABCFC DEFINITION                                 ║
║              Absolute Bounds Continuous Fan Chart                        ║
║                                                                          ║
║                        Created by: Yair Siegel                           ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  DEFINITION 1 (ABCFC):                                                   ║
║  ─────────────────────                                                   ║
║  An ABCFC is a triple (Ω, T, P) where:                                   ║
║                                                                          ║
║     • Ω = [a, b] ⊂ ℝ         (bounded outcome space)                    ║
║     • T ∈ ℝ⁺                 (duration)                                 ║
║     • P: Ω × [0,T] → ℝ≥0     (density function)                         ║
║                                                                          ║
║  satisfying:                                                             ║
║     (i)   P(x, t) ≥ 0        ∀ x ∈ Ω, t ∈ [0,T]   (non-negativity)     ║
║     (ii)  ∫_Ω P(x,t) dx = 1  ∀ t ∈ [0,T]          (normalization)       ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  DERIVED QUANTITIES:                                                     ║
║  ───────────────────                                                     ║
║                                                                          ║
║  Given an ABCFC (Ω, T, P), the following are defined:                    ║
║                                                                          ║
║     Expected Value:     E[X|t] = ∫_Ω x · P(x,t) dx                       ║
║                                                                          ║
║     Variance:           Var[X|t] = ∫_Ω (x - E[X|t])² · P(x,t) dx         ║
║                                                                          ║
║     Standard Dev:       σ[X|t] = √Var[X|t]                               ║
║                                                                          ║
║     CDF:                F(x,t) = ∫_a^x P(u,t) du                         ║
║                                                                          ║
║     Quantile:           Q(p,t) = inf{x : F(x,t) ≥ p}                     ║
║                                                                          ║
║     Median:             M(t) = Q(0.5, t)                                 ║
║                                                                          ║
║     Mode:               argmax_x P(x,t)                                  ║
║                                                                          ║
║     Marginal:           P(x) = (1/T) ∫_0^T P(x,t) dt                     ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  NOTATION:                                                               ║
║  ─────────                                                               ║
║     a       lower bound (worst case)                                     ║
║     b       upper bound (best case)                                      ║
║     T       duration / time horizon                                      ║
║     P(x,t)  probability density at value x, time t                       ║
║     E[X|t]  expected value at time t                                     ║
║     F(x,t)  cumulative distribution function                             ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  KEY PRINCIPLE:                                                          ║
║  ──────────────                                                          ║
║  The density function P(x,t) is a PARAMETER of the ABCFC.                ║
║                                                                          ║
║  The definition makes NO assumptions about:                              ║
║     • Shape of P (Gaussian, uniform, bimodal, custom, etc.)              ║
║     • How P evolves over t                                               ║
║     • Behavior at t=0 or t=T                                             ║
║     • Symmetry, continuity, or differentiability                         ║
║     • Number of modes                                                    ║
║     • Relationship between E[X|t] and bounds                             ║
║                                                                          ║
║  Different choices of P yield different ABCFC instances.                 ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  COMMON DENSITY CHOICES (examples, not requirements):                    ║
║  ─────────────────────────────────────────────────────                   ║
║                                                                          ║
║     Uniform:    P(x,t) = 1/(b-a)                                         ║
║     Gaussian:   P(x,t) ∝ exp(-(x-μ)²/2σ²)                                ║
║     Beta:       P(x,t) ∝ x^(α-1)(1-x)^(β-1)  (on normalized [0,1])       ║
║     Bimodal:    P(x,t) = mixture of two distributions                    ║
║     Custom:     Any function satisfying (i) and (ii)                     ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  VISUALIZATION:                                                          ║
║  ──────────────                                                          ║
║  An ABCFC is visualized as a 2D heatmap where:                           ║
║     • x-axis: time t ∈ [0, T]                                            ║
║     • y-axis: value x ∈ [a, b]                                           ║
║     • color:  density P(x, t)                                            ║
║                                                                          ║
║  Darker regions = higher probability density                             ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""


if __name__ == "__main__":
    print(ABCFC_DEFINITION)

    print("\n" + "=" * 60)
    print("EXAMPLES")
    print("=" * 60)

    # Example 1: Uniform
    uniform = create_abcfc((0, 100), duration=30, density_type="uniform")
    print(f"\n1. Uniform ABCFC:")
    print(f"   E[X|t=15] = {uniform.E(15):.1f}")
    print(f"   Var[X|t=15] = {uniform.Var(15):.1f}")

    # Example 2: Gaussian
    gauss = create_abcfc((0, 100), duration=30, density_type="gaussian", mu=60, sigma=15)
    print(f"\n2. Gaussian ABCFC (μ=60, σ=15):")
    print(f"   E[X|t=15] = {gauss.E(15):.1f}")
    print(f"   Std[X|t=15] = {gauss.std(15):.1f}")

    # Example 3: Bimodal
    bimodal = create_abcfc((0, 100), duration=30, density_type="bimodal", p_high=0.3)
    print(f"\n3. Bimodal ABCFC (p_high=0.3):")
    print(f"   E[X|t=15] = {bimodal.E(15):.1f}")

    # Example 4: Custom
    def my_density(x, t, a, b, T):
        # Triangular: peaks at midpoint
        mid = (a + b) / 2
        if x < mid:
            return (x - a) / (mid - a) if mid > a else 0
        else:
            return (b - x) / (b - mid) if b > mid else 0

    custom = create_abcfc((0, 100), duration=30, density_type="custom", func=my_density)
    print(f"\n4. Custom Triangular ABCFC:")
    print(f"   E[X|t=15] = {custom.E(15):.1f}")

    # Plot one
    print("\nGenerating plot...")
    result = gauss.plot(save_path="/tmp/abcfc_definition.png")
    print(f"   Chart: {result.get('chart_path')}")
