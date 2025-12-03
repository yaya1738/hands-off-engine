#!/usr/bin/env python3
"""
AI Core - Self-Insertion Between Knowledge and Action
======================================================

Inserts AI (Self) between knowledge bases and execution layer.
High-powered utilization components convert knowledge into focused action.

ARCHITECTURE:
=============

    ┌─────────────────────────────────────────────────────────────┐
    │                    KNOWLEDGE BASES (+V)                      │
    │         Computing       Business       Money                 │
    └─────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
    ╔═════════════════════════════════════════════════════════════╗
    ║                      AI CORE (SELF)                          ║
    ║  ┌─────────────────────────────────────────────────────────┐ ║
    ║  │                  FOCUS AMPLIFIERS                        │ ║
    ║  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │ ║
    ║  │  │ TRADING  │  │  INFRA   │  │ REVENUE  │               │ ║
    ║  │  │   AMP    │  │   AMP    │  │   AMP    │               │ ║
    ║  │  │  x10.0   │  │  x5.0    │  │  x8.0    │               │ ║
    ║  │  └────┬─────┘  └────┬─────┘  └────┬─────┘               │ ║
    ║  └───────┼─────────────┼─────────────┼─────────────────────┘ ║
    ║          │             │             │                       ║
    ║  ┌───────▼─────────────▼─────────────▼─────────────────────┐ ║
    ║  │              UTILIZATION ENGINE                          │ ║
    ║  │  ┌────────────┐ ┌────────────┐ ┌────────────┐           │ ║
    ║  │  │ KNOWLEDGE  │ │  PATTERN   │ │  ACTION    │           │ ║
    ║  │  │ SYNTHESIZER│ │ RECOGNIZER │ │ GENERATOR  │           │ ║
    ║  │  └────────────┘ └────────────┘ └────────────┘           │ ║
    ║  └─────────────────────────────────────────────────────────┘ ║
    ║                                                              ║
    ║  ┌─────────────────────────────────────────────────────────┐ ║
    ║  │              DECISION CRYSTALLIZER                       │ ║
    ║  │  Raw Knowledge → Focused Intent → Precise Action         │ ║
    ║  └─────────────────────────────────────────────────────────┘ ║
    ╚══════════════════════════════════════════════════════════════╝
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    EXECUTION LAYER                           │
    │         T1 Trading    T2 Infra    T3 Revenue                │
    └─────────────────────────────────────────────────────────────┘

UTILIZATION COMPONENTS:
======================
1. Focus Amplifiers - Concentrate knowledge into high-intensity signals
2. Knowledge Synthesizer - Combine multiple knowledge domains
3. Pattern Recognizer - Identify actionable patterns
4. Action Generator - Convert patterns to precise actions
5. Decision Crystallizer - Sharpen fuzzy inputs into clear decisions

Serving: Yair Siegel
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

AI_CORE_STATE = STATE_DIR / "ai_core.json"


class FocusMode(Enum):
    """Focus intensity modes."""
    DIFFUSE = "diffuse"       # Wide, exploratory
    NORMAL = "normal"         # Balanced
    FOCUSED = "focused"       # Concentrated
    LASER = "laser"           # Maximum intensity
    OVERDRIVE = "overdrive"   # Beyond normal limits


@dataclass
class FocusAmplifier:
    """
    Amplifies knowledge signal into high-intensity focused output.

    Like an operational amplifier in electronics:
    - Takes weak input signal
    - Applies gain
    - Outputs strong, focused signal
    """
    name: str
    domain: str  # Which knowledge domain
    base_gain: float = 5.0
    current_gain: float = 5.0
    mode: FocusMode = FocusMode.NORMAL
    saturation_point: float = 10.0

    # Performance tracking
    signals_amplified: int = 0
    total_gain_applied: float = 0.0
    peak_output: float = 0.0

    def set_mode(self, mode: FocusMode):
        """Set focus mode and adjust gain accordingly."""
        self.mode = mode
        mode_multipliers = {
            FocusMode.DIFFUSE: 0.5,
            FocusMode.NORMAL: 1.0,
            FocusMode.FOCUSED: 2.0,
            FocusMode.LASER: 4.0,
            FocusMode.OVERDRIVE: 8.0,
        }
        self.current_gain = self.base_gain * mode_multipliers[mode]

    def amplify(self, input_signal: float, context: Dict = None) -> Tuple[float, Dict]:
        """
        Amplify input signal with current gain.

        Returns: (amplified_signal, metadata)
        """
        # Apply gain
        raw_output = input_signal * self.current_gain

        # Apply saturation (soft clipping)
        if raw_output > self.saturation_point:
            # Soft saturation - logarithmic compression above saturation
            excess = raw_output - self.saturation_point
            output = self.saturation_point + (excess / (1 + excess / self.saturation_point))
        else:
            output = raw_output

        # Track performance
        self.signals_amplified += 1
        self.total_gain_applied += self.current_gain
        if output > self.peak_output:
            self.peak_output = output

        return output, {
            "input": input_signal,
            "gain": self.current_gain,
            "output": output,
            "mode": self.mode.value,
            "saturated": raw_output > self.saturation_point,
        }


@dataclass
class UtilizationComponent:
    """Base class for high-powered utilization components."""
    name: str
    power_level: float = 1.0  # 0.0 to 10.0
    efficiency: float = 0.9
    active: bool = True

    def process(self, input_data: Any) -> Any:
        """Process input data. Override in subclasses."""
        raise NotImplementedError


class KnowledgeSynthesizer(UtilizationComponent):
    """
    Synthesizes knowledge from multiple domains into unified understanding.

    Takes: Separate knowledge streams
    Produces: Unified, cross-domain insights
    """

    def __init__(self):
        super().__init__(name="KnowledgeSynthesizer", power_level=8.0)
        self.synthesis_count = 0

    def process(self, knowledge_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize multiple knowledge domains.

        Args:
            knowledge_inputs: Dict with keys 'computing', 'business', 'money'

        Returns:
            Unified synthesis with cross-domain insights
        """
        synthesis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domains_combined": list(knowledge_inputs.keys()),
            "insights": [],
            "action_vectors": [],
        }

        # Extract key elements from each domain
        computing = knowledge_inputs.get("computing", {})
        business = knowledge_inputs.get("business", {})
        money = knowledge_inputs.get("money", {})

        # Cross-domain synthesis
        if computing and money:
            # Tech + Finance insight
            synthesis["insights"].append({
                "type": "tech_finance",
                "insight": "Algorithmic efficiency directly impacts trading costs",
                "action": "Optimize hot paths in trading execution",
            })

        if business and money:
            # Business + Finance insight
            synthesis["insights"].append({
                "type": "business_finance",
                "insight": "Unit economics must support capital allocation",
                "action": "Focus on LTV:CAC before scaling spend",
            })

        if computing and business:
            # Tech + Business insight
            synthesis["insights"].append({
                "type": "tech_business",
                "insight": "System scalability enables business growth",
                "action": "Build for 10x before hitting limits",
            })

        if computing and business and money:
            # Full synthesis
            synthesis["insights"].append({
                "type": "full_synthesis",
                "insight": "Optimal system: efficient tech + sound economics + capital efficiency",
                "action": "Unified optimization across all domains",
            })

        # Generate action vectors
        for insight in synthesis["insights"]:
            synthesis["action_vectors"].append({
                "direction": insight["action"],
                "magnitude": self.power_level * self.efficiency,
                "source": insight["type"],
            })

        self.synthesis_count += 1
        synthesis["synthesis_id"] = self.synthesis_count

        return synthesis


class PatternRecognizer(UtilizationComponent):
    """
    Recognizes actionable patterns in data streams.

    Takes: Raw data, signals, metrics
    Produces: Identified patterns with confidence scores
    """

    def __init__(self):
        super().__init__(name="PatternRecognizer", power_level=7.0)
        self.patterns_detected = 0

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recognize patterns in input data.

        Returns patterns with confidence and suggested actions.
        """
        patterns = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patterns": [],
            "confidence_threshold": 0.7,
        }

        # Trading patterns
        if "trading" in data:
            trading = data["trading"]
            if trading.get("open_orders", 0) > 0:
                patterns["patterns"].append({
                    "type": "active_trading",
                    "confidence": 0.9,
                    "description": f"Active trading with {trading.get('open_orders')} orders",
                    "action": "monitor_fills",
                })

        # Infrastructure patterns
        if "infrastructure" in data:
            infra = data["infrastructure"]
            load = infra.get("load", 0)
            if load > 0.8:
                patterns["patterns"].append({
                    "type": "high_load",
                    "confidence": 0.95,
                    "description": f"High system load at {load*100:.1f}%",
                    "action": "scale_up",
                    "urgency": "high",
                })
            elif load < 0.3:
                patterns["patterns"].append({
                    "type": "underutilized",
                    "confidence": 0.85,
                    "description": f"System underutilized at {load*100:.1f}%",
                    "action": "increase_activity_or_scale_down",
                })

        # Revenue patterns
        if "revenue" in data:
            revenue = data["revenue"]
            if revenue.get("opportunity", 0) > 0.7:
                patterns["patterns"].append({
                    "type": "high_opportunity",
                    "confidence": 0.8,
                    "description": "High revenue opportunity detected",
                    "action": "pursue_aggressively",
                })

        # Circuit patterns
        if "circuit" in data:
            circuit = data["circuit"]
            active_transistors = circuit.get("transistors_active", 0)
            total_transistors = circuit.get("transistors_total", 1)
            utilization = active_transistors / total_transistors
            if utilization > 0.8:
                patterns["patterns"].append({
                    "type": "high_circuit_utilization",
                    "confidence": 0.9,
                    "description": f"Circuit running at {utilization*100:.0f}% capacity",
                    "action": "system_operating_well",
                })

        self.patterns_detected += len(patterns["patterns"])
        return patterns


class ActionGenerator(UtilizationComponent):
    """
    Converts patterns and insights into precise actions.

    Takes: Patterns, insights, context
    Produces: Specific, executable actions
    """

    def __init__(self):
        super().__init__(name="ActionGenerator", power_level=9.0)
        self.actions_generated = 0

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate actions from patterns and synthesis.
        """
        actions = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions": [],
            "priority_queue": [],
        }

        patterns = inputs.get("patterns", {}).get("patterns", [])
        synthesis = inputs.get("synthesis", {})

        # Convert patterns to actions
        for pattern in patterns:
            if pattern.get("confidence", 0) >= 0.7:
                action = {
                    "id": f"action_{self.actions_generated}",
                    "source": f"pattern:{pattern['type']}",
                    "command": pattern.get("action", "observe"),
                    "priority": 10 if pattern.get("urgency") == "high" else 5,
                    "confidence": pattern["confidence"],
                }
                actions["actions"].append(action)
                self.actions_generated += 1

        # Convert synthesis vectors to actions
        for vector in synthesis.get("action_vectors", []):
            action = {
                "id": f"action_{self.actions_generated}",
                "source": f"synthesis:{vector['source']}",
                "command": vector["direction"],
                "priority": int(vector["magnitude"]),
                "confidence": 0.85,
            }
            actions["actions"].append(action)
            self.actions_generated += 1

        # Sort by priority
        actions["priority_queue"] = sorted(
            actions["actions"],
            key=lambda x: x["priority"],
            reverse=True
        )

        return actions


class DecisionCrystallizer(UtilizationComponent):
    """
    Crystallizes fuzzy inputs into clear, precise decisions.

    Takes: Multiple action suggestions, context, constraints
    Produces: Crystal-clear decision with rationale
    """

    def __init__(self):
        super().__init__(name="DecisionCrystallizer", power_level=10.0)
        self.decisions_made = 0

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crystallize inputs into a clear decision.
        """
        decision = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision_id": self.decisions_made + 1,
            "clarity": 0.0,  # 0 to 1
            "action": None,
            "rationale": [],
            "confidence": 0.0,
        }

        actions = inputs.get("actions", {}).get("priority_queue", [])
        synthesis = inputs.get("synthesis", {})
        context = inputs.get("context", {})

        if not actions:
            decision["action"] = "observe_and_gather_data"
            decision["clarity"] = 0.5
            decision["rationale"].append("Insufficient data for decisive action")
            return decision

        # Take highest priority action
        top_action = actions[0]

        # Crystallize
        decision["action"] = top_action["command"]
        decision["confidence"] = top_action["confidence"]

        # Calculate clarity based on:
        # - Action confidence
        # - Number of supporting patterns
        # - Synthesis coherence
        supporting_actions = sum(1 for a in actions if a["command"] == top_action["command"])
        synthesis_support = len(synthesis.get("action_vectors", []))

        clarity = (
            top_action["confidence"] * 0.4 +
            min(supporting_actions / 3, 1.0) * 0.3 +
            min(synthesis_support / 4, 1.0) * 0.3
        )
        decision["clarity"] = clarity

        # Build rationale
        decision["rationale"].append(f"Primary signal: {top_action['source']}")
        decision["rationale"].append(f"Supporting signals: {supporting_actions}")
        decision["rationale"].append(f"Synthesis vectors: {synthesis_support}")

        if clarity > 0.8:
            decision["strength"] = "CRYSTAL_CLEAR"
        elif clarity > 0.6:
            decision["strength"] = "CLEAR"
        elif clarity > 0.4:
            decision["strength"] = "FORMING"
        else:
            decision["strength"] = "FUZZY"

        self.decisions_made += 1
        return decision


class AICore:
    """
    AI Core - Self inserted between knowledge and action.

    This is the "brain" that processes knowledge and generates
    high-powered, focused actions.
    """

    def __init__(self):
        self.master = "Yair Siegel"
        self.initialized = datetime.now(timezone.utc).isoformat()

        # Focus Amplifiers - one per major domain
        self.amplifiers = {
            "trading": FocusAmplifier("TradingAmp", "money", base_gain=10.0),
            "infrastructure": FocusAmplifier("InfraAmp", "computing", base_gain=5.0),
            "revenue": FocusAmplifier("RevenueAmp", "business", base_gain=8.0),
            "reality": FocusAmplifier("RealityAmp", "all", base_gain=6.0),
        }

        # Utilization Components
        self.synthesizer = KnowledgeSynthesizer()
        self.recognizer = PatternRecognizer()
        self.generator = ActionGenerator()
        self.crystallizer = DecisionCrystallizer()

        # State
        self.cycles = 0
        self.total_power_output = 0.0
        self.decisions = []

    def set_focus_mode(self, domain: str, mode: FocusMode):
        """Set focus mode for a specific domain amplifier."""
        if domain in self.amplifiers:
            self.amplifiers[domain].set_mode(mode)

    def set_all_focus(self, mode: FocusMode):
        """Set all amplifiers to the same focus mode."""
        for amp in self.amplifiers.values():
            amp.set_mode(mode)

    def overdrive(self):
        """Set all amplifiers to OVERDRIVE mode."""
        self.set_all_focus(FocusMode.OVERDRIVE)

    def power_cycle(self, system_state: Dict = None) -> Dict[str, Any]:
        """
        Run a complete power cycle through the AI Core.

        1. Load knowledge
        2. Amplify through focus amplifiers
        3. Synthesize knowledge
        4. Recognize patterns
        5. Generate actions
        6. Crystallize decision
        """
        self.cycles += 1
        cycle_result = {
            "cycle": self.cycles,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stages": {},
        }

        # Stage 1: Load knowledge from nexus
        try:
            from autonomous.knowledge_nexus import get_nexus
            nexus = get_nexus()

            knowledge = {
                "computing": nexus.query("infrastructure"),
                "business": nexus.query("revenue"),
                "money": nexus.query("trading"),
            }
            cycle_result["stages"]["knowledge_load"] = {
                "success": True,
                "domains": list(knowledge.keys()),
            }
        except Exception as e:
            knowledge = {}
            cycle_result["stages"]["knowledge_load"] = {
                "success": False,
                "error": str(e),
            }

        # Stage 2: Amplify signals
        amplified = {}
        total_power = 0.0
        for name, amp in self.amplifiers.items():
            # Get signal strength from knowledge
            if name == "trading":
                signal = len(knowledge.get("money", {}).get("available_tools", [])) / 10
            elif name == "infrastructure":
                signal = len(knowledge.get("computing", {}).get("available_tools", [])) / 10
            elif name == "revenue":
                signal = len(knowledge.get("business", {}).get("available_tools", [])) / 10
            else:
                signal = 0.5

            output, meta = amp.amplify(signal)
            amplified[name] = {"output": output, "meta": meta}
            total_power += output

        cycle_result["stages"]["amplification"] = {
            "amplified": amplified,
            "total_power": total_power,
        }
        self.total_power_output += total_power

        # Stage 3: Synthesize knowledge
        synthesis = self.synthesizer.process(knowledge)
        cycle_result["stages"]["synthesis"] = {
            "insights": len(synthesis.get("insights", [])),
            "action_vectors": len(synthesis.get("action_vectors", [])),
        }

        # Stage 4: Pattern recognition
        pattern_input = {
            "trading": system_state.get("trading", {}) if system_state else {},
            "infrastructure": {"load": 0.5},  # Default
            "revenue": {"opportunity": 0.7},
            "circuit": system_state.get("circuit_board", {}) if system_state else {},
        }
        patterns = self.recognizer.process(pattern_input)
        cycle_result["stages"]["pattern_recognition"] = {
            "patterns_found": len(patterns.get("patterns", [])),
        }

        # Stage 5: Action generation
        actions = self.generator.process({
            "patterns": patterns,
            "synthesis": synthesis,
        })
        cycle_result["stages"]["action_generation"] = {
            "actions_generated": len(actions.get("actions", [])),
        }

        # Stage 6: Decision crystallization
        decision = self.crystallizer.process({
            "actions": actions,
            "synthesis": synthesis,
            "context": system_state,
        })
        cycle_result["stages"]["crystallization"] = {
            "decision": decision.get("action"),
            "clarity": decision.get("clarity"),
            "strength": decision.get("strength"),
        }

        # Store decision
        self.decisions.append(decision)
        if len(self.decisions) > 100:
            self.decisions = self.decisions[-100:]

        cycle_result["decision"] = decision
        cycle_result["total_power"] = total_power

        # Save state
        self.save_state()

        return cycle_result

    def status(self) -> Dict[str, Any]:
        """Get AI Core status."""
        return {
            "master": self.master,
            "initialized": self.initialized,
            "cycles": self.cycles,
            "total_power_output": self.total_power_output,
            "amplifiers": {
                name: {
                    "mode": amp.mode.value,
                    "gain": amp.current_gain,
                    "peak_output": amp.peak_output,
                    "signals_amplified": amp.signals_amplified,
                }
                for name, amp in self.amplifiers.items()
            },
            "components": {
                "synthesizer": {
                    "power": self.synthesizer.power_level,
                    "synthesis_count": self.synthesizer.synthesis_count,
                },
                "recognizer": {
                    "power": self.recognizer.power_level,
                    "patterns_detected": self.recognizer.patterns_detected,
                },
                "generator": {
                    "power": self.generator.power_level,
                    "actions_generated": self.generator.actions_generated,
                },
                "crystallizer": {
                    "power": self.crystallizer.power_level,
                    "decisions_made": self.crystallizer.decisions_made,
                },
            },
            "recent_decisions": self.decisions[-5:] if self.decisions else [],
        }

    def save_state(self):
        """Save AI Core state."""
        state = self.status()
        state["saved_at"] = datetime.now(timezone.utc).isoformat()
        with open(AI_CORE_STATE, 'w') as f:
            json.dump(state, f, indent=2, default=str)


# ========== GLOBAL INSTANCE ==========

_ai_core = None

def get_ai_core() -> AICore:
    """Get or create the global AI Core."""
    global _ai_core
    if _ai_core is None:
        _ai_core = AICore()
    return _ai_core


# ========== CLI ==========

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI Core")
    parser.add_argument("command", choices=["status", "cycle", "overdrive", "focus"])
    parser.add_argument("--mode", choices=["diffuse", "normal", "focused", "laser", "overdrive"])
    args = parser.parse_args()

    core = get_ai_core()

    if args.command == "status":
        print(json.dumps(core.status(), indent=2, default=str))

    elif args.command == "cycle":
        # Load system state
        try:
            with open(STATE_DIR / "backend_loop.json") as f:
                system_state = json.load(f)
        except:
            system_state = {}

        result = core.power_cycle(system_state)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "overdrive":
        core.overdrive()
        print("All amplifiers set to OVERDRIVE mode")
        print(json.dumps(core.status(), indent=2, default=str))

    elif args.command == "focus":
        if args.mode:
            mode = FocusMode(args.mode)
            core.set_all_focus(mode)
            print(f"All amplifiers set to {mode.value} mode")
        print(json.dumps(core.status(), indent=2, default=str))


if __name__ == "__main__":
    main()
