#!/usr/bin/env python3
"""
Polymarket WebSocket - Unlimited Real-Time Data

SOLUTION TO RATE LIMITS:
- WebSocket = push-based (no polling)
- Subscribe once, receive unlimited updates
- No rate limits on RECEIVING data
- Only rate limits on SENDING orders

Channels:
- market: Price updates, trades, orderbook changes
- user: Your orders, fills, positions (requires auth)

Serving: Yair Siegel
"""

import os
import sys
import json
import time
import asyncio
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import hmac
import hashlib
import base64

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"


@dataclass
class MarketUpdate:
    """Real-time market update from WebSocket."""
    event_type: str  # price_change, trade, book_update
    token_id: str
    price: float
    timestamp: str
    data: Dict = field(default_factory=dict)


@dataclass
class UserUpdate:
    """Real-time user update from WebSocket."""
    event_type: str  # order_placed, order_filled, order_cancelled
    order_id: str
    timestamp: str
    data: Dict = field(default_factory=dict)


class PolymarketWebSocket:
    """
    WebSocket connection manager for Polymarket.

    UNLIMITED data throughput via push subscriptions.
    No rate limits on receiving WebSocket messages.
    """

    # Official WebSocket endpoint (from Polymarket/real-time-data-client)
    WSS_URL = "wss://ws-live-data.polymarket.com"

    def __init__(self):
        self._ws = None
        self._connected = False
        self._subscriptions: Dict[str, set] = {
            "market": set(),
            "user": set()
        }
        self._callbacks: Dict[str, List[Callable]] = {
            "market": [],
            "user": [],
            "all": []
        }
        self._message_count = 0
        self._last_message_time = None
        self._api_creds = None
        self._running = False
        self._thread = None
        self._loop = None

    # ==================== CREDENTIALS ====================

    def _get_api_creds(self):
        """Get or create API credentials for authenticated channel."""
        if self._api_creds:
            return self._api_creds

        private_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
        funder = os.environ.get("POLYMARKET_FUNDER_ADDRESS")

        if not private_key:
            return None

        try:
            from py_clob_client.client import ClobClient

            client = ClobClient(
                "https://clob.polymarket.com",
                key=private_key,
                chain_id=137,
                funder=funder
            )
            self._api_creds = client.create_or_derive_api_creds()
            return self._api_creds
        except Exception as e:
            print(f"Failed to get API creds: {e}")
            return None

    def _sign_message(self, timestamp: int, message: str) -> str:
        """Sign message for WebSocket authentication."""
        if not self._api_creds:
            return ""

        secret = self._api_creds.api_secret
        msg = f"{timestamp}{message}"
        signature = hmac.new(
            base64.b64decode(secret),
            msg.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()

    # ==================== CONNECTION ====================

    async def _connect(self):
        """Establish WebSocket connection."""
        try:
            import websockets

            self._ws = await websockets.connect(
                self.WSS_URL,
                ping_interval=30,
                ping_timeout=10
            )
            self._connected = True
            print(f"[WSS] Connected to {self.WSS_URL}")
            return True

        except ImportError:
            print("[WSS] websockets library not installed. Run: pip install websockets")
            return False
        except Exception as e:
            print(f"[WSS] Connection failed: {e}")
            self._connected = False
            return False

    async def _reconnect(self):
        """Reconnect and restore subscriptions."""
        print("[WSS] Reconnecting...")

        if await self._connect():
            # Restore market subscriptions
            for token_id in self._subscriptions["market"]:
                await self._send_subscribe("market", token_id)

            # Restore user subscription
            if self._subscriptions["user"]:
                await self._send_auth_subscribe()

    async def _send(self, message: Dict):
        """Send message to WebSocket."""
        if not self._ws or not self._connected:
            return False

        try:
            await self._ws.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"[WSS] Send failed: {e}")
            return False

    async def _receive_loop(self):
        """Main receive loop - processes all incoming messages."""
        while self._running:
            try:
                if not self._ws or not self._connected:
                    await asyncio.sleep(1)
                    await self._reconnect()
                    continue

                message = await asyncio.wait_for(
                    self._ws.recv(),
                    timeout=60
                )

                self._message_count += 1
                self._last_message_time = datetime.now(timezone.utc)

                data = json.loads(message)
                await self._handle_message(data)

            except asyncio.TimeoutError:
                # Send ping to keep alive
                if self._ws:
                    await self._ws.ping()

            except Exception as e:
                print(f"[WSS] Receive error: {e}")
                self._connected = False
                await asyncio.sleep(1)

    async def _handle_message(self, data: Dict):
        """Handle incoming WebSocket message."""
        msg_type = data.get("type", data.get("event_type", ""))

        # Market channel updates
        if msg_type in ["price_change", "trade", "book", "tick_size_change"]:
            update = MarketUpdate(
                event_type=msg_type,
                token_id=data.get("asset_id", data.get("market", "")),
                price=float(data.get("price", 0)),
                timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                data=data
            )

            for callback in self._callbacks["market"]:
                try:
                    callback(update)
                except Exception as e:
                    pass

        # User channel updates
        elif msg_type in ["order", "trade", "fill"]:
            update = UserUpdate(
                event_type=msg_type,
                order_id=data.get("order_id", data.get("id", "")),
                timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                data=data
            )

            for callback in self._callbacks["user"]:
                try:
                    callback(update)
                except Exception as e:
                    pass

        # All callbacks
        for callback in self._callbacks["all"]:
            try:
                callback(data)
            except Exception as e:
                pass

    # ==================== SUBSCRIPTIONS ====================

    async def _send_subscribe(self, channel: str, asset_id: str):
        """Subscribe to market channel for an asset."""
        message = {
            "type": "subscribe",
            "channel": channel,
            "market": asset_id,
            "assets_id": asset_id
        }
        return await self._send(message)

    async def _send_auth_subscribe(self):
        """Subscribe to authenticated user channel."""
        creds = self._get_api_creds()
        if not creds:
            print("[WSS] No API credentials for user channel")
            return False

        timestamp = int(time.time() * 1000)
        signature = self._sign_message(timestamp, "GET/ws/user")

        message = {
            "type": "subscribe",
            "channel": "user",
            "auth": {
                "apiKey": creds.api_key,
                "passphrase": creds.api_passphrase,
                "timestamp": str(timestamp),
                "signature": signature
            }
        }
        return await self._send(message)

    def subscribe_market(self, token_id: str):
        """Subscribe to market updates for a token."""
        self._subscriptions["market"].add(token_id)

        if self._loop and self._connected:
            asyncio.run_coroutine_threadsafe(
                self._send_subscribe("market", token_id),
                self._loop
            )

    def subscribe_user(self):
        """Subscribe to user channel (orders, fills)."""
        self._subscriptions["user"].add("user")

        if self._loop and self._connected:
            asyncio.run_coroutine_threadsafe(
                self._send_auth_subscribe(),
                self._loop
            )

    def on_market(self, callback: Callable[[MarketUpdate], None]):
        """Register callback for market updates."""
        self._callbacks["market"].append(callback)

    def on_user(self, callback: Callable[[UserUpdate], None]):
        """Register callback for user updates."""
        self._callbacks["user"].append(callback)

    def on_message(self, callback: Callable[[Dict], None]):
        """Register callback for all messages."""
        self._callbacks["all"].append(callback)

    # ==================== LIFECYCLE ====================

    def _run_loop(self):
        """Run the async event loop in a thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def main():
            await self._connect()

            # Subscribe to any pre-registered subscriptions
            for token_id in self._subscriptions["market"]:
                await self._send_subscribe("market", token_id)

            if self._subscriptions["user"]:
                await self._send_auth_subscribe()

            # Run receive loop
            await self._receive_loop()

        self._loop.run_until_complete(main())

    def start(self):
        """Start WebSocket connection in background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        # Wait for connection
        for _ in range(50):  # 5 second timeout
            if self._connected:
                break
            time.sleep(0.1)

        return self._connected

    def stop(self):
        """Stop WebSocket connection."""
        self._running = False

        if self._ws:
            if self._loop:
                asyncio.run_coroutine_threadsafe(
                    self._ws.close(),
                    self._loop
                )

        if self._thread:
            self._thread.join(timeout=2)

        self._connected = False

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get WebSocket status."""
        return {
            "connected": self._connected,
            "url": self.WSS_URL,
            "messages_received": self._message_count,
            "last_message": self._last_message_time.isoformat() if self._last_message_time else None,
            "market_subscriptions": len(self._subscriptions["market"]),
            "user_subscribed": bool(self._subscriptions["user"]),
            "callbacks_registered": {
                "market": len(self._callbacks["market"]),
                "user": len(self._callbacks["user"]),
                "all": len(self._callbacks["all"])
            }
        }

    def quick_status(self) -> str:
        """One-line status."""
        s = self.status()
        return f"WSS: {'LIVE' if s['connected'] else 'DISCONNECTED'} | Msgs: {s['messages_received']} | Subs: {s['market_subscriptions']}"


# Singleton
_websocket = None

def get_websocket() -> PolymarketWebSocket:
    """Get or create WebSocket singleton."""
    global _websocket
    if _websocket is None:
        _websocket = PolymarketWebSocket()
    return _websocket


# Convenience alias
poly_ws = get_websocket()


if __name__ == "__main__":
    print("=" * 60)
    print("POLYMARKET WEBSOCKET - UNLIMITED REAL-TIME DATA")
    print("=" * 60)

    ws = get_websocket()

    # Simple message counter
    received = {"count": 0}

    def on_any_message(data):
        received["count"] += 1
        msg_type = data.get("type", data.get("event_type", "unknown"))
        print(f"  [{received['count']}] {msg_type}: {str(data)[:100]}...")

    ws.on_message(on_any_message)

    # Start connection
    print("\n[CONNECTING...]")
    if ws.start():
        print("[CONNECTED] Listening for messages...")
        print()

        # Subscribe to user channel for our orders
        ws.subscribe_user()

        # Listen for 10 seconds
        try:
            for i in range(10):
                time.sleep(1)
                print(f"  Status: {ws.quick_status()}")
        except KeyboardInterrupt:
            pass

        ws.stop()
    else:
        print("[FAILED] Could not connect")

    print("\n" + "=" * 60)
    print(f"Total messages received: {received['count']}")
    print("=" * 60)
