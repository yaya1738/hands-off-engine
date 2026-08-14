#!/usr/bin/env python3
"""Fail-closed compatibility shim for the legacy Polymarket order helper.

This module intentionally contains NO live-order capability.  The current
Factory authority owns any future financial execution path, and live trading
is globally denied until explicitly unbanned.  Legacy callers remain importable
but every mutating/order method returns a deterministic DENIED result.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class Market:
    condition_id: str
    question: str
    yes_token_id: str
    no_token_id: str
    yes_price: float
    no_price: float


_DENIED = {
    "success": False,
    "status": "DENIED",
    "reason": "Legacy Polymarket order authority is quarantined; live trading is disabled.",
    "authority": "FactoryAuthorityGateway",
}


class PolymarketOrders:
    """Legacy API surface preserved without any order-submission authority."""

    def __init__(self):
        self._market_cache = {}

    @property
    def client(self):
        raise RuntimeError("Legacy Polymarket client access is disabled")

    def _denied(self, operation: str) -> Dict:
        return {**_DENIED, "operation": operation}

    def limit_buy_yes(self, market: str, price: float, size: float) -> Dict:
        return self._denied("limit_buy_yes")

    def limit_sell_yes(self, market: str, price: float, size: float) -> Dict:
        return self._denied("limit_sell_yes")

    def limit_buy_no(self, market: str, price: float, size: float) -> Dict:
        return self._denied("limit_buy_no")

    def limit_sell_no(self, market: str, price: float, size: float) -> Dict:
        return self._denied("limit_sell_no")

    def market_buy_yes(self, market: str, size: float) -> Dict:
        return self._denied("market_buy_yes")

    def market_sell_yes(self, market: str, size: float) -> Dict:
        return self._denied("market_sell_yes")

    def market_buy_no(self, market: str, size: float) -> Dict:
        return self._denied("market_buy_no")

    def market_sell_no(self, market: str, size: float) -> Dict:
        return self._denied("market_sell_no")

    def split(self, market: str, amount: float) -> Dict:
        return self._denied("split")

    def merge(self, market: str, amount: float) -> Dict:
        return self._denied("merge")

    def place_reward_order(self, market: str, size: float, side: str = "BOTH") -> Dict:
        return self._denied("place_reward_order")

    def cancel_all(self) -> Dict:
        return self._denied("cancel_all")

    def get_open_orders(self) -> List[Dict]:
        return []

    def get_book(self, market: str, side: str = "YES") -> Dict:
        return {"bids": [], "asks": [], "status": "DENIED", "reason": _DENIED["reason"]}

    def status(self) -> Dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open_orders": 0,
            "cached_markets": len(self._market_cache),
            "connected": False,
            "live_trading": False,
            "status": "DENIED",
        }

    def get_reward_config(self, market: str) -> Dict:
        return {"rewards_enabled": False, "status": "DENIED", "reason": _DENIED["reason"]}

    def is_reward_eligible(self, market: str, price: float, size: float) -> Dict:
        return {"eligible": False, "status": "DENIED", "reason": _DENIED["reason"]}

    def estimate_rewards(self, market: str, size: float, hours: float = 24) -> Dict:
        return {"estimate": 0, "status": "DENIED", "reason": _DENIED["reason"]}

    def project_profit(self, market: str, size: float, days: int = 30, n_simulations: int = 10000) -> Dict:
        return {"expected": 0, "status": "DENIED", "reason": _DENIED["reason"]}


orders = PolymarketOrders()
