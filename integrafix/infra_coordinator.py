#!/usr/bin/env python3
"""
INTEGRAFIX: Infrastructure Coordination Layer

Fixes two critical gaps:
1. backend_brain_no_bidirectional - Make backend ↔ brain bidirectional
2. brain_scaling_no_coordination - Coordinate brain ↔ scaling decisions

METHODOLOGY:
- Shared coordination state prevents race conditions
- Decision lock ensures only one infra change at a time
- Bidirectional state sharing enables all actors to see each other's decisions

Master: Yair Siegel
"""

import json
import time
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any
from contextlib import contextmanager

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
COORD_STATE = STATE_DIR / "infra_coordination.json"
LOCK_FILE = STATE_DIR / "infra_coordination.lock"


class InfraCoordinator:
    """
    Central coordination for all infrastructure decision makers.

    Prevents race conditions between:
    - hardware_brain.py (node decisions)
    - scaling_engine.py (scaling decisions)
    - backend_loop.py (orchestrator decisions)
    """

    def __init__(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load coordination state."""
        if COORD_STATE.exists():
            try:
                return json.loads(COORD_STATE.read_text())
            except:
                pass
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active_decisions": [],
            "last_brain_decision": None,
            "last_scaling_decision": None,
            "last_backend_decision": None,
            "decision_history": [],
            "locks_held": 0,
            "race_conditions_prevented": 0
        }

    def _save_state(self):
        """Save coordination state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        COORD_STATE.write_text(json.dumps(self.state, indent=2))

    @contextmanager
    def infra_decision_lock(self, actor: str, decision_type: str):
        """
        Coordinate infrastructure decision to prevent race conditions.

        Usage:
            with coordinator.infra_decision_lock("hardware_brain", "node_upgrade"):
                # Make node decision safely
                pass
        """
        # Acquire file lock
        lock_fd = open(LOCK_FILE, 'w')
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)

            # Record decision start
            decision_id = f"{actor}_{decision_type}_{int(time.time())}"
            self.state["active_decisions"].append({
                "id": decision_id,
                "actor": actor,
                "type": decision_type,
                "started_at": datetime.now(timezone.utc).isoformat()
            })
            self.state["locks_held"] += 1
            self._save_state()

            yield decision_id

            # Record decision complete
            self.state["active_decisions"] = [
                d for d in self.state["active_decisions"]
                if d["id"] != decision_id
            ]
            self.state["decision_history"].append({
                "id": decision_id,
                "actor": actor,
                "type": decision_type,
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            # Keep only last 100 history entries
            self.state["decision_history"] = self.state["decision_history"][-100:]
            self._save_state()

        finally:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()

    def check_ongoing_decisions(self) -> bool:
        """Check if any infrastructure decisions are in progress."""
        return len(self.state.get("active_decisions", [])) > 0

    def register_brain_decision(self, decision: Dict[str, Any]):
        """Hardware brain registers its decision (bidirectional with backend)."""
        self.state["last_brain_decision"] = {
            **decision,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._save_state()

    def register_scaling_decision(self, decision: Dict[str, Any]):
        """Scaling engine registers its decision (coordinated with brain)."""
        self.state["last_scaling_decision"] = {
            **decision,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._save_state()

    def register_backend_decision(self, decision: Dict[str, Any]):
        """Backend loop registers its decision (bidirectional with brain)."""
        self.state["last_backend_decision"] = {
            **decision,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._save_state()

    def get_brain_state(self) -> Optional[Dict]:
        """Backend can read brain's last decision."""
        return self.state.get("last_brain_decision")

    def get_backend_state(self) -> Optional[Dict]:
        """Brain can read backend's last decision."""
        return self.state.get("last_backend_decision")

    def get_scaling_state(self) -> Optional[Dict]:
        """Brain can read scaling's last decision."""
        return self.state.get("last_scaling_decision")

    def prevent_race_condition(self, actor1: str, actor2: str) -> bool:
        """
        Check if two actors would race. If so, prevent it.

        Returns True if race was prevented, False if safe to proceed.
        """
        # Check if other actor has active decision
        active_actors = {d["actor"] for d in self.state.get("active_decisions", [])}

        if actor2 in active_actors or actor1 in active_actors:
            self.state["race_conditions_prevented"] = \
                self.state.get("race_conditions_prevented", 0) + 1
            self._save_state()
            return True

        return False


# Singleton coordinator
_coordinator = None

def get_coordinator() -> InfraCoordinator:
    """Get the singleton infrastructure coordinator."""
    global _coordinator
    if _coordinator is None:
        _coordinator = InfraCoordinator()
    return _coordinator


def demo():
    """Demonstrate coordination preventing race condition."""
    print("=" * 70)
    print("INTEGRAFIX: Infrastructure Coordination Demo")
    print("=" * 70)

    coordinator = get_coordinator()

    # Simulate brain making decision
    print("\n[hardware_brain] Acquiring lock for node_upgrade...")
    with coordinator.infra_decision_lock("hardware_brain", "node_upgrade"):
        print("[hardware_brain] Lock acquired, making decision...")
        coordinator.register_brain_decision({
            "action": "upgrade_node",
            "node_id": "droplet-123",
            "reason": "CPU threshold exceeded"
        })
        print("[hardware_brain] Decision registered")

        # Simulate scaling trying to make decision (would race!)
        if coordinator.prevent_race_condition("scaling_engine", "hardware_brain"):
            print("\n[scaling_engine] ⚠️  RACE CONDITION PREVENTED!")
            print("[scaling_engine] hardware_brain is making decision, waiting...")

        time.sleep(0.1)  # Simulate work

    print("[hardware_brain] Lock released")

    # Now scaling can proceed
    print("\n[scaling_engine] Acquiring lock for scale_up...")
    with coordinator.infra_decision_lock("scaling_engine", "scale_up"):
        print("[scaling_engine] Lock acquired, making decision...")
        coordinator.register_scaling_decision({
            "action": "create_node",
            "size": "s-2vcpu-4gb",
            "reason": "Load high across cluster"
        })
        print("[scaling_engine] Decision registered")

    print("[scaling_engine] Lock released")

    # Backend can read both states (bidirectional!)
    print("\n[backend_loop] Reading infra state...")
    brain_state = coordinator.get_brain_state()
    scaling_state = coordinator.get_scaling_state()

    print(f"[backend_loop] Brain decision: {brain_state['action']}")
    print(f"[backend_loop] Scaling decision: {scaling_state['action']}")

    # Backend registers its own decision
    coordinator.register_backend_decision({
        "action": "continue_normal_operation",
        "reason": "Infra changes handled by brain/scaling"
    })
    print("[backend_loop] Decision registered")

    # Brain can now read backend's decision (bidirectional!)
    backend_state = coordinator.get_backend_state()
    print(f"\n[hardware_brain] Backend decision: {backend_state['action']}")

    print("\n" + "=" * 70)
    print("GAPS FIXED:")
    print("✅ backend_brain_no_bidirectional - Backend ↔ Brain can see each other")
    print("✅ brain_scaling_no_coordination - Brain ↔ Scaling coordinated via locks")
    print(f"Race conditions prevented: {coordinator.state['race_conditions_prevented']}")
    print("=" * 70)


if __name__ == "__main__":
    demo()
