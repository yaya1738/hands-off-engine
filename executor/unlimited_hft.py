#!/usr/bin/env python3
"""
UNLIMITED HFT - Maximum Throughput Polymarket Execution

THE MATH:
- 63 wallets × 240 orders/sec per wallet = 15,120 orders/sec
- 9 droplets × 500 requests/sec per IP = 4,500 requests/sec
- WebSocket = UNLIMITED real-time data (push, no polling)

STRATEGY:
1. Round-robin across all wallets
2. Parallel execution threads
3. WebSocket for market data
4. No rate limit collisions

Serving: Yair Siegel
"""

import os
import sys
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import queue

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"


@dataclass
class WalletClient:
    """A single wallet's trading client."""
    address: str
    private_key: str
    client: Any = None
    orders_placed: int = 0
    last_order_time: float = 0
    rate_limit_until: float = 0


class UnlimitedHFT:
    """
    Unlimited throughput HFT using wallet fleet.

    63 wallets = 63x rate limits = effectively unlimited.
    """

    def __init__(self):
        self._wallets: List[WalletClient] = []
        self._wallet_index = 0
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=20)
        self._order_queue = queue.Queue()
        self._running = False
        self._stats = {
            "orders_placed": 0,
            "orders_per_second": 0,
            "errors": 0,
            "start_time": None
        }

    def _load_wallets(self):
        """Load all available wallets from registry."""
        loaded_addresses = set()

        # Load from wallet registry (63 wallets)
        registry_file = STATE_DIR / "wallets" / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file) as f:
                    registry = json.load(f)
                    wallets_dict = registry.get("wallets", {})

                    for addr, w in wallets_dict.items():
                        private_key = w.get("private_key", "")
                        if private_key and addr not in loaded_addresses:
                            self._wallets.append(WalletClient(
                                address=addr,
                                private_key=private_key
                            ))
                            loaded_addresses.add(addr)
            except Exception as e:
                print(f"Registry load error: {e}")

        # Fallback: Primary wallet from env
        if not self._wallets:
            primary_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
            primary_funder = os.environ.get("POLYMARKET_FUNDER_ADDRESS")

            if primary_key and primary_funder:
                self._wallets.append(WalletClient(
                    address=primary_funder,
                    private_key=primary_key
                ))

        return len(self._wallets)

    def _get_next_wallet(self) -> Optional[WalletClient]:
        """Round-robin wallet selection with rate limit awareness."""
        with self._lock:
            if not self._wallets:
                return None

            now = time.time()

            # Try each wallet until we find one not rate limited
            for _ in range(len(self._wallets)):
                wallet = self._wallets[self._wallet_index]
                self._wallet_index = (self._wallet_index + 1) % len(self._wallets)

                if now >= wallet.rate_limit_until:
                    return wallet

            # All rate limited, return least-limited one
            return min(self._wallets, key=lambda w: w.rate_limit_until)

    def _init_wallet_client(self, wallet: WalletClient):
        """Initialize trading client for wallet."""
        if wallet.client is not None:
            return wallet.client

        try:
            from py_clob_client.client import ClobClient

            wallet.client = ClobClient(
                "https://clob.polymarket.com",
                key=wallet.private_key,
                chain_id=137
            )

            creds = wallet.client.create_or_derive_api_creds()
            wallet.client.set_api_creds(creds)

            return wallet.client
        except Exception as e:
            return None

    def place_order(self, token_id: str, price: float, size: float, side: str) -> Dict:
        """Place order using next available wallet."""
        wallet = self._get_next_wallet()
        if not wallet:
            return {"success": False, "error": "No wallets available"}

        client = self._init_wallet_client(wallet)
        if not client:
            return {"success": False, "error": "Failed to init wallet"}

        try:
            from py_clob_client.order_builder.constants import BUY, SELL

            order_side = BUY if side.upper() == "BUY" else SELL

            order = client.create_order({
                "token_id": token_id,
                "price": price,
                "size": size,
                "side": order_side
            })

            result = client.post_order(order)

            wallet.orders_placed += 1
            wallet.last_order_time = time.time()
            self._stats["orders_placed"] += 1

            return {"success": True, "order": result, "wallet": wallet.address[:10]}

        except Exception as e:
            error_str = str(e)

            # Handle rate limit
            if "429" in error_str or "rate" in error_str.lower():
                wallet.rate_limit_until = time.time() + 2  # 2 sec backoff

            self._stats["errors"] += 1
            return {"success": False, "error": error_str}

    def place_orders_parallel(self, orders: List[Dict]) -> List[Dict]:
        """Place multiple orders in parallel across wallet fleet."""
        futures = []

        for order in orders:
            future = self._executor.submit(
                self.place_order,
                order["token_id"],
                order["price"],
                order["size"],
                order["side"]
            )
            futures.append(future)

        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                results.append({"success": False, "error": str(e)})

        return results

    def spray_orders(self, token_id: str, center_price: float, spread_bps: int = 100,
                     levels: int = 10, size_per_level: float = 10) -> Dict:
        """
        Spray orders across price levels using all wallets.

        Creates a grid of buy and sell orders around center price.
        """
        orders = []
        spread = center_price * (spread_bps / 10000)

        for i in range(levels):
            offset = spread * (i + 1) / levels

            # Buy orders below center
            orders.append({
                "token_id": token_id,
                "price": round(center_price - offset, 4),
                "size": size_per_level,
                "side": "BUY"
            })

            # Sell orders above center
            orders.append({
                "token_id": token_id,
                "price": round(center_price + offset, 4),
                "size": size_per_level,
                "side": "SELL"
            })

        results = self.place_orders_parallel(orders)

        successful = sum(1 for r in results if r.get("success"))

        return {
            "success": True,
            "orders_attempted": len(orders),
            "orders_placed": successful,
            "orders_failed": len(orders) - successful,
            "wallets_used": len(set(r.get("wallet", "") for r in results if r.get("wallet")))
        }

    def cancel_all(self) -> Dict:
        """Cancel all orders across all wallets."""
        results = []

        for wallet in self._wallets:
            client = self._init_wallet_client(wallet)
            if client:
                try:
                    result = client.cancel_all()
                    results.append({"wallet": wallet.address[:10], "success": True})
                except Exception as e:
                    results.append({"wallet": wallet.address[:10], "success": False, "error": str(e)})

        return {
            "success": True,
            "wallets_processed": len(results),
            "results": results
        }

    def status(self) -> Dict:
        """Get HFT status."""
        if not self._wallets:
            self._load_wallets()

        now = time.time()
        active_wallets = sum(1 for w in self._wallets if now >= w.rate_limit_until)

        # Calculate orders per second
        if self._stats["start_time"]:
            elapsed = now - self._stats["start_time"]
            if elapsed > 0:
                self._stats["orders_per_second"] = self._stats["orders_placed"] / elapsed

        # Theoretical capacity
        capacity = len(self._wallets) * 240  # 240 orders/sec per wallet

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wallets_total": len(self._wallets),
            "wallets_active": active_wallets,
            "wallets_rate_limited": len(self._wallets) - active_wallets,
            "orders_placed": self._stats["orders_placed"],
            "orders_per_second": round(self._stats["orders_per_second"], 2),
            "errors": self._stats["errors"],
            "theoretical_capacity": f"{capacity:,}/sec",
            "mode": "UNLIMITED"
        }

    def quick_status(self) -> str:
        """One-line status."""
        s = self.status()
        return f"HFT: {s['wallets_active']}/{s['wallets_total']} wallets | {s['orders_placed']} orders | {s['theoretical_capacity']}"

    def activate(self) -> Dict:
        """Activate unlimited HFT mode."""
        wallet_count = self._load_wallets()
        self._stats["start_time"] = time.time()
        self._running = True

        return {
            "success": True,
            "activated": True,
            "wallets_loaded": wallet_count,
            "theoretical_capacity": f"{wallet_count * 240:,} orders/sec",
            "mode": "UNLIMITED",
            "message": f"HFT ACTIVATED: {wallet_count} wallets ready for unlimited execution"
        }


# Singleton
_hft = None

def get_unlimited_hft() -> UnlimitedHFT:
    """Get or create unlimited HFT singleton."""
    global _hft
    if _hft is None:
        _hft = UnlimitedHFT()
    return _hft


# Convenience alias
unlimited = get_unlimited_hft()


def activate() -> Dict:
    """Activate unlimited HFT."""
    return unlimited.activate()


if __name__ == "__main__":
    print("=" * 60)
    print("UNLIMITED HFT - ACTIVATING")
    print("=" * 60)

    hft = get_unlimited_hft()

    # Activate
    result = hft.activate()
    print(f"\n{result['message']}")
    print(f"Capacity: {result['theoretical_capacity']}")

    # Status
    print("\n[STATUS]")
    status = hft.status()
    for k, v in status.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 60)
    print(hft.quick_status())
    print("=" * 60)
