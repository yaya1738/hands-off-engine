#!/usr/bin/env python3
"""
Fleet Commander - Multi-Process Polymarket Orchestration
The master coordinator for running multiple parallel trading processes.

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────────┐
│                       FLEET COMMANDER                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │ Process 1│  │ Process 2│  │ Process 3│  │  ...Process N        │ │
│  │ Wallet A │  │ Wallet B │  │ Wallet C │  │  Wallet N            │ │
│  │ Orders   │  │ Orders   │  │ Orders   │  │  Orders              │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘ │
│                          ↑                                          │
│                    Shared State                                     │
│              ┌─────────────────────┐                                │
│              │  Market Analysis    │                                │
│              │  Order Book Data    │                                │
│              │  Position Tracker   │                                │
│              └─────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘

Serving: Yair Siegel
"""

import os
import sys
import json
import signal
import multiprocessing as mp
from multiprocessing import Process, Queue, Manager, Event
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
FLEET_STATE = STATE_DIR / "fleet_state.json"

MASTER = "Yair Siegel"


@dataclass
class ProcessStatus:
    """Status of a worker process."""
    process_id: int
    wallet_address: str
    alias: str
    status: str  # running, stopped, error
    started_at: str
    last_heartbeat: str
    orders_placed: int = 0
    orders_cancelled: int = 0
    errors: int = 0


@dataclass
class FleetCommand:
    """Command to send to fleet."""
    command: str  # start, stop, execute, status
    target: str  # "all" or wallet address
    params: Dict
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


def worker_process(
    wallet_address: str,
    private_key: str,
    funder_address: str,
    command_queue: mp.Queue,
    result_queue: mp.Queue,
    shutdown_event: mp.Event,
    alias: str = None
):
    """
    Worker process for a single wallet.
    Runs independently, receives commands via queue.
    """
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import OrderArgs
    from py_clob_client.order_builder.constants import BUY, SELL

    # Initialize client
    client = None
    try:
        client = ClobClient(
            "https://clob.polymarket.com",
            key=private_key,
            chain_id=137,
            funder=funder_address
        )
        creds = client.create_or_derive_api_creds()
        client.set_api_creds(creds)
    except Exception as e:
        result_queue.put({
            "type": "error",
            "wallet": wallet_address,
            "message": f"Client init failed: {e}"
        })
        return

    # Notify ready
    result_queue.put({
        "type": "ready",
        "wallet": wallet_address,
        "alias": alias,
        "pid": os.getpid()
    })

    stats = {"orders_placed": 0, "orders_cancelled": 0, "errors": 0}

    # Main loop
    while not shutdown_event.is_set():
        try:
            # Check for commands (non-blocking with timeout)
            try:
                cmd = command_queue.get(timeout=0.5)
            except queue.Empty:
                # Heartbeat
                result_queue.put({
                    "type": "heartbeat",
                    "wallet": wallet_address,
                    "stats": stats,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                continue

            # Process command
            action = cmd.get("action")
            params = cmd.get("params", {})

            result = {
                "type": "result",
                "wallet": wallet_address,
                "action": action,
                "success": False,
                "data": None
            }

            try:
                if action == "place_order":
                    side = BUY if params["side"].upper() == "BUY" else SELL
                    order_args = OrderArgs(
                        token_id=params["token_id"],
                        price=params["price"],
                        size=params["size"],
                        side=side
                    )
                    signed = client.create_order(order_args)
                    resp = client.post_order(signed)
                    result["success"] = True
                    result["data"] = resp
                    stats["orders_placed"] += 1

                elif action == "place_batch":
                    orders = params.get("orders", [])
                    signed_orders = []
                    for o in orders:
                        side = BUY if o["side"].upper() == "BUY" else SELL
                        order_args = OrderArgs(
                            token_id=o["token_id"],
                            price=o["price"],
                            size=o["size"],
                            side=side
                        )
                        signed_orders.append(client.create_order(order_args))
                    resp = client.post_orders(signed_orders)
                    result["success"] = True
                    result["data"] = resp
                    stats["orders_placed"] += len(orders)

                elif action == "cancel_all":
                    resp = client.cancel_all()
                    result["success"] = True
                    result["data"] = resp

                elif action == "get_orders":
                    orders = client.get_orders() or []
                    result["success"] = True
                    result["data"] = orders

                elif action == "market_maker_cycle":
                    # Cancel all
                    client.cancel_all()

                    # Get midpoint
                    token_id = params["token_id"]
                    try:
                        midpoint = float(client.get_midpoint(token_id))
                    except:
                        midpoint = params.get("default_midpoint", 0.5)

                    # Place grid
                    spread_bps = params.get("spread_bps", 100)
                    levels = params.get("levels", 5)
                    size = params.get("size_per_level", 10)
                    spread = spread_bps / 10000

                    orders = []
                    for i in range(1, levels + 1):
                        # Buy side
                        buy_price = round(midpoint - (i * spread), 4)
                        if 0.001 <= buy_price <= 0.999:
                            orders.append({
                                "token_id": token_id,
                                "price": buy_price,
                                "size": size,
                                "side": "BUY"
                            })
                        # Sell side
                        sell_price = round(midpoint + (i * spread), 4)
                        if 0.001 <= sell_price <= 0.999:
                            orders.append({
                                "token_id": token_id,
                                "price": sell_price,
                                "size": size,
                                "side": "SELL"
                            })

                    if orders:
                        signed_orders = []
                        for o in orders:
                            side = BUY if o["side"] == "BUY" else SELL
                            order_args = OrderArgs(
                                token_id=o["token_id"],
                                price=o["price"],
                                size=o["size"],
                                side=side
                            )
                            signed_orders.append(client.create_order(order_args))
                        client.post_orders(signed_orders)
                        stats["orders_placed"] += len(orders)

                    result["success"] = True
                    result["data"] = {
                        "midpoint": midpoint,
                        "orders_placed": len(orders)
                    }

                elif action == "stop":
                    result["success"] = True
                    result["data"] = "Stopping"
                    result_queue.put(result)
                    break

            except Exception as e:
                result["data"] = {"error": str(e)}
                stats["errors"] += 1

            result_queue.put(result)

        except Exception as e:
            result_queue.put({
                "type": "error",
                "wallet": wallet_address,
                "message": str(e)
            })
            stats["errors"] += 1

    # Final status
    result_queue.put({
        "type": "shutdown",
        "wallet": wallet_address,
        "stats": stats
    })


class FleetCommander:
    """
    Master coordinator for multi-process Polymarket trading.

    Manages fleet of worker processes, each handling one wallet.
    """

    def __init__(self):
        self.manager = Manager()
        self.processes: Dict[str, Process] = {}
        self.command_queues: Dict[str, mp.Queue] = {}
        self.result_queue = mp.Queue()
        self.shutdown_events: Dict[str, mp.Event] = {}
        self.wallets: Dict[str, Dict] = {}
        self.process_status: Dict[str, ProcessStatus] = {}
        self.running = False
        self._result_thread = None
        self._load_wallets()

    def _load_wallets(self):
        """Load wallets from registry."""
        registry_path = STATE_DIR / "wallets" / "registry.json"
        if registry_path.exists():
            with open(registry_path) as f:
                registry = json.load(f)
            self.wallets = registry.get("wallets", {})

    def _save_fleet_state(self):
        """Save fleet state to file."""
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processes": {
                addr: asdict(status)
                for addr, status in self.process_status.items()
            },
            "total_wallets": len(self.wallets),
            "active_processes": len(self.processes)
        }
        with open(FLEET_STATE, 'w') as f:
            json.dump(state, f, indent=2)

    def _result_handler(self):
        """Thread to handle results from all workers."""
        while self.running:
            try:
                result = self.result_queue.get(timeout=1)
                self._process_result(result)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Result handler error: {e}")

    def _process_result(self, result: Dict):
        """Process result from worker."""
        msg_type = result.get("type")
        wallet = result.get("wallet", "")

        if msg_type == "ready":
            print(f"  Worker ready: {result.get('alias', wallet[:10])} (PID: {result.get('pid')})")
            if wallet in self.process_status:
                self.process_status[wallet].status = "running"

        elif msg_type == "heartbeat":
            if wallet in self.process_status:
                self.process_status[wallet].last_heartbeat = result.get("timestamp")
                stats = result.get("stats", {})
                self.process_status[wallet].orders_placed = stats.get("orders_placed", 0)
                self.process_status[wallet].orders_cancelled = stats.get("orders_cancelled", 0)
                self.process_status[wallet].errors = stats.get("errors", 0)

        elif msg_type == "result":
            action = result.get("action")
            success = result.get("success")
            alias = self.wallets.get(wallet, {}).get("alias", wallet[:10])
            if success:
                print(f"  [{alias}] {action}: OK")
            else:
                print(f"  [{alias}] {action}: FAILED - {result.get('data')}")

        elif msg_type == "shutdown":
            if wallet in self.process_status:
                self.process_status[wallet].status = "stopped"
            print(f"  Worker stopped: {wallet[:10]}...")

        elif msg_type == "error":
            print(f"  Error from {wallet[:10]}...: {result.get('message')}")

    # ==================== PROCESS MANAGEMENT ====================

    def start_worker(self, wallet_address: str) -> bool:
        """Start worker process for wallet."""
        if wallet_address in self.processes:
            print(f"  Worker already running: {wallet_address[:10]}...")
            return False

        wallet = self.wallets.get(wallet_address)
        if not wallet:
            print(f"  Wallet not found: {wallet_address[:10]}...")
            return False

        # Create queues and events
        cmd_queue = mp.Queue()
        shutdown_event = mp.Event()

        # Start process
        p = Process(
            target=worker_process,
            args=(
                wallet_address,
                wallet["private_key"],
                wallet.get("funder_address", wallet_address),
                cmd_queue,
                self.result_queue,
                shutdown_event,
                wallet.get("alias")
            )
        )
        p.start()

        # Store references
        self.processes[wallet_address] = p
        self.command_queues[wallet_address] = cmd_queue
        self.shutdown_events[wallet_address] = shutdown_event

        # Track status
        self.process_status[wallet_address] = ProcessStatus(
            process_id=p.pid,
            wallet_address=wallet_address,
            alias=wallet.get("alias", wallet_address[:10]),
            status="starting",
            started_at=datetime.now(timezone.utc).isoformat(),
            last_heartbeat=datetime.now(timezone.utc).isoformat()
        )

        return True

    def stop_worker(self, wallet_address: str, force: bool = False) -> bool:
        """Stop worker process for wallet."""
        if wallet_address not in self.processes:
            return False

        # Signal shutdown
        self.shutdown_events[wallet_address].set()

        # Send stop command
        try:
            self.command_queues[wallet_address].put({"action": "stop", "params": {}})
        except:
            pass

        # Wait for graceful shutdown
        p = self.processes[wallet_address]
        p.join(timeout=5)

        # Force kill if needed
        if p.is_alive() and force:
            p.terminate()
            p.join(timeout=2)

        # Cleanup
        del self.processes[wallet_address]
        del self.command_queues[wallet_address]
        del self.shutdown_events[wallet_address]

        return True

    def start_fleet(self) -> Dict:
        """Start worker processes for all active wallets."""
        self.running = True

        # Start result handler thread
        self._result_thread = threading.Thread(target=self._result_handler, daemon=True)
        self._result_thread.start()

        results = {"started": [], "failed": []}

        for addr, data in self.wallets.items():
            if data.get("status") == "active":
                if self.start_worker(addr):
                    results["started"].append(addr)
                else:
                    results["failed"].append(addr)

        # Give workers time to initialize
        time.sleep(2)

        self._save_fleet_state()
        return results

    def stop_fleet(self, force: bool = False):
        """Stop all worker processes."""
        print("Stopping fleet...")

        for addr in list(self.processes.keys()):
            self.stop_worker(addr, force)

        self.running = False
        self._save_fleet_state()
        print("Fleet stopped.")

    # ==================== COMMAND DISTRIBUTION ====================

    def send_command(self, wallet_address: str, action: str, params: Dict) -> bool:
        """Send command to specific wallet worker."""
        if wallet_address not in self.command_queues:
            return False

        self.command_queues[wallet_address].put({
            "action": action,
            "params": params
        })
        return True

    def send_to_all(self, action: str, params: Dict) -> int:
        """Send command to all workers."""
        sent = 0
        for addr in self.command_queues:
            if self.send_command(addr, action, params):
                sent += 1
        return sent

    def execute_parallel(self, action: str, params: Dict) -> None:
        """Execute action on all wallets and wait briefly for results."""
        sent = self.send_to_all(action, params)
        print(f"  Command '{action}' sent to {sent} workers")
        time.sleep(1)  # Brief wait for initial responses

    # ==================== HIGH-LEVEL OPERATIONS ====================

    def fleet_cancel_all(self):
        """Cancel all orders on all wallets."""
        return self.execute_parallel("cancel_all", {})

    def fleet_get_orders(self):
        """Get orders from all wallets."""
        return self.execute_parallel("get_orders", {})

    def fleet_market_maker(self, token_id: str, spread_bps: int = 100, levels: int = 5, size: float = 10):
        """Run market maker cycle on all wallets."""
        params = {
            "token_id": token_id,
            "spread_bps": spread_bps,
            "levels": levels,
            "size_per_level": size
        }
        return self.execute_parallel("market_maker_cycle", params)

    def fleet_place_batch(self, orders: List[Dict]):
        """Place batch of orders across all wallets."""
        return self.execute_parallel("place_batch", {"orders": orders})

    def get_fleet_status(self) -> Dict:
        """Get status of all workers."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "running": self.running,
            "total_wallets": len(self.wallets),
            "active_workers": len(self.processes),
            "workers": {
                addr: asdict(status)
                for addr, status in self.process_status.items()
            }
        }

    # ==================== DEMO ====================

    def run_demo(self):
        """Demo fleet command operations."""
        print("=" * 70)
        print("FLEET COMMANDER - Multi-Process Polymarket Orchestration")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[ARCHITECTURE]")
        print("  Fleet Commander → Command Queues → Worker Processes")
        print("  Each worker = 1 wallet, 1 process, independent execution")
        print("  Shared result queue for coordination")
        print()

        print("[REGISTERED WALLETS]")
        active_count = 0
        for addr, data in self.wallets.items():
            alias = data.get("alias", addr[:10])
            status = data.get("status", "unknown")
            if status == "active":
                active_count += 1
            print(f"  {alias}: {addr[:20]}... [{status}]")
        print(f"  Total: {len(self.wallets)} wallets ({active_count} active)")
        print()

        if not self.wallets:
            print("[NO WALLETS] Run multi_wallet_manager.py first")
            return

        print("[CAPABILITIES]")
        print("  start_fleet()        - Launch all worker processes")
        print("  stop_fleet()         - Stop all workers")
        print("  fleet_cancel_all()   - Cancel orders on all wallets")
        print("  fleet_market_maker() - MM cycle on all wallets")
        print("  fleet_place_batch()  - Place orders on all wallets")
        print("  send_to_all()        - Send any command to all")
        print()

        print("[PROCESS STATUS]")
        for addr, status in self.process_status.items():
            print(f"  {status.alias}: PID {status.process_id} [{status.status}]")
            print(f"    Orders: {status.orders_placed} placed, {status.orders_cancelled} cancelled")
            print(f"    Errors: {status.errors}")
        if not self.process_status:
            print("  No processes running. Use start_fleet() to launch.")
        print()

        print("=" * 70)
        print("FLEET COMMANDER READY")
        print("=" * 70)


def main():
    commander = FleetCommander()
    commander.run_demo()
    return commander


if __name__ == "__main__":
    main()
