#!/usr/bin/env python3
"""
INTEGRAFIX METHODOLOGY
======================

The science of wiring islands together.

CORE PRINCIPLE: Islands exist because there are gaps. Gaps exist because:
1. Input ─X─ No receiver (dead end)
2. Output ─X─ No consumer (orphaned)
3. State ─X─ No persistence (ephemeral)
4. Process ─X─ No coordination (blind)

THE INTEGRAFIX EQUATION:
    Integration = Σ(connections) / Σ(potential_connections)

    When Integration → 1.0, the system becomes whole.
    When Integration → 0.0, the system is islands.

THE METHODOLOGY:
1. IDENTIFY - Find all components that should connect
2. MAP - Chart current connections and missing ones
3. WIRE - Create the connection (input→output, state→persist, process→coordinate)
4. TEST - Verify signal flows end-to-end
5. RECURSE - Apply methodology to the methodology itself

CONVERGENCE MODES:
- Exponential: Each fix enables N more fixes (compounding)
- Logarithmic: Diminishing returns as system stabilizes
- Reinforced: Fixes create feedback loops that prevent regression

This file is both documentation AND executable integrafix.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
INTEGRAFIX_STATE = STATE_DIR / "integrafix_state.json"


class GapType(Enum):
    """Types of integration gaps."""
    DEAD_END = "dead_end"          # Input with no receiver
    ORPHANED = "orphaned"          # Output with no consumer
    EPHEMERAL = "ephemeral"        # State not persisted
    BLIND = "blind"                # Process not coordinated
    CIRCULAR = "circular"          # Self-referential (no external input)
    MISSING = "missing"            # Component doesn't exist yet


class ConvergenceMode(Enum):
    """How fixes compound over time."""
    EXPONENTIAL = "exponential"    # Each fix enables N more
    LOGARITHMIC = "logarithmic"    # Diminishing returns
    REINFORCED = "reinforced"      # Feedback loops prevent regression


@dataclass
class Gap:
    """A gap in the integration."""
    id: str
    gap_type: GapType
    source: str                    # Component producing output
    target: str                    # Component that should receive
    description: str
    severity: float                # 0.0 to 1.0
    fix_complexity: float          # 0.0 to 1.0
    dependencies: List[str] = field(default_factory=list)  # Other gaps that must be fixed first
    fixed: bool = False
    fixed_at: Optional[str] = None
    fix_method: Optional[str] = None


@dataclass
class Wire:
    """A connection that integrates two components."""
    id: str
    source: str
    target: str
    wire_type: str                 # "data", "state", "signal", "coordination"
    description: str
    created_at: str
    test_passed: bool = False
    test_result: Optional[str] = None


@dataclass
class IntegrafixResult:
    """Result of applying integrafix methodology."""
    gaps_identified: int
    gaps_fixed: int
    wires_created: int
    integration_score: float       # 0.0 to 1.0
    convergence_mode: ConvergenceMode
    next_fixes: List[str]
    timestamp: str


class IntegrafixMethodology:
    """
    The methodology for wiring islands together.

    This class IS the integrafix - it identifies gaps, creates wires,
    and recursively applies itself to increase integration.
    """

    def __init__(self):
        self.state = self._load_state()
        self.gaps: Dict[str, Gap] = {}
        self.wires: Dict[str, Wire] = {}
        self._load_gaps_and_wires()

    def _load_state(self) -> Dict:
        if INTEGRAFIX_STATE.exists():
            with open(INTEGRAFIX_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "integration_history": [],
            "total_gaps_fixed": 0,
            "total_wires_created": 0,
            "current_integration_score": 0.0,
            "methodology_version": "1.0.0",
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        # Convert gaps with proper enum serialization
        self.state["gaps"] = {}
        for k, v in self.gaps.items():
            gap_dict = asdict(v)
            gap_dict["gap_type"] = v.gap_type.value  # Convert enum to string
            self.state["gaps"][k] = gap_dict
        # Convert wires
        self.state["wires"] = {k: asdict(v) for k, v in self.wires.items()}
        with open(INTEGRAFIX_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_gaps_and_wires(self):
        """Load existing gaps and wires from state."""
        for gap_id, gap_data in self.state.get("gaps", {}).items():
            gap_data["gap_type"] = GapType(gap_data["gap_type"])
            self.gaps[gap_id] = Gap(**gap_data)
        for wire_id, wire_data in self.state.get("wires", {}).items():
            self.wires[wire_id] = Wire(**wire_data)

    def _generate_id(self, prefix: str, source: str, target: str) -> str:
        """Generate unique ID for gap or wire."""
        content = f"{prefix}:{source}:{target}:{datetime.now().isoformat()}"
        return f"{prefix}_{hashlib.md5(content.encode()).hexdigest()[:8]}"

    # ==================== PHASE 1: IDENTIFY ====================

    def identify_gaps(self, components: Dict[str, Any]) -> List[Gap]:
        """
        Identify all integration gaps in the system.

        Args:
            components: Dict mapping component names to their metadata
                       Each component should have: inputs, outputs, state, coordinates_with
        """
        identified = []

        # Check each component
        for name, meta in components.items():
            inputs = meta.get("inputs", [])
            outputs = meta.get("outputs", [])
            state_fields = meta.get("state", [])
            coordinates = meta.get("coordinates_with", [])

            # Check for orphaned outputs (output with no consumer)
            for output in outputs:
                consumers = [
                    c for c, m in components.items()
                    if output in m.get("inputs", []) and c != name
                ]
                if not consumers:
                    gap = Gap(
                        id=self._generate_id("gap", name, output),
                        gap_type=GapType.ORPHANED,
                        source=name,
                        target=output,
                        description=f"{name} produces '{output}' but nothing consumes it",
                        severity=0.7,
                        fix_complexity=0.3,
                    )
                    identified.append(gap)
                    self.gaps[gap.id] = gap

            # Check for dead end inputs (input with no producer)
            for input_name in inputs:
                producers = [
                    c for c, m in components.items()
                    if input_name in m.get("outputs", []) and c != name
                ]
                if not producers:
                    gap = Gap(
                        id=self._generate_id("gap", input_name, name),
                        gap_type=GapType.DEAD_END,
                        source=input_name,
                        target=name,
                        description=f"{name} expects '{input_name}' but nothing produces it",
                        severity=0.8,
                        fix_complexity=0.5,
                    )
                    identified.append(gap)
                    self.gaps[gap.id] = gap

            # Check for coordination gaps
            for coord_target in coordinates:
                if coord_target not in components:
                    gap = Gap(
                        id=self._generate_id("gap", name, coord_target),
                        gap_type=GapType.BLIND,
                        source=name,
                        target=coord_target,
                        description=f"{name} should coordinate with {coord_target} but can't",
                        severity=0.9,
                        fix_complexity=0.6,
                    )
                    identified.append(gap)
                    self.gaps[gap.id] = gap

        return identified

    def identify_circular_gaps(self, analysis_functions: Dict[str, Callable]) -> List[Gap]:
        """
        Identify circular/self-referential gaps.

        These are the hardest to find - where a component uses its own
        output as input, creating no real signal.
        """
        identified = []

        for name, analyze_fn in analysis_functions.items():
            try:
                # Try to detect circular reference
                result = analyze_fn()
                if result.get("is_circular", False):
                    gap = Gap(
                        id=self._generate_id("gap", name, "self"),
                        gap_type=GapType.CIRCULAR,
                        source=name,
                        target=name,
                        description=f"{name} uses its own output as input - no external signal",
                        severity=1.0,  # Critical - this breaks everything downstream
                        fix_complexity=0.7,
                    )
                    identified.append(gap)
                    self.gaps[gap.id] = gap
            except Exception:
                pass

        return identified

    # ==================== PHASE 2: MAP ====================

    def map_connections(self, components: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Map all current and potential connections.

        Returns:
            Dict with keys: "existing", "potential", "blocked"
        """
        existing = []
        potential = []
        blocked = []

        for name, meta in components.items():
            outputs = meta.get("outputs", [])
            for output in outputs:
                for other_name, other_meta in components.items():
                    if other_name == name:
                        continue
                    if output in other_meta.get("inputs", []):
                        # Check if wire exists
                        wire_id = f"{name}:{output}:{other_name}"
                        if wire_id in [f"{w.source}:{w.wire_type}:{w.target}" for w in self.wires.values()]:
                            existing.append(wire_id)
                        else:
                            potential.append(wire_id)

        # Check for blocked connections (gaps that prevent wiring)
        for gap in self.gaps.values():
            if not gap.fixed:
                blocked.append(f"{gap.source}→{gap.target}")

        return {
            "existing": existing,
            "potential": potential,
            "blocked": blocked,
            "integration_ratio": len(existing) / max(1, len(existing) + len(potential)),
        }

    # ==================== PHASE 3: WIRE ====================

    def create_wire(
        self,
        source: str,
        target: str,
        wire_type: str,
        description: str,
        implementation: Optional[Callable] = None,
    ) -> Wire:
        """
        Create a wire connecting two components.

        Args:
            source: Component producing the output
            target: Component consuming the input
            wire_type: "data", "state", "signal", or "coordination"
            description: What this wire does
            implementation: Optional function that implements the wire
        """
        wire = Wire(
            id=self._generate_id("wire", source, target),
            source=source,
            target=target,
            wire_type=wire_type,
            description=description,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # If implementation provided, test it
        if implementation:
            try:
                result = implementation()
                wire.test_passed = result.get("success", False)
                wire.test_result = str(result)
            except Exception as e:
                wire.test_passed = False
                wire.test_result = str(e)

        self.wires[wire.id] = wire
        self.state["total_wires_created"] += 1
        self._save_state()

        return wire

    def fix_gap(self, gap_id: str, fix_method: str, implementation: Optional[Callable] = None) -> bool:
        """
        Fix a gap by implementing the solution.

        Args:
            gap_id: ID of the gap to fix
            fix_method: Description of how it was fixed
            implementation: Optional function that implements the fix
        """
        if gap_id not in self.gaps:
            return False

        gap = self.gaps[gap_id]

        # Check dependencies
        for dep_id in gap.dependencies:
            if dep_id in self.gaps and not self.gaps[dep_id].fixed:
                return False  # Dependency not fixed yet

        # Run implementation if provided
        if implementation:
            try:
                result = implementation()
                if not result.get("success", False):
                    return False
            except Exception:
                return False

        gap.fixed = True
        gap.fixed_at = datetime.now(timezone.utc).isoformat()
        gap.fix_method = fix_method
        self.state["total_gaps_fixed"] += 1
        self._save_state()

        return True

    # ==================== PHASE 4: TEST ====================

    def test_wire(self, wire_id: str, test_fn: Callable) -> bool:
        """
        Test that a wire is working.

        Args:
            wire_id: ID of wire to test
            test_fn: Function that returns {"success": bool, ...}
        """
        if wire_id not in self.wires:
            return False

        wire = self.wires[wire_id]
        try:
            result = test_fn()
            wire.test_passed = result.get("success", False)
            wire.test_result = str(result)
        except Exception as e:
            wire.test_passed = False
            wire.test_result = str(e)

        self._save_state()
        return wire.test_passed

    def test_all_wires(self, test_fns: Dict[str, Callable]) -> Dict[str, bool]:
        """Test all wires."""
        results = {}
        for wire_id, wire in self.wires.items():
            key = f"{wire.source}:{wire.target}"
            if key in test_fns:
                results[wire_id] = self.test_wire(wire_id, test_fns[key])
            else:
                results[wire_id] = wire.test_passed
        return results

    # ==================== PHASE 5: RECURSE ====================

    def calculate_integration_score(self) -> float:
        """
        Calculate current integration score.

        Score = (fixed_gaps + working_wires) / (total_gaps + potential_wires)
        """
        fixed_gaps = sum(1 for g in self.gaps.values() if g.fixed)
        total_gaps = len(self.gaps)
        working_wires = sum(1 for w in self.wires.values() if w.test_passed)
        total_wires = len(self.wires)

        numerator = fixed_gaps + working_wires
        denominator = max(1, total_gaps + total_wires)

        score = numerator / denominator
        self.state["current_integration_score"] = score
        self._save_state()

        return score

    def determine_convergence_mode(self) -> ConvergenceMode:
        """
        Determine how fixes are compounding.
        """
        history = self.state.get("integration_history", [])
        if len(history) < 3:
            return ConvergenceMode.EXPONENTIAL

        # Calculate deltas
        recent = history[-3:]
        deltas = [recent[i+1] - recent[i] for i in range(len(recent)-1)]

        if all(d > 0 for d in deltas) and deltas[-1] > deltas[0]:
            return ConvergenceMode.EXPONENTIAL
        elif all(d > 0 for d in deltas) and deltas[-1] < deltas[0]:
            return ConvergenceMode.LOGARITHMIC
        else:
            return ConvergenceMode.REINFORCED

    def get_next_fixes(self, max_count: int = 5) -> List[Gap]:
        """
        Get the next gaps to fix, ordered by priority.

        Priority = severity * (1 - fix_complexity) / (1 + len(dependencies))
        """
        unfixed = [g for g in self.gaps.values() if not g.fixed]

        def priority(gap: Gap) -> float:
            # Check if dependencies are met
            deps_met = all(
                self.gaps.get(d, Gap("", GapType.MISSING, "", "", "", 0, 0)).fixed
                for d in gap.dependencies
            )
            if not deps_met:
                return 0.0
            return gap.severity * (1 - gap.fix_complexity) / (1 + len(gap.dependencies))

        sorted_gaps = sorted(unfixed, key=priority, reverse=True)
        return sorted_gaps[:max_count]

    def apply_methodology(self, components: Dict[str, Any]) -> IntegrafixResult:
        """
        Apply the full integrafix methodology.

        This is the main entry point - it runs all phases.
        """
        # Phase 1: Identify
        gaps = self.identify_gaps(components)

        # Phase 2: Map
        connections = self.map_connections(components)

        # Phase 3 & 4: Wire and Test are done via specific implementations

        # Phase 5: Recurse
        score = self.calculate_integration_score()
        mode = self.determine_convergence_mode()
        next_fixes = self.get_next_fixes()

        # Record history
        self.state["integration_history"].append(score)
        self._save_state()

        return IntegrafixResult(
            gaps_identified=len(gaps),
            gaps_fixed=sum(1 for g in self.gaps.values() if g.fixed),
            wires_created=len(self.wires),
            integration_score=score,
            convergence_mode=mode,
            next_fixes=[g.description for g in next_fixes],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ==================== SPECIFIC INTEGRAFIX OPERATIONS ====================

    def register_known_gaps(self):
        """
        Register all known gaps in the hands-off-engine.

        These are the gaps identified in the system analysis.
        Only registers gaps that don't already exist (preserves fixed state).
        """
        # Check if gaps already loaded from state - don't override
        if len(self.gaps) > 0:
            return list(self.gaps.values())

        known_gaps = [
            # Edge Detection Gaps
            Gap(
                id="edge_circular_fair_price",
                gap_type=GapType.CIRCULAR,
                source="estimate_fair_price",
                target="estimate_fair_price",
                description="Fair price derived from market price + noise = circular, no real edge",
                severity=1.0,
                fix_complexity=0.6,
            ),
            Gap(
                id="wisdom_no_edge_output",
                gap_type=GapType.ORPHANED,
                source="yair_wisdom_engine.calculate_smart_edge",
                target="edge",
                description="Wisdom engine calculates analysis but never outputs edge value",
                severity=0.9,
                fix_complexity=0.3,
            ),

            # Process Coordination Gaps
            Gap(
                id="backend_brain_no_bidirectional",
                gap_type=GapType.BLIND,
                source="backend_loop",
                target="hardware_brain",
                description="Backend reads brain state but brain doesn't see backend decisions",
                severity=0.8,
                fix_complexity=0.5,
            ),
            Gap(
                id="brain_scaling_no_coordination",
                gap_type=GapType.BLIND,
                source="hardware_brain",
                target="scaling_engine",
                description="Brain and scaling make node decisions independently - race condition",
                severity=0.9,
                fix_complexity=0.6,
            ),
            Gap(
                id="no_process_coordinator",
                gap_type=GapType.MISSING,
                source="processes",
                target="coordinator",
                description="No central coordinator for backend_loop, hardware_brain, scaling_engine",
                severity=1.0,
                fix_complexity=0.7,
            ),

            # Trading Pipeline Gaps
            Gap(
                id="edge_to_executor_disconnected",
                gap_type=GapType.DEAD_END,
                source="edge_detection",
                target="concrete_executor",
                description="Edge detected but never passed to executor for action",
                severity=1.0,
                fix_complexity=0.5,
                dependencies=["edge_circular_fair_price"],
            ),
            Gap(
                id="executor_to_recorder_disconnected",
                gap_type=GapType.DEAD_END,
                source="executor",
                target="outcome_recorder",
                description="Trades executed but outcomes never recorded",
                severity=0.9,
                fix_complexity=0.4,
            ),
            Gap(
                id="recorder_to_learner_disconnected",
                gap_type=GapType.DEAD_END,
                source="outcome_recorder",
                target="learning_engine",
                description="Outcomes recorded but never fed to learning system",
                severity=0.8,
                fix_complexity=0.4,
            ),

            # AI Continuity Gaps
            Gap(
                id="ai_no_memory",
                gap_type=GapType.EPHEMERAL,
                source="claude_session",
                target="memory",
                description="Each Claude session starts fresh - no memory between sessions",
                severity=0.7,
                fix_complexity=0.5,
            ),
            Gap(
                id="ai_no_branch_merge",
                gap_type=GapType.ORPHANED,
                source="copilot_branches",
                target="main",
                description="170+ branches created but 0 merged to main",
                severity=0.6,
                fix_complexity=0.8,
            ),

            # Cron Coordination Gaps
            Gap(
                id="cron_no_coordination",
                gap_type=GapType.BLIND,
                source="cron_jobs",
                target="each_other",
                description="18 cron jobs run independently without coordination",
                severity=0.7,
                fix_complexity=0.6,
            ),

            # ============ GAPS DISCOVERED 2025-12-03 ============

            # Duplicate Systems Gaps
            Gap(
                id="duplicate_outcome_trackers",
                gap_type=GapType.BLIND,
                source="integrafix/outcome_tracker.py",
                target="autonomous/outcome_recorder.py",
                description="TWO outcome tracking systems both writing to trade_outcomes.jsonl with different logic",
                severity=1.0,
                fix_complexity=0.5,
            ),
            Gap(
                id="outcome_tracker_wrong_threshold",
                gap_type=GapType.CIRCULAR,
                source="outcome_tracker.check_resolutions",
                target="resolution",
                description="Used price>0.5 as 'resolution' instead of actual settlement (needs 0.95+)",
                severity=1.0,
                fix_complexity=0.3,
            ),
            Gap(
                id="fake_outcome_simulation",
                gap_type=GapType.CIRCULAR,
                source="backend_loop.simulate_outcomes",
                target="outcome_tracker",
                description="Simulated fake outcomes with hardcoded 55% win rate, polluting real data",
                severity=1.0,
                fix_complexity=0.2,
            ),

            # State Confusion Gaps
            Gap(
                id="trading_mode_conflicting_configs",
                gap_type=GapType.BLIND,
                source="config/trading_config.json",
                target="state/trading_mode.json",
                description="Two config files for trading mode with conflicting values",
                severity=0.8,
                fix_complexity=0.3,
            ),
            Gap(
                id="trade_executor_misleading_state",
                gap_type=GapType.ORPHANED,
                source="trade_executor_state.json",
                target="UI",
                description="Shows 'LIVE mode, 108 trades' but all were simulated with 0 real trades",
                severity=0.9,
                fix_complexity=0.3,
            ),

            # Silent Error Handling
            Gap(
                id="bare_except_handlers",
                gap_type=GapType.EPHEMERAL,
                source="125+ bare except: pass",
                target="error_visibility",
                description="125+ bare except handlers silently swallowing errors, masking failures",
                severity=0.8,
                fix_complexity=0.7,
            ),
        ]

        for gap in known_gaps:
            self.gaps[gap.id] = gap

        self._save_state()
        return known_gaps


# Singleton instance
_methodology = None

def get_methodology() -> IntegrafixMethodology:
    global _methodology
    if _methodology is None:
        _methodology = IntegrafixMethodology()
    return _methodology


def main():
    """Run integrafix methodology analysis."""
    methodology = get_methodology()

    # Register known gaps
    gaps = methodology.register_known_gaps()

    print("=" * 70)
    print("INTEGRAFIX METHODOLOGY - GAP ANALYSIS")
    print("=" * 70)
    print()

    print(f"Total gaps identified: {len(gaps)}")
    print()

    # Group by type
    by_type = {}
    for gap in gaps:
        t = gap.gap_type.value
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(gap)

    for gap_type, gap_list in by_type.items():
        print(f"\n[{gap_type.upper()}] ({len(gap_list)} gaps)")
        for gap in gap_list:
            status = "FIXED" if gap.fixed else "OPEN"
            print(f"  [{status}] {gap.description[:60]}")
            print(f"         Severity: {gap.severity:.0%} | Complexity: {gap.fix_complexity:.0%}")

    # Show next fixes
    print("\n" + "=" * 70)
    print("RECOMMENDED NEXT FIXES (by priority)")
    print("=" * 70)
    next_fixes = methodology.get_next_fixes()
    for i, gap in enumerate(next_fixes, 1):
        print(f"\n{i}. {gap.description}")
        print(f"   Source: {gap.source} → Target: {gap.target}")
        print(f"   Type: {gap.gap_type.value} | Severity: {gap.severity:.0%}")

    # Calculate score
    score = methodology.calculate_integration_score()
    print(f"\n\nCurrent Integration Score: {score:.1%}")

    return methodology


if __name__ == "__main__":
    main()
