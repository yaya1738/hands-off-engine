#!/usr/bin/env python3
"""Fail-closed compatibility shim for the legacy Polymarket live module.

The historical implementation contained a direct real-money execution path
and embedded trading credentials. Financial execution is intentionally banned.
Future activation must go through the authoritative Factory financial gate,
current-rules validation, and explicit human approval.
"""

from typing import Dict, List, Optional


class PolymarketLive:
    """Compatibility surface that cannot initialize or execute live trading."""

    EXECUTION_BLOCKED = True

    def __init__(self, *args, **kwargs):
        self.client = None
        self.state = {
            "execution_blocked": True,
            "reason": "legacy live trading module quarantined",
        }

    def _blocked(self, action: str) -> Dict:
        return {
            "status": "DENIED",
            "blocked": True,
            "reason": f"legacy Polymarket live execution blocked: {action}",
        }

    def get_open_orders(self) -> List[Dict]:
        return []

    def get_market_price(self, token_id: str) -> Optional[Dict]:
        return None

    def check_safety(self) -> Dict:
        return self._blocked("check_safety")

    def analyze_positions(self) -> Dict:
        return self._blocked("analyze_positions")

    def generate_smart_signals(self) -> List[Dict]:
        return []

    def execute_signal(self, *args, **kwargs) -> Dict:
        return self._blocked("execute_signal")

    def execute_trade(self, *args, **kwargs) -> Dict:
        return self._blocked("execute_trade")

    def cancel_order(self, *args, **kwargs) -> Dict:
        return self._blocked("cancel_order")

    def cancel_all_orders(self, *args, **kwargs) -> Dict:
        return self._blocked("cancel_all_orders")
