#!/usr/bin/env python3
"""
SIGNAL-EXECUTOR BRIDGE - Connects signals to execution
========================================================

This module bridges the gap between signal generation and trade execution.
Signals flow IN, decisions flow OUT to executor.

Master: Yair Siegel
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

SIGNAL_FILE = BASE_DIR / "state" / "trading_signals.json"
BRIDGE_STATE = BASE_DIR / "state" / "signal_bridge.json"


def get_pending_signals() -> list:
    """Get signals that haven't been executed."""
    if not SIGNAL_FILE.exists():
        return []

    try:
        data = json.load(open(SIGNAL_FILE))
        signals = data.get("signals", [])

        # Load bridge state to see what's been processed
        processed = set()
        if BRIDGE_STATE.exists():
            bridge = json.load(open(BRIDGE_STATE))
            processed = set(bridge.get("processed_signals", []))

        # Return unprocessed signals
        return [s for s in signals if s.get("id") not in processed]
    except:
        return []


def process_signals():
    """Process pending signals through unified_ai to executor."""
    from ai.unified_ai import should_execute, check_trading_allowed

    signals = get_pending_signals()
    if not signals:
        print("[BRIDGE] No pending signals")
        return

    print(f"[BRIDGE] Processing {len(signals)} signals")

    results = []
    processed_ids = []

    for signal in signals:
        signal_id = signal.get("id", "unknown")
        market = signal.get("market", "unknown")
        direction = signal.get("direction", "unknown")
        confidence = signal.get("confidence", 0)

        # Check if trading allowed
        allowed, reason = check_trading_allowed(amount=5.0)  # Default micro-trade
        if not allowed:
            print(f"[BRIDGE] Trading not allowed: {reason}")
            continue

        # Check if this action should execute
        action = f"trade {direction} on {market}"
        if should_execute(action, roi_estimate=confidence * 10):
            print(f"[BRIDGE] APPROVED: {action} (confidence: {confidence})")

            # Queue for execution
            results.append({
                "signal_id": signal_id,
                "action": action,
                "approved": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            print(f"[BRIDGE] REJECTED: {action}")
            results.append({
                "signal_id": signal_id,
                "action": action,
                "approved": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        processed_ids.append(signal_id)

    # Update bridge state
    bridge_state = {"processed_signals": processed_ids, "last_run": datetime.now(timezone.utc).isoformat()}
    if BRIDGE_STATE.exists():
        old = json.load(open(BRIDGE_STATE))
        bridge_state["processed_signals"] = list(set(old.get("processed_signals", []) + processed_ids))

    with open(BRIDGE_STATE, 'w') as f:
        json.dump(bridge_state, f, indent=2)

    # Write approved trades to execution queue AND EXECUTE THEM
    approved = [r for r in results if r.get("approved")]
    if approved:
        queue_file = BASE_DIR / "state" / "execution_queue.json"
        with open(queue_file, 'w') as f:
            json.dump({"trades": approved, "timestamp": datetime.now(timezone.utc).isoformat()}, f, indent=2)
        print(f"[BRIDGE] Queued {len(approved)} trades for execution")

        # ACTUALLY EXECUTE via UnifiedTradingHub
        try:
            from trading.unified_trading_hub import get_trading_hub, TradeRequest
            hub = get_trading_hub()

            for trade in approved:
                signal_id = trade.get("signal_id", "unknown")
                # Find original signal to get details
                original_signal = next((s for s in signals if s.get("id") == signal_id), None)
                if original_signal:
                    request = TradeRequest(
                        market_slug=original_signal.get("market_slug", original_signal.get("market", "")),
                        side=original_signal.get("direction", "YES").upper(),
                        amount_usd=original_signal.get("size_usd", 1.0),
                        confidence=original_signal.get("confidence", 0.7),
                        reason=f"Signal bridge: {original_signal.get('reason', 'auto')}",
                        source="signal_bridge"
                    )
                    result = hub.execute_trade(request)
                    print(f"[BRIDGE] Executed {signal_id}: {result.message}")
        except Exception as e:
            print(f"[BRIDGE] Execution error: {e}")

    return results


if __name__ == "__main__":
    process_signals()
