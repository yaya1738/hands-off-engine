"""Compatibility coordinator for the historical HFT design.

The historical implementation contained a direct Polymarket HTTP submission
path and an embedded fallback private key.  That path is intentionally removed.
This module remains import-compatible for analysis/demo callers, but consequential
order submission is delegated to the repository's single fail-closed authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from ai.factory.live_order_authority import LiveOrderAuthority


@dataclass
class HFTConfig:
    target_orders_per_sec: int = 1_000_000
    wallets_target: int = 1000
    processes_target: int = 10
    rate_per_wallet: int = 1000
    ring_buffer_size: int = 1_000_000
    presign_cache_size: int = 10_000_000
    connections_per_wallet: int = 100
    keepalive_seconds: int = 30
    batch_interval_ms: float = 1.0
    stats_interval_sec: float = 1.0


class ProcessWorker:
    """Analysis-only worker; live mutation always enters LiveOrderAuthority."""

    def __init__(self, worker_id: int, wallets: List[Dict], order_queue: Any,
                 stats_array: Any, shutdown_event: Any):
        self.worker_id = worker_id
        self.wallets = wallets
        self.order_queue = order_queue
        self.stats_array = stats_array
        self.shutdown_event = shutdown_event
        self.authority = LiveOrderAuthority()

    async def _submit_order(self, session: Any, order: Dict) -> bool:
        """Submit through the canonical fail-closed authority; never HTTP POST directly."""
        del session
        try:
            result = self.authority.submit(order)
        except (TypeError, ValueError, KeyError):
            return False
        return bool(result.get("executed") is True)


class HFTMillionCoordinator:
    """Retained compatibility surface with no direct exchange mutation capability."""

    def __init__(self, config: HFTConfig | None = None):
        self.config = config or HFTConfig()
        self.wallets: List[Dict] = []
        self.processes: List[Any] = []
        self.orders: List[Dict] = []
        self.running = False
        self.authority = LiveOrderAuthority()

    def _load_wallets(self) -> None:
        """Wallet discovery is deliberately omitted; credentials never enter this coordinator."""
        self.wallets = []

    def calculate_capacity(self) -> Dict[str, Any]:
        return {
            "wallets": len(self.wallets),
            "rate_per_wallet": self.config.rate_per_wallet,
            "processes": self.config.processes_target,
            "theoretical_single_process": 0,
            "theoretical_multi_process": 0,
            "target": self.config.target_orders_per_sec,
            "can_hit_target": False,
            "wallets_needed_for_1m": max(1, int(1_000_000 / self.config.rate_per_wallet / 0.8)),
            "live_submission": False,
            "authority": "ai.factory.live_order_authority.LiveOrderAuthority",
        }

    def push_order(self, order: Dict) -> bool:
        """Queue an intent for analysis only; it is never sent to an exchange."""
        if not isinstance(order, dict):
            return False
        self.orders.append(dict(order))
        return True

    def push_batch(self, orders: List[Dict]) -> int:
        return sum(1 for order in orders if self.push_order(order))

    def start(self) -> None:
        """Historical live workers are disabled; no background exchange clients are created."""
        self.running = False

    def stop(self) -> None:
        self.running = False
        self.processes.clear()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "submitted": 0,
            "successful": 0,
            "failed": len(self.orders),
            "queued_analysis_only": len(self.orders),
            "processes_running": 0,
            "wallets": 0,
            "live_submission": False,
        }

    def run_demo(self) -> Dict[str, Any]:
        return {
            "status": "analysis_only",
            "capacity": self.calculate_capacity(),
            "live_submission": False,
            "reason": "historical direct exchange path removed; use governed authority",
        }


def worker_process_main(*args: Any, **kwargs: Any) -> None:
    """Compatibility entrypoint; historical live worker is intentionally inert."""
    del args, kwargs
    return None


def main() -> HFTMillionCoordinator:
    coordinator = HFTMillionCoordinator()
    coordinator.run_demo()
    return coordinator


if __name__ == "__main__":
    main()
