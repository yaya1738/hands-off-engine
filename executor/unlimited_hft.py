#!/usr/bin/env python3
"""Fail-closed compatibility shim for the retired UnlimitedHFT executor.

This module is intentionally non-executable. Historical wallet-fleet/HFT code
must not remain an alternate financial authority. Analysis and simulation may
be performed elsewhere, but live order submission requires the authoritative
Factory financial gates and explicit human approval.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class WalletClient:
    address: str
    private_key: str = ""
    client: Any = None
    orders_placed: int = 0
    last_order_time: float = 0
    rate_limit_until: float = 0


class UnlimitedHFT:
    """Retired compatibility surface; every execution operation is denied."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._wallets: List[WalletClient] = []
        self._running = False
        self._stats = {"orders_placed": 0, "orders_per_second": 0, "errors": 0, "start_time": None}

    def _load_wallets(self) -> int:
        return 0

    def _get_next_wallet(self) -> Optional[WalletClient]:
        return None

    def _init_wallet_client(self, wallet: WalletClient):
        return None

    @staticmethod
    def _denied() -> Dict[str, Any]:
        return {"success": False, "status": "DENIED", "error": "UnlimitedHFT is retired; live financial execution is disabled."}

    def place_order(self, token_id: str, price: float, size: float, side: str) -> Dict[str, Any]:
        return self._denied()

    def place_orders_parallel(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self._denied() for _ in orders]

    def spray_orders(self, token_id: str, center_price: float, spread_bps: int = 100,
                     levels: int = 10, size_per_level: float = 10) -> Dict[str, Any]:
        return self._denied()

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self._denied()

    def cancel_all(self) -> Dict[str, Any]:
        return self._denied()
