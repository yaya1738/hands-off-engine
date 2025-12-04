#!/usr/bin/env python3
"""
INTEGRAFIX: ABCFC-HFT Frequency Bridge
======================================

CONCEPT: Everything happens at HFT frequency - including ABCFC updates.

The ABCFC hierarchy is not static - it's a living system that updates
in microseconds as trades execute and positions change.

FREQUENCY LAYERS:
1. MICROSECOND (1μs)    - HFT order placement
2. MILLISECOND (1ms)    - Position updates
3. SECOND (1s)          - ABCFC recalculation
4. MINUTE (60s)         - Nexus cloud evaluation
5. HOUR (3600s)         - Strategic rebalancing

ABCFC AT HFT SPEED:
- Every trade updates bounds [worst, best]
- Every fill updates expected value
- Every second, recalculate E[X|t]
- Every minute, re-evaluate nexus cloud
- Feed back into next trade decision

POLYMARKET FUNDAMENTALS (INTEGRAFIX):
- L2 order book depth analysis (walk the book)
- Maker vs Taker ABCFC distinction
- Self-impact awareness for large orders
- Kelly sizing from ABCFC edge
- Zero trading fees (but spread/slippage costs)
- Reusable collateral for limit orders

Created by: Yair Siegel
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

ABCFC_HFT_STATE = STATE_DIR / "abcfc_hft_frequency.json"


class FrequencyLayer(Enum):
    """Frequency layers for ABCFC updates."""
    MICRO = "microsecond"  # 1μs - order placement
    MILLI = "millisecond"  # 1ms - position update
    SECOND = "second"      # 1s - ABCFC recalc
    MINUTE = "minute"      # 60s - nexus eval
    HOUR = "hour"          # 3600s - rebalance


@dataclass
class ABCFC:
    """ABCFC bounds - worst/best/expected."""
    worst: float = 0.0
    best: float = 0.0
    expected: float = 0.0

    def to_dict(self) -> Dict:
        return {"worst": self.worst, "best": self.best, "expected": self.expected}


@dataclass
class HFTEvent:
    """Single HFT event with ABCFC impact."""
    timestamp_us: int  # Microsecond timestamp
    event_type: str    # order, fill, cancel, position_update
    side: str          # BUY, SELL
    size: float
    price: float
    pnl_impact: float  # How this changes expected value
    bounds_impact: Tuple[float, float]  # (worst_delta, best_delta)


@dataclass
class ABCFCHFTState:
    """Real-time ABCFC state at HFT frequency."""
    # Current ABCFC bounds
    total_abcfc: ABCFC = field(default_factory=ABCFC)
    trading_abcfc: ABCFC = field(default_factory=ABCFC)

    # HFT metrics
    events_per_second: float = 0.0
    updates_per_second: float = 0.0
    latency_us: int = 0

    # Flow rates ($/second)
    cost_per_sec: float = 0.0
    profit_per_sec: float = 0.0
    net_per_sec: float = 0.0

    # Nexus decision
    current_action: str = "hold"
    action_confidence: float = 0.0

    # Timestamps
    last_micro_update: int = 0
    last_second_update: int = 0
    last_nexus_eval: int = 0


class ABCFCHFTFrequency:
    """
    ABCFC at HFT Frequency - microsecond updates to hierarchical finance.

    Connects:
    - HFT Economics (cost/profit per second)
    - ABCFC Layers (hierarchical bounds)
    - ABCFC Nexus (decision engine)
    - HFT Execution Bridge (trade execution)
    """

    def __init__(self):
        self.state = ABCFCHFTState()
        self._events: deque = deque(maxlen=10000)  # Last 10K events
        self._lock = threading.Lock()

        # Lazy-loaded components
        self._hft_economics = None
        self._abcfc_layers = None
        self._abcfc_nexus = None
        self._hft_bridge = None

        # Load state
        self._load_state()

    # ==================== LAZY LOADING ====================

    @property
    def hft_economics(self):
        """HFT Economics for real-time cost/profit tracking."""
        if self._hft_economics is None:
            try:
                from integrafix.hft_economics import get_hft_economics
                self._hft_economics = get_hft_economics()
            except:
                pass
        return self._hft_economics

    @property
    def abcfc_layers(self):
        """ABCFC Layers for hierarchical updates."""
        if self._abcfc_layers is None:
            try:
                from executor.math.abcfc_layers import get_layers
                self._abcfc_layers = get_layers()
            except:
                pass
        return self._abcfc_layers

    @property
    def abcfc_nexus(self):
        """ABCFC Nexus for decision making."""
        if self._abcfc_nexus is None:
            try:
                from executor.math.abcfc_nexus import get_nexus
                self._abcfc_nexus = get_nexus()
            except:
                pass
        return self._abcfc_nexus

    @property
    def hft_bridge(self):
        """HFT Execution Bridge for trade execution."""
        if self._hft_bridge is None:
            try:
                from autonomous.hft_execution_bridge import hft_bridge
                self._hft_bridge = hft_bridge
            except:
                pass
        return self._hft_bridge

    # ==================== FREQUENCY UPDATES ====================

    def micro_update(self, event: HFTEvent):
        """
        Microsecond update - called on every order/fill.
        Updates ABCFC bounds immediately.
        """
        with self._lock:
            now_us = int(time.time() * 1_000_000)

            # Update bounds from event
            self.state.trading_abcfc.expected += event.pnl_impact
            self.state.trading_abcfc.worst += event.bounds_impact[0]
            self.state.trading_abcfc.best += event.bounds_impact[1]

            # Propagate to total
            self.state.total_abcfc.expected = self.state.trading_abcfc.expected
            self.state.total_abcfc.worst = self.state.trading_abcfc.worst
            self.state.total_abcfc.best = self.state.trading_abcfc.best

            # Update metrics
            self._events.append(event)
            self.state.last_micro_update = now_us
            self.state.latency_us = now_us - event.timestamp_us

    def second_update(self):
        """
        Second-level update - recalculate ABCFC from all positions.
        Called every second.
        """
        now_us = int(time.time() * 1_000_000)

        # Calculate events per second
        recent_events = [e for e in self._events
                        if e.timestamp_us > now_us - 1_000_000]
        self.state.events_per_second = len(recent_events)

        # Get flow rates from HFT Economics
        if self.hft_economics:
            try:
                flow = self.hft_economics.get_flow_rate()
                self.state.cost_per_sec = flow.cost_per_sec if hasattr(flow, 'cost_per_sec') else 0
                self.state.profit_per_sec = flow.profit_per_sec if hasattr(flow, 'profit_per_sec') else 0
                self.state.net_per_sec = flow.net_per_sec if hasattr(flow, 'net_per_sec') else 0
            except:
                pass

        # Sync with ABCFC Layers
        if self.abcfc_layers:
            try:
                tf = self.abcfc_layers.nodes.get('total_finance')
                if tf:
                    self.state.total_abcfc.expected = tf.expected
                    self.state.total_abcfc.worst = tf.worst_case
                    self.state.total_abcfc.best = tf.best_case
            except:
                pass

        self.state.last_second_update = now_us
        self.state.updates_per_second = self.state.events_per_second

    def minute_update(self):
        """
        Minute-level update - evaluate ABCFC Nexus for decisions.
        Called every minute.
        """
        now_us = int(time.time() * 1_000_000)

        # Evaluate nexus for best action
        if self.abcfc_nexus:
            try:
                evaluation = self.abcfc_nexus.evaluate()
                best = self.abcfc_nexus.best_action()
                if best:
                    self.state.current_action = best.name
                    self.state.action_confidence = best.risk_adjusted_score
            except:
                pass

        self.state.last_nexus_eval = now_us

    # ==================== HFT INTEGRATION ====================

    def process_hft_trade(self, side: str, size: float, price: float,
                         pnl: float = 0.0) -> Dict:
        """
        Process an HFT trade and update ABCFC.

        Called by HFT execution system after each trade.
        """
        now_us = int(time.time() * 1_000_000)

        # Calculate bounds impact
        if side == "BUY":
            # Buying increases upside potential
            worst_delta = -size * price  # Risk: price goes to 0
            best_delta = size * (1 - price)  # Reward: price goes to 1
        else:
            # Selling locks in value
            worst_delta = -size * (1 - price)  # Risk: price goes to 1
            best_delta = size * price  # Reward: price goes to 0

        event = HFTEvent(
            timestamp_us=now_us,
            event_type="fill",
            side=side,
            size=size,
            price=price,
            pnl_impact=pnl,
            bounds_impact=(worst_delta, best_delta)
        )

        # Micro update
        self.micro_update(event)

        return {
            "processed": True,
            "latency_us": self.state.latency_us,
            "new_expected": self.state.total_abcfc.expected,
            "bounds": [self.state.total_abcfc.worst, self.state.total_abcfc.best],
        }

    def get_trade_signal(self) -> Dict:
        """
        Get trade signal from ABCFC at HFT frequency.

        Returns action recommendation for HFT execution.
        """
        # Ensure recent updates
        self.second_update()

        # Get nexus decision
        action = self.state.current_action
        confidence = self.state.action_confidence

        # Calculate position sizing from ABCFC
        range_size = self.state.total_abcfc.best - self.state.total_abcfc.worst
        if range_size > 0:
            position_in_range = (self.state.total_abcfc.expected - self.state.total_abcfc.worst) / range_size
        else:
            position_in_range = 0.5

        # Signal strength based on position in range
        # If expected is closer to best, more bullish
        signal_strength = 2 * (position_in_range - 0.5)  # -1 to +1

        return {
            "action": action,
            "confidence": confidence,
            "signal_strength": signal_strength,
            "position_in_range": position_in_range,
            "recommended_side": "BUY" if signal_strength > 0 else "SELL",
            "abcfc": self.state.total_abcfc.to_dict(),
            "flow_rate": {
                "cost_per_sec": self.state.cost_per_sec,
                "profit_per_sec": self.state.profit_per_sec,
                "net_per_sec": self.state.net_per_sec,
            }
        }

    def run_cycle(self) -> Dict:
        """
        Run a full ABCFC-HFT cycle.

        1. Second update (ABCFC recalc)
        2. Check if minute update needed
        3. Get trade signal
        4. Return status
        """
        now_us = int(time.time() * 1_000_000)

        # Second update
        self.second_update()

        # Minute update if needed
        if now_us - self.state.last_nexus_eval > 60_000_000:  # 60 seconds
            self.minute_update()

        # Get signal
        signal = self.get_trade_signal()

        # Save state
        self._save_state()

        return {
            "success": True,
            "timestamp_us": now_us,
            "abcfc": {
                "total": self.state.total_abcfc.to_dict(),
                "trading": self.state.trading_abcfc.to_dict(),
            },
            "hft_metrics": {
                "events_per_second": self.state.events_per_second,
                "updates_per_second": self.state.updates_per_second,
                "latency_us": self.state.latency_us,
            },
            "flow_rate": {
                "cost_per_sec": round(self.state.cost_per_sec, 6),
                "profit_per_sec": round(self.state.profit_per_sec, 6),
                "net_per_sec": round(self.state.net_per_sec, 6),
            },
            "decision": {
                "action": self.state.current_action,
                "confidence": round(self.state.action_confidence, 4),
            },
            "signal": signal,
        }

    # ==================== STATE PERSISTENCE ====================

    def _load_state(self):
        """Load state from disk."""
        try:
            if ABCFC_HFT_STATE.exists():
                with open(ABCFC_HFT_STATE) as f:
                    data = json.load(f)
                self.state.total_abcfc = ABCFC(**data.get("total_abcfc", {}))
                self.state.trading_abcfc = ABCFC(**data.get("trading_abcfc", {}))
                self.state.current_action = data.get("current_action", "hold")
                self.state.action_confidence = data.get("action_confidence", 0)
        except:
            pass

    def _save_state(self):
        """Save state to disk."""
        try:
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_abcfc": self.state.total_abcfc.to_dict(),
                "trading_abcfc": self.state.trading_abcfc.to_dict(),
                "events_per_second": self.state.events_per_second,
                "latency_us": self.state.latency_us,
                "cost_per_sec": self.state.cost_per_sec,
                "profit_per_sec": self.state.profit_per_sec,
                "net_per_sec": self.state.net_per_sec,
                "current_action": self.state.current_action,
                "action_confidence": self.state.action_confidence,
            }
            with open(ABCFC_HFT_STATE, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def status(self) -> Dict:
        """Get current status."""
        return {
            "success": True,
            "total_expected": self.state.total_abcfc.expected,
            "total_bounds": [self.state.total_abcfc.worst, self.state.total_abcfc.best],
            "events_per_second": self.state.events_per_second,
            "latency_us": self.state.latency_us,
            "net_per_sec": self.state.net_per_sec,
            "current_action": self.state.current_action,
        }

    # ==================== POLYMARKET FUNDAMENTALS BRIDGE ====================

    def get_polymarket_abcfc(self, token_id: str, side: str, size: float,
                            price: float, our_prob: float) -> Dict:
        """
        INTEGRAFIX: Get full Polymarket ABCFC via HFT Execution Bridge.

        Includes:
        - L2 order book slippage calculation
        - Maker vs Taker distinction
        - Self-impact awareness
        - Kelly sizing

        This method bridges to the HFT execution bridge for full analysis.
        """
        if self.hft_bridge:
            try:
                from dataclasses import dataclass

                # Create a minimal opportunity object
                @dataclass
                class TempOpp:
                    opportunity_type: str = "hft_abcfc"
                    token_id: str = token_id
                    side: str = side
                    price: float = price
                    size: float = size
                    confidence: float = our_prob
                    source: str = "abcfc_hft_frequency"
                    reason: str = "Polymarket ABCFC analysis"

                opp = TempOpp()
                return self.hft_bridge.compute_action_abcfc(opp)
            except Exception as e:
                pass

        # Fallback: basic ABCFC calculation
        if side == "BUY":
            worst = -size * price
            best = size * (1 - price)
            edge = our_prob - price
            expected = size * edge
        else:
            worst = -size * (1 - price)
            best = size * price
            edge = our_prob - (1 - price)
            expected = size * edge

        return {
            "worst": round(worst, 4),
            "expected": round(expected, 4),
            "best": round(best, 4),
            "edge": round(edge, 4),
            "edge_pct": round(edge * 100, 2),
            "should_execute": expected > 0 and edge > 0,
            "polymarket_features": "unavailable (fallback mode)",
        }

    def should_execute_polymarket(self, token_id: str, side: str, size: float,
                                  price: float, our_prob: float) -> Dict:
        """
        INTEGRAFIX: Full Polymarket execution decision.

        Uses all market fundamentals:
        - L2 slippage analysis
        - Self-impact check
        - Kelly sizing validation
        - Maker vs Taker recommendation

        Returns decision with full reasoning.
        """
        abcfc = self.get_polymarket_abcfc(token_id, side, size, price, our_prob)

        decision = {
            "should_execute": abcfc.get("should_execute", False),
            "abcfc": abcfc,
            "reasoning": [],
        }

        # Build reasoning
        if abcfc.get("edge", 0) <= 0:
            decision["reasoning"].append("REJECT: No edge (our_prob <= market_price)")
        else:
            decision["reasoning"].append(f"Edge: {abcfc.get('edge_pct', 0):.2f}%")

        # Check slippage
        slippage = abcfc.get("slippage", {})
        if slippage.get("cost", 0) > 0:
            decision["reasoning"].append(f"Slippage: ${slippage['cost']:.4f}")

        # Check self-impact
        impact = abcfc.get("self_impact", {})
        if impact.get("should_split", False):
            decision["reasoning"].append(f"WARNING: Should split order (impact: {impact['impact_pct']:.2f}%)")
            decision["recommended_size"] = impact.get("safe_size", size)

        # Kelly check
        kelly = abcfc.get("kelly", {})
        if kelly.get("recommended_size", 0) > 0:
            if size > kelly["recommended_size"] * 2:
                decision["reasoning"].append(f"WARNING: Size exceeds 2x Kelly ({kelly['recommended_size']:.2f})")

        # Maker vs Taker
        mt = abcfc.get("maker_taker", {})
        if mt:
            decision["execution_recommendation"] = mt.get("recommendation", "maker")
            decision["reasoning"].append(f"Execution: {mt.get('recommendation', 'maker')}")

        return decision


# Singleton
_abcfc_hft = None

def get_abcfc_hft() -> ABCFCHFTFrequency:
    """Get or create the ABCFC-HFT frequency singleton."""
    global _abcfc_hft
    if _abcfc_hft is None:
        _abcfc_hft = ABCFCHFTFrequency()
    return _abcfc_hft


if __name__ == "__main__":
    print("=" * 70)
    print("ABCFC-HFT FREQUENCY - Microsecond ABCFC Updates")
    print("=" * 70)

    hft = get_abcfc_hft()

    # Run a cycle
    result = hft.run_cycle()

    print(f"\nTotal ABCFC:")
    print(f"  Worst:    ${result['abcfc']['total']['worst']:,.2f}")
    print(f"  Expected: ${result['abcfc']['total']['expected']:,.2f}")
    print(f"  Best:     ${result['abcfc']['total']['best']:,.2f}")

    print(f"\nHFT Metrics:")
    print(f"  Events/sec:  {result['hft_metrics']['events_per_second']}")
    print(f"  Latency:     {result['hft_metrics']['latency_us']}μs")

    print(f"\nFlow Rate ($/sec):")
    print(f"  Cost:   ${result['flow_rate']['cost_per_sec']:.6f}")
    print(f"  Profit: ${result['flow_rate']['profit_per_sec']:.6f}")
    print(f"  Net:    ${result['flow_rate']['net_per_sec']:.6f}")

    print(f"\nDecision: {result['decision']['action']} "
          f"(confidence: {result['decision']['confidence']:.2%})")

    print(f"\nSignal:")
    print(f"  Strength:    {result['signal']['signal_strength']:.2f}")
    print(f"  Recommended: {result['signal']['recommended_side']}")
