#!/usr/bin/env python3
"""
Rapid Order Manager - High-Speed Batch Order Operations
Exploits py-clob-client's batch capabilities for market making.

CAPABILITIES:
- post_orders: Place MANY orders in one call
- cancel_orders: Cancel MANY orders in one call
- get_order_books: Fetch multiple books simultaneously
- Async parallel execution for maximum throughput

This is the infrastructure for rapid limit order management.

Serving: Yair Siegel
"""

import os
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"

# Polymarket credentials
POLYMARKET_KEY = os.environ.get(
    "POLYMARKET_PRIVATE_KEY",
    "0x644444ab1d39e9074b01f085a27a4bbf5a8536f411b9b2bea04eb3934f038493"
)
POLYMARKET_FUNDER = os.environ.get(
    "POLYMARKET_FUNDER_ADDRESS",
    "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
)
POLYMARKET_HOST = "https://clob.polymarket.com"


@dataclass
class OrderSpec:
    """Specification for a single order."""
    token_id: str
    price: float
    size: float
    side: str  # "BUY" or "SELL"


@dataclass
class OrderGrid:
    """A grid of orders across price levels."""
    token_id: str
    center_price: float
    spread_bps: int  # Basis points between levels
    levels: int  # Number of levels on each side
    size_per_level: float
    side: str  # "BUY" or "SELL" or "BOTH"


class RapidOrderManager:
    """
    High-speed batch order management.

    Uses py-clob-client's batch APIs:
    - post_orders: Submit many orders at once
    - cancel_orders: Cancel many orders at once
    - Parallel execution for throughput
    """

    def __init__(self):
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._init_client()
        self.stats = {
            "orders_placed": 0,
            "orders_cancelled": 0,
            "batches_sent": 0,
            "avg_batch_time_ms": 0
        }

    def _init_client(self):
        """Initialize Polymarket client."""
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import OrderArgs
            from py_clob_client.order_builder.constants import BUY, SELL

            self.client = ClobClient(
                POLYMARKET_HOST,
                key=POLYMARKET_KEY,
                chain_id=137,
                funder=POLYMARKET_FUNDER
            )
            creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(creds)

            # Store constants
            self.BUY = BUY
            self.SELL = SELL
            self.OrderArgs = OrderArgs

        except Exception as e:
            print(f"Client init error: {e}")
            self.client = None

    def _side_const(self, side: str):
        """Convert string side to constant."""
        return self.BUY if side.upper() == "BUY" else self.SELL

    # ==================== BATCH ORDER PLACEMENT ====================

    def create_order_batch(self, specs: List[OrderSpec]) -> List:
        """
        Create signed orders for batch submission.
        """
        if not self.client:
            return []

        signed_orders = []
        for spec in specs:
            order_args = self.OrderArgs(
                token_id=spec.token_id,
                price=spec.price,
                size=spec.size,
                side=self._side_const(spec.side)
            )
            signed = self.client.create_order(order_args)
            signed_orders.append(signed)

        return signed_orders

    def place_orders_batch(self, specs: List[OrderSpec]) -> Dict:
        """
        Place multiple orders in a SINGLE API call.

        This is the key to rapid order management.
        """
        if not self.client:
            return {"success": False, "error": "No client"}

        start_time = time.time()

        try:
            # Create all signed orders
            signed_orders = self.create_order_batch(specs)

            if not signed_orders:
                return {"success": False, "error": "No orders created"}

            # BATCH POST - all orders in one call
            result = self.client.post_orders(signed_orders)

            elapsed_ms = (time.time() - start_time) * 1000

            self.stats["orders_placed"] += len(specs)
            self.stats["batches_sent"] += 1
            self.stats["avg_batch_time_ms"] = (
                (self.stats["avg_batch_time_ms"] * (self.stats["batches_sent"] - 1) + elapsed_ms)
                / self.stats["batches_sent"]
            )

            return {
                "success": True,
                "orders_placed": len(specs),
                "elapsed_ms": elapsed_ms,
                "result": result
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== BATCH ORDER CANCELLATION ====================

    def cancel_orders_batch(self, order_ids: List[str]) -> Dict:
        """
        Cancel multiple orders in a SINGLE API call.
        """
        if not self.client:
            return {"success": False, "error": "No client"}

        start_time = time.time()

        try:
            # BATCH CANCEL - all orders in one call
            result = self.client.cancel_orders(order_ids)

            elapsed_ms = (time.time() - start_time) * 1000

            self.stats["orders_cancelled"] += len(order_ids)

            return {
                "success": True,
                "orders_cancelled": len(order_ids),
                "elapsed_ms": elapsed_ms,
                "result": result
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_all_and_replace(self, new_specs: List[OrderSpec]) -> Dict:
        """
        Cancel all existing orders and place new ones.
        Classic market maker operation.
        """
        results = {
            "cancelled": None,
            "placed": None
        }

        # Get current orders
        current_orders = self.client.get_orders() or []
        order_ids = [o.get("id") for o in current_orders if o.get("id")]

        # Cancel all if any exist
        if order_ids:
            results["cancelled"] = self.cancel_orders_batch(order_ids)

        # Place new orders
        if new_specs:
            results["placed"] = self.place_orders_batch(new_specs)

        return results

    # ==================== ORDER GRID GENERATION ====================

    def generate_order_grid(self, grid: OrderGrid) -> List[OrderSpec]:
        """
        Generate a grid of orders around a center price.

        Example: center=0.50, spread_bps=100, levels=5
        BUY side:  0.49, 0.48, 0.47, 0.46, 0.45
        SELL side: 0.51, 0.52, 0.53, 0.54, 0.55
        """
        orders = []
        spread_decimal = grid.spread_bps / 10000

        if grid.side in ["BUY", "BOTH"]:
            for i in range(1, grid.levels + 1):
                price = round(grid.center_price - (i * spread_decimal), 4)
                if 0.001 <= price <= 0.999:
                    orders.append(OrderSpec(
                        token_id=grid.token_id,
                        price=price,
                        size=grid.size_per_level,
                        side="BUY"
                    ))

        if grid.side in ["SELL", "BOTH"]:
            for i in range(1, grid.levels + 1):
                price = round(grid.center_price + (i * spread_decimal), 4)
                if 0.001 <= price <= 0.999:
                    orders.append(OrderSpec(
                        token_id=grid.token_id,
                        price=price,
                        size=grid.size_per_level,
                        side="SELL"
                    ))

        return orders

    def place_order_grid(self, grid: OrderGrid) -> Dict:
        """
        Generate and place an order grid in one batch.
        """
        specs = self.generate_order_grid(grid)
        return self.place_orders_batch(specs)

    # ==================== MULTI-MARKET OPERATIONS ====================

    def fetch_multiple_books(self, token_ids: List[str]) -> Dict[str, Any]:
        """
        Fetch order books for multiple tokens at once.
        """
        if not self.client:
            return {}

        try:
            # BATCH fetch - multiple books in one call
            books = self.client.get_order_books(token_ids)
            return books
        except Exception as e:
            print(f"Error fetching books: {e}")
            return {}

    def fetch_multiple_spreads(self, token_ids: List[str]) -> Dict[str, float]:
        """
        Fetch spreads for multiple tokens at once.
        """
        if not self.client:
            return {}

        try:
            spreads = self.client.get_spreads(token_ids)
            return spreads
        except Exception as e:
            print(f"Error fetching spreads: {e}")
            return {}

    # ==================== PARALLEL EXECUTION ====================

    def parallel_place_grids(self, grids: List[OrderGrid]) -> List[Dict]:
        """
        Place multiple order grids in parallel.
        """
        results = []

        def place_single(grid):
            return self.place_order_grid(grid)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(place_single, g): g for g in grids}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})

        return results

    # ==================== MARKET MAKER LOOP ====================

    def run_market_maker_cycle(
        self,
        token_id: str,
        size_per_level: float = 10,
        levels: int = 5,
        spread_bps: int = 100
    ) -> Dict:
        """
        Run one market maker cycle:
        1. Get current midpoint
        2. Cancel all existing orders
        3. Place new grid around midpoint
        """
        if not self.client:
            return {"success": False, "error": "No client"}

        try:
            # Get current midpoint
            midpoint = self.client.get_midpoint(token_id)
            if not midpoint:
                return {"success": False, "error": "Could not get midpoint"}

            mid_price = float(midpoint)

            # Generate grid
            grid = OrderGrid(
                token_id=token_id,
                center_price=mid_price,
                spread_bps=spread_bps,
                levels=levels,
                size_per_level=size_per_level,
                side="BOTH"
            )

            # Cancel and replace
            result = self.cancel_all_and_replace(self.generate_order_grid(grid))
            result["midpoint"] = mid_price
            result["grid"] = {
                "levels": levels,
                "spread_bps": spread_bps,
                "size_per_level": size_per_level
            }

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict:
        """Get operation statistics."""
        return self.stats

    def run_demo(self):
        """Demo the rapid order capabilities."""
        print("=" * 70)
        print("RAPID ORDER MANAGER - Batch Operations Demo")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[CAPABILITIES]")
        print("  post_orders()   - Place MANY orders in ONE call")
        print("  cancel_orders() - Cancel MANY orders in ONE call")
        print("  get_order_books() - Fetch multiple books at once")
        print("  get_spreads()   - Fetch multiple spreads at once")
        print()

        print("[CURRENT ORDERS]")
        if self.client:
            orders = self.client.get_orders() or []
            print(f"  Open orders: {len(orders)}")
            for order in orders[:5]:
                side = order.get("side", "?")
                price = order.get("price", 0)
                size = order.get("original_size", order.get("size", 0))
                print(f"    {side} {size} @ {price}")
        print()

        print("[BATCH EXAMPLE]")
        print("  # Place 10 orders in ONE call:")
        print("  specs = [OrderSpec(token, 0.45, 10, 'BUY') for _ in range(10)]")
        print("  manager.place_orders_batch(specs)")
        print()

        print("[GRID EXAMPLE]")
        print("  # Create market making grid:")
        print("  grid = OrderGrid(token, center=0.50, spread_bps=100, levels=5, size=10, side='BOTH')")
        print("  # Places: BUY @ 0.49,0.48,0.47,0.46,0.45")
        print("  #         SELL @ 0.51,0.52,0.53,0.54,0.55")
        print("  manager.place_order_grid(grid)")
        print()

        print("[STATS]")
        print(f"  Orders placed: {self.stats['orders_placed']}")
        print(f"  Orders cancelled: {self.stats['orders_cancelled']}")
        print(f"  Batches sent: {self.stats['batches_sent']}")
        print(f"  Avg batch time: {self.stats['avg_batch_time_ms']:.1f}ms")
        print()

        print("=" * 70)
        print("READY FOR RAPID ORDER MANAGEMENT")
        print("=" * 70)


def main():
    manager = RapidOrderManager()
    manager.run_demo()
    return manager


if __name__ == "__main__":
    main()
