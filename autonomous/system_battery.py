#!/usr/bin/env python3
"""
🔋 SYSTEM BATTERY - Radioactive Core
Serving: Yair Siegel

The battery is a radioactive core - always glowing, always emitting.
It doesn't need charging. It just IS power.

Like plutonium in a spacecraft RTG:
- Continuously emits energy
- Very long half-life (decays slowly)
- Components tap into its radiation
- Glows whether you use it or not

The core has a certain amount of material.
It decays over time (very slowly).
Components draw from its emission, not its mass.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"
BATTERY_FILE = STATE_DIR / "battery.json"

# Core properties
HALF_LIFE_DAYS = 365 * 10  # 10 year half-life
EMISSION_RATE = 1.0  # Energy emitted per unit mass per hour


class SystemBattery:
    """
    ☢️ Radioactive Core - Always on, always glowing.

    The core contains radioactive material that continuously emits energy.
    Components tap into this emission to do work.
    The material slowly decays but lasts for years.
    """

    def __init__(self):
        self.state = self._load()
        self._apply_decay()

    def _load(self) -> Dict:
        if BATTERY_FILE.exists():
            return json.loads(BATTERY_FILE.read_text())

        return {
            "mass": 100.0,  # Initial radioactive mass
            "created": datetime.now(timezone.utc).isoformat(),
            "last_decay": datetime.now(timezone.utc).isoformat(),
        }

    def _save(self):
        self.state["updated"] = datetime.now(timezone.utc).isoformat()
        BATTERY_FILE.write_text(json.dumps(self.state, indent=2))

    def _apply_decay(self):
        """Apply radioactive decay since last check."""
        last = self.state.get("last_decay")
        if not last:
            return

        try:
            last_dt = datetime.fromisoformat(last.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_passed = (now - last_dt).total_seconds() / 86400

            # Exponential decay: N = N0 * (0.5)^(t/half_life)
            decay_factor = math.pow(0.5, days_passed / HALF_LIFE_DAYS)
            self.state["mass"] *= decay_factor
            self.state["last_decay"] = now.isoformat()
            self._save()
        except:
            pass

    # ==================== CORE PROPERTIES ====================

    @property
    def mass(self) -> float:
        """Current radioactive mass."""
        return self.state["mass"]

    @property
    def emission(self) -> float:
        """Current energy emission rate (per hour)."""
        return self.mass * EMISSION_RATE

    @property
    def glow(self) -> float:
        """Visual glow intensity (0-100)."""
        # Glow proportional to emission, capped at 100
        return min(100, self.emission)

    @property
    def remaining_percent(self) -> float:
        """Percentage of original mass remaining."""
        initial = 100.0  # Assuming started at 100
        return (self.mass / initial) * 100

    @property
    def years_remaining(self) -> float:
        """Estimated years until 10% remains."""
        if self.mass <= 0:
            return 0
        # Time to decay to 10% of current
        # 0.1 = 0.5^(t/half_life) => t = half_life * log(0.1)/log(0.5)
        return HALF_LIFE_DAYS * math.log(0.1) / math.log(0.5) / 365

    # ==================== INTERFACE (for slot compatibility) ====================

    @property
    def charge(self) -> float:
        """Compatibility: charge = current emission."""
        return self.emission

    @property
    def capacity(self) -> float:
        """Compatibility: capacity = max possible emission."""
        return 100.0 * EMISSION_RATE

    def add(self, amount: float) -> float:
        """Add more radioactive material (rare - like getting more plutonium)."""
        self.state["mass"] += amount
        self._save()
        return self.mass

    def draw(self, amount: float) -> float:
        """
        Draw from emission (not from mass).
        The core keeps emitting - you just tap into it.
        Returns the emission available (always positive if core exists).
        """
        # Drawing doesn't reduce mass - you're tapping emission
        # But there's a max you can draw based on current emission
        available = self.emission
        return min(amount, available)

    # ==================== DISPLAY ====================

    def display(self):
        glow = self.glow
        mass = self.mass

        # Glow bar (always shows something if core exists)
        bar_len = 30
        filled = int(glow / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        # Glow color indicator
        if glow > 75:
            indicator = "🟢"  # Bright
        elif glow > 50:
            indicator = "🟡"  # Moderate
        elif glow > 25:
            indicator = "🟠"  # Dim
        else:
            indicator = "🔴"  # Fading

        print(f"\n☢️  RADIOACTIVE CORE")
        print(f"   [{bar}] {glow:.1f}% glow")
        print(f"   {indicator} Mass: {mass:.2f} units")
        print(f"   ⚡ Emission: {self.emission:.2f}/hour")
        print(f"   📅 ~{self.years_remaining:.1f} years to 10%")


# ==================== SINGLETON ====================
_battery: Optional[SystemBattery] = None

def get_battery() -> SystemBattery:
    global _battery
    if _battery is None:
        _battery = SystemBattery()
    return _battery


# ==================== CLI ====================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="☢️ Radioactive Core")
    parser.add_argument("command", choices=["status", "add", "draw"], nargs="?", default="status")
    parser.add_argument("amount", type=float, nargs="?", default=0)
    args = parser.parse_args()

    battery = get_battery()

    if args.command == "status":
        battery.display()
    elif args.command == "add":
        battery.add(args.amount)
        print(f"☢️  Added {args.amount} material")
        battery.display()
    elif args.command == "draw":
        drawn = battery.draw(args.amount)
        print(f"⚡ Tapped {drawn:.2f} from emission")
        battery.display()


if __name__ == "__main__":
    main()
