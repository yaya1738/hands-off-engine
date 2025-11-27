"""
Polymarket CLOB API Client for Hands-Off Engine

Provides order execution, balance queries, and position management
for real trading on Polymarket.

Reference: https://docs.polymarket.com/developers/CLOB/

Safety: DRYRUN mode is enforced by default.
"""

import hashlib
import hmac
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


class PolymarketError(Exception):
    """Base exception for Polymarket API errors"""
    pass


class AuthenticationError(PolymarketError):
    """Raised when authentication fails"""
    pass


class InsufficientFundsError(PolymarketError):
    """Raised when account has insufficient funds"""
    pass


class InvalidMarketError(PolymarketError):
    """Raised when market ID is invalid"""
    pass


class RateLimitError(PolymarketError):
    """Raised when rate limit is hit"""
    pass


class OrderError(PolymarketError):
    """Raised when order placement/cancellation fails"""
    pass


class OrderSide(str, Enum):
    """Order side constants"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type constants"""
    GTC = "GTC"  # Good-Til-Cancelled
    GTD = "GTD"  # Good-Til-Date
    FOK = "FOK"  # Fill-Or-Kill


@dataclass
class OrderResult:
    """Result of an order operation"""
    success: bool
    order_id: Optional[str]
    message: str
    side: str
    size_usd: float
    price: float
    market_id: str
    dryrun: bool = True


@dataclass
class Position:
    """Represents a market position"""
    market_id: str
    token_id: str
    side: str
    size: float
    avg_price: float


@dataclass
class Balance:
    """Account balance information"""
    usdc_balance: float
    available_balance: float


class PolymarketClient:
    """
    Client for Polymarket CLOB API

    Usage:
        client = PolymarketClient(
            api_key="your_api_key",
            api_secret="your_api_secret",
            api_passphrase="your_passphrase"
        )

        # Get balance
        balance = client.get_balance()

        # Place order (DRYRUN by default)
        result = client.place_order(
            market_id="0x...",
            side=OrderSide.BUY,
            size_usd=10.0,
            price=0.55
        )
    """

    # CLOB API base URL
    BASE_URL = "https://clob.polymarket.com"

    # Rate limiting settings
    MAX_REQUESTS_PER_SECOND = 10
    RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 1.0
    RATE_LIMIT_DELAY = 0.1  # 100ms between requests

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_passphrase: Optional[str] = None,
        wallet_address: Optional[str] = None,
        dryrun: bool = True,
        base_url: Optional[str] = None
    ):
        """
        Initialize Polymarket client.

        Args:
            api_key: Polymarket API key (or POLYMARKET_API_KEY env var)
            api_secret: Polymarket API secret (or POLYMARKET_API_SECRET env var)
            api_passphrase: Polymarket API passphrase (or POLYMARKET_API_PASSPHRASE env var)
            wallet_address: Polygon wallet address (or POLYMARKET_WALLET_ADDRESS env var)
            dryrun: If True, no actual trades are executed (default: True)
            base_url: Override base URL for testing
        """
        self.api_key = api_key or os.environ.get("POLYMARKET_API_KEY")
        self.api_secret = api_secret or os.environ.get("POLYMARKET_API_SECRET")
        self.api_passphrase = api_passphrase or os.environ.get("POLYMARKET_API_PASSPHRASE")
        self.wallet_address = wallet_address or os.environ.get("POLYMARKET_WALLET_ADDRESS")
        self.dryrun = dryrun
        self.base_url = base_url or self.BASE_URL

        # Rate limiting
        self._last_request_time: float = 0.0

        # Audit logging
        self.audit = get_audit_logger(component="polymarket_client")

        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "hands-off-engine/1.0"
        })

    def _validate_credentials(self) -> None:
        """Validate that API credentials are set"""
        if not self.api_key:
            raise AuthenticationError("API key not set. Set POLYMARKET_API_KEY or pass api_key")
        if not self.api_secret:
            raise AuthenticationError("API secret not set. Set POLYMARKET_API_SECRET or pass api_secret")
        if not self.api_passphrase:
            raise AuthenticationError("API passphrase not set. Set POLYMARKET_API_PASSPHRASE or pass api_passphrase")
        if not self.wallet_address:
            raise AuthenticationError("Wallet address not set. Set POLYMARKET_WALLET_ADDRESS or pass wallet_address")

    def _generate_signature(
        self,
        timestamp: str,
        method: str,
        path: str,
        body: str = ""
    ) -> str:
        """
        Generate HMAC signature for API request.

        Args:
            timestamp: Unix timestamp as string
            method: HTTP method (GET, POST, DELETE)
            path: Request path (e.g., /order)
            body: Request body as string (empty for GET)

        Returns:
            Base64-encoded HMAC signature
        """
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_auth_headers(
        self,
        method: str,
        path: str,
        body: str = ""
    ) -> Dict[str, str]:
        """
        Get authentication headers for API request.

        Args:
            method: HTTP method
            path: Request path
            body: Request body

        Returns:
            Dict of authentication headers
        """
        timestamp = str(int(time.time()))
        signature = self._generate_signature(timestamp, method, path, body)

        return {
            "POLY_ADDRESS": self.wallet_address,
            "POLY_SIGNATURE": signature,
            "POLY_TIMESTAMP": timestamp,
            "POLY_API_KEY": self.api_key,
            "POLY_PASSPHRASE": self.api_passphrase
        }

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        require_auth: bool = True
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Make authenticated API request with retry logic.

        Args:
            method: HTTP method
            path: Request path
            body: Request body dict (will be JSON serialized)
            require_auth: Whether to include auth headers

        Returns:
            Tuple of (status_code, response_dict)

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            PolymarketError: For other API errors
        """
        if require_auth:
            self._validate_credentials()

        url = f"{self.base_url}{path}"
        body_str = json.dumps(body) if body else ""

        headers = dict(self._session.headers)
        if require_auth:
            headers.update(self._get_auth_headers(method, path, body_str))

        last_error = None
        for attempt in range(self.RETRY_ATTEMPTS):
            self._rate_limit()

            try:
                if method == "GET":
                    response = self._session.get(url, headers=headers, timeout=30)
                elif method == "POST":
                    response = self._session.post(
                        url,
                        headers=headers,
                        data=body_str,
                        timeout=30
                    )
                elif method == "DELETE":
                    response = self._session.delete(
                        url,
                        headers=headers,
                        data=body_str,
                        timeout=30
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Log the API call
                self.audit.log_data_fetch(
                    source="polymarket_clob",
                    params={"method": method, "path": path},
                    success=response.status_code < 400,
                    error=None if response.status_code < 400 else response.text[:200]
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    if attempt < self.RETRY_ATTEMPTS - 1:
                        time.sleep(retry_after)
                        continue
                    raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after}s")

                # Handle auth errors
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API credentials")
                if response.status_code == 403:
                    raise AuthenticationError("Access forbidden - check API key permissions")

                # Parse response
                try:
                    data = response.json() if response.text else {}
                except json.JSONDecodeError:
                    data = {"raw_response": response.text}

                return response.status_code, data

            except requests.exceptions.Timeout:
                last_error = PolymarketError("Request timed out")
                if attempt < self.RETRY_ATTEMPTS - 1:
                    time.sleep(self.RETRY_DELAY_SECONDS * (attempt + 1))
                    continue
            except requests.exceptions.ConnectionError as e:
                last_error = PolymarketError(f"Connection error: {e}")
                if attempt < self.RETRY_ATTEMPTS - 1:
                    time.sleep(self.RETRY_DELAY_SECONDS * (attempt + 1))
                    continue

        raise last_error or PolymarketError("Request failed after retries")

    def get_balance(self) -> Balance:
        """
        Get account USDC balance.

        Returns:
            Balance object with USDC balance info

        Raises:
            AuthenticationError: If credentials are invalid
            PolymarketError: If API call fails
        """
        if self.dryrun:
            # Return mock balance in dryrun mode
            self.audit.log_data_fetch(
                source="polymarket_balance",
                params={"mode": "DRYRUN"},
                success=True
            )
            return Balance(usdc_balance=1000.0, available_balance=1000.0)

        status, data = self._request("GET", "/balance")

        if status != 200:
            error_msg = data.get("error", data.get("message", "Unknown error"))
            raise PolymarketError(f"Failed to get balance: {error_msg}")

        return Balance(
            usdc_balance=float(data.get("balance", 0)),
            available_balance=float(data.get("available", data.get("balance", 0)))
        )

    def get_positions(self) -> List[Position]:
        """
        Get current market positions.

        Returns:
            List of Position objects

        Raises:
            AuthenticationError: If credentials are invalid
            PolymarketError: If API call fails
        """
        if self.dryrun:
            # Return empty positions in dryrun mode
            self.audit.log_data_fetch(
                source="polymarket_positions",
                params={"mode": "DRYRUN"},
                success=True,
                record_count=0
            )
            return []

        status, data = self._request("GET", "/positions")

        if status != 200:
            error_msg = data.get("error", data.get("message", "Unknown error"))
            raise PolymarketError(f"Failed to get positions: {error_msg}")

        positions = []
        for pos in data.get("positions", []):
            positions.append(Position(
                market_id=pos.get("market_id", ""),
                token_id=pos.get("token_id", ""),
                side=pos.get("side", ""),
                size=float(pos.get("size", 0)),
                avg_price=float(pos.get("avg_price", 0))
            ))

        self.audit.log_data_fetch(
            source="polymarket_positions",
            params={},
            success=True,
            record_count=len(positions)
        )

        return positions

    def place_order(
        self,
        market_id: str,
        side: OrderSide,
        size_usd: float,
        price: float,
        order_type: OrderType = OrderType.GTC,
        token_id: Optional[str] = None
    ) -> OrderResult:
        """
        Place an order on Polymarket.

        Args:
            market_id: Market/condition ID
            side: BUY or SELL
            size_usd: Order size in USD
            price: Limit price (0.0 to 1.0)
            order_type: Order type (GTC, GTD, FOK)
            token_id: Optional token ID (if not provided, will be resolved)

        Returns:
            OrderResult with order details

        Raises:
            InvalidMarketError: If market ID is invalid
            InsufficientFundsError: If account has insufficient funds
            OrderError: If order placement fails
        """
        # Validate inputs
        if not market_id:
            raise InvalidMarketError("Market ID is required")
        if not 0.0 < price <= 1.0:
            raise OrderError(f"Price must be between 0 and 1, got {price}")
        if size_usd <= 0:
            raise OrderError(f"Size must be positive, got {size_usd}")

        side_str = side.value if isinstance(side, OrderSide) else str(side).upper()

        # Log order attempt
        self.audit.log_order(
            order_type="limit",
            market=market_id,
            side=side_str,
            size=size_usd,
            price=price,
            dryrun=self.dryrun
        )

        if self.dryrun:
            # Return simulated success in dryrun mode
            order_id = f"dryrun_{int(time.time())}_{market_id[:8]}"
            self.audit.log_action(
                action_type="order_placed",
                action_data={
                    "order_id": order_id,
                    "market_id": market_id,
                    "side": side_str,
                    "size_usd": size_usd,
                    "price": price,
                    "mode": "DRYRUN"
                },
                result="simulated_success"
            )
            return OrderResult(
                success=True,
                order_id=order_id,
                message=f"DRYRUN: Would place {side_str} order for ${size_usd:.2f} at {price:.4f}",
                side=side_str,
                size_usd=size_usd,
                price=price,
                market_id=market_id,
                dryrun=True
            )

        # Build order payload
        order_payload = {
            "market": market_id,
            "side": side_str,
            "size": str(size_usd),
            "price": str(price),
            "type": order_type.value
        }
        if token_id:
            order_payload["token_id"] = token_id

        try:
            status, data = self._request("POST", "/order", order_payload)

            if status == 200 or status == 201:
                order_id = data.get("order_id", data.get("id", ""))
                self.audit.log_action(
                    action_type="order_placed",
                    action_data={
                        "order_id": order_id,
                        "market_id": market_id,
                        "side": side_str,
                        "size_usd": size_usd,
                        "price": price,
                        "mode": "LIVE"
                    },
                    result="success"
                )
                return OrderResult(
                    success=True,
                    order_id=order_id,
                    message=f"Order placed successfully",
                    side=side_str,
                    size_usd=size_usd,
                    price=price,
                    market_id=market_id,
                    dryrun=False
                )

            # Handle specific error cases
            error_msg = data.get("error", data.get("message", "Unknown error"))

            if "insufficient" in error_msg.lower() or "balance" in error_msg.lower():
                self.audit.log_error(
                    error_type="insufficient_funds",
                    error_message=error_msg,
                    context={"market_id": market_id, "size_usd": size_usd}
                )
                raise InsufficientFundsError(error_msg)

            if "market" in error_msg.lower() and ("invalid" in error_msg.lower() or "not found" in error_msg.lower()):
                self.audit.log_error(
                    error_type="invalid_market",
                    error_message=error_msg,
                    context={"market_id": market_id}
                )
                raise InvalidMarketError(error_msg)

            self.audit.log_error(
                error_type="order_failed",
                error_message=error_msg,
                context={"market_id": market_id, "status": status}
            )
            raise OrderError(f"Order failed: {error_msg}")

        except (AuthenticationError, InsufficientFundsError, InvalidMarketError, OrderError):
            raise
        except Exception as e:
            self.audit.log_error(
                error_type="order_exception",
                error_message=str(e),
                context={"market_id": market_id}
            )
            raise OrderError(f"Order failed: {e}")

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully

        Raises:
            OrderError: If cancellation fails
        """
        if not order_id:
            raise OrderError("Order ID is required")

        self.audit.log_action(
            action_type="cancel_order_attempt",
            action_data={"order_id": order_id, "mode": "DRYRUN" if self.dryrun else "LIVE"}
        )

        if self.dryrun:
            self.audit.log_action(
                action_type="order_cancelled",
                action_data={"order_id": order_id, "mode": "DRYRUN"},
                result="simulated_success"
            )
            return True

        try:
            status, data = self._request("DELETE", f"/order/{order_id}")

            if status == 200 or status == 204:
                self.audit.log_action(
                    action_type="order_cancelled",
                    action_data={"order_id": order_id, "mode": "LIVE"},
                    result="success"
                )
                return True

            error_msg = data.get("error", data.get("message", "Unknown error"))
            self.audit.log_error(
                error_type="cancel_failed",
                error_message=error_msg,
                context={"order_id": order_id}
            )
            raise OrderError(f"Failed to cancel order: {error_msg}")

        except OrderError:
            raise
        except Exception as e:
            self.audit.log_error(
                error_type="cancel_exception",
                error_message=str(e),
                context={"order_id": order_id}
            )
            raise OrderError(f"Failed to cancel order: {e}")

    def cancel_all_orders(self) -> int:
        """
        Cancel all open orders.

        Returns:
            Number of orders cancelled

        Raises:
            OrderError: If cancellation fails
        """
        self.audit.log_action(
            action_type="cancel_all_attempt",
            action_data={"mode": "DRYRUN" if self.dryrun else "LIVE"}
        )

        if self.dryrun:
            self.audit.log_action(
                action_type="all_orders_cancelled",
                action_data={"mode": "DRYRUN", "count": 0},
                result="simulated_success"
            )
            return 0

        try:
            status, data = self._request("DELETE", "/orders")

            if status == 200 or status == 204:
                count = data.get("cancelled_count", len(data.get("cancelled", [])))
                self.audit.log_action(
                    action_type="all_orders_cancelled",
                    action_data={"mode": "LIVE", "count": count},
                    result="success"
                )
                return count

            error_msg = data.get("error", data.get("message", "Unknown error"))
            raise OrderError(f"Failed to cancel all orders: {error_msg}")

        except OrderError:
            raise
        except Exception as e:
            self.audit.log_error(
                error_type="cancel_all_exception",
                error_message=str(e)
            )
            raise OrderError(f"Failed to cancel all orders: {e}")

    def get_open_orders(self) -> List[Dict[str, Any]]:
        """
        Get list of open orders.

        Returns:
            List of open order dictionaries

        Raises:
            PolymarketError: If API call fails
        """
        if self.dryrun:
            self.audit.log_data_fetch(
                source="polymarket_orders",
                params={"mode": "DRYRUN"},
                success=True,
                record_count=0
            )
            return []

        status, data = self._request("GET", "/orders")

        if status != 200:
            error_msg = data.get("error", data.get("message", "Unknown error"))
            raise PolymarketError(f"Failed to get orders: {error_msg}")

        orders = data.get("orders", data if isinstance(data, list) else [])
        self.audit.log_data_fetch(
            source="polymarket_orders",
            params={},
            success=True,
            record_count=len(orders)
        )
        return orders

    def get_market(self, market_id: str) -> Dict[str, Any]:
        """
        Get market details.

        Args:
            market_id: Market ID to query

        Returns:
            Market details dictionary

        Raises:
            InvalidMarketError: If market not found
            PolymarketError: If API call fails
        """
        if not market_id:
            raise InvalidMarketError("Market ID is required")

        status, data = self._request("GET", f"/markets/{market_id}", require_auth=False)

        if status == 404:
            raise InvalidMarketError(f"Market not found: {market_id}")

        if status != 200:
            error_msg = data.get("error", data.get("message", "Unknown error"))
            raise PolymarketError(f"Failed to get market: {error_msg}")

        return data

    def close(self) -> None:
        """Close the HTTP session"""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# Example usage
if __name__ == "__main__":
    print("Polymarket Client - DRYRUN Example")
    print("=" * 50)

    # Create client in DRYRUN mode (default)
    client = PolymarketClient(
        api_key="test_key",
        api_secret="test_secret",
        api_passphrase="test_passphrase",
        wallet_address="0x1234567890abcdef1234567890abcdef12345678",
        dryrun=True
    )

    # Get balance (simulated)
    balance = client.get_balance()
    print(f"Balance: ${balance.usdc_balance:.2f} USDC")
    print(f"Available: ${balance.available_balance:.2f} USDC")

    # Get positions (simulated)
    positions = client.get_positions()
    print(f"Positions: {len(positions)}")

    # Place order (simulated)
    result = client.place_order(
        market_id="0xabcd1234",
        side=OrderSide.BUY,
        size_usd=50.0,
        price=0.55
    )
    print(f"Order result: {result.message}")
    print(f"Order ID: {result.order_id}")

    # Cancel order (simulated)
    cancelled = client.cancel_order(result.order_id)
    print(f"Order cancelled: {cancelled}")

    client.close()
