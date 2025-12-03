#!/usr/bin/env python3
"""
HFT Auto-Scaler - Connects Wallet Creation to Order Frequency Demands

When order frequency needs increase, automatically provisions more wallets.
Capacity scales linearly: more wallets = higher throughput.

USAGE:
    from executor.hft_auto_scaler import scaler

    # Set target frequency
    scaler.set_target_frequency(100000)  # 100k orders/sec

    # Auto-scale to meet target
    scaler.auto_scale()

    # Or let it run continuously
    scaler.start_auto_scaling()

Serving: Yair Siegel
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
SCALER_STATE_FILE = STATE_DIR / "hft_scaler_state.json"


@dataclass
class ScalerConfig:
    """Configuration for auto-scaling behavior."""
    rate_per_wallet: int = 1000  # Orders/sec per wallet
    min_wallets: int = 1
    max_wallets: int = 10000  # Safety cap
    scale_up_threshold: float = 0.8  # Scale when at 80% capacity
    scale_down_threshold: float = 0.3  # Scale down when below 30%
    scale_up_increment: int = 10  # Add this many wallets at a time
    cooldown_seconds: int = 60  # Wait between scaling actions
    auto_scale_interval: int = 30  # Check every N seconds


@dataclass
class ScalerState:
    """Current state of the auto-scaler."""
    target_frequency: int = 0
    current_capacity: int = 0
    wallet_count: int = 0
    last_scale_time: float = 0
    last_scale_action: str = "none"
    scaling_history: list = field(default_factory=list)


class HFTAutoScaler:
    """
    Auto-scales wallet fleet based on order frequency demands.

    The core principle: each wallet can handle ~1000 orders/sec.
    To hit higher frequencies, we need more wallets.
    """

    def __init__(self, config: ScalerConfig = None):
        self.config = config or ScalerConfig()
        self.state = ScalerState()
        self._load_state()

        self._wallet_manager = None
        self._hft_api = None
        self._running = False
        self._thread = None

        # Callbacks for external systems
        self._on_scale_up: Optional[Callable] = None
        self._on_scale_down: Optional[Callable] = None
        self._on_capacity_change: Optional[Callable] = None

    @property
    def wallet_manager(self):
        if not self._wallet_manager:
            from executor.multi_wallet_manager import MultiWalletManager
            self._wallet_manager = MultiWalletManager()
        return self._wallet_manager

    @property
    def hft_api(self):
        if not self._hft_api:
            from executor.hft_agent_api import hft
            self._hft_api = hft
        return self._hft_api

    # ==================== STATE ====================

    def _load_state(self):
        """Load persisted state."""
        if SCALER_STATE_FILE.exists():
            try:
                data = json.loads(SCALER_STATE_FILE.read_text())
                self.state.target_frequency = data.get("target_frequency", 0)
                self.state.last_scale_time = data.get("last_scale_time", 0)
                self.state.scaling_history = data.get("scaling_history", [])[-100:]
            except:
                pass

    def _save_state(self):
        """Persist state."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "target_frequency": self.state.target_frequency,
            "current_capacity": self.state.current_capacity,
            "wallet_count": self.state.wallet_count,
            "last_scale_time": self.state.last_scale_time,
            "last_scale_action": self.state.last_scale_action,
            "scaling_history": self.state.scaling_history[-100:],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        SCALER_STATE_FILE.write_text(json.dumps(data, indent=2))

    # ==================== CAPACITY CALCULATION ====================

    def get_current_capacity(self) -> Dict:
        """Calculate current order capacity based on wallet count."""
        wallets = self.wallet_manager.list_wallets()
        active = [w for w in wallets if w.get("status") == "active"]

        wallet_count = len(active)
        capacity = wallet_count * self.config.rate_per_wallet

        self.state.wallet_count = wallet_count
        self.state.current_capacity = capacity

        return {
            "wallet_count": wallet_count,
            "rate_per_wallet": self.config.rate_per_wallet,
            "current_capacity": capacity,
            "target_frequency": self.state.target_frequency,
            "utilization": self.state.target_frequency / capacity if capacity > 0 else 0,
            "headroom": capacity - self.state.target_frequency
        }

    def wallets_needed_for(self, target_frequency: int) -> int:
        """Calculate how many wallets needed for target frequency."""
        needed = (target_frequency + self.config.rate_per_wallet - 1) // self.config.rate_per_wallet
        return max(self.config.min_wallets, min(needed, self.config.max_wallets))

    # ==================== TARGET SETTING ====================

    def set_target_frequency(self, orders_per_second: int) -> Dict:
        """
        Set target order frequency. System will scale to meet this.

        Args:
            orders_per_second: Target orders per second

        Returns:
            {"target": N, "wallets_needed": N, "current_wallets": N}
        """
        self.state.target_frequency = orders_per_second
        needed = self.wallets_needed_for(orders_per_second)
        current = self.get_current_capacity()

        self._save_state()

        return {
            "target": orders_per_second,
            "wallets_needed": needed,
            "current_wallets": current["wallet_count"],
            "current_capacity": current["current_capacity"],
            "action_needed": "scale_up" if needed > current["wallet_count"] else "none"
        }

    def increase_frequency(self, by_amount: int) -> Dict:
        """Increase target frequency by amount."""
        new_target = self.state.target_frequency + by_amount
        return self.set_target_frequency(new_target)

    def decrease_frequency(self, by_amount: int) -> Dict:
        """Decrease target frequency by amount."""
        new_target = max(0, self.state.target_frequency - by_amount)
        return self.set_target_frequency(new_target)

    # ==================== SCALING ACTIONS ====================

    def scale_to_capacity(self, target_capacity: int) -> Dict:
        """
        Scale wallet fleet to handle target capacity.

        Args:
            target_capacity: Orders/sec to support

        Returns:
            {"wallets_created": N, "total_wallets": N, "new_capacity": N}
        """
        needed = self.wallets_needed_for(target_capacity)
        current = len([w for w in self.wallet_manager.list_wallets() if w.get("status") == "active"])

        to_create = max(0, needed - current)

        if to_create > 0:
            result = self.hft_api.create_wallets(to_create, "scale")
            created = result.get("created", 0)

            # Record action
            self._record_scale_action("scale_up", created, target_capacity)

            if self._on_scale_up:
                self._on_scale_up(created, target_capacity)
        else:
            created = 0

        new_capacity = self.get_current_capacity()

        return {
            "wallets_created": created,
            "total_wallets": new_capacity["wallet_count"],
            "new_capacity": new_capacity["current_capacity"],
            "target_met": new_capacity["current_capacity"] >= target_capacity
        }

    def auto_scale(self) -> Dict:
        """
        Check current state and scale if needed.

        Returns:
            {"action": "scale_up"|"scale_down"|"none", "details": {...}}
        """
        # Check cooldown
        if time.time() - self.state.last_scale_time < self.config.cooldown_seconds:
            return {"action": "cooldown", "remaining": self.config.cooldown_seconds - (time.time() - self.state.last_scale_time)}

        capacity = self.get_current_capacity()
        utilization = capacity["utilization"]

        # Need to scale up?
        if utilization > self.config.scale_up_threshold:
            # Calculate how many more wallets
            target = int(self.state.target_frequency / self.config.scale_up_threshold)
            result = self.scale_to_capacity(target)
            return {"action": "scale_up", "details": result}

        # Could scale down? (optional - wallets are cheap to keep)
        if utilization < self.config.scale_down_threshold and capacity["wallet_count"] > self.config.min_wallets:
            # We don't actually delete wallets, just note the opportunity
            return {
                "action": "scale_down_opportunity",
                "current_wallets": capacity["wallet_count"],
                "needed_wallets": self.wallets_needed_for(self.state.target_frequency),
                "note": "Wallets retained for burst capacity"
            }

        return {"action": "none", "capacity": capacity}

    def _record_scale_action(self, action: str, count: int, target: int):
        """Record scaling action for history."""
        self.state.last_scale_time = time.time()
        self.state.last_scale_action = action
        self.state.scaling_history.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "count": count,
            "target": target
        })
        self._save_state()

        if self._on_capacity_change:
            self._on_capacity_change(self.get_current_capacity())

    # ==================== CONTINUOUS SCALING ====================

    def start_auto_scaling(self):
        """Start background auto-scaling thread."""
        if self._running:
            return {"status": "already_running"}

        self._running = True
        self._thread = threading.Thread(target=self._auto_scale_loop, daemon=True)
        self._thread.start()

        return {"status": "started", "interval": self.config.auto_scale_interval}

    def stop_auto_scaling(self):
        """Stop background auto-scaling."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        return {"status": "stopped"}

    def _auto_scale_loop(self):
        """Background loop for auto-scaling."""
        while self._running:
            try:
                self.auto_scale()
            except Exception as e:
                print(f"[AutoScaler] Error: {e}")
            time.sleep(self.config.auto_scale_interval)

    # ==================== CALLBACKS ====================

    def on_scale_up(self, callback: Callable):
        """Register callback for scale-up events."""
        self._on_scale_up = callback

    def on_scale_down(self, callback: Callable):
        """Register callback for scale-down events."""
        self._on_scale_down = callback

    def on_capacity_change(self, callback: Callable):
        """Register callback for capacity changes."""
        self._on_capacity_change = callback

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get complete scaler status."""
        capacity = self.get_current_capacity()

        return {
            "target_frequency": self.state.target_frequency,
            "current_capacity": capacity["current_capacity"],
            "wallet_count": capacity["wallet_count"],
            "utilization": f"{capacity['utilization']*100:.1f}%",
            "headroom": capacity["headroom"],
            "last_scale_action": self.state.last_scale_action,
            "auto_scaling_active": self._running,
            "config": {
                "rate_per_wallet": self.config.rate_per_wallet,
                "max_wallets": self.config.max_wallets,
                "scale_up_threshold": self.config.scale_up_threshold
            }
        }

    def quick_status(self) -> str:
        """One-line status."""
        s = self.status()
        return f"Scaler: {s['wallet_count']} wallets, {s['current_capacity']}/sec capacity, {s['utilization']} utilized"


# Singleton instance
scaler = HFTAutoScaler()


# ==================== CONVENIENCE FUNCTIONS ====================

def scale_for_frequency(orders_per_second: int) -> Dict:
    """Quick function: scale to handle target frequency."""
    scaler.set_target_frequency(orders_per_second)
    return scaler.scale_to_capacity(orders_per_second)


def ensure_capacity(min_orders_per_second: int) -> Dict:
    """Ensure at least this much capacity exists."""
    capacity = scaler.get_current_capacity()
    if capacity["current_capacity"] < min_orders_per_second:
        return scaler.scale_to_capacity(min_orders_per_second)
    return {"action": "none", "capacity_sufficient": True, "current": capacity["current_capacity"]}


def get_capacity() -> int:
    """Get current orders/sec capacity."""
    return scaler.get_current_capacity()["current_capacity"]


# ==================== CLI ====================

def main():
    import sys

    if len(sys.argv) < 2:
        print("HFT Auto-Scaler")
        print("Usage: python hft_auto_scaler.py <command>")
        print("Commands: status, scale <freq>, capacity")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(scaler.status(), indent=2))
    elif cmd == "scale":
        freq = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
        result = scale_for_frequency(freq)
        print(json.dumps(result, indent=2))
    elif cmd == "capacity":
        print(json.dumps(scaler.get_current_capacity(), indent=2))
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
