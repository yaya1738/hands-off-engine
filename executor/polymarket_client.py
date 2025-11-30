"""
Polymarket CLOB Client Adapter for Hands-Off Engine

Wraps py-clob-client for easy integration with the trading pipeline.
"""

import os
import logging
from dataclasses import dataclass
from typing import Literal, Optional, Dict, Any

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import MarketOrderArgs, OrderType, OrderArgs
from py_clob_client.order_builder.constants import BUY, SELL


Side = Literal["BUY", "SELL"]


@dataclass
class PolymarketConfig:
    """Configuration for Polymarket CLOB client"""
    host: str
    chain_id: int
    private_key: str
    funder_address: str
    signature_type: int = 1  # 0=EOA, 1=email/Magic, 2=proxy


class PolymarketTrader:
    """
    Polymarket trading client wrapper.

    Handles order placement via Polymarket's CLOB API.
    """

    def __init__(self, cfg: PolymarketConfig, logger: Optional[logging.Logger] = None):
        self.cfg = cfg
        self.logger = logger or logging.getLogger(__name__)

        self.client = ClobClient(
            cfg.host,
            key=cfg.private_key,
            chain_id=cfg.chain_id,
            signature_type=cfg.signature_type,
            funder=cfg.funder_address,
        )

        # Derive / create API credentials once
        self.client.set_api_creds(self.client.create_or_derive_api_creds())
        self.logger.info("Polymarket CLOB client initialized")

    @classmethod
    def from_env(cls) -> "PolymarketTrader":
        """
        Create PolymarketTrader from environment variables.

        Required env vars:
        - POLYMARKET_PRIVATE_KEY
        - POLYMARKET_FUNDER_ADDRESS

        Optional env vars:
        - POLYMARKET_CLOB_HOST (default: https://clob.polymarket.com)
        - POLYMARKET_CHAIN_ID (default: 137 = Polygon)
        - POLYMARKET_SIGNATURE_TYPE (default: 1 = email/Magic)
        """
        cfg = PolymarketConfig(
            host=os.getenv("POLYMARKET_CLOB_HOST", "https://clob.polymarket.com"),
            chain_id=int(os.getenv("POLYMARKET_CHAIN_ID", "137")),
            private_key=os.environ["POLYMARKET_PRIVATE_KEY"],
            funder_address=os.environ["POLYMARKET_FUNDER_ADDRESS"],
            signature_type=int(os.getenv("POLYMARKET_SIGNATURE_TYPE", "1")),
        )
        return cls(cfg)

    def _side_const(self, side: Side):
        """Convert string side to CLOB constant"""
        return BUY if side == "BUY" else SELL

    def get_server_time(self) -> Dict[str, Any]:
        """Test connection - get server timestamp"""
        return self.client.get_server_time()

    def check_health(self) -> bool:
        """Check if API is responding"""
        try:
            resp = self.client.get_ok()
            # Handle both dict and string responses
            if isinstance(resp, dict):
                return resp.get("status") == "ok"
            return resp == "ok" or resp == "OK"
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def place_market_order_usd(
        self,
        token_id: str,
        usd_amount: float,
        side: Side,
        order_type: OrderType = OrderType.FOK,
    ) -> Dict[str, Any]:
        """
        Place market order by USD amount.

        Args:
            token_id: Conditional token ID from Polymarket
            usd_amount: Dollar amount to spend/receive
            side: "BUY" or "SELL"
            order_type: FOK (fill-or-kill) or GTC (good-til-cancel)

        Returns:
            API response dict with order details
        """
        mo = MarketOrderArgs(
            token_id=token_id,
            amount=usd_amount,
            side=self._side_const(side),
            order_type=order_type,
        )
        signed = self.client.create_market_order(mo)
        resp = self.client.post_order(signed, order_type)

        self.logger.info(
            "Placed market order: %s %s $%.2f on token %s",
            side, order_type if isinstance(order_type, str) else order_type.value, usd_amount, token_id
        )
        return resp

    def place_limit_order(
        self,
        token_id: str,
        price: float,
        size: float,
        side: Side,
        order_type: OrderType = OrderType.GTC,
    ) -> Dict[str, Any]:
        """
        Place limit order.

        Args:
            token_id: Conditional token ID from Polymarket
            price: Limit price in [0, 1]
            size: Number of shares
            side: "BUY" or "SELL"
            order_type: GTC (good-til-cancel) or FOK (fill-or-kill)

        Returns:
            API response dict with order details
        """
        order = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=self._side_const(side),
        )
        signed = self.client.create_order(order)
        resp = self.client.post_order(signed, order_type)

        self.logger.info(
            "Placed limit order: %s %.2f shares @ %.4f on token %s",
            side, size, price, token_id
        )
        return resp

    def get_open_orders(self) -> list:
        """Get all open orders for this account"""
        return self.client.get_orders()

    def get_trades(self) -> list:
        """Get trade history for this account"""
        return self.client.get_trades()

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an open order"""
        return self.client.cancel(order_id)

    def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all open orders"""
        return self.client.cancel_all()
