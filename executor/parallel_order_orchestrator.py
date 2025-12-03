#!/usr/bin/env python3
"""
Parallel Order Orchestrator - Multi-Wallet Order Management
Run order operations across multiple wallets simultaneously.

ARCHITECTURE:
- Each wallet runs as independent process/thread
- Central coordinator distributes orders
- Shared order book analysis
- Coordinated position management

Serving: Yair Siegel
"""

import os
import json
import multiprocessing as mp
from multiprocessing import Process, Queue, Manager
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import threading
import time
import queue

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
POLYMARKET_HOST = "https://clob.polymarket.com"


@dataclass
class OrderTask:
    """Order task for distribution to wallets."""
    task_id: str
    wallet_address: str
    action: str  # place, cancel, cancel_all, grid
    params: Dict
    priority: int = 1  # 1=highest
    created_at: str = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class OrderResult:
    """Result from order execution."""
    task_id: str
    wallet_address: str
    success: bool
    result: Any
    elapsed_ms: float
    completed_at: str = None

    def __post_init__(self):
        if not self.completed_at:
            self.completed_at = datetime.now(timezone.utc).isoformat()


class WalletWorker:
    """
    Worker process for a single wallet.
    Handles all orders for one Polymarket account.
    """

    def __init__(self, wallet_address: str, private_key: str, funder_address: str):
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.funder_address = funder_address
        self.client = None
        self.stats = {
            "orders_placed": 0,
            "orders_cancelled": 0,
            "errors": 0
        }

    def init_client(self) -> bool:
        """Initialize Polymarket client."""
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import OrderArgs
            from py_clob_client.order_builder.constants import BUY, SELL

            self.client = ClobClient(
                POLYMARKET_HOST,
                key=self.private_key,
                chain_id=137,
                funder=self.funder_address
            )
            creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(creds)

            self.OrderArgs = OrderArgs
            self.BUY = BUY
            self.SELL = SELL

            return True
        except Exception as e:
            print(f"Worker init error for {self.wallet_address[:10]}...: {e}")
            return False

    def process_task(self, task: OrderTask) -> OrderResult:
        """Process a single order task."""
        start_time = time.time()
        result = None
        success = False

        try:
            if not self.client:
                if not self.init_client():
                    raise Exception("Client initialization failed")

            if task.action == "place":
                result = self._place_order(task.params)
                self.stats["orders_placed"] += 1
                success = True

            elif task.action == "place_batch":
                result = self._place_batch(task.params)
                self.stats["orders_placed"] += len(task.params.get("orders", []))
                success = True

            elif task.action == "cancel":
                result = self._cancel_order(task.params)
                self.stats["orders_cancelled"] += 1
                success = True

            elif task.action == "cancel_batch":
                result = self._cancel_batch(task.params)
                self.stats["orders_cancelled"] += len(task.params.get("order_ids", []))
                success = True

            elif task.action == "cancel_all":
                result = self._cancel_all()
                success = True

            elif task.action == "grid":
                result = self._place_grid(task.params)
                success = True

            elif task.action == "get_orders":
                result = self._get_orders()
                success = True

            elif task.action == "market_maker_cycle":
                result = self._market_maker_cycle(task.params)
                success = True

            else:
                raise ValueError(f"Unknown action: {task.action}")

        except Exception as e:
            result = {"error": str(e)}
            self.stats["errors"] += 1
            success = False

        elapsed = (time.time() - start_time) * 1000

        return OrderResult(
            task_id=task.task_id,
            wallet_address=self.wallet_address,
            success=success,
            result=result,
            elapsed_ms=elapsed
        )

    def _place_order(self, params: Dict) -> Dict:
        """Place single order."""
        side = self.BUY if params["side"].upper() == "BUY" else self.SELL
        order_args = self.OrderArgs(
            token_id=params["token_id"],
            price=params["price"],
            size=params["size"],
            side=side
        )
        signed = self.client.create_order(order_args)
        return self.client.post_order(signed)

    def _place_batch(self, params: Dict) -> Dict:
        """Place batch of orders."""
        orders = params.get("orders", [])
        signed_orders = []

        for o in orders:
            side = self.BUY if o["side"].upper() == "BUY" else self.SELL
            order_args = self.OrderArgs(
                token_id=o["token_id"],
                price=o["price"],
                size=o["size"],
                side=side
            )
            signed_orders.append(self.client.create_order(order_args))

        return self.client.post_orders(signed_orders)

    def _cancel_order(self, params: Dict) -> Dict:
        """Cancel single order."""
        return self.client.cancel(params["order_id"])

    def _cancel_batch(self, params: Dict) -> Dict:
        """Cancel batch of orders."""
        return self.client.cancel_orders(params["order_ids"])

    def _cancel_all(self) -> Dict:
        """Cancel all orders."""
        return self.client.cancel_all()

    def _get_orders(self) -> List:
        """Get all open orders."""
        return self.client.get_orders() or []

    def _place_grid(self, params: Dict) -> Dict:
        """Place order grid around center price."""
        token_id = params["token_id"]
        center_price = params["center_price"]
        spread_bps = params.get("spread_bps", 100)
        levels = params.get("levels", 5)
        size_per_level = params.get("size_per_level", 10)
        side = params.get("side", "BOTH")

        orders = []
        spread_decimal = spread_bps / 10000

        if side in ["BUY", "BOTH"]:
            for i in range(1, levels + 1):
                price = round(center_price - (i * spread_decimal), 4)
                if 0.001 <= price <= 0.999:
                    orders.append({
                        "token_id": token_id,
                        "price": price,
                        "size": size_per_level,
                        "side": "BUY"
                    })

        if side in ["SELL", "BOTH"]:
            for i in range(1, levels + 1):
                price = round(center_price + (i * spread_decimal), 4)
                if 0.001 <= price <= 0.999:
                    orders.append({
                        "token_id": token_id,
                        "price": price,
                        "size": size_per_level,
                        "side": "SELL"
                    })

        if orders:
            return self._place_batch({"orders": orders})
        return {"orders_placed": 0}

    def _market_maker_cycle(self, params: Dict) -> Dict:
        """Cancel all and replace with new grid."""
        # Cancel existing
        cancel_result = self._cancel_all()

        # Get midpoint
        token_id = params["token_id"]
        try:
            midpoint = float(self.client.get_midpoint(token_id))
        except:
            midpoint = params.get("default_midpoint", 0.5)

        # Place new grid
        grid_params = {
            "token_id": token_id,
            "center_price": midpoint,
            "spread_bps": params.get("spread_bps", 100),
            "levels": params.get("levels", 5),
            "size_per_level": params.get("size_per_level", 10),
            "side": params.get("side", "BOTH")
        }
        grid_result = self._place_grid(grid_params)

        return {
            "cancelled": cancel_result,
            "grid": grid_result,
            "midpoint": midpoint
        }


class ParallelOrderOrchestrator:
    """
    Coordinate order operations across multiple wallets.

    Distributes tasks, collects results, manages parallelism.
    """

    def __init__(self):
        self.wallets: Dict[str, Dict] = {}
        self.workers: Dict[str, WalletWorker] = {}
        self.task_queue = queue.PriorityQueue()
        self.results: List[OrderResult] = []
        self.lock = threading.Lock()
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_elapsed_ms": 0
        }

    def register_wallet(self, address: str, private_key: str, funder_address: str, alias: str = None):
        """Register a wallet for orchestration."""
        self.wallets[address] = {
            "private_key": private_key,
            "funder_address": funder_address,
            "alias": alias or address[:10]
        }
        self.workers[address] = WalletWorker(address, private_key, funder_address)

    def load_wallets_from_registry(self):
        """Load wallets from multi_wallet_manager registry."""
        registry_path = STATE_DIR / "wallets" / "registry.json"
        if not registry_path.exists():
            return

        with open(registry_path) as f:
            registry = json.load(f)

        for address, data in registry.get("wallets", {}).items():
            if data.get("status") == "active":
                self.register_wallet(
                    address,
                    data["private_key"],
                    data["funder_address"],
                    data.get("alias")
                )

    def submit_task(self, task: OrderTask):
        """Submit task to queue."""
        self.task_queue.put((task.priority, task))
        self.stats["total_tasks"] += 1

    def submit_to_wallet(self, wallet_address: str, action: str, params: Dict, priority: int = 1) -> str:
        """Submit task to specific wallet."""
        task_id = f"{wallet_address[:8]}_{action}_{int(time.time()*1000)}"
        task = OrderTask(
            task_id=task_id,
            wallet_address=wallet_address,
            action=action,
            params=params,
            priority=priority
        )
        self.submit_task(task)
        return task_id

    def submit_to_all_wallets(self, action: str, params: Dict, priority: int = 1) -> List[str]:
        """Submit same task to all wallets."""
        task_ids = []
        for address in self.wallets:
            task_id = self.submit_to_wallet(address, action, params, priority)
            task_ids.append(task_id)
        return task_ids

    def execute_task(self, task: OrderTask) -> OrderResult:
        """Execute single task."""
        worker = self.workers.get(task.wallet_address)
        if not worker:
            return OrderResult(
                task_id=task.task_id,
                wallet_address=task.wallet_address,
                success=False,
                result={"error": "Worker not found"},
                elapsed_ms=0
            )
        return worker.process_task(task)

    def execute_all_pending(self, max_parallel: int = 10) -> List[OrderResult]:
        """Execute all pending tasks in parallel."""
        results = []
        tasks = []

        # Drain queue
        while not self.task_queue.empty():
            try:
                priority, task = self.task_queue.get_nowait()
                tasks.append(task)
            except queue.Empty:
                break

        if not tasks:
            return results

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            futures = {executor.submit(self.execute_task, t): t for t in tasks}
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                with self.lock:
                    self.results.append(result)
                    if result.success:
                        self.stats["completed_tasks"] += 1
                    else:
                        self.stats["failed_tasks"] += 1
                    self.stats["total_elapsed_ms"] += result.elapsed_ms

        return results

    def execute_immediate(self, wallet_address: str, action: str, params: Dict) -> OrderResult:
        """Execute task immediately, bypassing queue."""
        task = OrderTask(
            task_id=f"immediate_{int(time.time()*1000)}",
            wallet_address=wallet_address,
            action=action,
            params=params,
            priority=0
        )
        return self.execute_task(task)

    def execute_on_all_immediate(self, action: str, params: Dict, max_parallel: int = 10) -> List[OrderResult]:
        """Execute action on all wallets immediately in parallel."""
        results = []

        def run_on_wallet(address):
            return self.execute_immediate(address, action, params)

        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            futures = {executor.submit(run_on_wallet, addr): addr for addr in self.wallets}
            for future in as_completed(futures):
                results.append(future.result())

        return results

    # ==================== HIGH-LEVEL OPERATIONS ====================

    def place_grid_all_wallets(
        self,
        token_id: str,
        center_price: float,
        spread_bps: int = 100,
        levels: int = 5,
        size_per_level: float = 10,
        side: str = "BOTH"
    ) -> List[OrderResult]:
        """Place order grid on all wallets simultaneously."""
        params = {
            "token_id": token_id,
            "center_price": center_price,
            "spread_bps": spread_bps,
            "levels": levels,
            "size_per_level": size_per_level,
            "side": side
        }
        return self.execute_on_all_immediate("grid", params)

    def cancel_all_all_wallets(self) -> List[OrderResult]:
        """Cancel all orders on all wallets."""
        return self.execute_on_all_immediate("cancel_all", {})

    def market_maker_cycle_all(
        self,
        token_id: str,
        spread_bps: int = 100,
        levels: int = 5,
        size_per_level: float = 10
    ) -> List[OrderResult]:
        """Run market maker cycle on all wallets."""
        params = {
            "token_id": token_id,
            "spread_bps": spread_bps,
            "levels": levels,
            "size_per_level": size_per_level,
            "side": "BOTH"
        }
        return self.execute_on_all_immediate("market_maker_cycle", params)

    def get_all_orders(self) -> Dict[str, List]:
        """Get orders from all wallets."""
        results = self.execute_on_all_immediate("get_orders", {})
        orders_by_wallet = {}
        for r in results:
            if r.success:
                orders_by_wallet[r.wallet_address] = r.result
            else:
                orders_by_wallet[r.wallet_address] = {"error": r.result}
        return orders_by_wallet

    def get_fleet_stats(self) -> Dict:
        """Get stats for entire wallet fleet."""
        all_orders = self.get_all_orders()

        total_orders = 0
        total_working_capital = 0

        for addr, orders in all_orders.items():
            if isinstance(orders, list):
                total_orders += len(orders)
                for o in orders:
                    price = float(o.get("price", 0))
                    size = float(o.get("original_size", o.get("size", 0)))
                    total_working_capital += price * size

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wallets_active": len(self.wallets),
            "total_open_orders": total_orders,
            "total_working_capital": total_working_capital,
            "orchestrator_stats": self.stats,
            "worker_stats": {
                addr: self.workers[addr].stats
                for addr in self.workers
            }
        }

    def run_demo(self):
        """Demo parallel orchestration."""
        print("=" * 70)
        print("PARALLEL ORDER ORCHESTRATOR - Multi-Wallet Operations")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        # Load wallets
        self.load_wallets_from_registry()

        print("[REGISTERED WALLETS]")
        for addr, data in self.wallets.items():
            print(f"  {data['alias']}: {addr[:15]}...")
        print(f"  Total: {len(self.wallets)} wallets")
        print()

        if not self.wallets:
            print("[NO WALLETS] Run multi_wallet_manager.py first to create wallets")
            return

        print("[CAPABILITIES]")
        print("  place_grid_all_wallets()     - Grid on all wallets")
        print("  cancel_all_all_wallets()     - Cancel all on all wallets")
        print("  market_maker_cycle_all()     - MM cycle on all wallets")
        print("  execute_on_all_immediate()   - Any action on all wallets")
        print()

        # Get fleet stats
        print("[FLEET STATUS]")
        stats = self.get_fleet_stats()
        print(f"  Active wallets: {stats['wallets_active']}")
        print(f"  Total open orders: {stats['total_open_orders']}")
        print(f"  Working capital: ${stats['total_working_capital']:.2f}")
        print()

        print("=" * 70)
        print("PARALLEL ORCHESTRATION READY")
        print("=" * 70)


def main():
    orchestrator = ParallelOrderOrchestrator()
    orchestrator.run_demo()
    return orchestrator


if __name__ == "__main__":
    main()
