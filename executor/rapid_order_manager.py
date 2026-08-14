#!/usr/bin/env python3
"""Fail-closed compatibility shim for retired RapidOrderManager.

No credentials are loaded and no Polymarket order API is reachable from this
legacy surface. Financial execution belongs exclusively to the authoritative
Factory gateway and its current-rules/human-approval gates.
"""
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class OrderSpec:
    token_id: str
    price: float
    size: float
    side: str


@dataclass
class OrderGrid:
    token_id: str
    center_price: float
    spread_bps: int
    levels: int
    size_per_level: float
    side: str


class RapidOrderManager:
    """Retired compatibility surface; all mutation operations are denied."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.client = None
        self.stats = {"orders_placed": 0, "orders_cancelled": 0, "batches_sent": 0, "avg_batch_time_ms": 0}

    @staticmethod
    def _denied() -> Dict[str, Any]:
        return {"success": False, "status": "DENIED", "error": "RapidOrderManager is retired; live financial execution is disabled."}

    def create_order_batch(self, specs: List[OrderSpec]) -> List[Any]:
        return []

    def place_orders_batch(self, specs: List[OrderSpec]) -> Dict[str, Any]:
        return self._denied()

    def cancel_orders_batch(self, order_ids: List[str]) -> Dict[str, Any]:
        return self._denied()

    def cancel_all_and_replace(self, new_specs: List[OrderSpec]) -> Dict[str, Any]:
        return self._denied()

    def get_order_books(self, token_ids: List[str]) -> Dict[str, Any]:
        return {"success": False, "status": "DENIED", "error": "Retired financial client surface."}
