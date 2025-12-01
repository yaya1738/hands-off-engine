#!/usr/bin/env python3
"""
🔌 BATTERY SLOT - Where battery connects to system
Serving: Yair Siegel

This is the INTERFACE - the +/- terminals where a battery plugs in.
Components connect here to draw power.
When we find a real power source, it plugs into this slot.

The slot doesn't care what battery is installed.
It just provides the interface: draw(), charge(), level()
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable, Any

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"
SLOT_FILE = STATE_DIR / "battery_slot.json"


class BatterySlot:
    """
    🔌 The slot where battery connects to system.

    + terminal: charge()
    - terminal: draw()

    Components use the slot, not the battery directly.
    """

    def __init__(self):
        self._battery = None  # The actual battery (plugged in later)
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if SLOT_FILE.exists():
            return json.loads(SLOT_FILE.read_text())
        return {
            "installed": False,
            "battery_type": None,
            "total_drawn": 0,
            "total_charged": 0,
            "draw_count": 0,
            "charge_count": 0,
        }

    def _save_state(self):
        self._state["updated"] = datetime.now(timezone.utc).isoformat()
        SLOT_FILE.write_text(json.dumps(self._state, indent=2))

    # ==================== SLOT INTERFACE ====================

    def install(self, battery):
        """
        Install a battery into the slot.

        Battery must have: charge, capacity, add(), draw()
        """
        self._battery = battery
        self._state["installed"] = True
        self._state["battery_type"] = type(battery).__name__
        self._save_state()

    def remove(self):
        """Remove the battery."""
        self._battery = None
        self._state["installed"] = False
        self._state["battery_type"] = None
        self._save_state()

    @property
    def has_battery(self) -> bool:
        """Is a battery installed?"""
        return self._battery is not None

    # ==================== TERMINALS ====================

    def draw(self, amount: float = 1) -> float:
        """
        - TERMINAL: Draw power from battery.
        Returns amount actually drawn (0 if no battery).
        """
        if not self._battery:
            return 0

        drawn = self._battery.draw(amount)
        self._state["total_drawn"] += drawn
        self._state["draw_count"] += 1
        self._save_state()
        return drawn

    def charge(self, amount: float) -> float:
        """
        + TERMINAL: Charge the battery.
        Returns new charge level (0 if no battery).
        """
        if not self._battery:
            return 0

        result = self._battery.add(amount)
        self._state["total_charged"] += amount
        self._state["charge_count"] += 1
        self._save_state()
        return result

    @property
    def level(self) -> float:
        """Current charge level."""
        if not self._battery:
            return 0
        return self._battery.charge

    @property
    def capacity(self) -> float:
        """Battery capacity."""
        if not self._battery:
            return 0
        return self._battery.capacity

    @property
    def percent(self) -> float:
        """Charge percentage."""
        if not self._battery or self.capacity == 0:
            return 0
        return (self.level / self.capacity) * 100

    # ==================== POWERED EXECUTION ====================

    def power(self, func: Callable, cost: float = 1) -> Any:
        """
        Execute function if enough power, drawing from battery.
        Returns None if insufficient power.
        """
        if self.level < cost:
            return None

        self.draw(cost)
        return func()

    # ==================== STATUS ====================

    def status(self) -> dict:
        return {
            "installed": self.has_battery,
            "type": self._state.get("battery_type"),
            "level": self.level,
            "capacity": self.capacity,
            "percent": self.percent,
            "total_drawn": self._state["total_drawn"],
            "total_charged": self._state["total_charged"],
        }

    def display(self):
        if not self.has_battery:
            print("\n🔌 [NO BATTERY INSTALLED]")
            return

        bar_len = 30
        filled = int(self.percent / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        print(f"\n🔌 [{bar}] {self.level:.0f}/{self.capacity:.0f} ({self.percent:.1f}%)")
        print(f"   Type: {self._state.get('battery_type', 'unknown')}")
        print(f"   Total drawn: {self._state['total_drawn']:.0f}")
        print(f"   Total charged: {self._state['total_charged']:.0f}")


# ==================== SINGLETON ====================
_slot: Optional[BatterySlot] = None

def get_slot() -> BatterySlot:
    """Get the system's battery slot."""
    global _slot
    if _slot is None:
        _slot = BatterySlot()
    return _slot


# ==================== AUTO-INSTALL DEFAULT BATTERY ====================
def _auto_install():
    """Auto-install the default battery if available."""
    slot = get_slot()
    if not slot.has_battery:
        try:
            from autonomous.system_battery import get_battery
            slot.install(get_battery())
        except:
            pass

_auto_install()


# ==================== CLI ====================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="🔌 Battery Slot")
    parser.add_argument("command", choices=["status", "draw", "charge"], nargs="?", default="status")
    parser.add_argument("amount", type=float, nargs="?", default=1)
    args = parser.parse_args()

    slot = get_slot()

    if args.command == "status":
        slot.display()
    elif args.command == "draw":
        drawn = slot.draw(args.amount)
        print(f"⚡ Drew {drawn}")
        slot.display()
    elif args.command == "charge":
        slot.charge(args.amount)
        print(f"🔋 Charged {args.amount}")
        slot.display()


if __name__ == "__main__":
    main()
