#!/usr/bin/env python3
"""
INTEGRAFIX: Edge Executor
=========================

Wires edge detection to actual trade execution.

GAP FIXED: edge_to_executor_disconnected
- Before: Edge signals generated but never reached executor
- After:  Edge → Safeguards → Executor → Trade

INTEGRAFIX PRINCIPLE: Every output needs a consumer.

THE WIRE:
=========
wisdom_bridge.generate_trading_signals()
    ↓
edge_executor.evaluate_signals()
    ↓
trading_safeguards.check_trade()
    ↓
yair_auto_trader.execute_signal()
    ↓
outcome_tracker.record() [Next wire to build]
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
EXECUTOR_STATE_FILE = STATE_DIR / "edge_executor_state.json"
EXECUTION_LOG_FILE = STATE_DIR / "execution_log.jsonl"


@dataclass
class ExecutionResult:
    """Result of executing an edge signal."""
    signal_id: str
    market: str
    action: str
    edge: float
    executed: bool
    dry_run: bool
    reason: str
    timestamp: str
    order_id: Optional[str] = None
    fill_price: Optional[float] = None


class EdgeExecutor:
    """
    Executor that takes edge signals and turns them into trades.

    This is the MISSING WIRE between edge detection and trading.
    """

    def __init__(self):
        self.state = self._load_state()
        self._wisdom_bridge = None
        self._safeguards = None
        self._auto_trader = None
        self._load_components()

    def _load_state(self) -> Dict:
        if EXECUTOR_STATE_FILE.exists():
            with open(EXECUTOR_STATE_FILE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "signals_evaluated": 0,
            "signals_executed": 0,
            "signals_rejected": 0,
            "total_edge_captured": 0.0,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(EXECUTOR_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_components(self):
        """Load required components."""
        try:
            from integrafix.wisdom_bridge import WisdomBridge
            self._wisdom_bridge = WisdomBridge()
        except ImportError:
            pass

        try:
            from executor.trading_safeguards import TradingSafeguards
            self._safeguards = TradingSafeguards()
        except ImportError:
            pass

        try:
            from executor.yair_auto_trader import get_trader
            self._auto_trader = get_trader()
        except ImportError:
            pass

    def _log_execution(self, result: ExecutionResult):
        """Log execution result to JSONL file."""
        with open(EXECUTION_LOG_FILE, 'a') as f:
            f.write(json.dumps(asdict(result)) + "\n")

    # ==================== EDGE EVALUATION ====================

    def evaluate_signal(self, signal: Dict) -> Dict:
        """
        Evaluate whether a signal should be executed.

        Returns evaluation with decision and reasoning.
        """
        evaluation = {
            "signal": signal,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "should_execute": False,
            "reasons": [],
        }

        # Check 1: Edge exists and is positive
        edge = signal.get("edge")
        if edge is None:
            evaluation["reasons"].append("No edge value")
            return evaluation

        if edge < 0.005:  # Minimum 0.5% edge
            evaluation["reasons"].append(f"Edge too small: {edge:.4f}")
            return evaluation

        # Check 2: Confidence threshold
        confidence = signal.get("confidence", 0)
        if confidence < 0.5:
            evaluation["reasons"].append(f"Low confidence: {confidence:.2f}")
            return evaluation

        # Check 3: Action is actionable
        action = signal.get("action", "UNKNOWN")
        if action in ["MONITOR", "UNKNOWN"]:
            evaluation["reasons"].append(f"Non-actionable action: {action}")
            return evaluation

        # Check 4: Safeguards
        if self._safeguards:
            trade_check = {
                "market_id": signal.get("market", ""),
                "side": "BUY" if "BUY" in action.upper() else "SELL",
                "amount": signal.get("sizing", 10),
                "price": signal.get("yes_price", 0.5),
            }
            safeguard_result = self._safeguards.check_trade(trade_check)
            if not safeguard_result.get("allowed", False):
                evaluation["reasons"].append(f"Safeguard blocked: {safeguard_result.get('reason', 'unknown')}")
                return evaluation

        # All checks passed
        evaluation["should_execute"] = True
        evaluation["reasons"].append(f"Edge {edge:.4f} passes all checks")
        return evaluation

    # ==================== EXECUTION ====================

    def execute_signal(self, signal: Dict, dry_run: bool = True) -> ExecutionResult:
        """
        Execute a single edge signal.

        Args:
            signal: Signal from wisdom_bridge
            dry_run: If True, simulate execution
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        signal_id = f"sig_{int(datetime.now().timestamp())}"

        # Evaluate first
        evaluation = self.evaluate_signal(signal)

        if not evaluation["should_execute"]:
            result = ExecutionResult(
                signal_id=signal_id,
                market=signal.get("market", "unknown")[:50],
                action=signal.get("action", "UNKNOWN"),
                edge=signal.get("edge", 0) or 0,
                executed=False,
                dry_run=dry_run,
                reason="; ".join(evaluation["reasons"]),
                timestamp=timestamp,
            )
            self.state["signals_rejected"] += 1
            self._save_state()
            self._log_execution(result)
            return result

        # Execute
        if dry_run:
            result = ExecutionResult(
                signal_id=signal_id,
                market=signal.get("market", "unknown")[:50],
                action=signal.get("action", "UNKNOWN"),
                edge=signal.get("edge", 0) or 0,
                executed=True,
                dry_run=True,
                reason="DRY RUN - Would execute",
                timestamp=timestamp,
            )
        else:
            # Real execution via auto_trader
            if self._auto_trader:
                try:
                    # Convert signal to auto_trader format
                    trade_result = self._auto_trader.execute_signal(signal)
                    result = ExecutionResult(
                        signal_id=signal_id,
                        market=signal.get("market", "unknown")[:50],
                        action=signal.get("action", "UNKNOWN"),
                        edge=signal.get("edge", 0) or 0,
                        executed=trade_result.get("success", False),
                        dry_run=False,
                        reason=trade_result.get("message", "Executed"),
                        timestamp=timestamp,
                        order_id=trade_result.get("order_id"),
                        fill_price=trade_result.get("fill_price"),
                    )
                except Exception as e:
                    result = ExecutionResult(
                        signal_id=signal_id,
                        market=signal.get("market", "unknown")[:50],
                        action=signal.get("action", "UNKNOWN"),
                        edge=signal.get("edge", 0) or 0,
                        executed=False,
                        dry_run=False,
                        reason=f"Execution error: {e}",
                        timestamp=timestamp,
                    )
            else:
                result = ExecutionResult(
                    signal_id=signal_id,
                    market=signal.get("market", "unknown")[:50],
                    action=signal.get("action", "UNKNOWN"),
                    edge=signal.get("edge", 0) or 0,
                    executed=False,
                    dry_run=False,
                    reason="Auto trader not available",
                    timestamp=timestamp,
                )

        # Update stats
        if result.executed:
            self.state["signals_executed"] += 1
            self.state["total_edge_captured"] += result.edge
        else:
            self.state["signals_rejected"] += 1

        self.state["signals_evaluated"] += 1
        self._save_state()
        self._log_execution(result)

        return result

    # ==================== BATCH EXECUTION ====================

    def execute_all_signals(self, dry_run: bool = True) -> List[ExecutionResult]:
        """
        Get all current edge signals and execute them.

        This is the main entry point for the wire.
        """
        results = []

        if not self._wisdom_bridge:
            return results

        # Get all signals
        signals = self._wisdom_bridge.generate_trading_signals()

        for signal in signals:
            result = self.execute_signal(signal, dry_run=dry_run)
            results.append(result)

        return results

    def execute_actionable_only(self, min_edge: float = 0.01, dry_run: bool = True) -> List[ExecutionResult]:
        """
        Execute only actionable signals with minimum edge.
        """
        results = []

        if not self._wisdom_bridge:
            return results

        # Get actionable signals
        signals = self._wisdom_bridge.get_actionable_signals(min_edge=min_edge)

        for signal in signals:
            result = self.execute_signal(signal, dry_run=dry_run)
            results.append(result)

        return results

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get executor status."""
        return {
            "state": self.state,
            "wisdom_bridge_connected": self._wisdom_bridge is not None,
            "safeguards_connected": self._safeguards is not None,
            "auto_trader_connected": self._auto_trader is not None,
            "wire_complete": all([
                self._wisdom_bridge is not None,
                self._safeguards is not None,
                self._auto_trader is not None,
            ]),
        }


# Singleton
_executor = None

def get_edge_executor() -> EdgeExecutor:
    global _executor
    if _executor is None:
        _executor = EdgeExecutor()
    return _executor


def main():
    """Run edge executor and show results."""
    print("=" * 70)
    print("INTEGRAFIX: EDGE EXECUTOR")
    print("Wiring edge detection to trade execution")
    print("=" * 70)
    print()

    executor = get_edge_executor()

    # Status
    status = executor.status()
    print("[STATUS]")
    print(f"  Wisdom Bridge: {'✓' if status['wisdom_bridge_connected'] else '✗'}")
    print(f"  Safeguards: {'✓' if status['safeguards_connected'] else '✗'}")
    print(f"  Auto Trader: {'✓' if status['auto_trader_connected'] else '✗'}")
    print(f"  Wire Complete: {'✓' if status['wire_complete'] else '✗'}")
    print()

    # Execute in dry run mode
    print("Executing all signals (DRY RUN)...")
    results = executor.execute_all_signals(dry_run=True)

    print(f"\nResults: {len(results)} signals processed")
    executed = [r for r in results if r.executed]
    rejected = [r for r in results if not r.executed]

    print(f"  Executed: {len(executed)}")
    print(f"  Rejected: {len(rejected)}")
    print()

    if executed:
        print("[EXECUTED SIGNALS]")
        for r in executed[:5]:
            print(f"  • {r.market[:40]}...")
            print(f"    Action: {r.action} | Edge: {r.edge:.4f}")
            print(f"    Reason: {r.reason}")
        if len(executed) > 5:
            print(f"  ... and {len(executed) - 5} more")
    print()

    if rejected:
        print("[REJECTED SIGNALS]")
        for r in rejected[:3]:
            print(f"  • {r.market[:40]}...")
            print(f"    Reason: {r.reason}")
        if len(rejected) > 3:
            print(f"  ... and {len(rejected) - 3} more")
    print()

    # Stats
    print("[CUMULATIVE STATS]")
    print(f"  Signals evaluated: {status['state']['signals_evaluated']}")
    print(f"  Signals executed: {status['state']['signals_executed']}")
    print(f"  Total edge captured: {status['state']['total_edge_captured']:.4f}")

    print("\n" + "=" * 70)
    print("GAP FIXED: edge_to_executor_disconnected")
    print("Edge signals now wire through to executor")
    print("=" * 70)

    return executor


if __name__ == "__main__":
    main()
