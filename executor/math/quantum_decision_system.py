#!/usr/bin/env python3
"""
QUANTUM DECISION SYSTEM - Derived from QM Foundations

Built backwards from quantum mechanics:
1. Wave function ψ(x,t) → ABCFC P(x,t)
2. Density matrix ρ → Nexus cloud mixed state
3. Hamiltonian Ĥ → Evolution (diffusion + mean reversion)
4. Conjugate pairs → Uncertainty relations
5. Entanglement → Position correlations
6. Measurement → Decision collapse

Created by: Yair Siegel
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from datetime import datetime, timezone

# ============================================================================
# WAVE FUNCTION (Pure State)
# ============================================================================

@dataclass
class WaveFunction:
    """
    ψ(x,t) - Probability amplitude over outcome space.

    |ψ(x)|² = P(x) probability density
    This IS an ABCFC at the quantum level.
    """

    # Discretized wave function on grid
    x_grid: np.ndarray  # Position grid points
    psi: np.ndarray     # Complex amplitudes (we use real for simplicity)

    # Bounds
    x_min: float
    x_max: float

    # Time
    t: float = 0.0

    def __post_init__(self):
        self._normalize()

    def _normalize(self):
        """Ensure ∫|ψ|²dx = 1"""
        norm = np.sqrt(np.trapz(self.psi**2, self.x_grid))
        if norm > 0:
            self.psi = self.psi / norm

    @classmethod
    def gaussian(cls, x_min: float, x_max: float,
                 center: float, sigma: float, n_points: int = 100):
        """Create Gaussian wave packet."""
        x = np.linspace(x_min, x_max, n_points)
        psi = np.exp(-(x - center)**2 / (2 * sigma**2))
        return cls(x_grid=x, psi=psi, x_min=x_min, x_max=x_max)

    @classmethod
    def from_abcfc(cls, worst: float, best: float, expected: float, n_points: int = 100):
        """Create wave function from ABCFC bounds."""
        sigma = (best - worst) / 4  # 2σ covers ~95% of distribution
        return cls.gaussian(worst, best, expected, sigma, n_points)

    def probability_density(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return (x, |ψ|²) for plotting."""
        return self.x_grid, self.psi**2

    def expectation(self) -> float:
        """⟨x⟩ = ∫ x |ψ|² dx"""
        return np.trapz(self.x_grid * self.psi**2, self.x_grid)

    def variance(self) -> float:
        """Δx² = ⟨x²⟩ - ⟨x⟩²"""
        x_mean = self.expectation()
        x2_mean = np.trapz(self.x_grid**2 * self.psi**2, self.x_grid)
        return x2_mean - x_mean**2

    def uncertainty(self) -> float:
        """Δx = √(variance)"""
        return math.sqrt(max(0, self.variance()))

    def collapse_to(self, x_value: float, collapse_width: float = 1.0):
        """Collapse wave function to narrow peak at x_value."""
        self.psi = np.exp(-(self.x_grid - x_value)**2 / (2 * collapse_width**2))
        self._normalize()

    def measure(self) -> float:
        """Perform measurement - collapse and return eigenvalue."""
        # Sample from |ψ|² distribution
        probs = self.psi**2
        probs = probs / probs.sum()
        idx = np.random.choice(len(self.x_grid), p=probs)
        measured = self.x_grid[idx]

        # Collapse
        self.collapse_to(measured)
        return measured


# ============================================================================
# DENSITY MATRIX (Mixed State)
# ============================================================================

@dataclass
class DensityMatrix:
    """
    ρ = Σᵢ pᵢ |ψᵢ⟩⟨ψᵢ| - Classical mixture of quantum states.

    This represents the nexus cloud - classical uncertainty
    about which ABCFC (wave function) we'll be in.
    """

    # List of (probability, wave_function) pairs
    components: List[Tuple[float, WaveFunction, str]] = field(default_factory=list)
    # str is the action label

    def add_component(self, prob: float, psi: WaveFunction, label: str):
        """Add a pure state to the mixture."""
        self.components.append((prob, psi, label))
        self._normalize_probs()

    def _normalize_probs(self):
        """Ensure probabilities sum to 1."""
        total = sum(p for p, _, _ in self.components)
        if total > 0:
            self.components = [(p/total, psi, l) for p, psi, l in self.components]

    @classmethod
    def from_nexus_cloud(cls, futures: List[Dict], score_key: str = "score"):
        """Create density matrix from nexus cloud futures."""
        dm = cls()

        if not futures:
            return dm

        # Convert scores to probabilities
        scores = [f.get(score_key, 0) for f in futures]
        min_score = min(scores)
        shifted = [s - min_score + 1 for s in scores]
        total = sum(shifted)

        for i, f in enumerate(futures):
            prob = shifted[i] / total

            # Create wave function from ABCFC bounds
            tl = f.get("top_line", {})
            worst = tl.get("worst", -100)
            best = tl.get("best", 100)
            expected = tl.get("expected", 0)

            psi = WaveFunction.from_abcfc(worst, best, expected)
            label = f"{f.get('action', 'unknown')}_{f.get('node', 'unknown')[:10]}"

            dm.add_component(prob, psi, label)

        return dm

    def purity(self) -> float:
        """
        γ = Tr(ρ²) = Σᵢ pᵢ²

        γ = 1: pure state (certain)
        γ = 1/N: maximally mixed
        """
        return sum(p**2 for p, _, _ in self.components)

    def von_neumann_entropy(self) -> float:
        """
        S = -Tr(ρ log ρ) = -Σᵢ pᵢ log(pᵢ)

        S = 0: pure state
        S = log(N): maximally mixed
        """
        entropy = 0
        for p, _, _ in self.components:
            if p > 0:
                entropy -= p * math.log(p)
        return entropy

    def max_entropy(self) -> float:
        """Maximum possible entropy = log(N)"""
        n = len(self.components)
        return math.log(n) if n > 0 else 0

    def normalized_entropy(self) -> float:
        """Entropy / max_entropy ∈ [0, 1]"""
        max_s = self.max_entropy()
        return self.von_neumann_entropy() / max_s if max_s > 0 else 0

    def expectation(self) -> float:
        """Expected value over mixed state."""
        return sum(p * psi.expectation() for p, psi, _ in self.components)

    def measure(self) -> Tuple[str, float]:
        """
        Measure the density matrix.

        1. Classically sample which pure state (collapse mixed → pure)
        2. Quantum measure that pure state (collapse wave function → eigenvalue)

        Returns: (action_label, measured_value)
        """
        if not self.components:
            return ("none", 0.0)

        # Step 1: Classical collapse - which pure state?
        probs = [p for p, _, _ in self.components]
        idx = np.random.choice(len(self.components), p=probs)
        _, chosen_psi, label = self.components[idx]

        # Step 2: Quantum collapse - what value?
        value = chosen_psi.measure()

        return (label, value)

    def top_actions(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N actions by probability."""
        sorted_comps = sorted(self.components, key=lambda x: -x[0])
        return [(label, prob) for prob, _, label in sorted_comps[:n]]


# ============================================================================
# HAMILTONIAN (Evolution)
# ============================================================================

class Hamiltonian:
    """
    Ĥ = (σ²/2) ∂²/∂x² - λ(x - x_fair)

    Generates time evolution via Fokker-Planck:
    ∂P/∂t = (σ²/2) ∂²P/∂x² + λ ∂/∂x[(x - x_fair)P]

    - σ: volatility (diffusion coefficient)
    - λ: mean reversion strength
    - x_fair: fair value (potential minimum)
    """

    def __init__(self, sigma: float = 10.0, lam: float = 0.1, x_fair: float = 0.0):
        self.sigma = sigma
        self.lam = lam
        self.x_fair = x_fair

    def evolve(self, psi: WaveFunction, dt: float) -> WaveFunction:
        """
        Evolve wave function forward by time dt.

        Uses simple finite difference for Fokker-Planck.
        """
        x = psi.x_grid
        dx = x[1] - x[0] if len(x) > 1 else 1.0
        P = psi.psi**2  # Probability density

        # Diffusion term: (σ²/2) ∂²P/∂x²
        d2P = np.zeros_like(P)
        d2P[1:-1] = (P[2:] - 2*P[1:-1] + P[:-2]) / dx**2
        diffusion = (self.sigma**2 / 2) * d2P

        # Drift term: λ ∂/∂x[(x - x_fair)P]
        drift_flux = self.lam * (x - self.x_fair) * P
        drift = np.zeros_like(P)
        drift[1:-1] = (drift_flux[2:] - drift_flux[:-2]) / (2*dx)

        # Update
        P_new = P + dt * (diffusion + drift)
        P_new = np.maximum(P_new, 0)  # Keep positive

        # Convert back to amplitude
        psi_new = np.sqrt(P_new)

        return WaveFunction(
            x_grid=x.copy(),
            psi=psi_new,
            x_min=psi.x_min,
            x_max=psi.x_max,
            t=psi.t + dt
        )


# ============================================================================
# CONJUGATE PAIRS (Uncertainty Relations)
# ============================================================================

@dataclass
class ConjugatePair:
    """
    A pair of observables that satisfy [Â, B̂] ≠ 0
    → ΔA · ΔB ≥ ℏ_eff/2
    """
    name_A: str
    name_B: str
    h_eff: float  # Effective Planck constant for this pair

    def uncertainty_bound(self) -> float:
        """Minimum ΔA·ΔB"""
        return self.h_eff / 2

    def check_violation(self, delta_A: float, delta_B: float) -> bool:
        """True if uncertainty relation is violated (shouldn't happen)."""
        return delta_A * delta_B < self.uncertainty_bound()


# Standard conjugate pairs for trading
CONJUGATE_PAIRS = [
    ConjugatePair("value", "momentum", h_eff=1.0),
    ConjugatePair("position_size", "entry_flexibility", h_eff=10.0),
    ConjugatePair("information", "opportunity", h_eff=1.0),
]


# ============================================================================
# ENTANGLEMENT
# ============================================================================

@dataclass
class EntangledSystem:
    """
    Track entanglement between positions.

    Entangled positions can't be treated independently -
    measuring one collapses the other.
    """

    # Correlation matrix between positions
    # corr[i,j] = correlation coefficient
    positions: List[str] = field(default_factory=list)
    correlations: np.ndarray = None

    def __post_init__(self):
        n = len(self.positions)
        if self.correlations is None and n > 0:
            self.correlations = np.eye(n)

    def add_position(self, name: str):
        """Add a position to track."""
        self.positions.append(name)
        n = len(self.positions)
        new_corr = np.eye(n)
        if self.correlations is not None:
            new_corr[:-1, :-1] = self.correlations
        self.correlations = new_corr

    def set_correlation(self, pos_a: str, pos_b: str, corr: float):
        """Set correlation between two positions."""
        if pos_a not in self.positions or pos_b not in self.positions:
            return
        i = self.positions.index(pos_a)
        j = self.positions.index(pos_b)
        self.correlations[i, j] = corr
        self.correlations[j, i] = corr

    def entanglement_entropy(self, position: str) -> float:
        """
        Entanglement entropy for a position.

        S = -Σⱼ |ρᵢⱼ|² log |ρᵢⱼ|² (simplified)

        Higher = more entangled with others.
        """
        if position not in self.positions:
            return 0

        i = self.positions.index(position)
        row = self.correlations[i, :]

        # Use absolute correlations as "entanglement strength"
        abs_corr = np.abs(row)
        abs_corr = abs_corr / abs_corr.sum()  # Normalize

        entropy = 0
        for c in abs_corr:
            if c > 0:
                entropy -= c * math.log(c)

        return entropy

    def is_entangled(self, pos_a: str, pos_b: str, threshold: float = 0.5) -> bool:
        """Check if two positions are significantly entangled."""
        if pos_a not in self.positions or pos_b not in self.positions:
            return False
        i = self.positions.index(pos_a)
        j = self.positions.index(pos_b)
        return abs(self.correlations[i, j]) > threshold


# ============================================================================
# QUANTUM DECISION SYSTEM (Complete)
# ============================================================================

class QuantumDecisionSystem:
    """
    Complete decision system derived from QM foundations.

    - State: Wave functions (ABCFC) + Density matrix (nexus cloud)
    - Dynamics: Hamiltonian evolution
    - Uncertainty: Conjugate pairs
    - Entanglement: Position correlations
    - Measurement: Decision collapse
    """

    def __init__(self, name: str = "Yair Siegel"):
        self.name = name

        # Current quantum state (pure)
        self.psi: Optional[WaveFunction] = None

        # Decision state (mixed)
        self.rho: Optional[DensityMatrix] = None

        # Evolution
        self.hamiltonian = Hamiltonian(sigma=10.0, lam=0.1, x_fair=0.0)

        # Entanglement tracking
        self.entanglement = EntangledSystem()

        # Conjugate pairs
        self.conjugate_pairs = CONJUGATE_PAIRS

        # Measurement history
        self.measurements: List[Dict] = []

    def set_state_from_abcfc(self, worst: float, best: float, expected: float):
        """Initialize quantum state from ABCFC bounds."""
        self.psi = WaveFunction.from_abcfc(worst, best, expected)
        self.hamiltonian.x_fair = expected

    def set_decision_state(self, futures: List[Dict]):
        """Initialize decision state from nexus cloud."""
        self.rho = DensityMatrix.from_nexus_cloud(futures)

    def evolve(self, dt: float):
        """Evolve the quantum state forward in time."""
        if self.psi:
            self.psi = self.hamiltonian.evolve(self.psi, dt)

    def measure_value(self) -> float:
        """Measure the value observable (collapses wave function)."""
        if self.psi is None:
            return 0.0

        value = self.psi.measure()

        self.measurements.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "observable": "value",
            "result": value,
        })

        return value

    def decide(self) -> Tuple[str, float]:
        """
        Make a decision (measure the density matrix).

        Returns: (action_label, collapsed_value)
        """
        if self.rho is None:
            return ("none", 0.0)

        action, value = self.rho.measure()

        self.measurements.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "observable": "decision",
            "action": action,
            "value": value,
        })

        return action, value

    def purity(self) -> float:
        """Decision state purity."""
        return self.rho.purity() if self.rho else 1.0

    def entropy(self) -> float:
        """Decision state entropy."""
        return self.rho.von_neumann_entropy() if self.rho else 0.0

    def uncertainty(self, observable: str = "value") -> float:
        """Uncertainty in observable."""
        if observable == "value" and self.psi:
            return self.psi.uncertainty()
        return float('inf')

    def check_uncertainty_relations(self) -> List[Dict]:
        """Check all conjugate pair uncertainty relations."""
        results = []
        for pair in self.conjugate_pairs:
            # Simplified: just report the pair and bound
            results.append({
                "pair": (pair.name_A, pair.name_B),
                "bound": pair.uncertainty_bound(),
                "h_eff": pair.h_eff,
            })
        return results

    def status(self) -> Dict:
        """Get full quantum status."""
        return {
            "name": self.name,
            "wave_function": {
                "expectation": self.psi.expectation() if self.psi else None,
                "uncertainty": self.psi.uncertainty() if self.psi else None,
            },
            "density_matrix": {
                "n_components": len(self.rho.components) if self.rho else 0,
                "purity": self.purity(),
                "entropy": self.entropy(),
                "normalized_entropy": self.rho.normalized_entropy() if self.rho else 0,
                "top_actions": self.rho.top_actions(5) if self.rho else [],
            },
            "entanglement": {
                "n_positions": len(self.entanglement.positions),
                "positions": self.entanglement.positions,
            },
            "n_measurements": len(self.measurements),
        }

    def print_status(self):
        """Print quantum status."""
        s = self.status()
        print("=" * 70)
        print(f"QUANTUM DECISION SYSTEM: {s['name']}")
        print("=" * 70)

        print("\n[WAVE FUNCTION]")
        wf = s['wave_function']
        if wf['expectation'] is not None:
            print(f"  ⟨x⟩ = ${wf['expectation']:.2f}")
            print(f"  Δx = ${wf['uncertainty']:.2f}")
        else:
            print("  Not initialized")

        print("\n[DENSITY MATRIX]")
        dm = s['density_matrix']
        print(f"  Components: {dm['n_components']}")
        print(f"  Purity γ = {dm['purity']:.3f}  (1=pure, 1/N=mixed)")
        print(f"  Entropy S = {dm['entropy']:.3f}  (0=pure, logN=mixed)")
        print(f"  Normalized entropy = {dm['normalized_entropy']:.1%}")
        print(f"  Top actions:")
        for label, prob in dm['top_actions']:
            print(f"    {prob:.1%} | {label}")

        print("\n[ENTANGLEMENT]")
        ent = s['entanglement']
        print(f"  Tracking {ent['n_positions']} positions")

        print("\n[MEASUREMENTS]")
        print(f"  {s['n_measurements']} measurements recorded")

        print("=" * 70)


# ============================================================================
# INTEGRATION WITH EXISTING SYSTEM
# ============================================================================

def create_from_nexus_cloud(cloud: Dict) -> QuantumDecisionSystem:
    """Create quantum decision system from ABCFC nexus cloud."""
    qds = QuantumDecisionSystem()

    # Set current state from cloud's current
    current = cloud.get("current", {})
    if current:
        qds.set_state_from_abcfc(
            worst=current.get("worst", -100),
            best=current.get("best", 100),
            expected=current.get("expected", 0)
        )

    # Set decision state from futures
    futures = cloud.get("futures", [])
    if futures:
        qds.set_decision_state(futures)

    return qds


def monte_carlo_collapse(cloud: Dict, n_samples: int = 100) -> Dict:
    """
    Run multiple quantum collapses to show probability distribution.

    This demonstrates the quantum nature - same state collapses to
    different outcomes with probabilities matching the density matrix.

    Returns distribution of collapsed actions and values.
    """
    from collections import Counter

    action_counts = Counter()
    values = []

    for _ in range(n_samples):
        qds = create_from_nexus_cloud(cloud)
        action, value = qds.decide()
        action_counts[action] += 1
        values.append(value)

    # Convert to probabilities
    action_probs = {a: c/n_samples for a, c in action_counts.items()}

    return {
        "n_samples": n_samples,
        "action_distribution": dict(action_counts.most_common()),
        "action_probabilities": action_probs,
        "value_mean": np.mean(values),
        "value_std": np.std(values),
        "value_min": np.min(values),
        "value_max": np.max(values),
    }


def quantum_vs_classical(cloud: Dict) -> Dict:
    """
    Compare quantum and classical decision making.

    Classical: Always picks highest score (deterministic)
    Quantum: Probabilistically samples from distribution

    Returns comparison metrics.
    """
    # Classical decision
    futures = cloud.get("futures", [])
    if not futures:
        return {"error": "No futures in cloud"}

    classical_best = futures[0]  # Already sorted by score
    classical_action = f"{classical_best['action']}_{classical_best['node'][:10]}"
    classical_expected = classical_best["top_line"]["expected"]

    # Quantum Monte Carlo
    mc = monte_carlo_collapse(cloud, n_samples=100)

    # Most likely quantum action
    quantum_most_likely = max(mc["action_probabilities"], key=mc["action_probabilities"].get)
    quantum_prob = mc["action_probabilities"][quantum_most_likely]

    return {
        "classical": {
            "action": classical_action,
            "expected": classical_expected,
            "deterministic": True,
        },
        "quantum": {
            "most_likely_action": quantum_most_likely,
            "most_likely_prob": quantum_prob,
            "mean_value": mc["value_mean"],
            "value_std": mc["value_std"],
            "unique_outcomes": len(mc["action_distribution"]),
            "deterministic": False,
        },
        "agreement": quantum_most_likely == classical_action,
        "entropy_captured": len(mc["action_distribution"]) / len(futures) if futures else 0,
    }


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("QUANTUM DECISION SYSTEM DEMO")
    print("=" * 70)

    # Create system
    qds = QuantumDecisionSystem("Yair Siegel")

    # Initialize from ABCFC-like bounds
    qds.set_state_from_abcfc(worst=-100, best=2000, expected=1000)

    print("\n1. Initial wave function:")
    print(f"   ⟨x⟩ = ${qds.psi.expectation():.2f}")
    print(f"   Δx = ${qds.psi.uncertainty():.2f}")

    # Evolve
    print("\n2. Evolving for 10 time steps...")
    for _ in range(10):
        qds.evolve(dt=0.1)
    print(f"   ⟨x⟩ = ${qds.psi.expectation():.2f}")
    print(f"   Δx = ${qds.psi.uncertainty():.2f}")

    # Create decision state (mock nexus cloud)
    mock_futures = [
        {"action": "hedge", "node": "Trading", "score": 173,
         "top_line": {"worst": -50, "best": 1500, "expected": 900}},
        {"action": "hold", "node": "Trading", "score": 150,
         "top_line": {"worst": -100, "best": 2000, "expected": 1000}},
        {"action": "buy", "node": "Polymarket", "score": 120,
         "top_line": {"worst": -200, "best": 2500, "expected": 1100}},
    ]
    qds.set_decision_state(mock_futures)

    print("\n3. Decision state (density matrix):")
    qds.print_status()

    # Decide
    print("\n4. Making decision (measurement)...")
    action, value = qds.decide()
    print(f"   COLLAPSED TO: {action}")
    print(f"   Measured value: ${value:.2f}")

    # Check uncertainty relations
    print("\n5. Conjugate pairs:")
    for pair in qds.check_uncertainty_relations():
        print(f"   ({pair['pair'][0]}, {pair['pair'][1]}): ΔA·ΔB ≥ {pair['bound']:.2f}")

    print("\n" + "=" * 70)
    print("Quantum decision system operational")
    print("=" * 70)
