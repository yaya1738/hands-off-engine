#!/usr/bin/env python3
"""
QUANTUM ABCFC - Heisenberg Uncertainty + Wave Function Collapse

Integrates quantum concepts into the ABCFC decision system:

1. UNCERTAINTY SPHERES: Position (value) and momentum (rate of change)
   cannot both be known precisely. Δx·Δp ≥ ℏ/2

2. WAVE FUNCTION: State exists in superposition until observation.
   |ψ⟩ = Σ αᵢ|stateᵢ⟩

3. COLLAPSE: Observation forces state to eigenvalue.
   Measure → collapse → determinate outcome

4. ENTANGLEMENT: Correlated ABCFCs - observing one affects another.

Created by: Yair Siegel
"""

import os
import sys
import math
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from executor.math.abcfc_system import ABCFCSystem, Action as ABCFCAction, ABCFC

# Reduced Planck constant analog for our system
HBAR = 1.0  # Uncertainty constant


# ============================================================================
# UNCERTAINTY SPHERE
# ============================================================================

@dataclass
class UncertaintySphere:
    """
    Heisenberg Uncertainty Sphere for an ABCFC.

    You cannot know both:
    - Position (current value) with precision Δx
    - Momentum (rate of change) with precision Δp

    Constraint: Δx · Δp ≥ ℏ/2

    Measuring one more precisely makes the other less certain.
    """

    # Position uncertainty (value)
    delta_x: float  # Uncertainty in current expected value

    # Momentum uncertainty (rate of change)
    delta_p: float  # Uncertainty in how fast value is changing

    # Center of sphere
    x_center: float = 0.0  # Expected value center
    p_center: float = 0.0  # Expected momentum center

    def __post_init__(self):
        # Enforce Heisenberg constraint
        if self.delta_x * self.delta_p < HBAR / 2:
            # Minimum uncertainty state - adjust
            min_product = HBAR / 2
            ratio = math.sqrt(min_product / (self.delta_x * self.delta_p + 0.001))
            self.delta_x *= ratio
            self.delta_p *= ratio

    @property
    def uncertainty_product(self) -> float:
        """The Δx·Δp product - always ≥ ℏ/2."""
        return self.delta_x * self.delta_p

    @property
    def is_minimum_uncertainty(self) -> bool:
        """True if at minimum uncertainty (coherent state)."""
        return abs(self.uncertainty_product - HBAR/2) < 0.01

    def measure_position(self, precision: float) -> Tuple[float, 'UncertaintySphere']:
        """
        Measure position with given precision.

        Returns:
            (measured_value, new_sphere_after_measurement)

        Measuring position precisely increases momentum uncertainty.
        """
        # Collapse position to a value within uncertainty
        measured = random.gauss(self.x_center, self.delta_x)

        # New uncertainties after measurement
        new_delta_x = min(precision, self.delta_x)
        new_delta_p = max(HBAR / (2 * new_delta_x), self.delta_p)

        new_sphere = UncertaintySphere(
            delta_x=new_delta_x,
            delta_p=new_delta_p,
            x_center=measured,
            p_center=self.p_center
        )

        return measured, new_sphere

    def measure_momentum(self, precision: float) -> Tuple[float, 'UncertaintySphere']:
        """
        Measure momentum (rate of change) with given precision.

        Measuring momentum precisely increases position uncertainty.
        """
        measured = random.gauss(self.p_center, self.delta_p)

        new_delta_p = min(precision, self.delta_p)
        new_delta_x = max(HBAR / (2 * new_delta_p), self.delta_x)

        new_sphere = UncertaintySphere(
            delta_x=new_delta_x,
            delta_p=new_delta_p,
            x_center=self.x_center,
            p_center=measured
        )

        return measured, new_sphere

    def evolve(self, dt: float) -> 'UncertaintySphere':
        """Evolve sphere forward in time (uncertainty spreads)."""
        # Position uncertainty grows with momentum uncertainty
        new_delta_x = math.sqrt(self.delta_x**2 + (self.delta_p * dt)**2)

        return UncertaintySphere(
            delta_x=new_delta_x,
            delta_p=self.delta_p,
            x_center=self.x_center + self.p_center * dt,
            p_center=self.p_center
        )

    def __repr__(self):
        return f"Sphere(x={self.x_center:.1f}±{self.delta_x:.1f}, p={self.p_center:.1f}±{self.delta_p:.1f})"


# ============================================================================
# WAVE FUNCTION
# ============================================================================

class QuantumState(Enum):
    """Possible basis states for an ABCFC."""
    SUPERPOSITION = "superposition"
    COLLAPSED = "collapsed"


@dataclass
class WaveFunction:
    """
    Wave function for an ABCFC decision.

    |ψ⟩ = Σ αᵢ|actionᵢ⟩

    Stays in superposition of possible actions until observed.
    Observation collapses to one eigenstate.
    """

    # Amplitudes for each possible action (complex, but we use real for simplicity)
    amplitudes: Dict[str, float] = field(default_factory=dict)

    # Current state
    state: QuantumState = QuantumState.SUPERPOSITION

    # Collapsed value (if collapsed)
    collapsed_to: Optional[str] = None

    def __post_init__(self):
        if self.amplitudes:
            self._normalize()

    def _normalize(self):
        """Normalize amplitudes so probabilities sum to 1."""
        total = sum(a**2 for a in self.amplitudes.values())
        if total > 0:
            factor = 1.0 / math.sqrt(total)
            self.amplitudes = {k: v * factor for k, v in self.amplitudes.items()}

    def probability(self, action: str) -> float:
        """Probability of collapsing to this action (|α|²)."""
        if self.state == QuantumState.COLLAPSED:
            return 1.0 if action == self.collapsed_to else 0.0
        return self.amplitudes.get(action, 0) ** 2

    def observe(self) -> str:
        """
        Observe the wave function → collapse to eigenstate.

        Returns the action that the wave function collapsed to.
        """
        if self.state == QuantumState.COLLAPSED:
            return self.collapsed_to

        # Probabilistic collapse based on amplitudes
        r = random.random()
        cumulative = 0.0

        for action, amplitude in self.amplitudes.items():
            cumulative += amplitude ** 2
            if r <= cumulative:
                self.state = QuantumState.COLLAPSED
                self.collapsed_to = action
                return action

        # Fallback (shouldn't happen if normalized)
        action = list(self.amplitudes.keys())[-1]
        self.state = QuantumState.COLLAPSED
        self.collapsed_to = action
        return action

    def interfere(self, other: 'WaveFunction') -> 'WaveFunction':
        """
        Quantum interference between two wave functions.

        Amplitudes add (can constructively or destructively interfere).
        """
        all_actions = set(self.amplitudes.keys()) | set(other.amplitudes.keys())

        new_amplitudes = {}
        for action in all_actions:
            a1 = self.amplitudes.get(action, 0)
            a2 = other.amplitudes.get(action, 0)
            new_amplitudes[action] = a1 + a2  # Interference!

        return WaveFunction(amplitudes=new_amplitudes)

    @classmethod
    def from_abcfc_scores(cls, scores: Dict[str, float]) -> 'WaveFunction':
        """
        Create wave function from ABCFC nexus cloud scores.

        Higher scores → higher amplitudes.
        """
        if not scores:
            return cls()

        # Convert scores to amplitudes (sqrt of normalized scores)
        min_score = min(scores.values())
        shifted = {k: v - min_score + 1 for k, v in scores.items()}
        total = sum(shifted.values())

        amplitudes = {k: math.sqrt(v / total) for k, v in shifted.items()}
        return cls(amplitudes=amplitudes)

    def __repr__(self):
        if self.state == QuantumState.COLLAPSED:
            return f"|ψ⟩ = |{self.collapsed_to}⟩ (collapsed)"

        terms = [f"{a:.2f}|{k}⟩" for k, a in sorted(self.amplitudes.items(), key=lambda x: -x[1])]
        return f"|ψ⟩ = {' + '.join(terms[:3])}..."


# ============================================================================
# ENTANGLEMENT
# ============================================================================

@dataclass
class EntangledPair:
    """
    Two ABCFCs that are entangled.

    Measuring one instantly affects the other.
    """

    abcfc_a: str  # Name of first ABCFC
    abcfc_b: str  # Name of second ABCFC

    # Correlation: +1 = same direction, -1 = opposite, 0 = uncorrelated
    correlation: float = 1.0

    # Whether either has been measured
    a_measured: bool = False
    b_measured: bool = False
    a_value: Optional[float] = None
    b_value: Optional[float] = None

    def measure_a(self, value: float) -> Optional[float]:
        """
        Measure A, which instantly determines B's value.

        Returns: B's collapsed value
        """
        self.a_measured = True
        self.a_value = value

        if not self.b_measured:
            # B collapses based on correlation
            self.b_value = value * self.correlation
            self.b_measured = True

        return self.b_value

    def measure_b(self, value: float) -> Optional[float]:
        """Measure B, which determines A."""
        self.b_measured = True
        self.b_value = value

        if not self.a_measured:
            self.a_value = value * self.correlation
            self.a_measured = True

        return self.a_value


# ============================================================================
# QUANTUM ABCFC SYSTEM
# ============================================================================

class QuantumABCFCSystem:
    """
    ABCFC System with quantum properties:

    1. Each ABCFC has an uncertainty sphere
    2. Decisions exist as wave functions until observed
    3. Related ABCFCs can be entangled
    4. Observation causes collapse
    """

    def __init__(self, name: str = "Yair Siegel"):
        self.name = name
        self.classical = ABCFCSystem(name)

        # Quantum properties
        self.spheres: Dict[str, UncertaintySphere] = {}
        self.wave_functions: Dict[str, WaveFunction] = {}
        self.entanglements: List[EntangledPair] = []

        # Observation history
        self.observations: List[Dict] = []

    def add_position(self, parent: str, name: str,
                     worst: float, best: float, expected: float,
                     momentum: float = 0.0,
                     delta_x: float = 10.0,
                     delta_p: float = 1.0):
        """Add a position with quantum properties."""

        # Classical
        self.classical.add_position(parent, name, worst, best, expected)

        # Quantum - uncertainty sphere
        self.spheres[name] = UncertaintySphere(
            delta_x=delta_x,
            delta_p=delta_p,
            x_center=expected,
            p_center=momentum
        )

    def entangle(self, name_a: str, name_b: str, correlation: float = 1.0):
        """Create entanglement between two ABCFCs."""
        self.entanglements.append(EntangledPair(name_a, name_b, correlation))

    def get_decision_wave_function(self, actions: List[ABCFCAction] = None) -> WaveFunction:
        """
        Get wave function of possible decisions.

        Stays in superposition until observe() is called.
        """
        if actions is None:
            actions = [
                ABCFCAction("hold", "hold", {}),
                ABCFCAction("hedge", "hedge", {"ratio": 0.5}),
                ABCFCAction("buy", "buy", {"size": 25}),
                ABCFCAction("sell", "sell", {"size": 25}),
            ]

        # Get scores from classical nexus cloud
        cloud = self.classical.get_top_line_nexus_cloud(actions)

        # Convert to wave function
        scores = {}
        for future in cloud.get("futures", []):
            key = f"{future['action']}_{future['node']}"
            scores[key] = future["score"]

        wf = WaveFunction.from_abcfc_scores(scores)
        self.wave_functions["decision"] = wf

        return wf

    def observe_decision(self) -> Dict:
        """
        Observe the decision wave function → collapse.

        Returns the collapsed decision.
        """
        wf = self.wave_functions.get("decision")
        if wf is None:
            wf = self.get_decision_wave_function()

        # COLLAPSE
        collapsed = wf.observe()

        # Parse the collapsed state
        parts = collapsed.split("_", 1)
        action = parts[0] if parts else "hold"
        node = parts[1] if len(parts) > 1 else "unknown"

        # Record observation
        self.observations.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "decision",
            "collapsed_to": collapsed,
            "action": action,
            "node": node,
        })

        # Handle entanglements
        for pair in self.entanglements:
            if pair.abcfc_a == node or pair.abcfc_b == node:
                # Measuring one affects the other
                pass  # Would propagate collapse

        return {
            "action": action,
            "node": node,
            "wave_function": str(wf),
            "collapsed": True,
        }

    def measure_position(self, name: str, precision: float = 1.0) -> Dict:
        """
        Measure an ABCFC's position (value) with given precision.

        This increases momentum uncertainty per Heisenberg.
        """
        sphere = self.spheres.get(name)
        if sphere is None:
            return {"error": f"No sphere for {name}"}

        value, new_sphere = sphere.measure_position(precision)
        self.spheres[name] = new_sphere

        self.observations.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "position",
            "name": name,
            "measured": value,
            "precision": precision,
            "new_uncertainty": new_sphere.delta_x,
            "momentum_uncertainty": new_sphere.delta_p,
        })

        return {
            "name": name,
            "measured_value": value,
            "position_uncertainty": new_sphere.delta_x,
            "momentum_uncertainty": new_sphere.delta_p,
            "heisenberg_product": new_sphere.uncertainty_product,
        }

    def measure_momentum(self, name: str, precision: float = 1.0) -> Dict:
        """
        Measure an ABCFC's momentum (rate of change).

        This increases position uncertainty.
        """
        sphere = self.spheres.get(name)
        if sphere is None:
            return {"error": f"No sphere for {name}"}

        value, new_sphere = sphere.measure_momentum(precision)
        self.spheres[name] = new_sphere

        self.observations.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "momentum",
            "name": name,
            "measured": value,
            "precision": precision,
        })

        return {
            "name": name,
            "measured_momentum": value,
            "momentum_uncertainty": new_sphere.delta_p,
            "position_uncertainty": new_sphere.delta_x,
            "heisenberg_product": new_sphere.uncertainty_product,
        }

    def evolve(self, dt: float = 1.0):
        """Evolve all uncertainty spheres forward in time."""
        for name, sphere in self.spheres.items():
            self.spheres[name] = sphere.evolve(dt)

    def superposition_status(self) -> Dict:
        """Get status of all wave functions."""
        return {
            name: {
                "state": wf.state.value,
                "collapsed_to": wf.collapsed_to,
                "top_amplitudes": dict(sorted(
                    wf.amplitudes.items(),
                    key=lambda x: -x[1]
                )[:5])
            }
            for name, wf in self.wave_functions.items()
        }

    def uncertainty_status(self) -> Dict:
        """Get status of all uncertainty spheres."""
        return {
            name: {
                "x": sphere.x_center,
                "delta_x": sphere.delta_x,
                "p": sphere.p_center,
                "delta_p": sphere.delta_p,
                "product": sphere.uncertainty_product,
                "minimum": sphere.is_minimum_uncertainty,
            }
            for name, sphere in self.spheres.items()
        }

    def print_quantum_state(self):
        """Print full quantum state."""
        print("=" * 70)
        print(f"QUANTUM ABCFC SYSTEM: {self.name}")
        print("=" * 70)

        print("\n[UNCERTAINTY SPHERES]")
        for name, sphere in self.spheres.items():
            print(f"  {name}: {sphere}")

        print("\n[WAVE FUNCTIONS]")
        for name, wf in self.wave_functions.items():
            print(f"  {name}: {wf}")

        print("\n[ENTANGLEMENTS]")
        for pair in self.entanglements:
            status = "measured" if pair.a_measured or pair.b_measured else "superposed"
            print(f"  {pair.abcfc_a} <--({pair.correlation:+.1f})--> {pair.abcfc_b} [{status}]")

        print("\n[RECENT OBSERVATIONS]")
        for obs in self.observations[-5:]:
            print(f"  {obs['type']}: {obs.get('collapsed_to') or obs.get('measured', 'N/A')}")

        print("=" * 70)


# ============================================================================
# INTEGRATION WITH HANDS-OFF SYSTEM
# ============================================================================

def create_quantum_trading_system() -> QuantumABCFCSystem:
    """Create quantum ABCFC system for Polymarket trading."""

    q = QuantumABCFCSystem("Yair Siegel Quantum")

    # Add classical hierarchy
    q.classical.add_category("Trading")
    q.classical.add_subcategory("Trading", "Polymarket")

    return q


def integrate_with_polymarket(q: QuantumABCFCSystem):
    """Load real Polymarket positions into quantum system."""

    try:
        from executor.math.abcfc_cloud_flyer import ABCFCCloudFlyer
        flyer = ABCFCCloudFlyer()
        state = flyer.observe()

        for pos in state.positions:
            q.add_position(
                parent="Polymarket",
                name=pos["name"],
                worst=pos["worst"],
                best=pos["best"],
                expected=pos["expected"],
                momentum=0,  # Could calculate from historical data
                delta_x=abs(pos["best"] - pos["worst"]) / 4,  # Uncertainty from bounds
                delta_p=1.0
            )

        # Entangle correlated positions (if any)
        # Example: positions in same market are entangled
        names = [p["name"] for p in state.positions]
        for i, n1 in enumerate(names):
            for n2 in names[i+1:]:
                # Light entanglement between all positions
                q.entangle(n1, n2, correlation=0.3)

        return True
    except Exception as e:
        print(f"Integration error: {e}")
        return False


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("QUANTUM ABCFC SYSTEM DEMO")
    print("=" * 70)

    # Create quantum system
    q = create_quantum_trading_system()

    # Try to integrate with real Polymarket
    if integrate_with_polymarket(q):
        print("\nIntegrated with real Polymarket positions")
    else:
        # Demo positions
        print("\nUsing demo positions")
        q.add_position("Polymarket", "Market_A", worst=-50, best=100, expected=30, delta_x=20, delta_p=2)
        q.add_position("Polymarket", "Market_B", worst=-30, best=80, expected=40, delta_x=15, delta_p=3)
        q.add_position("Polymarket", "Market_C", worst=-10, best=50, expected=20, delta_x=10, delta_p=1)
        q.entangle("Market_A", "Market_B", correlation=0.8)

    # Show initial state
    print("\n[INITIAL STATE - SUPERPOSITION]")
    q.print_quantum_state()

    # Get decision wave function (superposition of actions)
    print("\n[DECISION WAVE FUNCTION]")
    wf = q.get_decision_wave_function()
    print(f"Decision state: {wf}")
    print(f"State: {wf.state.value}")

    # Observe - causes collapse!
    print("\n[OBSERVING - WAVE FUNCTION COLLAPSE]")
    decision = q.observe_decision()
    print(f"COLLAPSED TO: {decision['action']} on {decision['node']}")

    # Measure position with high precision
    print("\n[MEASURING POSITION - HEISENBERG IN ACTION]")
    if q.spheres:
        name = list(q.spheres.keys())[0]
        before = q.spheres[name]
        print(f"Before: {before}")

        result = q.measure_position(name, precision=5.0)
        print(f"Measured: {result['measured_value']:.2f}")
        print(f"Position uncertainty: {result['position_uncertainty']:.2f}")
        print(f"Momentum uncertainty: {result['momentum_uncertainty']:.2f}")
        print(f"Heisenberg product: {result['heisenberg_product']:.2f} (must be ≥ {HBAR/2})")

    # Final state
    print("\n[FINAL STATE - COLLAPSED]")
    q.print_quantum_state()

    print("\n" + "=" * 70)
    print("Quantum ABCFC system operational")
    print("Decisions exist in superposition until observed")
    print("Heisenberg uncertainty governs position/momentum tradeoff")
    print("=" * 70)
