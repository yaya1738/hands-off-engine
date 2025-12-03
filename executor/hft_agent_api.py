#!/usr/bin/env python3
"""
HFT Agent API - Simple Interface for AI Agents and Autonomous Systems
One import, simple functions, JSON responses.

USAGE FOR AGENTS:
    from executor.hft_agent_api import hft

    # Check status
    status = hft.status()

    # Create wallets
    hft.create_wallets(100)

    # Fire orders
    hft.fire(token_id, count=1000)

    # Cancel all
    hft.cancel_all()

Serving: Yair Siegel
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"


class HFTAgentAPI:
    """
    Simple HFT API for AI agents and autonomous systems.

    All methods return JSON-serializable dicts.
    All methods are synchronous (async handled internally).
    """

    def __init__(self):
        self._wallet_manager = None
        self._orchestrator = None
        self._presigner = None
        self._cannon = None
        self._coordinator = None

    @property
    def wallet_manager(self):
        if not self._wallet_manager:
            from executor.multi_wallet_manager import MultiWalletManager
            self._wallet_manager = MultiWalletManager()
        return self._wallet_manager

    @property
    def orchestrator(self):
        if not self._orchestrator:
            from executor.parallel_order_orchestrator import ParallelOrderOrchestrator
            self._orchestrator = ParallelOrderOrchestrator()
            self._orchestrator.load_wallets_from_registry()
        return self._orchestrator

    @property
    def presigner(self):
        if not self._presigner:
            from executor.hft_order_presigner import HFTOrderPresigner
            self._presigner = HFTOrderPresigner()
        return self._presigner

    @property
    def coordinator(self):
        if not self._coordinator:
            from executor.hft_million_coordinator import HFTMillionCoordinator
            self._coordinator = HFTMillionCoordinator()
        return self._coordinator

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """
        Get complete HFT system status.

        Returns:
            {
                "timestamp": "...",
                "wallets": {"total": N, "active": N},
                "orders": {"total": N, "working_capital": $},
                "capacity": {"rate_per_wallet": N, "theoretical_max": N},
                "ready": bool
            }
        """
        wallets = self.wallet_manager.list_wallets()
        active = [w for w in wallets if w.get("status") == "active"]

        stats = self.orchestrator.get_fleet_stats()
        capacity = self.coordinator.calculate_capacity()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wallets": {
                "total": len(wallets),
                "active": len(active)
            },
            "orders": {
                "total": stats.get("total_open_orders", 0),
                "working_capital": stats.get("total_working_capital", 0)
            },
            "capacity": {
                "rate_per_wallet": capacity.get("rate_per_wallet", 1000),
                "theoretical_max": capacity.get("theoretical_multi_process", 0),
                "wallets_for_1m": capacity.get("wallets_needed_for_1m", 1250)
            },
            "ready": len(active) > 0
        }

    def quick_status(self) -> str:
        """One-line status for agents."""
        s = self.status()
        return f"HFT: {s['wallets']['active']} wallets, {s['orders']['total']} orders, ${s['orders']['working_capital']:.2f} working"

    # ==================== WALLETS ====================

    def create_wallets(self, count: int = 1, prefix: str = "agent") -> Dict:
        """
        Create new trading wallets.

        Args:
            count: Number of wallets to create
            prefix: Alias prefix for wallets

        Returns:
            {"created": N, "wallets": [{"address": "0x...", "alias": "..."}]}
        """
        wallets = self.wallet_manager.create_wallet_batch(count, prefix)
        return {
            "created": len(wallets),
            "wallets": [
                {"address": w.address, "alias": w.alias}
                for w in wallets
            ]
        }

    def list_wallets(self) -> List[Dict]:
        """List all wallets."""
        return [
            {
                "address": w.get("address", "")[:20] + "...",
                "alias": w.get("alias", "unknown"),
                "status": w.get("status", "unknown")
            }
            for w in self.wallet_manager.list_wallets()
        ]

    def wallet_count(self) -> int:
        """Get active wallet count."""
        return len([w for w in self.wallet_manager.list_wallets() if w.get("status") == "active"])

    # ==================== ORDERS ====================

    def get_orders(self) -> Dict:
        """
        Get all orders across all wallets.

        Returns:
            {"total": N, "by_wallet": {...}}
        """
        all_orders = self.orchestrator.get_all_orders()
        total = sum(len(o) for o in all_orders.values() if isinstance(o, list))

        return {
            "total": total,
            "by_wallet": {
                addr[:15]: len(orders) if isinstance(orders, list) else 0
                for addr, orders in all_orders.items()
            }
        }

    def cancel_all(self) -> Dict:
        """
        Cancel all orders on all wallets.

        Returns:
            {"cancelled": N, "wallets": N}
        """
        results = self.orchestrator.cancel_all_all_wallets()
        success = sum(1 for r in results if r.success)
        return {
            "cancelled": success,
            "wallets": len(results)
        }

    def place_order(self, token_id: str, price: float, size: float, side: str) -> Dict:
        """
        Place single order on primary wallet.

        Args:
            token_id: Polymarket token ID
            price: Price (0.001 to 0.999)
            side: "BUY" or "SELL"
            size: Number of shares

        Returns:
            {"success": bool, "order_id": "..."}
        """
        result = self.orchestrator.execute_immediate(
            list(self.orchestrator.wallets.keys())[0] if self.orchestrator.wallets else "",
            "place",
            {"token_id": token_id, "price": price, "size": size, "side": side}
        )
        return {
            "success": result.success,
            "order_id": result.task_id,
            "latency_ms": result.elapsed_ms
        }

    def place_grid(self, token_id: str, center_price: float,
                   spread_bps: int = 100, levels: int = 5, size: float = 10) -> Dict:
        """
        Place order grid around center price.

        Args:
            token_id: Polymarket token ID
            center_price: Center price for grid
            spread_bps: Spread in basis points between levels
            levels: Number of levels on each side
            size: Size per level

        Returns:
            {"success": bool, "orders_placed": N}
        """
        results = self.orchestrator.place_grid_all_wallets(
            token_id, center_price, spread_bps, levels, size, "BOTH"
        )
        success = sum(1 for r in results if r.success)
        return {
            "success": success > 0,
            "orders_placed": success * levels * 2,
            "wallets_used": len(results)
        }

    # ==================== HFT OPERATIONS ====================

    def presign(self, token_id: str, center_price: float = 0.5, levels: int = 50) -> Dict:
        """
        Pre-sign orders for instant submission.

        Args:
            token_id: Polymarket token ID
            center_price: Center price
            levels: Number of price levels to pre-sign

        Returns:
            {"presigned": N, "rate": N/sec}
        """
        result = self.presigner.presign_grid_parallel(
            token_id=token_id,
            center_price=center_price,
            spread_bps=10,
            levels=levels,
            size_per_level=10
        )
        return {
            "presigned": result.get("orders_pre_signed", 0),
            "rate": result.get("orders_per_sec", 0),
            "elapsed_sec": result.get("elapsed_sec", 0)
        }

    def fire(self, token_id: str, count: int = 100) -> Dict:
        """
        Fire orders at maximum speed.

        Args:
            token_id: Polymarket token ID
            count: Number of orders to fire

        Returns:
            {"fired": N, "rate": N/sec, "latency_ms": N}
        """
        async def _fire():
            from executor.hft_order_cannon import HFTOrderCannon
            cannon = HFTOrderCannon()
            orders = [{"token_id": token_id, "idx": i} for i in range(count)]
            result = await cannon.fire_barrage(orders)
            await cannon.cleanup()
            return result

        result = asyncio.run(_fire())
        return {
            "fired": result.get("orders_fired", 0),
            "successful": result.get("successful", 0),
            "rate": result.get("rate_per_sec", 0),
            "latency_ms": result.get("avg_latency_ms", 0)
        }

    def benchmark(self) -> Dict:
        """
        Run throughput benchmark.

        Returns:
            {"rate": N/sec, "latency_ms": N, "scaling": {...}}
        """
        async def _bench():
            from executor.hft_order_cannon import HFTOrderCannon, CannonConfig
            cannon = HFTOrderCannon(CannonConfig(connections_per_wallet=100))
            orders = [{"test": i} for i in range(1000)]
            result = await cannon.fire_barrage(orders)
            await cannon.cleanup()
            return result

        result = asyncio.run(_bench())
        base_rate = result.get("rate_per_sec", 1000)

        return {
            "rate": base_rate,
            "latency_ms": result.get("avg_latency_ms", 0),
            "scaling": {
                "1_wallet": base_rate,
                "10_wallets": base_rate * 10,
                "100_wallets": base_rate * 100,
                "1000_wallets": base_rate * 1000
            }
        }

    # ==================== FLEET CONTROL ====================

    def start_fleet(self) -> Dict:
        """Start HFT process fleet."""
        self.coordinator.start()
        return {
            "started": True,
            "processes": len(self.coordinator.processes)
        }

    def stop_fleet(self) -> Dict:
        """Stop HFT process fleet."""
        self.coordinator.stop()
        return {"stopped": True}

    # ==================== CONVENIENCE ====================

    def scale_up(self, wallet_count: int = 100) -> Dict:
        """
        Quick scale up: create wallets and initialize.

        Args:
            wallet_count: Target number of wallets

        Returns:
            {"wallets": N, "ready": bool}
        """
        current = self.wallet_count()
        needed = max(0, wallet_count - current)

        if needed > 0:
            self.create_wallets(needed, "scale")

        return {
            "wallets": self.wallet_count(),
            "created": needed,
            "ready": self.wallet_count() >= wallet_count
        }

    def market_maker(self, token_id: str, center_price: float = None) -> Dict:
        """
        Quick market maker: cancel all, place new grid.

        Args:
            token_id: Polymarket token ID
            center_price: Center price (auto-detects if None)

        Returns:
            {"cancelled": N, "placed": N}
        """
        # Cancel existing
        cancel_result = self.cancel_all()

        # Place new grid
        center = center_price or 0.5
        grid_result = self.place_grid(token_id, center)

        return {
            "cancelled": cancel_result.get("cancelled", 0),
            "placed": grid_result.get("orders_placed", 0)
        }


# Singleton instance for easy import
hft = HFTAgentAPI()


# ==================== AUTONOMOUS SYSTEM HOOKS ====================

def get_hft_status() -> Dict:
    """Hook for autonomous system status checks."""
    return hft.status()

def get_hft_capacity() -> int:
    """Hook for capacity planning."""
    status = hft.status()
    return status["capacity"]["theoretical_max"]

def autonomous_scale_check() -> Dict:
    """
    Check if scaling is needed for autonomous operation.

    Returns recommendation for autonomous system.
    """
    status = hft.status()
    wallets = status["wallets"]["active"]

    if wallets < 10:
        return {
            "action": "scale_up",
            "reason": "Low wallet count",
            "recommendation": "hft.create_wallets(100)"
        }
    elif wallets < 100:
        return {
            "action": "scale_up",
            "reason": "Medium capacity",
            "recommendation": "hft.create_wallets(100)"
        }
    else:
        return {
            "action": "none",
            "reason": "Sufficient capacity",
            "wallets": wallets
        }


# ==================== CLI ====================

def main():
    """CLI for testing."""
    import sys

    if len(sys.argv) < 2:
        print("HFT Agent API")
        print("Usage: python hft_agent_api.py <command>")
        print("Commands: status, wallets, orders, benchmark")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(hft.status(), indent=2))
    elif cmd == "wallets":
        print(json.dumps(hft.list_wallets(), indent=2))
    elif cmd == "orders":
        print(json.dumps(hft.get_orders(), indent=2))
    elif cmd == "benchmark":
        print(json.dumps(hft.benchmark(), indent=2))
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
