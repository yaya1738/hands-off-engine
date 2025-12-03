#!/usr/bin/env python3
"""
Circuit Board - Full System Interconnect Architecture
======================================================

Complete circuit board where EVERYTHING connects to EVERYTHING.
Transistors at every inflection point control signal flow.

ARCHITECTURE:
============

                    ┌─────────────────────────────────────────────────────────┐
                    │                    POWER RAIL (+V)                       │
                    │  Knowledge: Computing | Business | Money                 │
                    └─────────────────────────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
               ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
               │   T1    │              │   T2    │              │   T3    │
               │ TRADING │              │ INFRA   │              │ REVENUE │
               └────┬────┘              └────┬────┘              └────┬────┘
                    │                        │                        │
          ┌─────────┼────────────────────────┼────────────────────────┼─────────┐
          │         │                        │                        │         │
          │    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐    │
          │    │ MARKET  │◄────────────►│ SCALING │◄────────────►│ GROWTH  │    │
          │    │ EXECUTOR│              │ ENGINE  │              │ ENGINE  │    │
          │    └────┬────┘              └────┬────┘              └────┬────┘    │
          │         │                        │                        │         │
          │         └────────────┬───────────┴───────────┬────────────┘         │
          │                      │                       │                      │
          │                 ┌────▼────┐            ┌────▼────┐                  │
          │                 │   T4    │            │   T5    │                  │
          │                 │ REALITY │            │ HEALING │                  │
          │                 └────┬────┘            └────┬────┘                  │
          │                      │                      │                       │
          │                      └──────────┬───────────┘                       │
          │                                 │                                   │
          │                           ┌─────▼─────┐                             │
          │                           │  SIGNAL   │                             │
          │                           │   BUS     │                             │
          │                           └─────┬─────┘                             │
          │                                 │                                   │
          └─────────────────────────────────┼───────────────────────────────────┘
                                            │
                    ┌───────────────────────▼───────────────────────┐
                    │                 GROUND (GND)                   │
                    │            State Persistence Layer             │
                    └───────────────────────────────────────────────┘

TRANSISTORS (Control Gates):
============================
T1 - Trading Gate: Controls market execution signals
T2 - Infrastructure Gate: Controls scaling/resource signals
T3 - Revenue Gate: Controls income optimization signals
T4 - Reality Gate: Controls external state feedback
T5 - Healing Gate: Controls self-repair signals

SIGNAL TYPES:
=============
- VOLTAGE (V): Knowledge potential energy
- CURRENT (I): Active execution flow
- RESISTANCE (R): Risk/constraint factors
- CAPACITANCE (C): State storage
- INDUCTANCE (L): Momentum/trend

Serving: Yair Siegel
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

CIRCUIT_STATE = STATE_DIR / "circuit_board.json"


class SignalType(Enum):
    """Types of signals flowing through the circuit."""
    VOLTAGE = "voltage"      # Knowledge potential
    CURRENT = "current"      # Execution flow
    PULSE = "pulse"          # Event trigger
    DATA = "data"            # Information packet
    FEEDBACK = "feedback"    # Return signal
    CONTROL = "control"      # Gate control


@dataclass
class Signal:
    """A signal flowing through the circuit."""
    type: SignalType
    source: str
    destination: str
    payload: Any
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    strength: float = 1.0  # 0.0 to 1.0
    priority: int = 5      # 1-10, higher = more urgent


@dataclass
class Transistor:
    """
    Control gate at an inflection point.

    Like a real transistor:
    - Base: Control input (knowledge/context)
    - Collector: High-potential input (opportunity)
    - Emitter: Output (action)

    Gate opens when base signal exceeds threshold.
    """
    name: str
    threshold: float = 0.5
    gain: float = 1.0
    state: str = "off"  # off, saturated, active

    # Connected knowledge sources
    knowledge_sources: List[str] = field(default_factory=list)

    # Signal routing
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)

    # Statistics
    signals_processed: int = 0
    signals_blocked: int = 0
    last_activation: Optional[str] = None

    def evaluate(self, base_signal: float, collector_signal: float) -> tuple:
        """
        Evaluate transistor output.

        Returns: (output_signal, state)
        """
        if base_signal < self.threshold:
            self.state = "off"
            self.signals_blocked += 1
            return 0.0, "blocked"

        if base_signal >= 0.9:
            self.state = "saturated"
            output = collector_signal * self.gain
        else:
            self.state = "active"
            # Linear region: output proportional to base
            output = collector_signal * (base_signal / self.threshold) * self.gain

        self.signals_processed += 1
        self.last_activation = datetime.now(timezone.utc).isoformat()
        return min(output, 1.0), self.state


class SignalBus:
    """
    Central signal bus connecting all components.

    Like a PCB trace carrying signals between components.
    """

    def __init__(self):
        self.queue = Queue()
        self.subscribers: Dict[str, List[Callable]] = {}
        self.history: List[Signal] = []
        self.max_history = 1000
        self.running = False
        self._thread = None

    def publish(self, signal: Signal):
        """Publish a signal to the bus."""
        self.queue.put(signal)
        self.history.append(signal)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def subscribe(self, destination: str, callback: Callable):
        """Subscribe to signals for a destination."""
        if destination not in self.subscribers:
            self.subscribers[destination] = []
        self.subscribers[destination].append(callback)

    def _process_signals(self):
        """Process signals in the queue."""
        while self.running:
            try:
                signal = self.queue.get(timeout=0.1)
                dest = signal.destination

                # Deliver to all subscribers for this destination
                if dest in self.subscribers:
                    for callback in self.subscribers[dest]:
                        try:
                            callback(signal)
                        except Exception as e:
                            pass  # Log but don't crash

                # Also deliver to wildcard subscribers
                if "*" in self.subscribers:
                    for callback in self.subscribers["*"]:
                        try:
                            callback(signal)
                        except:
                            pass

            except Empty:
                continue

    def start(self):
        """Start the signal bus."""
        self.running = True
        self._thread = threading.Thread(target=self._process_signals, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the signal bus."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)


class CircuitBoard:
    """
    Full system circuit board - everything connected to everything.

    Components:
    - Power Rail: Knowledge bases (computing, business, money)
    - Transistors: Control gates at inflection points
    - Signal Bus: Central interconnect
    - Ground: State persistence
    """

    def __init__(self):
        self.master = "Yair Siegel"
        self.initialized = datetime.now(timezone.utc).isoformat()

        # Initialize signal bus
        self.bus = SignalBus()

        # Initialize transistors at inflection points
        self.transistors = self._init_transistors()

        # Initialize component connections
        self.components = self._init_components()

        # Load knowledge (power rail)
        self.power_rail = self._init_power_rail()

        # Circuit state
        self.state = {
            "power_on": False,
            "cycles": 0,
            "total_signals": 0,
            "last_cycle": None,
        }

    def _init_transistors(self) -> Dict[str, Transistor]:
        """Initialize transistors at all inflection points."""
        return {
            # Primary gates
            "T1_TRADING": Transistor(
                name="Trading Gate",
                threshold=0.4,  # Lower threshold - we want to trade
                gain=1.2,       # Amplify good signals
                knowledge_sources=["money"],
                inputs=["market_data", "signals", "portfolio"],
                outputs=["orders", "positions"],
            ),
            "T2_INFRA": Transistor(
                name="Infrastructure Gate",
                threshold=0.6,
                gain=1.0,
                knowledge_sources=["computing"],
                inputs=["load", "health", "costs"],
                outputs=["scaling", "provisioning"],
            ),
            "T3_REVENUE": Transistor(
                name="Revenue Gate",
                threshold=0.5,
                gain=1.1,
                knowledge_sources=["business", "money"],
                inputs=["opportunities", "leads", "conversions"],
                outputs=["outreach", "pricing"],
            ),
            "T4_REALITY": Transistor(
                name="Reality Gate",
                threshold=0.3,  # Very sensitive to reality
                gain=1.0,
                knowledge_sources=["computing", "business", "money"],
                inputs=["external_state", "feedback", "metrics"],
                outputs=["adjustments", "alerts"],
            ),
            "T5_HEALING": Transistor(
                name="Healing Gate",
                threshold=0.7,  # Only heal when necessary
                gain=1.5,       # Strong response when needed
                knowledge_sources=["computing"],
                inputs=["errors", "anomalies", "degradation"],
                outputs=["repairs", "recovery"],
            ),

            # Secondary gates (cross-connections)
            "T6_TRADE_INFRA": Transistor(
                name="Trade-Infra Bridge",
                threshold=0.5,
                knowledge_sources=["computing", "money"],
                inputs=["trading_load", "latency"],
                outputs=["trading_resources"],
            ),
            "T7_REVENUE_TRADE": Transistor(
                name="Revenue-Trade Bridge",
                threshold=0.5,
                knowledge_sources=["business", "money"],
                inputs=["trading_pnl", "revenue_targets"],
                outputs=["capital_allocation"],
            ),
            "T8_REALITY_HEAL": Transistor(
                name="Reality-Heal Bridge",
                threshold=0.6,
                knowledge_sources=["computing"],
                inputs=["reality_issues", "system_health"],
                outputs=["proactive_fixes"],
            ),

            # Feedback gates
            "T9_FEEDBACK_TRADE": Transistor(
                name="Trade Feedback",
                threshold=0.4,
                knowledge_sources=["money"],
                inputs=["trade_outcomes", "market_response"],
                outputs=["strategy_adjustments"],
            ),
            "T10_FEEDBACK_REVENUE": Transistor(
                name="Revenue Feedback",
                threshold=0.4,
                knowledge_sources=["business"],
                inputs=["conversion_rates", "customer_feedback"],
                outputs=["offer_adjustments"],
            ),
        }

    def _init_components(self) -> Dict[str, Dict]:
        """Initialize all system components and their connections."""
        return {
            # Execution components
            "market_executor": {
                "type": "executor",
                "inputs": ["T1_TRADING"],
                "outputs": ["T9_FEEDBACK_TRADE"],
                "module": "executor.polymarket_full_stack",
            },
            "scaling_engine": {
                "type": "executor",
                "inputs": ["T2_INFRA", "T6_TRADE_INFRA"],
                "outputs": ["T4_REALITY"],
                "module": "autonomous.scaling_engine",
            },
            "growth_engine": {
                "type": "executor",
                "inputs": ["T3_REVENUE", "T7_REVENUE_TRADE"],
                "outputs": ["T10_FEEDBACK_REVENUE"],
                "module": "autonomous.active_pursuit",
            },

            # Monitoring components
            "reality_monitor": {
                "type": "monitor",
                "inputs": ["T4_REALITY"],
                "outputs": ["T8_REALITY_HEAL", "T1_TRADING", "T2_INFRA", "T3_REVENUE"],
                "module": "autonomous.reality_feedback",
            },
            "self_healer": {
                "type": "healer",
                "inputs": ["T5_HEALING", "T8_REALITY_HEAL"],
                "outputs": ["T4_REALITY"],
                "module": "autonomous.self_healer",
            },

            # Knowledge components (power rail)
            "knowledge_nexus": {
                "type": "power",
                "inputs": [],
                "outputs": ["T1_TRADING", "T2_INFRA", "T3_REVENUE", "T4_REALITY", "T5_HEALING"],
                "module": "autonomous.knowledge_nexus",
            },

            # Coordination components
            "mega_coordinator": {
                "type": "coordinator",
                "inputs": ["T4_REALITY"],
                "outputs": ["T2_INFRA", "T5_HEALING"],
                "module": "autonomous.mega_integration",
            },
            "backend_loop": {
                "type": "orchestrator",
                "inputs": ["*"],  # Receives all signals
                "outputs": ["*"],  # Can send to all
                "module": "autonomous.backend_loop",
            },
        }

    def _init_power_rail(self) -> Dict[str, Any]:
        """Initialize power rail (knowledge bases)."""
        power = {
            "voltage": 0.0,  # Overall system potential
            "sources": {},
        }

        try:
            from autonomous.knowledge_nexus import get_nexus
            nexus = get_nexus()
            status = nexus.status()

            power["sources"] = {
                "computing": {
                    "loaded": status["knowledge_bases"]["computing"]["loaded"],
                    "voltage": 1.0 if status["knowledge_bases"]["computing"]["loaded"] else 0.0,
                },
                "business": {
                    "loaded": status["knowledge_bases"]["business"]["loaded"],
                    "voltage": 1.0 if status["knowledge_bases"]["business"]["loaded"] else 0.0,
                },
                "money": {
                    "loaded": status["knowledge_bases"]["money"]["loaded"],
                    "voltage": 1.0 if status["knowledge_bases"]["money"]["loaded"] else 0.0,
                },
            }

            # Total voltage = average of all sources
            voltages = [s["voltage"] for s in power["sources"].values()]
            power["voltage"] = sum(voltages) / len(voltages) if voltages else 0.0

        except Exception as e:
            power["error"] = str(e)

        return power

    def power_on(self):
        """Power on the circuit board."""
        self.bus.start()
        self.state["power_on"] = True

        # Send initial power signal to all transistors
        for t_name, transistor in self.transistors.items():
            signal = Signal(
                type=SignalType.VOLTAGE,
                source="power_rail",
                destination=t_name,
                payload={"voltage": self.power_rail["voltage"]},
                strength=self.power_rail["voltage"],
            )
            self.bus.publish(signal)

        return {"status": "powered_on", "voltage": self.power_rail["voltage"]}

    def power_off(self):
        """Power off the circuit board."""
        self.bus.stop()
        self.state["power_on"] = False
        return {"status": "powered_off"}

    def send_signal(self, source: str, destination: str,
                    signal_type: SignalType, payload: Any,
                    strength: float = 1.0) -> Dict:
        """Send a signal through the circuit."""
        signal = Signal(
            type=signal_type,
            source=source,
            destination=destination,
            payload=payload,
            strength=strength,
        )

        # If destination is a transistor, evaluate it
        if destination in self.transistors:
            transistor = self.transistors[destination]

            # Get base signal from knowledge
            base_signal = self._get_knowledge_signal(transistor.knowledge_sources)

            # Evaluate transistor
            output, state = transistor.evaluate(base_signal, strength)

            if output > 0:
                # Signal passed through - publish to next destinations
                for out_dest in transistor.outputs:
                    out_signal = Signal(
                        type=signal_type,
                        source=destination,
                        destination=out_dest,
                        payload=payload,
                        strength=output,
                    )
                    self.bus.publish(out_signal)

                return {
                    "status": "passed",
                    "transistor": destination,
                    "state": state,
                    "output_strength": output,
                }
            else:
                return {
                    "status": "blocked",
                    "transistor": destination,
                    "state": state,
                    "reason": "below_threshold",
                }
        else:
            # Direct signal to component
            self.bus.publish(signal)
            return {"status": "sent", "destination": destination}

    def _get_knowledge_signal(self, sources: List[str]) -> float:
        """Get combined knowledge signal from sources."""
        if not sources:
            return 0.5  # Default neutral

        total = 0.0
        for source in sources:
            if source in self.power_rail.get("sources", {}):
                total += self.power_rail["sources"][source].get("voltage", 0)

        return total / len(sources) if sources else 0.0

    def run_cycle(self) -> Dict[str, Any]:
        """Run one complete circuit cycle."""
        self.state["cycles"] += 1
        self.state["last_cycle"] = datetime.now(timezone.utc).isoformat()

        cycle_result = {
            "cycle": self.state["cycles"],
            "timestamp": self.state["last_cycle"],
            "power_rail": self.power_rail["voltage"],
            "transistors": {},
            "signals_sent": 0,
        }

        # 1. Refresh power rail
        self.power_rail = self._init_power_rail()

        # 2. Query reality (T4)
        reality_signal = self._query_reality()
        result = self.send_signal(
            "reality_monitor", "T4_REALITY",
            SignalType.DATA, reality_signal,
            strength=0.8
        )
        cycle_result["transistors"]["T4_REALITY"] = result
        cycle_result["signals_sent"] += 1

        # 3. Trading signal (T1)
        trading_signal = self._query_trading()
        result = self.send_signal(
            "market_executor", "T1_TRADING",
            SignalType.DATA, trading_signal,
            strength=trading_signal.get("opportunity_strength", 0.5)
        )
        cycle_result["transistors"]["T1_TRADING"] = result
        cycle_result["signals_sent"] += 1

        # 4. Infrastructure signal (T2)
        infra_signal = self._query_infrastructure()
        result = self.send_signal(
            "scaling_engine", "T2_INFRA",
            SignalType.DATA, infra_signal,
            strength=infra_signal.get("load", 0.5)
        )
        cycle_result["transistors"]["T2_INFRA"] = result
        cycle_result["signals_sent"] += 1

        # 5. Revenue signal (T3)
        revenue_signal = self._query_revenue()
        result = self.send_signal(
            "growth_engine", "T3_REVENUE",
            SignalType.DATA, revenue_signal,
            strength=revenue_signal.get("opportunity", 0.5)
        )
        cycle_result["transistors"]["T3_REVENUE"] = result
        cycle_result["signals_sent"] += 1

        # 6. Check if healing needed (T5)
        healing_signal = self._query_health()
        if healing_signal.get("needs_healing", False):
            result = self.send_signal(
                "self_healer", "T5_HEALING",
                SignalType.PULSE, healing_signal,
                strength=healing_signal.get("severity", 0.5)
            )
            cycle_result["transistors"]["T5_HEALING"] = result
            cycle_result["signals_sent"] += 1

        # 7. Bridge transistors - cross-domain connections
        # T6: Trade-Infra Bridge (trading needs resources)
        if cycle_result["transistors"].get("T1_TRADING", {}).get("status") == "passed":
            trade_infra_signal = {
                "trading_load": trading_signal.get("opportunity_strength", 0.5),
                "latency_requirement": "low",
                "source": "T1_TRADING",
            }
            result = self.send_signal(
                "T1_TRADING", "T6_TRADE_INFRA",
                SignalType.CONTROL, trade_infra_signal,
                strength=0.7
            )
            cycle_result["transistors"]["T6_TRADE_INFRA"] = result
            cycle_result["signals_sent"] += 1

        # T7: Revenue-Trade Bridge (revenue affects capital allocation)
        if cycle_result["transistors"].get("T3_REVENUE", {}).get("status") == "passed":
            revenue_trade_signal = {
                "revenue_status": revenue_signal.get("opportunity", 0.5),
                "capital_available": True,
                "source": "T3_REVENUE",
            }
            result = self.send_signal(
                "T3_REVENUE", "T7_REVENUE_TRADE",
                SignalType.CONTROL, revenue_trade_signal,
                strength=0.6
            )
            cycle_result["transistors"]["T7_REVENUE_TRADE"] = result
            cycle_result["signals_sent"] += 1

        # T8: Reality-Heal Bridge (reality issues trigger healing)
        if cycle_result["transistors"].get("T4_REALITY", {}).get("status") == "passed":
            reality_heal_signal = {
                "reality_check": reality_signal,
                "proactive": True,
                "source": "T4_REALITY",
            }
            result = self.send_signal(
                "T4_REALITY", "T8_REALITY_HEAL",
                SignalType.CONTROL, reality_heal_signal,
                strength=0.6
            )
            cycle_result["transistors"]["T8_REALITY_HEAL"] = result
            cycle_result["signals_sent"] += 1

        # T9: Trade Feedback (learning from outcomes)
        if cycle_result["transistors"].get("T1_TRADING", {}).get("status") == "passed":
            trade_feedback_signal = {
                "trade_executed": True,
                "feedback_type": "outcome",
                "source": "T1_TRADING",
            }
            result = self.send_signal(
                "T1_TRADING", "T9_FEEDBACK_TRADE",
                SignalType.FEEDBACK, trade_feedback_signal,
                strength=0.5
            )
            cycle_result["transistors"]["T9_FEEDBACK_TRADE"] = result
            cycle_result["signals_sent"] += 1

        # T10: Revenue Feedback (conversion learning)
        if cycle_result["transistors"].get("T3_REVENUE", {}).get("status") == "passed":
            revenue_feedback_signal = {
                "revenue_cycle": True,
                "feedback_type": "conversion",
                "source": "T3_REVENUE",
            }
            result = self.send_signal(
                "T3_REVENUE", "T10_FEEDBACK_REVENUE",
                SignalType.FEEDBACK, revenue_feedback_signal,
                strength=0.5
            )
            cycle_result["transistors"]["T10_FEEDBACK_REVENUE"] = result
            cycle_result["signals_sent"] += 1

        # Update total signals
        self.state["total_signals"] += cycle_result["signals_sent"]

        # Save state
        self.save_state()

        return cycle_result

    def _query_reality(self) -> Dict:
        """Query reality state."""
        try:
            from autonomous.knowledge_nexus import get_nexus
            nexus = get_nexus()
            return nexus.query("reality")
        except:
            return {"status": "unknown"}

    def _query_trading(self) -> Dict:
        """Query trading state."""
        try:
            from autonomous.knowledge_nexus import get_nexus
            nexus = get_nexus()
            context = nexus.query("trading")

            # Add opportunity strength based on recommendations
            recs = len(context.get("recommendations", []))
            context["opportunity_strength"] = min(0.4 + (recs * 0.1), 1.0)

            return context
        except:
            return {"opportunity_strength": 0.3}

    def _query_infrastructure(self) -> Dict:
        """Query infrastructure state."""
        try:
            from autonomous.mega_integration import MegaCoordinator
            mc = MegaCoordinator()
            status = mc.status()

            # Calculate load from status
            mega = status.get("mega_state", {})
            health = mega.get("system_health_score", 80) / 100

            return {
                "load": 1.0 - health,  # Higher load = lower health
                "vcpus": mega.get("total_vcpus", 0),
                "nodes": mega.get("total_nodes", 0),
            }
        except:
            return {"load": 0.5}

    def _query_revenue(self) -> Dict:
        """Query revenue state."""
        try:
            from autonomous.knowledge_nexus import get_nexus
            nexus = get_nexus()
            context = nexus.query("revenue")

            # Calculate opportunity score
            tools = len(context.get("available_tools", []))
            context["opportunity"] = min(0.3 + (tools * 0.1), 1.0)

            return context
        except:
            return {"opportunity": 0.3}

    def _query_health(self) -> Dict:
        """Query system health for healing."""
        try:
            # Check for issues
            issues = []

            # Check power rail
            if self.power_rail["voltage"] < 0.8:
                issues.append("low_power")

            # Check transistor states
            for name, t in self.transistors.items():
                if t.signals_blocked > t.signals_processed * 2:
                    issues.append(f"{name}_blocking")

            return {
                "needs_healing": len(issues) > 0,
                "issues": issues,
                "severity": min(len(issues) * 0.3, 1.0),
            }
        except:
            return {"needs_healing": False}

    def get_circuit_diagram(self) -> str:
        """Get ASCII circuit diagram."""
        diagram = """
╔════════════════════════════════════════════════════════════════════════════╗
║                         HANDS-OFF ENGINE CIRCUIT BOARD                      ║
║                              Serving: Yair Siegel                           ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  ┌─────────────────────────── POWER RAIL (+V) ───────────────────────────┐ ║
║  │  Computing [{c}]     Business [{b}]     Money [{m}]    │ ║
║  │                        Voltage: {v:.2f}V                              │ ║
║  └───────────────────────────────┬───────────────────────────────────────┘ ║
║                                  │                                          ║
║          ┌───────────────────────┼───────────────────────┐                  ║
║          │                       │                       │                  ║
║     ┌────▼────┐             ┌────▼────┐            ┌────▼────┐             ║
║     │ T1 [{t1}] │             │ T2 [{t2}] │            │ T3 [{t3}] │             ║
║     │ TRADING │             │  INFRA  │            │ REVENUE │             ║
║     │ thr:{th1:.1f} │             │ thr:{th2:.1f} │            │ thr:{th3:.1f} │             ║
║     └────┬────┘             └────┬────┘            └────┬────┘             ║
║          │                       │                      │                   ║
║    ┌─────▼─────┐           ┌─────▼─────┐          ┌─────▼─────┐            ║
║    │  MARKET   │◄─────────►│  SCALING  │◄────────►│  GROWTH   │            ║
║    │ EXECUTOR  │           │  ENGINE   │          │  ENGINE   │            ║
║    └─────┬─────┘           └─────┬─────┘          └─────┬─────┘            ║
║          │                       │                      │                   ║
║          └───────────┬───────────┴───────────┬──────────┘                   ║
║                      │                       │                              ║
║                 ┌────▼────┐            ┌────▼────┐                          ║
║                 │ T4 [{t4}] │            │ T5 [{t5}] │                          ║
║                 │ REALITY │            │ HEALING │                          ║
║                 │ thr:{th4:.1f} │            │ thr:{th5:.1f} │                          ║
║                 └────┬────┘            └────┬────┘                          ║
║                      │                      │                               ║
║                      └──────────┬───────────┘                               ║
║                                 │                                           ║
║                      ┌──────────▼──────────┐                                ║
║                      │     SIGNAL BUS      │                                ║
║                      │   Signals: {sig:>6}   │                                ║
║                      └──────────┬──────────┘                                ║
║                                 │                                           ║
║  ┌──────────────────────────────▼──────────────────────────────────────┐   ║
║  │                         GROUND (State Layer)                         │   ║
║  │                    Cycles: {cyc:>6}  │  Last: {last}                │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
        # Fill in values
        sources = self.power_rail.get("sources", {})
        t = self.transistors

        return diagram.format(
            c="✓" if sources.get("computing", {}).get("loaded") else "✗",
            b="✓" if sources.get("business", {}).get("loaded") else "✗",
            m="✓" if sources.get("money", {}).get("loaded") else "✗",
            v=self.power_rail.get("voltage", 0),
            t1=t["T1_TRADING"].state[0].upper(),
            t2=t["T2_INFRA"].state[0].upper(),
            t3=t["T3_REVENUE"].state[0].upper(),
            t4=t["T4_REALITY"].state[0].upper(),
            t5=t["T5_HEALING"].state[0].upper(),
            th1=t["T1_TRADING"].threshold,
            th2=t["T2_INFRA"].threshold,
            th3=t["T3_REVENUE"].threshold,
            th4=t["T4_REALITY"].threshold,
            th5=t["T5_HEALING"].threshold,
            sig=self.state["total_signals"],
            cyc=self.state["cycles"],
            last=self.state.get("last_cycle", "never")[:19] if self.state.get("last_cycle") else "never",
        )

    def status(self) -> Dict[str, Any]:
        """Get circuit board status."""
        return {
            "master": self.master,
            "initialized": self.initialized,
            "power_on": self.state["power_on"],
            "power_rail": {
                "voltage": self.power_rail["voltage"],
                "sources": {k: v["loaded"] for k, v in self.power_rail.get("sources", {}).items()},
            },
            "transistors": {
                name: {
                    "state": t.state,
                    "threshold": t.threshold,
                    "processed": t.signals_processed,
                    "blocked": t.signals_blocked,
                }
                for name, t in self.transistors.items()
            },
            "state": self.state,
        }

    def save_state(self):
        """Save circuit state."""
        state = self.status()
        state["saved_at"] = datetime.now(timezone.utc).isoformat()
        with open(CIRCUIT_STATE, 'w') as f:
            json.dump(state, f, indent=2, default=str)


# ========== GLOBAL INSTANCE ==========

_circuit = None

def get_circuit() -> CircuitBoard:
    """Get or create the global circuit board."""
    global _circuit
    if _circuit is None:
        _circuit = CircuitBoard()
    return _circuit


# ========== CLI ==========

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Circuit Board")
    parser.add_argument("command", choices=["status", "diagram", "cycle", "power-on", "run"])
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles for run")
    parser.add_argument("--interval", type=int, default=60, help="Interval between cycles")
    args = parser.parse_args()

    circuit = get_circuit()

    if args.command == "status":
        print(json.dumps(circuit.status(), indent=2))

    elif args.command == "diagram":
        print(circuit.get_circuit_diagram())

    elif args.command == "power-on":
        result = circuit.power_on()
        print(f"Circuit powered on: {result}")
        print(circuit.get_circuit_diagram())

    elif args.command == "cycle":
        result = circuit.run_cycle()
        print(json.dumps(result, indent=2))

    elif args.command == "run":
        print("Starting circuit board continuous operation...")
        circuit.power_on()

        for i in range(args.cycles):
            print(f"\n=== Cycle {i+1}/{args.cycles} ===")
            result = circuit.run_cycle()
            print(f"Signals sent: {result['signals_sent']}")
            for t_name, t_result in result["transistors"].items():
                print(f"  {t_name}: {t_result['status']}")

            if i < args.cycles - 1:
                print(f"Next cycle in {args.interval}s...")
                time.sleep(args.interval)

        circuit.power_off()
        print("\nCircuit powered off.")


if __name__ == "__main__":
    main()
