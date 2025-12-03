#!/usr/bin/env python3
"""
INTEGRAFIX: Wisdom Bridge
=========================

Wires yair_wisdom_engine.py into the trading pipeline.

GAP FIXED: wisdom_no_edge_output
- Before: Wisdom engine calculates analysis but edge never reaches trading
- After:  Wisdom → Bridge → Trading Pipeline

INTEGRAFIX PRINCIPLE: Connect outputs to consumers.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from autonomous.yair_wisdom_engine import YairWisdomEngine, YAIR_TEACHINGS
from integrafix.methodology import get_methodology, GapType, Gap

STATE_DIR = PROJECT_ROOT / "state"
WISDOM_BRIDGE_STATE = STATE_DIR / "wisdom_bridge.json"


class WisdomBridge:
    """
    Bridge connecting Yair's wisdom to actionable trading signals.

    This is the MISSING WIRE between yair_wisdom_engine and the trading pipeline.
    """

    def __init__(self):
        self.engine = YairWisdomEngine()
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if WISDOM_BRIDGE_STATE.exists():
            with open(WISDOM_BRIDGE_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "signals_generated": 0,
            "signals_with_edge": 0,
            "average_edge": 0.0,
            "teachings_applied": [],
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(WISDOM_BRIDGE_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def generate_trading_signals(self) -> List[Dict]:
        """
        Apply all Yair teachings and generate trading signals with EDGE.

        This is the key integration - wisdom_engine outputs -> trading signals.
        """
        signals = []

        # Apply all teachings
        results = self.engine.apply_all_teachings()

        # Convert merge arbitrage to signals with edge
        for arb in results.get("merge_arbitrage", []):
            signal = {
                "type": "merge_arbitrage",
                "teaching": "YES + NO < $1 = free money",
                "market": arb["market"],
                "action": "BUY_BOTH",
                "yes_price": arb["yes_price"],
                "no_price": arb["no_price"],
                "edge": arb["profit_per_pair"],  # THE EDGE OUTPUT THAT WAS MISSING
                "edge_pct": arb["profit_pct"],
                "confidence": 0.95,  # Arbitrage is certain
                "sizing": min(100, arb["profit_per_pair"] * 1000),  # $1 per bp of edge
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            signals.append(signal)

        # Convert ESPN signals to signals (need external data for edge)
        for espn in results.get("espn_signals", []):
            signal = {
                "type": "espn_divergence",
                "teaching": "ESPN mid-game probability = very accurate",
                "market": espn["market"],
                "action": "MONITOR",  # Need ESPN data for full signal
                "polymarket_yes": espn["polymarket_yes"],
                "edge": None,  # Set when ESPN data available
                "data_needed": "ESPN probability",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            signals.append(signal)

        # Convert new market thin book to signals
        for nm in results.get("new_market_edge", []):
            # Thin books have edge from being able to post at favorable levels
            estimated_edge = nm["spread_bps"] / 10000 * 0.5  # Capture half the spread
            signal = {
                "type": "thin_book",
                "teaching": "Thin books = easier fills at edges",
                "market": nm["market"],
                "action": "POST_LIMITS",
                "yes_price": nm["yes_price"],
                "edge": estimated_edge,
                "edge_pct": estimated_edge * 100,
                "confidence": 0.6,
                "sizing": 20,  # Small size for thin books
                "exit_rule": nm["exit_rule"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            signals.append(signal)

        # Update state
        self.state["signals_generated"] += len(signals)
        signals_with_edge = [s for s in signals if s.get("edge") is not None]
        self.state["signals_with_edge"] += len(signals_with_edge)
        if signals_with_edge:
            edges = [s["edge"] for s in signals_with_edge]
            self.state["average_edge"] = sum(edges) / len(edges)
        self._save_state()

        return signals

    def get_actionable_signals(self, min_edge: float = 0.01) -> List[Dict]:
        """
        Get only signals with actionable edge >= min_edge.
        """
        all_signals = self.generate_trading_signals()
        return [
            s for s in all_signals
            if s.get("edge") is not None and s["edge"] >= min_edge
        ]

    def apply_smart_edge_to_market(self, market_data: Dict) -> Dict:
        """
        Apply Yair's smart edge analysis to a specific market.

        Returns signal with edge, fair_prob, and recommendation.
        """
        analysis = self.engine.calculate_smart_edge(market_data)

        # Transform analysis to trading signal format
        signal = {
            "type": "smart_edge",
            "market": analysis["market"],
            "action": analysis.get("recommendation", "HOLD"),
            "edge": analysis.get("edge", 0.0),
            "fair_prob": analysis.get("fair_prob"),
            "confidence": analysis.get("confidence", 0.0),
            "analysis": analysis.get("analysis", {}),
            "edge_actionable": analysis.get("edge_actionable", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return signal

    def status(self) -> Dict:
        """Get bridge status."""
        return {
            "state": self.state,
            "teachings_available": list(YAIR_TEACHINGS.keys()),
            "engine_state": self.engine.state,
        }


def register_wisdom_wire():
    """
    Register the wisdom bridge as a wire in integrafix methodology.
    """
    methodology = get_methodology()

    # Create the wire
    wire = methodology.create_wire(
        source="yair_wisdom_engine",
        target="trading_pipeline",
        wire_type="signal",
        description="Wisdom engine signals with edge → trading decisions",
    )

    # Mark the gap as fixed
    methodology.fix_gap(
        "wisdom_no_edge_output",
        fix_method="Created wisdom_bridge.py to extract edge values from wisdom analysis"
    )

    return wire


def main():
    """Run wisdom bridge and show signals."""
    print("=" * 70)
    print("INTEGRAFIX: WISDOM BRIDGE")
    print("Wiring Yair's teachings to trading signals")
    print("=" * 70)
    print()

    bridge = WisdomBridge()

    # Generate signals
    signals = bridge.generate_trading_signals()

    print(f"Total signals generated: {len(signals)}")
    print()

    # Show actionable signals
    actionable = [s for s in signals if s.get("edge") is not None and s["edge"] >= 0.01]
    print(f"Actionable signals (edge >= 1%): {len(actionable)}")
    print()

    for signal in actionable[:5]:
        print(f"[{signal['type'].upper()}]")
        print(f"  Market: {signal['market'][:50]}...")
        print(f"  Action: {signal['action']}")
        print(f"  Edge: {signal['edge']:.4f} ({signal.get('edge_pct', signal['edge']*100):.2f}%)")
        print(f"  Teaching: {signal['teaching']}")
        print()

    # Register the wire
    print("-" * 70)
    print("Registering wire in integrafix methodology...")
    wire = register_wisdom_wire()
    print(f"Wire created: {wire.id}")
    print(f"  {wire.source} → {wire.target}")
    print()

    # Show status
    status = bridge.status()
    print(f"Bridge status:")
    print(f"  Signals generated: {status['state']['signals_generated']}")
    print(f"  Signals with edge: {status['state']['signals_with_edge']}")
    print(f"  Average edge: {status['state']['average_edge']:.4f}")

    return bridge


if __name__ == "__main__":
    main()
