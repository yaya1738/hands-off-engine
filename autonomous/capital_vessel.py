#!/usr/bin/env python3
"""
🏺 CAPITAL VESSEL - Where Capital Actually Lives
Serving: Yair Siegel

Not a pipe. Not a meter. A VESSEL.

Like a ship's hull holds cargo, or a reservoir holds water -
this is where capital actually SITS. It has:
- Volume (how much it can hold)
- Contents (what's actually in it)
- Compartments (different purposes)
- Walls (protection)
- Inlets/Outlets (controlled flow)

The vessel gives the system SUBSTANCE for its capital.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"
VESSEL_STATE = STATE_DIR / "capital_vessel.json"
VESSEL_LOG = STATE_DIR / "vessel_transactions.jsonl"


class Compartment(Enum):
    """Compartments within the vessel - different purposes."""
    RESERVE = "reserve"          # Emergency fund - don't touch
    OPERATING = "operating"      # Day-to-day operations
    TRADING = "trading"          # Active trading capital
    GROWTH = "growth"            # Investment for expansion
    BUFFER = "buffer"            # Overflow/temporary holding


@dataclass
class VesselCompartment:
    """A compartment within the vessel."""
    name: str
    purpose: str
    capacity: float              # Max this compartment can hold
    contents: float = 0.0        # Current amount
    minimum: float = 0.0         # Don't drain below this
    locked: bool = False         # If locked, can't withdraw

    @property
    def available(self) -> float:
        """Amount available for withdrawal."""
        if self.locked:
            return 0.0
        return max(0, self.contents - self.minimum)

    @property
    def space(self) -> float:
        """Remaining capacity."""
        return max(0, self.capacity - self.contents)

    @property
    def fill_level(self) -> float:
        """Fill percentage 0-100."""
        if self.capacity == 0:
            return 0
        return (self.contents / self.capacity) * 100

    def deposit(self, amount: float) -> float:
        """Deposit into compartment. Returns actual deposited."""
        actual = min(amount, self.space)
        self.contents += actual
        return actual

    def withdraw(self, amount: float) -> float:
        """Withdraw from compartment. Returns actual withdrawn."""
        if self.locked:
            return 0.0
        actual = min(amount, self.available)
        self.contents -= actual
        return actual


@dataclass
class VesselWall:
    """The vessel's walls - protection layer."""
    integrity: float = 100.0     # Wall strength 0-100
    thickness: float = 1.0       # How much protection
    material: str = "standard"   # Wall material type

    def take_damage(self, amount: float):
        """Wall takes damage (from losses, attacks, etc.)."""
        self.integrity = max(0, self.integrity - amount)

    def repair(self, amount: float):
        """Repair wall integrity."""
        self.integrity = min(100, self.integrity + amount)

    @property
    def is_breached(self) -> bool:
        """Is the wall compromised?"""
        return self.integrity < 20


@dataclass
class FlowValve:
    """Controls flow in/out of vessel."""
    name: str
    direction: str  # "inlet" or "outlet"
    max_flow: float  # Max per transaction
    open: bool = True
    daily_limit: float = 0.0  # 0 = unlimited
    daily_used: float = 0.0

    def can_flow(self, amount: float) -> bool:
        """Can this amount flow through?"""
        if not self.open:
            return False
        if amount > self.max_flow:
            return False
        if self.daily_limit > 0 and (self.daily_used + amount) > self.daily_limit:
            return False
        return True

    def flow(self, amount: float) -> float:
        """Execute flow, returns actual amount."""
        if not self.can_flow(amount):
            return 0.0
        actual = min(amount, self.max_flow)
        if self.daily_limit > 0:
            actual = min(actual, self.daily_limit - self.daily_used)
        self.daily_used += actual
        return actual


class CapitalVessel:
    """
    🏺 THE CAPITAL VESSEL

    A container with substance that holds the system's capital.

    Structure:
    ┌─────────────────────────────────────────────┐
    │  ╔═══════════════════════════════════════╗  │
    │  ║           CAPITAL VESSEL              ║  │
    │  ╠═══════════════════════════════════════╣  │
    │  ║  ┌─────────┐ ┌─────────┐ ┌─────────┐ ║  │
    │  ║  │ RESERVE │ │OPERATING│ │ TRADING │ ║  │
    │  ║  │  $___   │ │  $___   │ │  $___   │ ║  │
    │  ║  │ LOCKED  │ │         │ │         │ ║  │
    │  ║  └─────────┘ └─────────┘ └─────────┘ ║  │
    │  ║  ┌─────────┐ ┌─────────────────────┐ ║  │
    │  ║  │ GROWTH  │ │       BUFFER        │ ║  │
    │  ║  │  $___   │ │        $___         │ ║  │
    │  ║  └─────────┘ └─────────────────────┘ ║  │
    │  ╚═══════════════════════════════════════╝  │
    │           ↑ INLET          ↓ OUTLET         │
    └─────────────────────────────────────────────┘
    """

    def __init__(self):
        self.state = self._load_state()
        self._init_structure()

    def _load_state(self) -> Dict:
        if VESSEL_STATE.exists():
            try:
                return json.loads(VESSEL_STATE.read_text())
            except:
                pass
        return {
            "created": datetime.now(timezone.utc).isoformat(),
            "total_deposited": 0.0,
            "total_withdrawn": 0.0,
        }

    def _init_structure(self):
        """Initialize vessel structure."""
        # Compartments
        self.compartments = {
            Compartment.RESERVE: VesselCompartment(
                name="Reserve",
                purpose="Emergency fund - untouchable",
                capacity=1000.0,
                minimum=0,
                locked=True,  # Reserve is locked
                contents=self.state.get("compartments", {}).get("reserve", {}).get("contents", 0)
            ),
            Compartment.OPERATING: VesselCompartment(
                name="Operating",
                purpose="Day-to-day operations",
                capacity=500.0,
                minimum=10.0,  # Keep $10 min for ops
                contents=self.state.get("compartments", {}).get("operating", {}).get("contents", 0)
            ),
            Compartment.TRADING: VesselCompartment(
                name="Trading",
                purpose="Active trading capital",
                capacity=5000.0,
                minimum=0,
                contents=self.state.get("compartments", {}).get("trading", {}).get("contents", 0)
            ),
            Compartment.GROWTH: VesselCompartment(
                name="Growth",
                purpose="Investment for expansion",
                capacity=2000.0,
                minimum=0,
                contents=self.state.get("compartments", {}).get("growth", {}).get("contents", 0)
            ),
            Compartment.BUFFER: VesselCompartment(
                name="Buffer",
                purpose="Overflow/temporary",
                capacity=10000.0,  # Large buffer
                minimum=0,
                contents=self.state.get("compartments", {}).get("buffer", {}).get("contents", 0)
            ),
        }

        # Walls
        self.wall = VesselWall(
            integrity=self.state.get("wall", {}).get("integrity", 100.0),
            thickness=1.0,
            material="standard"
        )

        # Valves
        self.inlet = FlowValve(
            name="Main Inlet",
            direction="inlet",
            max_flow=10000.0,  # Can receive large deposits
            open=True,
        )
        self.outlet = FlowValve(
            name="Main Outlet",
            direction="outlet",
            max_flow=1000.0,  # Limited withdrawals
            open=True,
            daily_limit=500.0,  # Max $500/day out
        )

    def _save_state(self):
        """Save vessel state."""
        self.state.update({
            "updated": datetime.now(timezone.utc).isoformat(),
            "compartments": {
                c.value: asdict(comp)
                for c, comp in self.compartments.items()
            },
            "wall": asdict(self.wall),
            "total_contents": self.total_contents,
        })
        VESSEL_STATE.write_text(json.dumps(self.state, indent=2))

    def _log_transaction(self, txn: Dict):
        """Log a vessel transaction."""
        txn["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(VESSEL_LOG, "a") as f:
            f.write(json.dumps(txn) + "\n")

    # ==================== PROPERTIES ====================

    @property
    def total_contents(self) -> float:
        """Total capital in vessel."""
        return sum(c.contents for c in self.compartments.values())

    @property
    def total_available(self) -> float:
        """Total available for withdrawal."""
        return sum(c.available for c in self.compartments.values())

    @property
    def total_capacity(self) -> float:
        """Total vessel capacity."""
        return sum(c.capacity for c in self.compartments.values())

    @property
    def total_space(self) -> float:
        """Total remaining space."""
        return sum(c.space for c in self.compartments.values())

    @property
    def fill_level(self) -> float:
        """Overall fill percentage."""
        if self.total_capacity == 0:
            return 0
        return (self.total_contents / self.total_capacity) * 100

    # ==================== OPERATIONS ====================

    def deposit(self, amount: float, target: Compartment = None) -> Dict:
        """
        Deposit capital into vessel.
        If no target specified, auto-distribute.
        """
        result = {
            "operation": "deposit",
            "requested": amount,
            "deposited": 0.0,
            "distribution": {},
        }

        # Check inlet
        if not self.inlet.can_flow(amount):
            result["error"] = "Inlet blocked or limit exceeded"
            return result

        remaining = amount

        if target:
            # Deposit to specific compartment
            comp = self.compartments[target]
            deposited = comp.deposit(remaining)
            result["distribution"][target.value] = deposited
            result["deposited"] = deposited
        else:
            # Auto-distribute by priority
            priority = [
                Compartment.OPERATING,  # First fill operating
                Compartment.TRADING,    # Then trading
                Compartment.RESERVE,    # Then reserve (if unlocked)
                Compartment.GROWTH,     # Then growth
                Compartment.BUFFER,     # Finally buffer
            ]

            for comp_type in priority:
                if remaining <= 0:
                    break
                comp = self.compartments[comp_type]
                if comp.locked and comp_type != Compartment.RESERVE:
                    continue
                deposited = comp.deposit(remaining)
                if deposited > 0:
                    result["distribution"][comp_type.value] = deposited
                    remaining -= deposited

            result["deposited"] = amount - remaining

        # Update totals
        self.state["total_deposited"] = self.state.get("total_deposited", 0) + result["deposited"]
        self._save_state()
        self._log_transaction(result)

        return result

    def withdraw(self, amount: float, source: Compartment = None) -> Dict:
        """
        Withdraw capital from vessel.
        If no source specified, auto-select.
        """
        result = {
            "operation": "withdraw",
            "requested": amount,
            "withdrawn": 0.0,
            "source": {},
        }

        # Check outlet
        actual_amount = self.outlet.flow(amount)
        if actual_amount == 0:
            result["error"] = "Outlet blocked or daily limit exceeded"
            return result

        remaining = actual_amount

        if source:
            # Withdraw from specific compartment
            comp = self.compartments[source]
            withdrawn = comp.withdraw(remaining)
            result["source"][source.value] = withdrawn
            result["withdrawn"] = withdrawn
        else:
            # Auto-select by priority (inverse of deposit)
            priority = [
                Compartment.BUFFER,     # First from buffer
                Compartment.OPERATING,  # Then operating
                Compartment.TRADING,    # Then trading
                Compartment.GROWTH,     # Then growth
                # Reserve is locked, never auto-withdraw
            ]

            for comp_type in priority:
                if remaining <= 0:
                    break
                comp = self.compartments[comp_type]
                withdrawn = comp.withdraw(remaining)
                if withdrawn > 0:
                    result["source"][comp_type.value] = withdrawn
                    remaining -= withdrawn

            result["withdrawn"] = actual_amount - remaining

        # Update totals
        self.state["total_withdrawn"] = self.state.get("total_withdrawn", 0) + result["withdrawn"]
        self._save_state()
        self._log_transaction(result)

        return result

    def transfer(self, amount: float, from_comp: Compartment, to_comp: Compartment) -> Dict:
        """Transfer between compartments."""
        result = {
            "operation": "transfer",
            "from": from_comp.value,
            "to": to_comp.value,
            "requested": amount,
            "transferred": 0.0,
        }

        source = self.compartments[from_comp]
        dest = self.compartments[to_comp]

        # Check source available
        available = source.available
        if available == 0:
            result["error"] = f"No available funds in {from_comp.value}"
            return result

        # Check dest space
        space = dest.space
        if space == 0:
            result["error"] = f"No space in {to_comp.value}"
            return result

        # Transfer
        actual = min(amount, available, space)
        source.withdraw(actual)
        dest.deposit(actual)
        result["transferred"] = actual

        self._save_state()
        self._log_transaction(result)

        return result

    def sync_from_reality(self):
        """Sync vessel contents from actual financial state."""
        fin_file = STATE_DIR / "financial_state.json"
        if fin_file.exists():
            try:
                data = json.loads(fin_file.read_text())
                balance = data.get("balance", 0)
                positions = data.get("positions_value", 0)

                # Put current balance in operating
                self.compartments[Compartment.OPERATING].contents = balance

                # Put positions value in trading (as pending)
                self.compartments[Compartment.TRADING].contents = positions

                self._save_state()
            except:
                pass

    # ==================== DISPLAY ====================

    def display(self):
        """Display vessel status."""
        print("\n🏺 CAPITAL VESSEL")
        print("═" * 60)

        # Wall status
        wall_status = "🟢 INTACT" if self.wall.integrity > 80 else "🟡 DAMAGED" if self.wall.integrity > 20 else "🔴 BREACHED"
        print(f"Wall: {wall_status} ({self.wall.integrity:.0f}% integrity)")

        # Overall
        print(f"\nTotal: ${self.total_contents:.2f} / ${self.total_capacity:.0f} ({self.fill_level:.1f}% full)")
        print(f"Available: ${self.total_available:.2f}")

        # Compartments
        print("\n┌─ COMPARTMENTS ─────────────────────────────────────────┐")
        for comp_type, comp in self.compartments.items():
            lock_icon = "🔒" if comp.locked else "  "
            bar_len = 20
            filled = int(comp.fill_level / 100 * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)

            print(f"│ {lock_icon} {comp.name:10} [{bar}] ${comp.contents:>8.2f} / ${comp.capacity:.0f}")
            print(f"│    └─ {comp.purpose[:45]}")

        print("└────────────────────────────────────────────────────────┘")

        # Valves
        inlet_status = "🟢 OPEN" if self.inlet.open else "🔴 CLOSED"
        outlet_status = "🟢 OPEN" if self.outlet.open else "🔴 CLOSED"
        print(f"\n↓ Inlet: {inlet_status} (max ${self.inlet.max_flow}/txn)")
        print(f"↑ Outlet: {outlet_status} (max ${self.outlet.max_flow}/txn, ${self.outlet.daily_limit}/day)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="🏺 Capital Vessel")
    parser.add_argument("command", choices=["status", "deposit", "withdraw", "sync"],
                       nargs="?", default="status")
    parser.add_argument("--amount", type=float, help="Amount for deposit/withdraw")
    parser.add_argument("--compartment", choices=["reserve", "operating", "trading", "growth", "buffer"],
                       help="Target compartment")
    args = parser.parse_args()

    vessel = CapitalVessel()

    if args.command == "status":
        vessel.display()
    elif args.command == "sync":
        print("🔄 Syncing from financial state...")
        vessel.sync_from_reality()
        vessel.display()
    elif args.command == "deposit":
        if not args.amount:
            print("Error: --amount required")
            return
        comp = Compartment(args.compartment) if args.compartment else None
        result = vessel.deposit(args.amount, comp)
        print(f"💰 Deposited: ${result['deposited']:.2f}")
        print(f"Distribution: {result['distribution']}")
        vessel.display()
    elif args.command == "withdraw":
        if not args.amount:
            print("Error: --amount required")
            return
        comp = Compartment(args.compartment) if args.compartment else None
        result = vessel.withdraw(args.amount, comp)
        print(f"💸 Withdrawn: ${result['withdrawn']:.2f}")
        print(f"Source: {result['source']}")
        vessel.display()


if __name__ == "__main__":
    main()
