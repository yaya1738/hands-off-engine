#!/usr/bin/env python3
"""
QUANTUM HANDS-OFF SYSTEM - True QM for System Decisions

Not trading - the system itself.

Hilbert spaces:
- H_agent: {idle, working, blocked, complete}
- H_task: {task_1, task_2, ..., task_n}
- H_total = H_agent ⊗ H_task

Key QM features used:
- Superposition: considering multiple tasks simultaneously
- Interference: contradictory tasks cancel
- Decoherence: options close over time (deadline pressure)
- Entanglement: correlated agent decisions
- Tunneling: spontaneous task transitions

Created by: Yair Siegel
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import math
from datetime import datetime, timezone
from pathlib import Path
import json

# Import our true QM foundation
from executor.math.true_quantum_decision import (
    HilbertSpace, QuantumState, Operator, DensityMatrix,
    Hamiltonian, CompositeSystem
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "quantum_handsoff_state.json"


# ============================================================================
# AGENT STATES
# ============================================================================

AGENT_STATES = ["idle", "working", "blocked", "complete"]


# ============================================================================
# TASK QUANTUM STATE
# ============================================================================

@dataclass
class Task:
    """A task in the hands-off system."""
    name: str
    value: float  # How valuable completing this is
    urgency: float  # Time pressure
    complexity: float  # How hard (affects decoherence rate)

    # For interference: tasks with same "type" can interfere
    task_type: str = "general"  # general, income, maintenance, research


class TaskHilbertSpace(HilbertSpace):
    """Hilbert space specialized for tasks."""

    def __init__(self, tasks: List[Task]):
        self.tasks = {t.name: t for t in tasks}
        super().__init__([t.name for t in tasks])

    def get_task(self, name: str) -> Optional[Task]:
        return self.tasks.get(name)

    def value_operator(self) -> Operator:
        """V̂ = Σⱼ valueⱼ |taskⱼ⟩⟨taskⱼ|"""
        values = {t.name: t.value for t in self.tasks.values()}
        return Operator.from_diagonal(self, values)

    def urgency_operator(self) -> Operator:
        """Û = Σⱼ urgencyⱼ |taskⱼ⟩⟨taskⱼ|"""
        urgencies = {t.name: t.urgency for t in self.tasks.values()}
        return Operator.from_diagonal(self, urgencies)


# ============================================================================
# QUANTUM HANDS-OFF SYSTEM
# ============================================================================

class QuantumHandsOff:
    """
    The hands-off system modeled as a quantum system.

    State: |ψ⟩ ∈ H_task
    Observable: which task to work on
    Evolution: Hamiltonian driven by value/urgency
    Collapse: actually starting a task
    """

    def __init__(self, tasks: List[Task] = None):
        """Initialize with tasks."""
        self.tasks = tasks or self._default_tasks()
        self.hilbert = TaskHilbertSpace(self.tasks)

        # Quantum state - start in uniform superposition
        self.state = QuantumState.uniform_superposition(self.hilbert)

        # Density matrix for mixed states
        self.rho = DensityMatrix.from_pure_state(self.state)

        # Build Hamiltonian
        self._build_hamiltonian()

        # Decoherence rate (environment measuring us)
        self.decoherence_rate = 0.1

        # History
        self.history: List[Dict] = []
        self.time = 0.0

    def _default_tasks(self) -> List[Task]:
        """Default hands-off tasks."""
        return [
            Task("pursue_income", value=100, urgency=0.8, complexity=0.7, task_type="income"),
            Task("fix_bugs", value=30, urgency=0.5, complexity=0.4, task_type="maintenance"),
            Task("self_heal", value=50, urgency=0.6, complexity=0.3, task_type="maintenance"),
            Task("research", value=40, urgency=0.2, complexity=0.5, task_type="research"),
            Task("rest", value=10, urgency=0.1, complexity=0.1, task_type="general"),
            Task("coordinate", value=60, urgency=0.7, complexity=0.6, task_type="general"),
        ]

    def _build_hamiltonian(self):
        """
        Build Hamiltonian for system evolution.

        Ĥ = -Σⱼ (valueⱼ + urgencyⱼ) |taskⱼ⟩⟨taskⱼ|  # Diagonal: pulls to high-value
          + Σⱼₖ tunnelingⱼₖ |taskⱼ⟩⟨taskₖ|          # Off-diagonal: task transitions
        """
        dim = self.hilbert.dim
        H = np.zeros((dim, dim), dtype=complex)

        # Diagonal: -(value + urgency) so high value = low energy = favored
        for i, task_name in enumerate(self.hilbert.actions):
            task = self.hilbert.get_task(task_name)
            H[i, i] = -(task.value + task.urgency * 50)  # Scale urgency

        # Off-diagonal: tunneling between tasks of same type
        for i, task_i in enumerate(self.hilbert.actions):
            for j, task_j in enumerate(self.hilbert.actions):
                if i != j:
                    t_i = self.hilbert.get_task(task_i)
                    t_j = self.hilbert.get_task(task_j)

                    # Same type = easier tunneling
                    if t_i.task_type == t_j.task_type:
                        H[i, j] = 5.0  # Strong tunneling
                    else:
                        H[i, j] = 1.0  # Weak tunneling

        self.hamiltonian = Hamiltonian(self.hilbert, H)

    def add_task(self, task: Task):
        """Add a new task to the system."""
        self.tasks.append(task)
        self.hilbert = TaskHilbertSpace(self.tasks)

        # Expand state to include new task (zero amplitude initially)
        old_amp = self.state.amplitudes
        new_amp = np.zeros(self.hilbert.dim, dtype=complex)
        new_amp[:len(old_amp)] = old_amp
        self.state = QuantumState(self.hilbert, new_amp)

        # Rebuild Hamiltonian
        self._build_hamiltonian()

    def set_priority(self, task_name: str, boost: float):
        """
        Boost a task's amplitude (like applying attention).

        This is like a "soft measurement" - increases probability
        without full collapse.
        """
        if task_name not in self.hilbert.action_to_idx:
            return

        idx = self.hilbert.action_to_idx[task_name]

        # Boost amplitude
        self.state.amplitudes[idx] *= (1 + boost)

        # Renormalize
        norm = self.hilbert.norm(self.state.amplitudes)
        self.state.amplitudes /= norm

        # Update density matrix
        self.rho = DensityMatrix.from_pure_state(self.state)

    def interfere(self, task_a: str, task_b: str, phase: float = np.pi):
        """
        Set relative phase between tasks.

        phase = π: destructive interference (contradictory tasks)
        phase = 0: constructive interference (synergistic tasks)
        """
        if task_a not in self.hilbert.action_to_idx:
            return
        if task_b not in self.hilbert.action_to_idx:
            return

        idx_b = self.hilbert.action_to_idx[task_b]

        # Apply phase to task_b relative to task_a
        self.state.amplitudes[idx_b] *= np.exp(1j * phase)

        # Update density matrix
        self.rho = DensityMatrix.from_pure_state(self.state)

    def evolve(self, dt: float = 0.1):
        """
        Evolve the quantum state.

        1. Unitary evolution via Hamiltonian
        2. Decoherence from environment
        """
        # Unitary evolution
        self.state = self.hamiltonian.evolve_state(self.state, dt)
        self.rho = self.hamiltonian.evolve_density(self.rho, dt)

        # Decoherence
        self.rho = self.rho.decohere(self.decoherence_rate * dt)

        self.time += dt

    def measure(self) -> str:
        """
        Measure the system - collapse to a specific task.

        This is "deciding what to work on".
        Returns task name.
        """
        task = self.rho.measure()

        self.history.append({
            "time": self.time,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "collapsed_to": task,
            "task_value": self.hilbert.get_task(task).value if task else 0,
        })

        return task

    def expected_value(self) -> float:
        """⟨V̂⟩ - expected value of current state."""
        V = self.hilbert.value_operator()
        return float(np.real(self.rho.expectation(V)))

    def coherence(self) -> float:
        """How quantum is the current state."""
        return self.rho.coherence()

    def purity(self) -> float:
        """How pure is the state (1=pure, 1/N=mixed)."""
        return self.rho.purity()

    def entropy(self) -> float:
        """Von Neumann entropy."""
        return self.rho.von_neumann_entropy()

    def probabilities(self) -> Dict[str, float]:
        """Get task probabilities."""
        return self.rho.probabilities()

    def status(self) -> Dict:
        """Full quantum status."""
        probs = self.probabilities()

        return {
            "time": self.time,
            "n_tasks": len(self.tasks),
            "expected_value": self.expected_value(),
            "purity": self.purity(),
            "entropy": self.entropy(),
            "coherence": self.coherence(),
            "probabilities": probs,
            "top_task": max(probs, key=probs.get) if probs else None,
            "top_prob": max(probs.values()) if probs else 0,
            "n_measurements": len(self.history),
        }

    def print_status(self):
        """Print quantum status."""
        s = self.status()

        print("=" * 60)
        print(f"QUANTUM HANDS-OFF SYSTEM  [t={s['time']:.1f}]")
        print("=" * 60)

        print(f"\nTasks: {s['n_tasks']}")
        print(f"Expected value: {s['expected_value']:.1f}")
        print(f"Purity: {s['purity']:.3f}  (1=pure, 1/N={1/s['n_tasks']:.3f}=mixed)")
        print(f"Entropy: {s['entropy']:.3f}")
        print(f"Coherence: {s['coherence']:.3f}  (0=classical, >0=quantum)")

        print(f"\nTask probabilities:")
        for task, prob in sorted(s['probabilities'].items(), key=lambda x: -x[1]):
            t = self.hilbert.get_task(task)
            bar = "█" * int(prob * 30)
            print(f"  {prob:5.1%} | {task:<20} (V={t.value:3.0f}, U={t.urgency:.1f}) {bar}")

        print("=" * 60)

    def save(self):
        """Save state to file."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "time": self.time,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tasks": [
                {
                    "name": t.name,
                    "value": t.value,
                    "urgency": t.urgency,
                    "complexity": t.complexity,
                    "task_type": t.task_type,
                }
                for t in self.tasks
            ],
            "probabilities": self.probabilities(),
            "status": self.status(),
            "history": self.history[-100:],  # Last 100
        }

        with open(STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls) -> 'QuantumHandsOff':
        """Load from file."""
        if not STATE_FILE.exists():
            return cls()

        with open(STATE_FILE) as f:
            data = json.load(f)

        tasks = [
            Task(**t) for t in data.get("tasks", [])
        ]

        qho = cls(tasks)
        qho.time = data.get("time", 0)
        qho.history = data.get("history", [])

        return qho


# ============================================================================
# ENTANGLED AGENTS
# ============================================================================

class EntangledAgents:
    """
    Multiple agents that are quantum entangled.

    If agent A is working, agent B must be idle.
    This is modeled as entanglement - measuring one collapses the other.
    """

    def __init__(self, agent_names: List[str]):
        self.agent_names = agent_names

        # Each agent has a state space
        self.agent_hilbert = HilbertSpace(AGENT_STATES)

        # Composite system
        self.composite = CompositeSystem([self.agent_hilbert] * len(agent_names))

        # Start in maximally entangled state
        # |ψ⟩ = (1/√2)(|working_A, idle_B⟩ + |idle_A, working_B⟩)
        self._initialize_entangled()

    def _initialize_entangled(self):
        """Create entangled initial state."""
        if len(self.agent_names) != 2:
            # Only support 2 agents for now
            self.state = QuantumState.uniform_superposition(self.composite.combined_hilbert)
            return

        # Build specific entangled state
        dim = self.composite.total_dim
        amp = np.zeros(dim, dtype=complex)

        # |working, idle⟩
        idx1 = AGENT_STATES.index("working") * len(AGENT_STATES) + AGENT_STATES.index("idle")
        # |idle, working⟩
        idx2 = AGENT_STATES.index("idle") * len(AGENT_STATES) + AGENT_STATES.index("working")

        amp[idx1] = 1/np.sqrt(2)
        amp[idx2] = 1/np.sqrt(2)

        self.state = QuantumState(self.composite.combined_hilbert, amp)

    def measure_agent(self, agent_idx: int) -> str:
        """
        Measure one agent's state.

        This collapses the entangled state!
        """
        probs = np.abs(self.state.amplitudes)**2

        # Marginalize over other agents to get this agent's probabilities
        dim_per_agent = len(AGENT_STATES)
        n_agents = len(self.agent_names)

        # Reshape to tensor
        shape = [dim_per_agent] * n_agents
        tensor = probs.reshape(shape)

        # Sum over all other axes
        axes_to_sum = [i for i in range(n_agents) if i != agent_idx]
        marginal = np.sum(tensor, axis=tuple(axes_to_sum))
        marginal = marginal / marginal.sum()

        # Sample
        result_idx = np.random.choice(dim_per_agent, p=marginal)
        result_state = AGENT_STATES[result_idx]

        # Collapse full state
        # Zero out all amplitudes inconsistent with this measurement
        new_amp = self.state.amplitudes.copy()
        tensor_amp = new_amp.reshape(shape)

        for i in range(dim_per_agent):
            if i != result_idx:
                # Zero this slice
                slices = [slice(None)] * n_agents
                slices[agent_idx] = i
                tensor_amp[tuple(slices)] = 0

        # Renormalize
        new_amp = tensor_amp.flatten()
        norm = np.sqrt(np.sum(np.abs(new_amp)**2))
        if norm > 0:
            new_amp /= norm

        self.state = QuantumState(self.composite.combined_hilbert, new_amp)

        return result_state

    def entanglement_entropy(self) -> float:
        """Measure entanglement between agents."""
        if len(self.agent_names) != 2:
            return 0
        return self.composite.entanglement_entropy(self.state, subsystem_idx=0)


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("QUANTUM HANDS-OFF SYSTEM")
    print("=" * 70)

    # Create system
    qho = QuantumHandsOff()

    print("\n1. INITIAL STATE (uniform superposition)")
    qho.print_status()

    # Evolve
    print("\n2. QUANTUM EVOLUTION (20 steps)")
    for _ in range(20):
        qho.evolve(dt=0.1)
    qho.print_status()

    # Set priority (soft measurement)
    print("\n3. BOOSTING 'pursue_income' (attention)")
    qho.set_priority("pursue_income", boost=2.0)
    qho.print_status()

    # Interference
    print("\n4. INTERFERENCE: 'pursue_income' and 'rest' are contradictory")
    qho.interfere("pursue_income", "rest", phase=np.pi)  # Destructive
    qho.print_status()

    # More evolution
    print("\n5. EVOLUTION WITH DECOHERENCE")
    for _ in range(10):
        qho.evolve(dt=0.1)
    qho.print_status()

    # Decision (measurement)
    print("\n6. DECISION (measurement collapse)")
    task = qho.measure()
    print(f"   COLLAPSED TO: {task}")
    print(f"   Value: {qho.hilbert.get_task(task).value}")

    # Monte Carlo
    print("\n7. MONTE CARLO (100 runs)")
    from collections import Counter
    counts = Counter()
    for _ in range(100):
        q = QuantumHandsOff()
        q.set_priority("pursue_income", boost=2.0)
        q.interfere("pursue_income", "rest", phase=np.pi)
        for _ in range(20):
            q.evolve(dt=0.1)
        t = q.measure()
        counts[t] += 1

    print("   Distribution:")
    for t, c in counts.most_common():
        print(f"     {c:3d}% | {t}")

    # Entangled agents
    print("\n" + "=" * 70)
    print("8. ENTANGLED AGENTS")
    print("=" * 70)

    ent = EntangledAgents(["self_healing", "pursuit"])
    print(f"   Entanglement entropy: {ent.entanglement_entropy():.3f}")
    print(f"   (log(2) = {np.log(2):.3f} = maximally entangled)")

    print("\n   Measuring self_healing agent...")
    state_a = ent.measure_agent(0)
    print(f"   self_healing collapsed to: {state_a}")

    print("\n   Now measuring pursuit agent...")
    state_b = ent.measure_agent(1)
    print(f"   pursuit collapsed to: {state_b}")
    print(f"   (Entanglement ensures they're anti-correlated!)")

    print("\n" + "=" * 70)
    print("QUANTUM HANDS-OFF SYSTEM OPERATIONAL")
    print("=" * 70)
