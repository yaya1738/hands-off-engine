"""Fail-closed compatibility shim for the legacy Polymarket client.

Financial/live execution is intentionally unavailable. This module preserves
legacy imports without loading credentials, constructing a CLOB client, or
sending/cancelling orders. Any future financial execution must go through the
authoritative Factory financial gate and explicit human approval path.
"""

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

Side = Literal["BUY", "SELL"]


@dataclass
class PolymarketConfig:
    host: str = ""
    chain_id: int = 137
    private_key: str = ""
    funder_address: str = ""
    signature_type: int = 1


class PolymarketTradingBlocked(RuntimeError):
    """Raised when a legacy financial execution surface is invoked."""


class PolymarketTrader:
    """Compatibility surface that can never execute financial actions."""

    EXECUTION_BLOCKED = True

    def __init__(self, cfg: PolymarketConfig, logger: Optional[Any] = None):
        self.cfg = cfg
        self.logger = logger
        self.client = None

    @classmethod
    def from_env(cls) -> "PolymarketTrader":
        # Deliberately do not read private keys or other trading credentials.
        return cls(PolymarketConfig())

    def _blocked(self, action: str) -> Dict[str, Any]:
        message = f"DENIED: legacy Polymarket execution surface blocked: {action}"
        if self.logger:
            self.logger.warning(message)
        return {"status": "DENIED", "blocked": True, "reason": message}

    def get_server_time(self) -> Dict[str, Any]:
        return self._blocked("get_server_time")

    def check_health(self) -> bool:
        return False

    def place_market_order_usd(self, token_id: str, usd_amount: float, side: Side, order_type: Any = None) -> Dict[str, Any]:
        return self._blocked("place_market_order_usd")

    def place_limit_order(self, token_id: str, price: float, size: float, side: Side, order_type: Any = None) -> Dict[str, Any]:
        return self._blocked("place_limit_order")

    def get_open_orders(self) -> list:
        return []

    def get_trades(self) -> list:
        return []

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self._blocked("cancel_order")

    def cancel_all_orders(self) -> Dict[str, Any]:
        return self._blocked("cancel_all_orders")
