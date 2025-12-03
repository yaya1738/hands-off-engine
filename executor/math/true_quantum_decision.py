#!/usr/bin/env python3
"""
TRUE QUANTUM DECISION SYSTEM - Built from QM First Principles

Starting from quantum mechanics, not retrofitting terminology.

Key structures:
1. Hilbert space H with discrete action basis
2. State vectors |ψ⟩ with complex amplitudes
3. Operators (Hermitian for observables)
4. Unitary evolution via Schrödinger equation
5. Proper density matrices for mixed states
6. Tensor products for composite systems
7. Decoherence for quantum→classical transition

Created by: Yair Siegel
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import math
from datetime import datetime, timezone


# ============================================================================
# HILBERT SPACE - The Foundation
# ============================================================================

class HilbertSpace:
    """
    Finite-dimensional Hilbert space for decision making.

    Basis: {|a₁⟩, |a₂⟩, ..., |aₙ⟩} = possible actions
    Dimension: N = number of actions
    """

    def __init__(self, actions: List[str]):
        """Create Hilbert space with action basis."""
        self.actions = actions
        self.dim = len(actions)
        self.action_to_idx = {a: i for i, a in enumerate(actions)}

        # Basis vectors (standard basis)
        self.basis = {
            a: self._basis_vector(i)
            for i, a in enumerate(actions)
        }

    def _basis_vector(self, i: int) -> np.ndarray:
        """Create |aᵢ⟩ basis vector."""
        v = np.zeros(self.dim, dtype=complex)
        v[i] = 1.0
        return v

    def get_basis(self, action: str) -> np.ndarray:
        """Get basis vector for action."""
        return self.basis.get(action, np.zeros(self.dim, dtype=complex))

    def inner_product(self, psi: np.ndarray, phi: np.ndarray) -> complex:
        """Compute ⟨ψ|φ⟩."""
        return np.vdot(psi, phi)  # conjugate of first arg

    def norm(self, psi: np.ndarray) -> float:
        """Compute ||ψ|| = √⟨ψ|ψ⟩."""
        return np.sqrt(np.real(self.inner_product(psi, psi)))

    def normalize(self, psi: np.ndarray) -> np.ndarray:
        """Return normalized state."""
        n = self.norm(psi)
        return psi / n if n > 0 else psi


# ============================================================================
# STATE VECTORS - Quantum States
# ============================================================================

@dataclass
class QuantumState:
    """
    |ψ⟩ = Σᵢ cᵢ|aᵢ⟩

    Complex amplitudes cᵢ, probabilities P(aᵢ) = |cᵢ|²
    THIS is superposition - not a mixture!
    """

    hilbert: HilbertSpace
    amplitudes: np.ndarray  # Complex amplitudes

    def __post_init__(self):
        """Ensure normalization."""
        norm = self.hilbert.norm(self.amplitudes)
        if norm > 0:
            self.amplitudes = self.amplitudes / norm

    @classmethod
    def from_action(cls, hilbert: HilbertSpace, action: str) -> 'QuantumState':
        """Create pure state |action⟩."""
        return cls(hilbert, hilbert.get_basis(action).copy())

    @classmethod
    def uniform_superposition(cls, hilbert: HilbertSpace) -> 'QuantumState':
        """Create |ψ⟩ = (1/√N) Σᵢ|aᵢ⟩."""
        amp = np.ones(hilbert.dim, dtype=complex) / np.sqrt(hilbert.dim)
        return cls(hilbert, amp)

    @classmethod
    def from_probabilities(cls, hilbert: HilbertSpace, probs: Dict[str, float]) -> 'QuantumState':
        """Create state with given probabilities (phases = 0)."""
        amp = np.zeros(hilbert.dim, dtype=complex)
        for action, prob in probs.items():
            if action in hilbert.action_to_idx:
                idx = hilbert.action_to_idx[action]
                amp[idx] = np.sqrt(prob)
        return cls(hilbert, amp)

    def probability(self, action: str) -> float:
        """P(action) = |⟨action|ψ⟩|²."""
        if action not in self.hilbert.action_to_idx:
            return 0.0
        idx = self.hilbert.action_to_idx[action]
        return float(np.abs(self.amplitudes[idx])**2)

    def probabilities(self) -> Dict[str, float]:
        """Get all probabilities."""
        return {a: self.probability(a) for a in self.hilbert.actions}

    def measure(self) -> str:
        """
        Perform measurement in action basis.

        Collapses to |aᵢ⟩ with probability |cᵢ|²
        Returns the action.
        """
        probs = np.abs(self.amplitudes)**2
        probs = probs / probs.sum()  # Ensure normalization

        idx = np.random.choice(self.hilbert.dim, p=probs)
        action = self.hilbert.actions[idx]

        # Collapse state
        self.amplitudes = self.hilbert.get_basis(action).copy()

        return action

    def expectation(self, observable: 'Operator') -> complex:
        """⟨ψ|Ô|ψ⟩."""
        return observable.expectation(self)

    def purity(self) -> float:
        """For a pure state, purity = 1."""
        return 1.0  # Pure states always have purity 1


# ============================================================================
# OPERATORS - Observables and Evolution
# ============================================================================

class Operator:
    """
    Linear operator on Hilbert space.

    Represented as N×N matrix.
    For observables: Hermitian (Ô = Ô†)
    For evolution: Unitary (Û†Û = I)
    """

    def __init__(self, hilbert: HilbertSpace, matrix: np.ndarray):
        self.hilbert = hilbert
        self.matrix = matrix.astype(complex)

    @classmethod
    def from_diagonal(cls, hilbert: HilbertSpace, values: Dict[str, float]) -> 'Operator':
        """Create diagonal operator Ô = Σᵢ vᵢ|aᵢ⟩⟨aᵢ|."""
        mat = np.zeros((hilbert.dim, hilbert.dim), dtype=complex)
        for action, val in values.items():
            if action in hilbert.action_to_idx:
                idx = hilbert.action_to_idx[action]
                mat[idx, idx] = val
        return cls(hilbert, mat)

    @classmethod
    def identity(cls, hilbert: HilbertSpace) -> 'Operator':
        """Identity operator."""
        return cls(hilbert, np.eye(hilbert.dim, dtype=complex))

    def __matmul__(self, other: 'Operator') -> 'Operator':
        """Operator composition Â @ B̂ = ÂB̂."""
        return Operator(self.hilbert, self.matrix @ other.matrix)

    def __add__(self, other: 'Operator') -> 'Operator':
        """Operator addition."""
        return Operator(self.hilbert, self.matrix + other.matrix)

    def __mul__(self, scalar: complex) -> 'Operator':
        """Scalar multiplication."""
        return Operator(self.hilbert, scalar * self.matrix)

    def __rmul__(self, scalar: complex) -> 'Operator':
        return self.__mul__(scalar)

    def dagger(self) -> 'Operator':
        """Hermitian conjugate Ô†."""
        return Operator(self.hilbert, self.matrix.conj().T)

    def is_hermitian(self, tol: float = 1e-10) -> bool:
        """Check if Ô = Ô†."""
        return np.allclose(self.matrix, self.matrix.conj().T, atol=tol)

    def is_unitary(self, tol: float = 1e-10) -> bool:
        """Check if Ô†Ô = I."""
        prod = self.dagger().matrix @ self.matrix
        return np.allclose(prod, np.eye(self.hilbert.dim), atol=tol)

    def apply(self, state: QuantumState) -> QuantumState:
        """Apply operator to state: Ô|ψ⟩."""
        new_amp = self.matrix @ state.amplitudes
        return QuantumState(self.hilbert, new_amp)

    def expectation(self, state: QuantumState) -> complex:
        """⟨ψ|Ô|ψ⟩."""
        return np.vdot(state.amplitudes, self.matrix @ state.amplitudes)

    def commutator(self, other: 'Operator') -> 'Operator':
        """[Â, B̂] = ÂB̂ - B̂Â."""
        return (self @ other) + (-1.0) * (other @ self)

    def eigenvalues(self) -> np.ndarray:
        """Get eigenvalues."""
        return np.linalg.eigvalsh(self.matrix) if self.is_hermitian() else np.linalg.eigvals(self.matrix)


# ============================================================================
# DENSITY MATRIX - Mixed States (Classical + Quantum Uncertainty)
# ============================================================================

class DensityMatrix:
    """
    ρ = Σᵢ pᵢ |ψᵢ⟩⟨ψᵢ|

    For pure state: ρ = |ψ⟩⟨ψ|, Tr(ρ²) = 1
    For mixed state: Tr(ρ²) < 1

    Key insight: Density matrix captures BOTH
    - Quantum superposition (off-diagonal coherence)
    - Classical uncertainty (statistical mixture)
    """

    def __init__(self, hilbert: HilbertSpace, matrix: np.ndarray = None):
        self.hilbert = hilbert
        if matrix is None:
            # Default: maximally mixed state
            self.matrix = np.eye(hilbert.dim, dtype=complex) / hilbert.dim
        else:
            self.matrix = matrix.astype(complex)

    @classmethod
    def from_pure_state(cls, state: QuantumState) -> 'DensityMatrix':
        """ρ = |ψ⟩⟨ψ|."""
        outer = np.outer(state.amplitudes, state.amplitudes.conj())
        return cls(state.hilbert, outer)

    @classmethod
    def from_mixture(cls, hilbert: HilbertSpace,
                     states_and_probs: List[Tuple[QuantumState, float]]) -> 'DensityMatrix':
        """ρ = Σᵢ pᵢ |ψᵢ⟩⟨ψᵢ|."""
        mat = np.zeros((hilbert.dim, hilbert.dim), dtype=complex)
        for state, prob in states_and_probs:
            outer = np.outer(state.amplitudes, state.amplitudes.conj())
            mat += prob * outer
        return cls(hilbert, mat)

    @classmethod
    def from_classical_probs(cls, hilbert: HilbertSpace, probs: Dict[str, float]) -> 'DensityMatrix':
        """Classical mixture of basis states (no coherence)."""
        mat = np.zeros((hilbert.dim, hilbert.dim), dtype=complex)
        for action, prob in probs.items():
            if action in hilbert.action_to_idx:
                idx = hilbert.action_to_idx[action]
                mat[idx, idx] = prob
        return cls(hilbert, mat)

    def trace(self) -> complex:
        """Tr(ρ) - should be 1."""
        return np.trace(self.matrix)

    def purity(self) -> float:
        """
        γ = Tr(ρ²)

        γ = 1: pure state (no classical uncertainty)
        γ = 1/N: maximally mixed
        """
        return float(np.real(np.trace(self.matrix @ self.matrix)))

    def von_neumann_entropy(self) -> float:
        """
        S = -Tr(ρ log ρ)

        S = 0: pure state
        S = log(N): maximally mixed
        """
        eigenvalues = np.linalg.eigvalsh(self.matrix)
        eigenvalues = eigenvalues[eigenvalues > 1e-15]  # Remove zeros
        return -float(np.sum(eigenvalues * np.log(eigenvalues)))

    def coherence(self) -> float:
        """
        Measure of quantum coherence (off-diagonal elements).

        C = Σᵢ≠ⱼ |ρᵢⱼ|

        C = 0: classical (diagonal)
        C > 0: quantum coherence
        """
        off_diag = self.matrix.copy()
        np.fill_diagonal(off_diag, 0)
        return float(np.sum(np.abs(off_diag)))

    def probabilities(self) -> Dict[str, float]:
        """Diagonal elements = measurement probabilities."""
        return {
            self.hilbert.actions[i]: float(np.real(self.matrix[i, i]))
            for i in range(self.hilbert.dim)
        }

    def expectation(self, operator: Operator) -> complex:
        """Tr(ρÔ)."""
        return np.trace(self.matrix @ operator.matrix)

    def measure(self) -> str:
        """
        Measurement collapses to basis state.

        Returns action, modifies self to collapsed state.
        """
        probs = np.real(np.diag(self.matrix))
        probs = probs / probs.sum()

        idx = np.random.choice(self.hilbert.dim, p=probs)
        action = self.hilbert.actions[idx]

        # Collapse to pure state
        self.matrix = np.zeros_like(self.matrix)
        self.matrix[idx, idx] = 1.0

        return action

    def decohere(self, rate: float = 0.1) -> 'DensityMatrix':
        """
        Apply decoherence - destroys off-diagonal coherence.

        Models interaction with environment that measures the system.
        Quantum → Classical transition.
        """
        new_mat = self.matrix.copy()
        for i in range(self.hilbert.dim):
            for j in range(self.hilbert.dim):
                if i != j:
                    new_mat[i, j] *= (1 - rate)
        return DensityMatrix(self.hilbert, new_mat)


# ============================================================================
# HAMILTONIAN & TIME EVOLUTION
# ============================================================================

class Hamiltonian(Operator):
    """
    Ĥ - Energy operator, generates time evolution.

    Must be Hermitian.

    For decision systems:
    - Diagonal elements: "energy" of each action (negative of value?)
    - Off-diagonal elements: "tunneling" between actions
    """

    def __init__(self, hilbert: HilbertSpace, matrix: np.ndarray):
        super().__init__(hilbert, matrix)
        if not self.is_hermitian():
            # Force Hermitian by symmetrization
            self.matrix = (self.matrix + self.matrix.conj().T) / 2

    @classmethod
    def from_values(cls, hilbert: HilbertSpace, values: Dict[str, float],
                    tunneling: float = 0.0) -> 'Hamiltonian':
        """
        Create Hamiltonian with:
        - Diagonal: action values (as negative energies - lower energy = better)
        - Off-diagonal: tunneling strength
        """
        mat = np.zeros((hilbert.dim, hilbert.dim), dtype=complex)

        # Diagonal: -value (so higher value = lower energy = more likely)
        for action, val in values.items():
            if action in hilbert.action_to_idx:
                idx = hilbert.action_to_idx[action]
                mat[idx, idx] = -val

        # Off-diagonal: tunneling (uniform for simplicity)
        if tunneling > 0:
            for i in range(hilbert.dim):
                for j in range(hilbert.dim):
                    if i != j:
                        mat[i, j] = tunneling

        return cls(hilbert, mat)

    def evolution_operator(self, dt: float, hbar: float = 1.0) -> Operator:
        """
        Û(dt) = exp(-iĤdt/ℏ)

        Unitary time evolution operator.
        """
        # Matrix exponential
        U = np.linalg.matrix_power(
            np.eye(self.hilbert.dim) - 1j * self.matrix * dt / hbar,
            1
        )
        # More accurate: use scipy.linalg.expm
        # For small dt, first-order approx is ok

        # Actually use eigendecomposition for exactness
        eigenvalues, eigenvectors = np.linalg.eigh(self.matrix)
        exp_diag = np.diag(np.exp(-1j * eigenvalues * dt / hbar))
        U = eigenvectors @ exp_diag @ eigenvectors.conj().T

        return Operator(self.hilbert, U)

    def evolve_state(self, state: QuantumState, dt: float, hbar: float = 1.0) -> QuantumState:
        """Evolve pure state: |ψ(t+dt)⟩ = Û(dt)|ψ(t)⟩."""
        U = self.evolution_operator(dt, hbar)
        return U.apply(state)

    def evolve_density(self, rho: DensityMatrix, dt: float, hbar: float = 1.0) -> DensityMatrix:
        """Evolve density matrix: ρ(t+dt) = Û ρ(t) Û†."""
        U = self.evolution_operator(dt, hbar)
        U_dag = U.dagger()
        new_mat = U.matrix @ rho.matrix @ U_dag.matrix
        return DensityMatrix(self.hilbert, new_mat)


# ============================================================================
# COMPOSITE SYSTEMS & ENTANGLEMENT
# ============================================================================

class CompositeSystem:
    """
    Tensor product of multiple Hilbert spaces.

    H_AB = H_A ⊗ H_B

    For multiple positions/portfolios.
    """

    def __init__(self, subsystems: List[HilbertSpace]):
        self.subsystems = subsystems
        self.dims = [h.dim for h in subsystems]
        self.total_dim = np.prod(self.dims)

        # Combined action labels
        self._build_combined_basis()

    def _build_combined_basis(self):
        """Build tensor product basis."""
        from itertools import product

        action_lists = [h.actions for h in self.subsystems]
        self.combined_actions = list(product(*action_lists))
        self.combined_hilbert = HilbertSpace([str(a) for a in self.combined_actions])

    def tensor_product_state(self, states: List[QuantumState]) -> QuantumState:
        """
        |ψ_A⟩ ⊗ |ψ_B⟩ ⊗ ...

        Tensor product of individual states.
        """
        result = states[0].amplitudes
        for state in states[1:]:
            result = np.kron(result, state.amplitudes)
        return QuantumState(self.combined_hilbert, result)

    def is_separable(self, state: QuantumState, tol: float = 1e-10) -> bool:
        """
        Check if state is separable (not entangled).

        |ψ⟩ = |ψ_A⟩ ⊗ |ψ_B⟩?

        For 2 subsystems only (general case is NP-hard).
        """
        if len(self.subsystems) != 2:
            return None  # Not implemented for >2

        # Reshape into matrix
        d1, d2 = self.dims[0], self.dims[1]
        mat = state.amplitudes.reshape(d1, d2)

        # Check rank - separable iff rank 1
        _, s, _ = np.linalg.svd(mat)
        return np.sum(s > tol) == 1

    def entanglement_entropy(self, state: QuantumState, subsystem_idx: int = 0) -> float:
        """
        Entanglement entropy S_A = -Tr(ρ_A log ρ_A).

        Where ρ_A = Tr_B(|ψ⟩⟨ψ|) is reduced density matrix.

        S = 0: separable
        S > 0: entangled
        """
        if len(self.subsystems) != 2:
            return 0  # Not implemented for >2

        d1, d2 = self.dims[0], self.dims[1]
        mat = state.amplitudes.reshape(d1, d2)

        # Reduced density matrix for subsystem 0
        if subsystem_idx == 0:
            rho_reduced = mat @ mat.conj().T
        else:
            rho_reduced = mat.T @ mat.conj()

        # Von Neumann entropy
        eigenvalues = np.linalg.eigvalsh(rho_reduced)
        eigenvalues = eigenvalues[eigenvalues > 1e-15]
        return -float(np.sum(eigenvalues * np.log(eigenvalues)))


# ============================================================================
# TRUE QUANTUM DECISION SYSTEM
# ============================================================================

class TrueQuantumDecision:
    """
    Decision system built from QM first principles.

    Actions form basis of Hilbert space.
    Superposition = considering multiple actions simultaneously.
    Measurement = making a decision (collapses state).
    Entanglement = correlated decisions across positions.
    """

    def __init__(self, actions: List[str], values: Dict[str, float] = None):
        """
        Initialize with available actions.

        Args:
            actions: List of action names (basis states)
            values: Expected value for each action
        """
        self.hilbert = HilbertSpace(actions)
        self.values = values or {a: 0.0 for a in actions}

        # Current state (starts in uniform superposition)
        self.state = QuantumState.uniform_superposition(self.hilbert)

        # Or as density matrix for mixed states
        self.rho = DensityMatrix.from_pure_state(self.state)

        # Value observable
        self.value_operator = Operator.from_diagonal(self.hilbert, self.values)

        # Hamiltonian for evolution
        self.hamiltonian = Hamiltonian.from_values(self.hilbert, self.values, tunneling=0.1)

        # History
        self.history: List[Dict] = []

    def set_state_from_scores(self, scores: Dict[str, float]):
        """
        Set quantum state where amplitude ~ score.

        Higher score = higher probability.
        """
        # Normalize scores to probabilities
        total = sum(scores.values())
        if total > 0:
            probs = {a: s/total for a, s in scores.items()}
        else:
            probs = {a: 1/len(scores) for a in scores}

        self.state = QuantumState.from_probabilities(self.hilbert, probs)
        self.rho = DensityMatrix.from_pure_state(self.state)

    def evolve(self, dt: float = 0.1):
        """Unitary evolution via Schrödinger equation."""
        self.state = self.hamiltonian.evolve_state(self.state, dt)
        self.rho = self.hamiltonian.evolve_density(self.rho, dt)

    def decohere(self, rate: float = 0.1):
        """Apply decoherence (quantum → classical)."""
        self.rho = self.rho.decohere(rate)

    def expected_value(self) -> float:
        """⟨V̂⟩ = Tr(ρV̂)."""
        return float(np.real(self.rho.expectation(self.value_operator)))

    def decide(self) -> Tuple[str, float]:
        """
        Make decision (measurement).

        Returns: (action, value of that action)
        """
        action = self.rho.measure()
        value = self.values.get(action, 0.0)

        self.history.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "value": value,
            "purity_before": self.rho.purity(),
        })

        return action, value

    def status(self) -> Dict:
        """Get current quantum status."""
        return {
            "actions": self.hilbert.actions,
            "probabilities": self.rho.probabilities(),
            "expected_value": self.expected_value(),
            "purity": self.rho.purity(),
            "entropy": self.rho.von_neumann_entropy(),
            "coherence": self.rho.coherence(),
            "n_measurements": len(self.history),
        }

    def print_status(self):
        """Print quantum status."""
        s = self.status()
        print("=" * 60)
        print("TRUE QUANTUM DECISION SYSTEM")
        print("=" * 60)

        print(f"\nActions: {len(s['actions'])}")
        print(f"Expected value: ${s['expected_value']:.2f}")
        print(f"Purity: {s['purity']:.3f} (1=pure, 1/N=mixed)")
        print(f"Entropy: {s['entropy']:.3f}")
        print(f"Coherence: {s['coherence']:.3f} (0=classical, >0=quantum)")

        print("\nProbabilities:")
        for action, prob in sorted(s['probabilities'].items(), key=lambda x: -x[1])[:10]:
            bar = "█" * int(prob * 40)
            print(f"  {prob:5.1%} | {action[:30]:<30} {bar}")

        print("=" * 60)


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TRUE QUANTUM DECISION SYSTEM - FROM QM FIRST PRINCIPLES")
    print("=" * 70)

    # Define actions and their values
    actions = ["hold", "hedge_50", "hedge_25", "buy_more", "sell_half"]
    values = {
        "hold": 1000,
        "hedge_50": 930,
        "hedge_25": 965,
        "buy_more": 1100,
        "sell_half": 850,
    }

    # Create system
    qds = TrueQuantumDecision(actions, values)

    print("\n1. INITIAL STATE (uniform superposition)")
    qds.print_status()

    # Set state from scores (like nexus cloud)
    scores = {
        "hold": 150,
        "hedge_50": 173,  # Highest score
        "hedge_25": 160,
        "buy_more": 120,
        "sell_half": 100,
    }
    qds.set_state_from_scores(scores)

    print("\n2. STATE FROM SCORES")
    qds.print_status()

    # Evolve (quantum dynamics)
    print("\n3. QUANTUM EVOLUTION (10 steps)")
    for _ in range(10):
        qds.evolve(dt=0.1)
    qds.print_status()

    # Decoherence (quantum → classical)
    print("\n4. DECOHERENCE (environment interaction)")
    for _ in range(5):
        qds.decohere(rate=0.3)
    qds.print_status()

    # Decision (measurement)
    print("\n5. DECISION (measurement collapse)")
    action, value = qds.decide()
    print(f"   COLLAPSED TO: {action}")
    print(f"   Value: ${value:.2f}")

    # Monte Carlo
    print("\n6. MONTE CARLO (100 runs)")
    from collections import Counter
    counts = Counter()
    for _ in range(100):
        q = TrueQuantumDecision(actions, values)
        q.set_state_from_scores(scores)
        for _ in range(10):
            q.evolve(dt=0.1)
        a, _ = q.decide()
        counts[a] += 1

    print("   Distribution:")
    for a, c in counts.most_common():
        print(f"     {c:3d}% | {a}")

    print("\n" + "=" * 70)
    print("This is ACTUAL quantum mechanics applied to decisions")
    print("=" * 70)
