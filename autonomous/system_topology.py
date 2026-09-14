#!/usr/bin/env python3
"""
4D SYSTEM TOPOLOGY - Understanding How Everything Fits Together
================================================================

The system must ALWAYS understand:
1. WHAT - What components exist (X axis)
2. WHY - Why each component exists (Y axis)
3. HOW - How components connect and interact (Z axis)
4. TIME - The 4th dimension: PAST → PRESENT → FUTURE

This is NOT just monitoring - it's UNDERSTANDING through TIME.
The system sees itself as a CONTINUUM, not a snapshot.

4 DIMENSIONS:
- X: Components (what exists)
- Y: Purpose (why they exist)
- Z: Relationships (how they connect)
- T: TIME (the true 4th dimension)
    - PAST: Historical states, what happened, learned patterns
    - PRESENT: Current state, active status
    - FUTURE: Predictions, projections, planned actions

The system remembers its past, knows its present, and predicts its future.

Serving: Yair Siegel
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import deque

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
TOPOLOGY_FILE = STATE_DIR / 'system_topology.json'
TIMELINE_FILE = STATE_DIR / 'system_timeline.jsonl'  # Append-only history
PREDICTIONS_FILE = STATE_DIR / 'system_predictions.json'

# How much history to keep in memory
HISTORY_WINDOW = 100  # Last 100 state snapshots


@dataclass
class TemporalState:
    """A point in time for the system."""
    timestamp: str
    components_active: int
    components_degraded: int
    balance: float
    positions_value: float
    ai_calls_today: int
    infra_cost_hourly: float
    events: List[str] = field(default_factory=list)


@dataclass
class Prediction:
    """A prediction about future state."""
    target_time: str
    prediction_type: str  # balance, capacity, cost, etc.
    predicted_value: float
    confidence: float
    basis: str  # What data this prediction is based on
    created_at: str = ""


@dataclass
class Component:
    """A system component with 4D awareness."""
    id: str
    name: str
    type: str  # infra, service, data, process

    # DIMENSION 1: WHAT (X axis)
    description: str
    location: str  # droplet, local, cloud
    status: str

    # DIMENSION 2: WHY (Y axis)
    purpose: str = ""
    value_to_master: str = ""
    criticality: str = "standard"  # critical, high, standard, low

    # DIMENSION 3: HOW (Z axis - relationships)
    depends_on: List[str] = field(default_factory=list)
    provides_to: List[str] = field(default_factory=list)
    communicates_via: str = ""  # api, file, network, etc.

    # DIMENSION 4: TIME (T axis - the true 4th dimension)
    # PAST
    created: str = ""
    state_history: List[Dict] = field(default_factory=list)  # [{timestamp, status, event}]
    learned_patterns: List[str] = field(default_factory=list)  # What we learned from past

    # PRESENT
    last_active: str = ""
    current_state: str = "nominal"

    # FUTURE
    schedule: str = ""  # continuous, hourly, daily, on-demand
    next_action: str = ""
    predicted_state: str = ""  # Where we expect this to be
    predicted_needs: List[str] = field(default_factory=list)  # What it will need


@dataclass
class SystemTopology:
    """Complete 4D system understanding through TIME."""
    master: str
    timestamp: str
    components: Dict[str, Component]
    flows: List[Dict]  # Data/process flows
    temporal_schedule: Dict[str, List[str]]  # When things run
    health_summary: Dict

    # TIME DIMENSION - The 4th Dimension
    timeline: List[TemporalState] = field(default_factory=list)  # PAST
    current_state: Optional[TemporalState] = None  # PRESENT
    predictions: List[Prediction] = field(default_factory=list)  # FUTURE


class TopologyManager:
    """
    Manages the 4D system topology through TIME.

    The system uses this to:
    - REMEMBER the past (timeline)
    - KNOW the present (current state)
    - PREDICT the future (projections)

    Time is the 4th dimension. The system exists as a continuum.
    """

    def __init__(self):
        self.topology = self._load_topology()
        self.timeline: deque = deque(maxlen=HISTORY_WINDOW)  # Rolling window of past states
        self.predictions: List[Prediction] = []
        self._load_timeline()
        self._define_core_components()

    def _load_topology(self) -> Dict:
        """Load existing topology."""
        if TOPOLOGY_FILE.exists():
            try:
                with open(TOPOLOGY_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "master": MASTER,
            "components": {},
            "flows": [],
            "temporal_schedule": {},
            "last_updated": None
        }

    def _save_topology(self):
        """Save topology."""
        self.topology["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(TOPOLOGY_FILE, 'w') as f:
            json.dump(self.topology, f, indent=2)

    def _load_timeline(self):
        """Load historical timeline from append-only file."""
        if TIMELINE_FILE.exists():
            try:
                with open(TIMELINE_FILE) as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            self.timeline.append(entry)
            except Exception as e:
                print(f"[4D] Timeline load error: {e}")

    # =========================================================================
    # TIME DIMENSION: PAST → PRESENT → FUTURE
    # =========================================================================

    def record_state(self, events: List[str] = None) -> TemporalState:
        """
        Record current state to timeline (PAST accumulation).

        This is how the system REMEMBERS.
        """
        now = datetime.now(timezone.utc)
        events = events or []

        # Gather current metrics
        state = TemporalState(
            timestamp=now.isoformat(),
            components_active=self._count_active_components(),
            components_degraded=self._count_degraded_components(),
            balance=self._get_current_balance(),
            positions_value=self._get_positions_value(),
            ai_calls_today=self._get_ai_calls_today(),
            infra_cost_hourly=self._get_infra_cost(),
            events=events
        )

        # Add to in-memory timeline
        self.timeline.append(asdict(state))

        # Append to persistent timeline (never lose history)
        with open(TIMELINE_FILE, 'a') as f:
            f.write(json.dumps(asdict(state)) + '\n')

        return state

    def get_past(self, hours: int = 24) -> List[Dict]:
        """
        Get historical states from the past N hours.

        This is how the system REMEMBERS.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        past_states = [
            s for s in self.timeline
            if s.get('timestamp', '') >= cutoff_str
        ]

        return past_states

    def get_present(self) -> Dict:
        """
        Get current system state.

        This is how the system KNOWS NOW.
        """
        now = datetime.now(timezone.utc)

        return {
            "timestamp": now.isoformat(),
            "master": MASTER,

            # Current component states
            "components_active": self._count_active_components(),
            "components_degraded": self._count_degraded_components(),

            # Current financial state
            "balance": self._get_current_balance(),
            "positions_value": self._get_positions_value(),

            # Current operational state
            "ai_calls_today": self._get_ai_calls_today(),
            "infra_cost_hourly": self._get_infra_cost(),

            # Component health
            "component_health": self._get_component_health(),

            # Active flows
            "active_flows": self._get_active_flows()
        }

    def predict_future(self, hours: int = 24) -> List[Prediction]:
        """
        Generate predictions about future state.

        This is how the system FORESEES.
        """
        predictions = []
        now = datetime.now(timezone.utc)
        target = now + timedelta(hours=hours)
        target_str = target.isoformat()

        # Get historical data for trend analysis
        past = self.get_past(hours=48)  # Look at last 48h to predict next 24h

        if past:
            # Predict balance trend
            balances = [s.get('balance', 0) for s in past if s.get('balance')]
            if len(balances) >= 2:
                trend = (balances[-1] - balances[0]) / max(len(balances), 1)
                predicted_balance = balances[-1] + (trend * hours)
                predictions.append(Prediction(
                    target_time=target_str,
                    prediction_type="balance",
                    predicted_value=predicted_balance,
                    confidence=0.6 if len(balances) > 10 else 0.3,
                    basis=f"Linear trend from {len(balances)} data points",
                    created_at=now.isoformat()
                ))

            # Predict infrastructure cost
            costs = [s.get('infra_cost_hourly', 0) for s in past if s.get('infra_cost_hourly')]
            if costs:
                avg_cost = sum(costs) / len(costs)
                predicted_cost_24h = avg_cost * hours
                predictions.append(Prediction(
                    target_time=target_str,
                    prediction_type="infra_cost_24h",
                    predicted_value=predicted_cost_24h,
                    confidence=0.8,  # Cost is more predictable
                    basis=f"Average hourly cost: ${avg_cost:.4f}",
                    created_at=now.isoformat()
                ))

            # Predict AI usage
            ai_calls = [s.get('ai_calls_today', 0) for s in past]
            if ai_calls:
                avg_calls = sum(ai_calls) / len(ai_calls)
                predictions.append(Prediction(
                    target_time=target_str,
                    prediction_type="ai_calls",
                    predicted_value=avg_calls,
                    confidence=0.5,
                    basis=f"Historical average: {avg_calls:.0f} calls/snapshot",
                    created_at=now.isoformat()
                ))

        # Store predictions
        self.predictions = predictions
        self._save_predictions()

        return predictions

    def _save_predictions(self):
        """Save predictions to file."""
        data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "predictions": [asdict(p) for p in self.predictions]
        }
        with open(PREDICTIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    # Helper methods for gathering current state
    def _count_active_components(self) -> int:
        return sum(1 for c in self.topology.get('components', {}).values()
                   if c.get('status') == 'active')

    def _count_degraded_components(self) -> int:
        return sum(1 for c in self.topology.get('components', {}).values()
                   if c.get('status') != 'active')

    def _get_current_balance(self) -> float:
        """Get current balance from finance system."""
        try:
            from trading.balance_tracker import BalanceTracker
            tracker = BalanceTracker()
            return tracker.get_usdc_balance()
        except:
            return 0.0

    def _get_positions_value(self) -> float:
        """Get current positions value."""
        try:
            from trading.balance_tracker import BalanceTracker
            tracker = BalanceTracker()
            return tracker.get_positions_value()
        except:
            return 0.0

    def _get_ai_calls_today(self) -> int:
        """Get AI API calls made today."""
        try:
            from ai.dense_ai import get_dense_ai
            dense = get_dense_ai()
            return getattr(dense, 'calls_today', 0)
        except:
            return 0

    def _get_infra_cost(self) -> float:
        """Get hourly infrastructure cost."""
        try:
            from finance.cost_tracker import get_cost_tracker
            tracker = get_cost_tracker()
            return tracker.get_hourly_rate()
        except:
            return 0.0

    def _get_component_health(self) -> Dict[str, str]:
        """Get health status of each component."""
        return {
            comp_id: comp.get('status', 'unknown')
            for comp_id, comp in self.topology.get('components', {}).items()
        }

    def _get_active_flows(self) -> List[str]:
        """Get currently active process flows."""
        return [f['name'] for f in self.topology.get('flows', [])]

    # =========================================================================
    # END TIME DIMENSION
    # =========================================================================

    def _define_core_components(self):
        """Define the core system components with 4D awareness."""

        core_components = [
            # ========== INFRASTRUCTURE LAYER ==========
            Component(
                id="infra_droplets",
                name="DigitalOcean Droplets",
                type="infra",
                description="Cloud compute nodes running the system",
                location="digitalocean",
                status="active",
                depends_on=["provider_do"],
                provides_to=["services_all"],
                communicates_via="ssh, api",
                purpose="Provide compute capacity for all operations",
                value_to_master="Foundation of all system capabilities",
                criticality="critical",
                schedule="continuous"
            ),

            # ========== FINANCE LAYER ==========
            Component(
                id="finance_cost_gate",
                name="Autonomous Cost Gate",
                type="process",
                description="Checks cost/ROI before any action",
                location="local",
                status="active",
                depends_on=["finance_provider_intel", "finance_terms"],
                provides_to=["unified_ai", "scaling_engine"],
                communicates_via="python import",
                purpose="Prevent wasteful spending, ensure positive ROI",
                value_to_master="Protects capital, optimizes spending",
                criticality="critical",
                schedule="on-demand"
            ),
            Component(
                id="finance_provider_intel",
                name="Provider Intelligence",
                type="data",
                description="Atomic cost decomposition for all actions",
                location="local",
                status="active",
                depends_on=["finance_terms"],
                provides_to=["finance_cost_gate"],
                communicates_via="python import",
                purpose="Break actions into atomic costs for precise calculations",
                value_to_master="Know exactly what every action costs",
                criticality="high",
                schedule="on-demand"
            ),
            Component(
                id="finance_terms",
                name="Partner Terms",
                type="data",
                description="All provider contracts, timing, billing rules",
                location="local",
                status="active",
                depends_on=[],
                provides_to=["finance_provider_intel", "finance_cost_gate"],
                communicates_via="json file",
                purpose="Central truth for all provider billing rules",
                value_to_master="Never be surprised by charges",
                criticality="high",
                schedule="static"
            ),

            # ========== INFRASTRUCTURE MANAGEMENT ==========
            Component(
                id="infra_proactive",
                name="Proactive Infrastructure",
                type="process",
                description="Predicts and prepares capacity before needed",
                location="local",
                status="active",
                depends_on=["infra_droplets", "finance_cost_gate"],
                provides_to=["scaling_engine"],
                communicates_via="python import",
                purpose="Ensure infrastructure is ready BEFORE it's needed",
                value_to_master="Never hit capacity limits, always room to grow",
                criticality="high",
                schedule="hourly"
            ),
            Component(
                id="infra_protection",
                name="Infrastructure Protection",
                type="process",
                description="Prevents destruction of valuable infrastructure",
                location="local",
                status="active",
                depends_on=["infra_droplets"],
                provides_to=["scaling_engine"],
                communicates_via="python import",
                purpose="Preserve infrastructure - build UP not tear DOWN",
                value_to_master="Never lose valuable resources",
                criticality="critical",
                schedule="on-demand"
            ),

            # ========== AI/DECISION LAYER ==========
            Component(
                id="unified_ai",
                name="Unified AI Brain",
                type="process",
                description="Central decision-making with cost awareness",
                location="local",
                status="active",
                depends_on=["finance_cost_gate"],
                provides_to=["executor", "trading"],
                communicates_via="python import",
                purpose="Make all decisions serving Yair Siegel",
                value_to_master="Autonomous agent serving your interests",
                criticality="critical",
                schedule="continuous"
            ),
            Component(
                id="dense_ai",
                name="Dense AI Analysis",
                type="service",
                description="Multi-provider AI with free-first fallback",
                location="local",
                status="active",
                depends_on=["provider_groq", "provider_google", "provider_openai"],
                provides_to=["unified_ai", "trading"],
                communicates_via="api",
                purpose="Maximum AI capability at minimum cost",
                value_to_master="Smart analysis without burning money",
                criticality="high",
                schedule="on-demand"
            ),

            # ========== TRADING LAYER ==========
            Component(
                id="trading_decider",
                name="Trading Decider",
                type="process",
                description="Converts signals to planned actions",
                location="local",
                status="active",
                depends_on=["unified_ai", "trading_signals"],
                provides_to=["trading_executor"],
                communicates_via="python objects",
                purpose="Smart position sizing and trade planning",
                value_to_master="Intelligent trading decisions",
                criticality="high",
                schedule="on-demand"
            ),
            Component(
                id="trading_executor",
                name="Trading Executor",
                type="process",
                description="Executes trades with safety checks",
                location="local",
                status="active",
                depends_on=["trading_decider", "provider_polymarket", "finance_cost_gate"],
                provides_to=[],
                communicates_via="api",
                purpose="Safe execution of trading decisions",
                value_to_master="Execute trades without catastrophic errors",
                criticality="critical",
                schedule="on-demand"
            ),

            # ========== PROVIDERS ==========
            Component(
                id="provider_do",
                name="DigitalOcean Provider",
                type="provider",
                description="Cloud infrastructure provider",
                location="cloud",
                status="active",
                depends_on=[],
                provides_to=["infra_droplets"],
                communicates_via="api",
                purpose="Provide compute resources",
                value_to_master="Foundation infrastructure",
                criticality="critical",
                schedule="continuous"
            ),
            Component(
                id="provider_groq",
                name="Groq AI Provider",
                type="provider",
                description="FREE AI inference",
                location="cloud",
                status="active",
                depends_on=[],
                provides_to=["dense_ai"],
                communicates_via="api",
                purpose="Free AI - use FIRST",
                value_to_master="AI without cost",
                criticality="high",
                schedule="on-demand"
            ),
            Component(
                id="provider_google",
                name="Google AI Provider",
                type="provider",
                description="FREE AI inference (Gemini)",
                location="cloud",
                status="active",
                depends_on=[],
                provides_to=["dense_ai"],
                communicates_via="api",
                purpose="Free AI - use SECOND after Groq",
                value_to_master="Backup free AI",
                criticality="high",
                schedule="on-demand"
            ),
            Component(
                id="provider_polymarket",
                name="Polymarket Provider",
                type="provider",
                description="Prediction market platform",
                location="cloud",
                status="active",
                depends_on=[],
                provides_to=["trading_executor"],
                communicates_via="api",
                purpose="Trading venue for predictions",
                value_to_master="Income generation through trading",
                criticality="high",
                schedule="on-demand"
            ),
        ]

        for component in core_components:
            self.topology["components"][component.id] = asdict(component)

        self._define_flows()
        self._define_schedule()
        self._save_topology()

    def _define_flows(self):
        """Define how data/processes flow through the system."""
        self.topology["flows"] = [
            {
                "name": "Cost-Aware Decision Flow",
                "description": "Every action checks cost before execution",
                "path": ["action_request", "finance_cost_gate", "unified_ai", "execution"],
                "purpose": "Ensure no action wastes money"
            },
            {
                "name": "Trading Flow",
                "description": "Signal to execution pipeline",
                "path": ["market_data", "trading_decider", "unified_ai", "trading_executor", "provider_polymarket"],
                "purpose": "Convert signals to profitable trades"
            },
            {
                "name": "Infrastructure Flow",
                "description": "Proactive capacity management",
                "path": ["infra_proactive", "finance_cost_gate", "scaling_engine", "provider_do"],
                "purpose": "Always have infrastructure ready"
            },
            {
                "name": "AI Provider Cascade",
                "description": "Free first, paid last",
                "path": ["dense_ai", "provider_groq", "provider_google", "provider_openai"],
                "purpose": "Maximum AI capability at minimum cost"
            }
        ]

    def _define_schedule(self):
        """Define when things run."""
        self.topology["temporal_schedule"] = {
            "continuous": [
                "infra_droplets",
                "unified_ai",
                "provider_do"
            ],
            "hourly": [
                "infra_proactive"
            ],
            "on_demand": [
                "finance_cost_gate",
                "dense_ai",
                "trading_decider",
                "trading_executor"
            ],
            "daily": [
                "cost_report",
                "system_health_check"
            ]
        }

    def get_component(self, component_id: str) -> Optional[Dict]:
        """Get a component's full 4D understanding."""
        return self.topology.get("components", {}).get(component_id)

    def get_why(self, component_id: str) -> str:
        """Get WHY a component exists."""
        component = self.get_component(component_id)
        if component:
            return f"{component['purpose']} → Value: {component['value_to_master']}"
        return "Unknown component"

    def get_dependencies(self, component_id: str) -> Dict:
        """Get what a component depends on and provides to."""
        component = self.get_component(component_id)
        if component:
            return {
                "depends_on": component.get("depends_on", []),
                "provides_to": component.get("provides_to", []),
                "criticality": component.get("criticality", "unknown")
            }
        return {"depends_on": [], "provides_to": [], "criticality": "unknown"}

    def get_flow_for_action(self, action: str) -> List[str]:
        """Get the flow path for a given action type."""
        action_lower = action.lower()

        if "trade" in action_lower or "buy" in action_lower or "sell" in action_lower:
            return ["Trading Flow"]
        elif "scale" in action_lower or "provision" in action_lower or "droplet" in action_lower:
            return ["Infrastructure Flow"]
        elif "ai" in action_lower or "analyze" in action_lower:
            return ["AI Provider Cascade"]
        else:
            return ["Cost-Aware Decision Flow"]

    def understand_system(self) -> Dict:
        """
        Get complete 4D system understanding.

        This is the main API for system self-awareness.
        The system understands itself through SPACE (X,Y,Z) and TIME (T).
        """
        components = self.topology.get("components", {})

        # Count by type
        by_type = {}
        for comp in components.values():
            t = comp.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1

        # Count by criticality
        by_criticality = {}
        for comp in components.values():
            c = comp.get("criticality", "standard")
            by_criticality[c] = by_criticality.get(c, 0) + 1

        # Identify critical paths
        critical_components = [
            comp["name"] for comp in components.values()
            if comp.get("criticality") == "critical"
        ]

        # TIME DIMENSION
        past_states = self.get_past(hours=24)
        present = self.get_present()
        future = self.predict_future(hours=24)

        return {
            "master": MASTER,
            "timestamp": datetime.now(timezone.utc).isoformat(),

            # DIMENSION X: WHAT
            "total_components": len(components),
            "components_by_type": by_type,

            # DIMENSION Y: WHY
            "system_purpose": f"Autonomous system serving {MASTER}",
            "critical_components": critical_components,
            "criticality_distribution": by_criticality,

            # DIMENSION Z: HOW
            "flows": [f["name"] for f in self.topology.get("flows", [])],
            "main_flow": "Cost-Aware Decision Flow",

            # DIMENSION T: TIME (the true 4th dimension)
            "time": {
                # PAST - What happened
                "past": {
                    "states_recorded": len(past_states),
                    "oldest_state": past_states[0].get('timestamp') if past_states else None,
                    "events_24h": sum(len(s.get('events', [])) for s in past_states),
                    "balance_change_24h": (
                        past_states[-1].get('balance', 0) - past_states[0].get('balance', 0)
                        if len(past_states) >= 2 else 0
                    )
                },
                # PRESENT - What is
                "present": {
                    "balance": present.get('balance'),
                    "positions": present.get('positions_value'),
                    "components_active": present.get('components_active'),
                    "infra_cost_hourly": present.get('infra_cost_hourly')
                },
                # FUTURE - What will be
                "future": {
                    "predictions": len(future),
                    "details": [
                        {
                            "type": p.prediction_type,
                            "value": p.predicted_value,
                            "confidence": p.confidence
                        } for p in future
                    ]
                }
            },

            # Schedule
            "schedule": self.topology.get("temporal_schedule", {}),

            # UNDERSTANDING
            "key_insight": "The system exists as a CONTINUUM through time. It remembers its past, knows its present, and predicts its future."
        }

    def print_topology(self):
        """Print human-readable 4D topology."""
        understanding = self.understand_system()

        print(f"\n{'='*70}")
        print(f"4D SYSTEM TOPOLOGY - PAST → PRESENT → FUTURE")
        print(f"{'='*70}")
        print(f"Master: {understanding['master']}")
        print(f"Purpose: {understanding['system_purpose']}")

        print(f"\n[X] WHAT - Components: {understanding['total_components']}")
        for t, count in understanding['components_by_type'].items():
            print(f"  {t}: {count}")

        print(f"\n[Y] WHY - Critical Components:")
        for comp in understanding['critical_components']:
            print(f"  - {comp}")

        print(f"\n[Z] HOW - Process Flows:")
        for flow in understanding['flows']:
            print(f"  - {flow}")

        # TIME - The 4th Dimension
        time_data = understanding.get('time', {})
        print(f"\n[T] TIME - The 4th Dimension:")

        past = time_data.get('past', {})
        print(f"\n  PAST (What Happened):")
        print(f"    States recorded: {past.get('states_recorded', 0)}")
        print(f"    Events (24h): {past.get('events_24h', 0)}")
        balance_change = past.get('balance_change_24h', 0)
        change_symbol = '+' if balance_change >= 0 else ''
        print(f"    Balance change (24h): {change_symbol}${balance_change:.2f}")

        present = time_data.get('present', {})
        print(f"\n  PRESENT (What Is):")
        print(f"    Balance: ${present.get('balance', 0):.2f}")
        print(f"    Positions: ${present.get('positions', 0):.2f}")
        print(f"    Active components: {present.get('components_active', 0)}")
        print(f"    Hourly cost: ${present.get('infra_cost_hourly', 0):.4f}")

        future = time_data.get('future', {})
        print(f"\n  FUTURE (What Will Be):")
        print(f"    Predictions: {future.get('predictions', 0)}")
        for pred in future.get('details', []):
            print(f"    - {pred['type']}: {pred['value']:.2f} ({pred['confidence']*100:.0f}% confidence)")

        print(f"\n[SCHEDULE]")
        for timing, components in understanding.get('schedule', {}).items():
            print(f"  {timing}: {len(components)} components")

        print(f"\n[INSIGHT] {understanding['key_insight']}")
        print(f"{'='*70}")


# Global instance
_topology: Optional[TopologyManager] = None


def get_topology() -> TopologyManager:
    """Get or create global topology manager."""
    global _topology
    if _topology is None:
        _topology = TopologyManager()
    return _topology


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description="4D System Topology - PAST → PRESENT → FUTURE")
    parser.add_argument("command", choices=["show", "component", "why", "flow", "past", "present", "future", "record"])
    parser.add_argument("--id", help="Component ID")
    parser.add_argument("--action", help="Action to trace")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back/forward")
    parser.add_argument("--event", help="Event to record")

    args = parser.parse_args()
    topology = get_topology()

    if args.command == "show":
        topology.print_topology()

    elif args.command == "component":
        if not args.id:
            print("Available components:")
            for comp_id in topology.topology.get("components", {}).keys():
                print(f"  - {comp_id}")
        else:
            comp = topology.get_component(args.id)
            if comp:
                print(f"\n{comp['name']} ({comp['id']})")
                print(f"  Type: {comp['type']}")
                print(f"  Status: {comp['status']}")
                print(f"  Purpose: {comp['purpose']}")
                print(f"  Value: {comp['value_to_master']}")
                print(f"  Criticality: {comp['criticality']}")
                print(f"  Depends on: {comp['depends_on']}")
                print(f"  Provides to: {comp['provides_to']}")
            else:
                print(f"Component {args.id} not found")

    elif args.command == "why":
        if args.id:
            print(topology.get_why(args.id))
        else:
            print("Use --id to specify component")

    elif args.command == "flow":
        if args.action:
            flows = topology.get_flow_for_action(args.action)
            print(f"Action '{args.action}' follows: {flows}")
        else:
            for flow in topology.topology.get("flows", []):
                print(f"\n{flow['name']}")
                print(f"  {flow['description']}")
                print(f"  Path: {' → '.join(flow['path'])}")

    # TIME DIMENSION COMMANDS
    elif args.command == "past":
        print(f"\n{'='*60}")
        print(f"PAST - Last {args.hours} hours")
        print(f"{'='*60}")
        past = topology.get_past(hours=args.hours)
        print(f"States recorded: {len(past)}")
        if past:
            print(f"Oldest: {past[0].get('timestamp', 'unknown')}")
            print(f"Newest: {past[-1].get('timestamp', 'unknown')}")
            print(f"\nBalance trend:")
            for state in past[-5:]:  # Last 5 states
                print(f"  {state.get('timestamp', '?')[:19]}: ${state.get('balance', 0):.2f}")
            print(f"\nEvents:")
            for state in past:
                for event in state.get('events', []):
                    print(f"  - {event}")

    elif args.command == "present":
        print(f"\n{'='*60}")
        print(f"PRESENT - Current State")
        print(f"{'='*60}")
        present = topology.get_present()
        print(f"Timestamp: {present.get('timestamp', 'unknown')}")
        print(f"Master: {present.get('master')}")
        print(f"\nFinancial:")
        print(f"  Balance: ${present.get('balance', 0):.2f}")
        print(f"  Positions: ${present.get('positions_value', 0):.2f}")
        print(f"  Total: ${present.get('balance', 0) + present.get('positions_value', 0):.2f}")
        print(f"\nOperational:")
        print(f"  Components active: {present.get('components_active', 0)}")
        print(f"  AI calls today: {present.get('ai_calls_today', 0)}")
        print(f"  Hourly infra cost: ${present.get('infra_cost_hourly', 0):.4f}")

    elif args.command == "future":
        print(f"\n{'='*60}")
        print(f"FUTURE - Predictions for next {args.hours} hours")
        print(f"{'='*60}")
        predictions = topology.predict_future(hours=args.hours)
        if predictions:
            for pred in predictions:
                confidence_bar = '█' * int(pred.confidence * 10) + '░' * (10 - int(pred.confidence * 10))
                print(f"\n{pred.prediction_type}:")
                print(f"  Predicted: {pred.predicted_value:.2f}")
                print(f"  Confidence: [{confidence_bar}] {pred.confidence*100:.0f}%")
                print(f"  Basis: {pred.basis}")
        else:
            print("No predictions available (need more historical data)")

    elif args.command == "record":
        events = [args.event] if args.event else []
        state = topology.record_state(events=events)
        print(f"State recorded at {state.timestamp}")
        print(f"  Components active: {state.components_active}")
        print(f"  Balance: ${state.balance:.2f}")
        if events:
            print(f"  Events: {events}")


if __name__ == "__main__":
    main()
