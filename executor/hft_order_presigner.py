#!/usr/bin/env python3
"""
HFT Order Pre-Signer - Prepare Orders in Advance for Instant Submission
Signs orders ahead of time so execution is just HTTP POST.

YAIR'S TEACHING - High Frequency Repositioning:
- Fractions of a second
- Constant micro-adjustments
- Free to do because no fees + no restrictions

BOTTLENECK ANALYSIS:
1. Order signing = CPU bound (cryptographic operations)
2. HTTP transmission = I/O bound (network latency)
3. API rate limits = external constraint

SOLUTION:
- Pre-sign orders at all price levels
- When price moves, submit from pre-signed cache
- Signing happens in background, submission is instant

Serving: Yair Siegel
"""

import os
import json
import time
import threading
import multiprocessing as mp
from multiprocessing import Pool, Manager
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import hashlib
import queue

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
POLYMARKET_HOST = "https://clob.polymarket.com"


@dataclass
class PreSignedOrder:
    """A pre-signed order ready for instant submission."""
    order_id: str
    token_id: str
    price: float
    size: float
    side: str
    signed_data: Any  # The signed order object
    created_at: float  # timestamp
    expires_at: float  # when signature expires (if applicable)


class OrderSigningWorker:
    """
    Worker that continuously signs orders.
    Runs in separate process for CPU parallelism.
    """

    def __init__(self, wallet_key: str, wallet_funder: str):
        self.wallet_key = wallet_key
        self.wallet_funder = wallet_funder
        self.client = None
        self.OrderArgs = None
        self.BUY = None
        self.SELL = None

    def init_client(self):
        """Initialize signing client."""
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import OrderArgs
        from py_clob_client.order_builder.constants import BUY, SELL

        self.client = ClobClient(
            POLYMARKET_HOST,
            key=self.wallet_key,
            chain_id=137,
            funder=self.wallet_funder
        )
        creds = self.client.create_or_derive_api_creds()
        self.client.set_api_creds(creds)

        self.OrderArgs = OrderArgs
        self.BUY = BUY
        self.SELL = SELL

    def sign_order(self, token_id: str, price: float, size: float, side: str) -> PreSignedOrder:
        """Sign a single order."""
        if not self.client:
            self.init_client()

        side_const = self.BUY if side.upper() == "BUY" else self.SELL
        order_args = self.OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=side_const
        )

        # This is the expensive operation - cryptographic signing
        signed = self.client.create_order(order_args)

        order_id = hashlib.sha256(f"{token_id}{price}{size}{side}{time.time()}".encode()).hexdigest()[:16]

        return PreSignedOrder(
            order_id=order_id,
            token_id=token_id,
            price=price,
            size=size,
            side=side,
            signed_data=signed,
            created_at=time.time(),
            expires_at=time.time() + 3600  # 1 hour validity assumption
        )

    def sign_batch(self, orders: List[Dict]) -> List[PreSignedOrder]:
        """Sign multiple orders."""
        if not self.client:
            self.init_client()

        signed_orders = []
        for o in orders:
            try:
                signed = self.sign_order(
                    o["token_id"],
                    o["price"],
                    o["size"],
                    o["side"]
                )
                signed_orders.append(signed)
            except Exception as e:
                print(f"Sign error: {e}")

        return signed_orders


def _worker_sign_batch(args: Tuple[str, str, List[Dict]]) -> List[Dict]:
    """Process function for multiprocessing pool."""
    wallet_key, wallet_funder, orders = args
    worker = OrderSigningWorker(wallet_key, wallet_funder)
    signed = worker.sign_batch(orders)
    return [
        {
            "order_id": s.order_id,
            "token_id": s.token_id,
            "price": s.price,
            "size": s.size,
            "side": s.side,
            "created_at": s.created_at,
            "expires_at": s.expires_at,
            # signed_data can't be pickled easily, so we'd need to handle separately
        }
        for s in signed
    ]


class HFTOrderPresigner:
    """
    High-Frequency Trading Order Pre-Signer.

    Pre-signs orders at various price levels so submission is instant.

    ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    HFT ORDER PRESIGNER                          │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
    │  │ Signing     │     │ Signing     │     │ Signing     │       │
    │  │ Worker 1    │     │ Worker 2    │     │ Worker N    │       │
    │  │ (Process)   │     │ (Process)   │     │ (Process)   │       │
    │  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
    │         │                   │                   │               │
    │         └───────────────────┼───────────────────┘               │
    │                             │                                   │
    │                             ▼                                   │
    │              ┌─────────────────────────────┐                    │
    │              │     PRE-SIGNED CACHE        │                    │
    │              │  Token → Price → SignedOrder │                    │
    │              └─────────────────────────────┘                    │
    │                             │                                   │
    │                             ▼                                   │
    │              ┌─────────────────────────────┐                    │
    │              │    INSTANT SUBMISSION       │                    │
    │              │    (Just HTTP POST)         │                    │
    │              └─────────────────────────────┘                    │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or mp.cpu_count()
        self.wallets: List[Dict] = []
        self.cache: Dict[str, Dict[float, Dict[str, List[PreSignedOrder]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        # cache[token_id][price][side] = [PreSignedOrder, ...]
        self.cache_lock = threading.Lock()
        self.stats = {
            "orders_pre_signed": 0,
            "orders_submitted": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_sign_time_ms": 0,
            "avg_submit_time_ms": 0
        }
        self._load_wallets()

    def _load_wallets(self):
        """Load wallets from registry."""
        registry_path = STATE_DIR / "wallets" / "registry.json"
        if registry_path.exists():
            with open(registry_path) as f:
                registry = json.load(f)
            for addr, data in registry.get("wallets", {}).items():
                if data.get("status") == "active":
                    self.wallets.append({
                        "address": addr,
                        "private_key": data["private_key"],
                        "funder_address": data.get("funder_address", addr)
                    })

        # Add default wallet if none loaded
        if not self.wallets:
            self.wallets.append({
                "address": os.environ.get("POLYMARKET_FUNDER_ADDRESS", ""),
                "private_key": os.environ.get(
                    "POLYMARKET_PRIVATE_KEY",
                    ""
                ),
                "funder_address": os.environ.get(
                    "POLYMARKET_FUNDER_ADDRESS",
                    "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
                )
            })

    def generate_price_ladder(
        self,
        center_price: float,
        spread_bps: int = 10,
        levels: int = 100,
        tick_size: float = 0.001
    ) -> List[float]:
        """
        Generate price ladder around center.

        For HFT, we want many price levels pre-signed.
        """
        prices = []
        spread = spread_bps / 10000

        # Generate prices on both sides
        for i in range(-levels, levels + 1):
            price = round(center_price + (i * spread), 4)
            if 0.001 <= price <= 0.999:
                prices.append(price)

        return sorted(set(prices))

    def presign_grid(
        self,
        token_id: str,
        center_price: float,
        spread_bps: int = 10,
        levels: int = 100,
        size_per_level: float = 10,
        wallet_idx: int = 0
    ) -> Dict:
        """
        Pre-sign a full grid of orders around center price.

        This is CPU-intensive - uses multiprocessing.
        """
        wallet = self.wallets[wallet_idx % len(self.wallets)]
        prices = self.generate_price_ladder(center_price, spread_bps, levels)

        # Generate order specs
        orders_to_sign = []
        for price in prices:
            # BUY orders below center
            if price < center_price:
                orders_to_sign.append({
                    "token_id": token_id,
                    "price": price,
                    "size": size_per_level,
                    "side": "BUY"
                })
            # SELL orders above center
            elif price > center_price:
                orders_to_sign.append({
                    "token_id": token_id,
                    "price": price,
                    "size": size_per_level,
                    "side": "SELL"
                })

        # Sign in batches using worker
        start_time = time.time()
        worker = OrderSigningWorker(wallet["private_key"], wallet["funder_address"])
        signed_orders = worker.sign_batch(orders_to_sign)
        elapsed = time.time() - start_time

        # Cache the signed orders
        cached = 0
        with self.cache_lock:
            for so in signed_orders:
                self.cache[so.token_id][so.price][so.side].append(so)
                cached += 1

        self.stats["orders_pre_signed"] += cached
        orders_per_sec = cached / elapsed if elapsed > 0 else 0

        return {
            "token_id": token_id,
            "center_price": center_price,
            "prices_covered": len(prices),
            "orders_pre_signed": cached,
            "elapsed_sec": elapsed,
            "orders_per_sec": orders_per_sec,
            "cache_size": sum(
                len(orders)
                for prices in self.cache.values()
                for sides in prices.values()
                for orders in sides.values()
            )
        }

    def presign_grid_parallel(
        self,
        token_id: str,
        center_price: float,
        spread_bps: int = 10,
        levels: int = 100,
        size_per_level: float = 10
    ) -> Dict:
        """
        Pre-sign grid using ALL wallets in parallel.

        Distributes signing work across wallets for maximum throughput.
        """
        if not self.wallets:
            return {"error": "No wallets available"}

        prices = self.generate_price_ladder(center_price, spread_bps, levels)

        # Distribute prices across wallets
        wallet_orders = [[] for _ in self.wallets]
        for i, price in enumerate(prices):
            wallet_idx = i % len(self.wallets)
            if price < center_price:
                wallet_orders[wallet_idx].append({
                    "token_id": token_id,
                    "price": price,
                    "size": size_per_level,
                    "side": "BUY"
                })
            elif price > center_price:
                wallet_orders[wallet_idx].append({
                    "token_id": token_id,
                    "price": price,
                    "size": size_per_level,
                    "side": "SELL"
                })

        start_time = time.time()
        total_signed = 0

        # Sign in parallel using thread pool (processes would require serialization)
        def sign_for_wallet(wallet_idx):
            wallet = self.wallets[wallet_idx]
            orders = wallet_orders[wallet_idx]
            if not orders:
                return 0

            worker = OrderSigningWorker(wallet["private_key"], wallet["funder_address"])
            signed = worker.sign_batch(orders)

            with self.cache_lock:
                for so in signed:
                    self.cache[so.token_id][so.price][so.side].append(so)

            return len(signed)

        with ThreadPoolExecutor(max_workers=len(self.wallets)) as executor:
            results = list(executor.map(sign_for_wallet, range(len(self.wallets))))
            total_signed = sum(results)

        elapsed = time.time() - start_time
        self.stats["orders_pre_signed"] += total_signed

        return {
            "token_id": token_id,
            "center_price": center_price,
            "wallets_used": len(self.wallets),
            "prices_covered": len(prices),
            "orders_pre_signed": total_signed,
            "elapsed_sec": elapsed,
            "orders_per_sec": total_signed / elapsed if elapsed > 0 else 0
        }

    def get_presigned(self, token_id: str, price: float, side: str) -> Optional[PreSignedOrder]:
        """
        Get a pre-signed order from cache.

        Returns None if not cached (cache miss).
        """
        with self.cache_lock:
            orders = self.cache.get(token_id, {}).get(price, {}).get(side, [])
            if orders:
                self.stats["cache_hits"] += 1
                # Return and remove from cache (one-time use)
                return orders.pop(0)

            self.stats["cache_misses"] += 1
            return None

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        with self.cache_lock:
            total_cached = sum(
                len(orders)
                for token in self.cache.values()
                for prices in token.values()
                for orders in prices.values()
            )

            tokens_cached = len(self.cache)
            prices_per_token = {
                token: len(prices)
                for token, prices in self.cache.items()
            }

        return {
            "total_cached": total_cached,
            "tokens_cached": tokens_cached,
            "prices_per_token": prices_per_token,
            "stats": self.stats.copy()
        }

    def clear_expired(self) -> int:
        """Clear expired pre-signed orders."""
        now = time.time()
        cleared = 0

        with self.cache_lock:
            for token_id in list(self.cache.keys()):
                for price in list(self.cache[token_id].keys()):
                    for side in list(self.cache[token_id][price].keys()):
                        orders = self.cache[token_id][price][side]
                        before = len(orders)
                        self.cache[token_id][price][side] = [
                            o for o in orders if o.expires_at > now
                        ]
                        cleared += before - len(self.cache[token_id][price][side])

        return cleared

    def run_demo(self):
        """Demo pre-signing capabilities."""
        print("=" * 70)
        print("HFT ORDER PRE-SIGNER")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[CONCEPT]")
        print("  Problem: Order signing is CPU-bound (cryptographic ops)")
        print("  Solution: Pre-sign orders at all price levels")
        print("  Result: Submission becomes just HTTP POST - instant")
        print()

        print("[WALLETS AVAILABLE]")
        print(f"  {len(self.wallets)} wallets loaded")
        for w in self.wallets[:3]:
            addr = w.get("address", w.get("funder_address", ""))[:20]
            print(f"    - {addr}...")
        print()

        print("[SIGNING BENCHMARK]")
        # Quick benchmark with small grid
        if self.wallets:
            # Use a test token ID
            test_token = "48331043336612883890938759509493159234755048973500640148014422747788308965732"

            print("  Testing single-wallet signing (10 orders)...")
            start = time.time()
            result = self.presign_grid(
                token_id=test_token,
                center_price=0.5,
                spread_bps=100,
                levels=5,
                size_per_level=10,
                wallet_idx=0
            )
            elapsed = time.time() - start
            print(f"    Signed: {result['orders_pre_signed']} orders")
            print(f"    Time: {elapsed*1000:.1f}ms")
            print(f"    Rate: {result['orders_per_sec']:.0f} orders/sec")
            print()

            if len(self.wallets) > 1:
                print(f"  Testing parallel signing ({len(self.wallets)} wallets)...")
                start = time.time()
                result = self.presign_grid_parallel(
                    token_id=test_token,
                    center_price=0.5,
                    spread_bps=100,
                    levels=5,
                    size_per_level=10
                )
                elapsed = time.time() - start
                print(f"    Signed: {result['orders_pre_signed']} orders")
                print(f"    Time: {elapsed*1000:.1f}ms")
                print(f"    Rate: {result['orders_per_sec']:.0f} orders/sec")
                print()

        print("[CACHE STATUS]")
        cache_stats = self.get_cache_stats()
        print(f"  Total cached: {cache_stats['total_cached']} orders")
        print(f"  Tokens cached: {cache_stats['tokens_cached']}")
        print(f"  Cache hits: {cache_stats['stats']['cache_hits']}")
        print(f"  Cache misses: {cache_stats['stats']['cache_misses']}")
        print()

        print("[SCALING TO 1M+ ORDERS/SEC]")
        print("  1. Pre-sign in advance during quiet periods")
        print("  2. Use multiple wallets (each wallet = more signing capacity)")
        print("  3. Distribute across processes (CPU parallelism)")
        print("  4. When price moves, submit from pre-signed cache")
        print("  5. Submission = just HTTP POST (no crypto work)")
        print()

        print("=" * 70)
        print("PRE-SIGNER READY")
        print("=" * 70)


def main():
    presigner = HFTOrderPresigner()
    presigner.run_demo()
    return presigner


if __name__ == "__main__":
    main()
