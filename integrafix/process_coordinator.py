#!/usr/bin/env python3
"""
INTEGRAFIX: Process Coordinator
===============================

PROBLEM SOLVED:
Three processes run independently with no coordination:
- backend_loop: Reads state files but can't signal others
- hardware_brain: Makes node decisions without knowing scaling plans
- scaling_engine: Provisions nodes without knowing brain constraints

SOLUTION:
A coordination layer that:
1. Registers all processes
2. Manages locks for shared resources (nodes)
3. Signals between processes
4. Prevents race conditions
5. Provides bidirectional state awareness

This file CREATES coordination where none existed.
"""

import json
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import fcntl

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
COORDINATION_STATE = STATE_DIR / "process_coordination.json"
COORDINATION_LOCK = STATE_DIR / ".coordination.lock"


class ProcessState(Enum):
    """State of a registered process."""
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    EXECUTING = "executing"
    STOPPING = "stopping"
    DEAD = "dead"


class LockType(Enum):
    """Types of resource locks."""
    EXCLUSIVE = "exclusive"     # Only one process can hold
    SHARED = "shared"           # Multiple readers, exclusive writers
    INTENT = "intent"           # Signal intent without blocking


@dataclass
class ProcessInfo:
    """Information about a registered process."""
    name: str
    pid: Optional[int]
    state: ProcessState
    last_heartbeat: str
    current_action: Optional[str] = None
    waiting_on: List[str] = field(default_factory=list)
    holding_locks: List[str] = field(default_factory=list)
    pending_signals: List[Dict] = field(default_factory=list)
    state_file: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)


@dataclass
class ResourceLock:
    """A lock on a shared resource."""
    resource: str
    lock_type: LockType
    holder: str                  # Process name
    acquired_at: str
    timeout_sec: int = 60
    reason: str = ""


@dataclass
class Signal:
    """A signal between processes."""
    id: str
    from_process: str
    to_process: str
    signal_type: str             # "request", "response", "event", "command"
    payload: Dict
    created_at: str
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    response: Optional[Dict] = None


class ProcessCoordinator:
    """
    Coordinate multiple processes to prevent race conditions
    and enable bidirectional communication.

    This is the INTEGRATION LAYER that was missing.
    """

    def __init__(self):
        self.processes: Dict[str, ProcessInfo] = {}
        self.locks: Dict[str, ResourceLock] = {}
        self.signals: Dict[str, Signal] = {}
        self._lock_file = None
        self._load_state()

    def _get_file_lock(self):
        """Get file lock for atomic state operations."""
        if self._lock_file is None:
            self._lock_file = open(COORDINATION_LOCK, 'w')
        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX)

    def _release_file_lock(self):
        """Release file lock."""
        if self._lock_file:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)

    def _load_state(self):
        """Load coordination state from file."""
        if COORDINATION_STATE.exists():
            try:
                self._get_file_lock()
                with open(COORDINATION_STATE) as f:
                    data = json.load(f)

                # Rebuild processes
                for name, pdata in data.get("processes", {}).items():
                    pdata["state"] = ProcessState(pdata.get("state", "unknown"))
                    self.processes[name] = ProcessInfo(**pdata)

                # Rebuild locks
                for resource, ldata in data.get("locks", {}).items():
                    ldata["lock_type"] = LockType(ldata.get("lock_type", "exclusive"))
                    self.locks[resource] = ResourceLock(**ldata)

                # Rebuild signals
                for sig_id, sdata in data.get("signals", {}).items():
                    self.signals[sig_id] = Signal(**sdata)

            finally:
                self._release_file_lock()

    def _save_state(self):
        """Save coordination state to file."""
        try:
            self._get_file_lock()

            # Serialize
            data = {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "processes": {},
                "locks": {},
                "signals": {},
            }

            for name, proc in self.processes.items():
                pdict = asdict(proc)
                pdict["state"] = proc.state.value
                data["processes"][name] = pdict

            for resource, lock in self.locks.items():
                ldict = asdict(lock)
                ldict["lock_type"] = lock.lock_type.value
                data["locks"][resource] = ldict

            for sig_id, sig in self.signals.items():
                data["signals"][sig_id] = asdict(sig)

            with open(COORDINATION_STATE, 'w') as f:
                json.dump(data, f, indent=2)

        finally:
            self._release_file_lock()

    # ==================== PROCESS REGISTRATION ====================

    def register(
        self,
        name: str,
        pid: Optional[int] = None,
        state_file: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
    ) -> ProcessInfo:
        """
        Register a process with the coordinator.

        Args:
            name: Unique process name (e.g., "backend_loop")
            pid: Process ID (optional, for monitoring)
            state_file: Path to process state file (for bidirectional awareness)
            capabilities: What this process can do
        """
        proc = ProcessInfo(
            name=name,
            pid=pid or os.getpid(),
            state=ProcessState.STARTING,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            state_file=state_file,
            capabilities=capabilities or [],
        )

        self.processes[name] = proc
        self._save_state()
        return proc

    def heartbeat(self, name: str, state: ProcessState = None, action: str = None):
        """
        Send heartbeat from a process.

        Args:
            name: Process name
            state: New state (optional)
            action: What the process is currently doing
        """
        if name not in self.processes:
            self.register(name)

        proc = self.processes[name]
        proc.last_heartbeat = datetime.now(timezone.utc).isoformat()
        if state:
            proc.state = state
        if action:
            proc.current_action = action

        self._save_state()

    def get_process_state(self, name: str) -> Optional[ProcessInfo]:
        """Get state of a process."""
        return self.processes.get(name)

    def is_alive(self, name: str, max_age_sec: int = 120) -> bool:
        """Check if a process is alive (recent heartbeat)."""
        proc = self.processes.get(name)
        if not proc:
            return False

        last = datetime.fromisoformat(proc.last_heartbeat.replace('Z', '+00:00'))
        age = (datetime.now(timezone.utc) - last).total_seconds()
        return age < max_age_sec

    # ==================== RESOURCE LOCKING ====================

    def acquire_lock(
        self,
        resource: str,
        process: str,
        lock_type: LockType = LockType.EXCLUSIVE,
        timeout_sec: int = 60,
        reason: str = "",
        wait: bool = True,
        max_wait_sec: int = 30,
    ) -> bool:
        """
        Acquire a lock on a resource.

        Args:
            resource: Resource name (e.g., "node_provisioning")
            process: Process requesting the lock
            lock_type: Type of lock
            timeout_sec: How long the lock is valid
            reason: Why the lock is needed
            wait: Whether to wait if locked
            max_wait_sec: How long to wait
        """
        start = time.time()

        while True:
            # Check if resource is locked
            existing = self.locks.get(resource)

            if existing:
                # Check if lock has expired
                acquired = datetime.fromisoformat(existing.acquired_at.replace('Z', '+00:00'))
                age = (datetime.now(timezone.utc) - acquired).total_seconds()

                if age > existing.timeout_sec:
                    # Expired - release it
                    del self.locks[resource]
                    existing = None
                elif existing.holder == process:
                    # Already hold this lock
                    return True
                elif not wait:
                    return False
                else:
                    # Wait
                    if time.time() - start > max_wait_sec:
                        return False
                    time.sleep(0.1)
                    continue

            # Acquire lock
            lock = ResourceLock(
                resource=resource,
                lock_type=lock_type,
                holder=process,
                acquired_at=datetime.now(timezone.utc).isoformat(),
                timeout_sec=timeout_sec,
                reason=reason,
            )
            self.locks[resource] = lock

            # Update process info
            if process in self.processes:
                self.processes[process].holding_locks.append(resource)

            self._save_state()
            return True

    def release_lock(self, resource: str, process: str) -> bool:
        """Release a lock on a resource."""
        lock = self.locks.get(resource)
        if not lock:
            return True  # Already released

        if lock.holder != process:
            return False  # Can't release someone else's lock

        del self.locks[resource]

        # Update process info
        if process in self.processes:
            if resource in self.processes[process].holding_locks:
                self.processes[process].holding_locks.remove(resource)

        self._save_state()
        return True

    def check_conflict(self, process: str, action: str) -> Optional[str]:
        """
        Check if an action would conflict with another process.

        Args:
            process: Process wanting to act
            action: What it wants to do

        Returns:
            None if no conflict, else description of conflict
        """
        # Define conflicting actions
        conflicts = {
            "provision_node": ["remove_node", "heal_node"],
            "remove_node": ["provision_node", "heal_node"],
            "heal_node": ["provision_node", "remove_node"],
            "scale_up": ["scale_down", "heal"],
            "scale_down": ["scale_up", "heal"],
        }

        # Check if any other process is doing a conflicting action
        for other_name, other_proc in self.processes.items():
            if other_name == process:
                continue

            if other_proc.current_action in conflicts.get(action, []):
                return f"{other_name} is doing {other_proc.current_action}, conflicts with {action}"

        return None

    # ==================== SIGNALING ====================

    def send_signal(
        self,
        from_process: str,
        to_process: str,
        signal_type: str,
        payload: Dict,
    ) -> Signal:
        """
        Send a signal to another process.

        Args:
            from_process: Sender
            to_process: Recipient
            signal_type: "request", "response", "event", "command"
            payload: Signal data
        """
        sig = Signal(
            id=f"sig_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            from_process=from_process,
            to_process=to_process,
            signal_type=signal_type,
            payload=payload,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self.signals[sig.id] = sig

        # Add to recipient's pending signals
        if to_process in self.processes:
            self.processes[to_process].pending_signals.append({
                "id": sig.id,
                "type": signal_type,
                "from": from_process,
            })

        self._save_state()
        return sig

    def get_pending_signals(self, process: str) -> List[Signal]:
        """Get all pending signals for a process."""
        pending = []
        for sig in self.signals.values():
            if sig.to_process == process and not sig.acknowledged:
                pending.append(sig)
        return pending

    def acknowledge_signal(self, signal_id: str, response: Optional[Dict] = None) -> bool:
        """Acknowledge a signal."""
        sig = self.signals.get(signal_id)
        if not sig:
            return False

        sig.acknowledged = True
        sig.acknowledged_at = datetime.now(timezone.utc).isoformat()
        sig.response = response

        self._save_state()
        return True

    def request_and_wait(
        self,
        from_process: str,
        to_process: str,
        request: Dict,
        timeout_sec: int = 30,
    ) -> Optional[Dict]:
        """
        Send a request and wait for response.

        Args:
            from_process: Requester
            to_process: Responder
            request: Request payload
            timeout_sec: How long to wait

        Returns:
            Response payload, or None if timeout
        """
        sig = self.send_signal(from_process, to_process, "request", request)

        start = time.time()
        while time.time() - start < timeout_sec:
            # Reload state to get updates
            self._load_state()

            updated_sig = self.signals.get(sig.id)
            if updated_sig and updated_sig.acknowledged:
                return updated_sig.response

            time.sleep(0.1)

        return None

    # ==================== BIDIRECTIONAL STATE ====================

    def read_all_states(self) -> Dict[str, Dict]:
        """
        Read state files from all registered processes.

        This enables true bidirectional awareness.
        """
        states = {}

        for name, proc in self.processes.items():
            if proc.state_file and Path(proc.state_file).exists():
                try:
                    with open(proc.state_file) as f:
                        states[name] = json.load(f)
                except Exception:
                    states[name] = {"error": "failed to read"}
            else:
                states[name] = {"error": "no state file"}

        return states

    def broadcast_state_update(self, from_process: str, update: Dict):
        """
        Broadcast a state update to all other processes.

        Args:
            from_process: Process that changed
            update: What changed
        """
        for name in self.processes:
            if name != from_process:
                self.send_signal(
                    from_process=from_process,
                    to_process=name,
                    signal_type="event",
                    payload={
                        "event": "state_update",
                        "update": update,
                    }
                )

    # ==================== COORDINATION PROTOCOLS ====================

    def coordinate_node_operation(
        self,
        process: str,
        operation: str,       # "provision", "remove", "heal"
        node_id: str,
    ) -> Dict:
        """
        Coordinate a node operation across processes.

        Ensures hardware_brain and scaling_engine don't conflict.
        """
        resource = f"node:{node_id}"

        # Check for conflicts
        conflict = self.check_conflict(process, f"{operation}_node")
        if conflict:
            return {"success": False, "error": conflict}

        # Try to acquire lock
        got_lock = self.acquire_lock(
            resource=resource,
            process=process,
            reason=f"{operation} node {node_id}",
            wait=True,
            max_wait_sec=10,
        )

        if not got_lock:
            return {"success": False, "error": f"Could not acquire lock on {resource}"}

        # Signal intent to other processes
        for other_name in ["hardware_brain", "scaling_engine"]:
            if other_name != process and other_name in self.processes:
                self.send_signal(
                    from_process=process,
                    to_process=other_name,
                    signal_type="event",
                    payload={
                        "event": "node_operation_starting",
                        "operation": operation,
                        "node_id": node_id,
                    }
                )

        return {
            "success": True,
            "lock_acquired": resource,
            "release_when_done": lambda: self.release_lock(resource, process),
        }

    def wait_for_process(
        self,
        process: str,
        expected_state: ProcessState,
        timeout_sec: int = 30,
    ) -> bool:
        """
        Wait for a process to reach an expected state.

        Useful for sequencing operations.
        """
        start = time.time()
        while time.time() - start < timeout_sec:
            self._load_state()
            proc = self.processes.get(process)
            if proc and proc.state == expected_state:
                return True
            time.sleep(0.1)
        return False

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get full coordinator status."""
        return {
            "processes": {
                name: {
                    "state": proc.state.value,
                    "alive": self.is_alive(name),
                    "action": proc.current_action,
                    "locks": proc.holding_locks,
                    "pending_signals": len(proc.pending_signals),
                }
                for name, proc in self.processes.items()
            },
            "locks": {
                resource: {
                    "holder": lock.holder,
                    "type": lock.lock_type.value,
                    "reason": lock.reason,
                }
                for resource, lock in self.locks.items()
            },
            "pending_signals": sum(
                1 for s in self.signals.values() if not s.acknowledged
            ),
            "total_signals": len(self.signals),
        }


# Singleton instance
_coordinator = None

def get_coordinator() -> ProcessCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = ProcessCoordinator()
    return _coordinator


def main():
    """Test the process coordinator."""
    coord = get_coordinator()

    # Register processes
    coord.register(
        "backend_loop",
        state_file=str(STATE_DIR / "backend_loop.json"),
        capabilities=["trading", "ai_core", "knowledge"],
    )
    coord.register(
        "hardware_brain",
        state_file=str(STATE_DIR / "brain_state.json"),
        capabilities=["node_provision", "node_heal", "node_remove"],
    )
    coord.register(
        "scaling_engine",
        state_file=str(STATE_DIR / "scaling_state.json"),
        capabilities=["scale_up", "scale_down"],
    )

    print("=" * 70)
    print("INTEGRAFIX: Process Coordinator Test")
    print("=" * 70)
    print()

    # Test coordination
    print("Testing node operation coordination...")
    result = coord.coordinate_node_operation(
        process="scaling_engine",
        operation="provision",
        node_id="test-node-1",
    )
    print(f"  Result: {result['success']}")
    if result['success']:
        print(f"  Lock acquired: {result['lock_acquired']}")
        result['release_when_done']()
        print("  Lock released")

    print()
    print("Testing signal between processes...")
    sig = coord.send_signal(
        from_process="backend_loop",
        to_process="hardware_brain",
        signal_type="request",
        payload={"action": "get_health"},
    )
    print(f"  Signal sent: {sig.id}")

    # Get pending for hardware_brain
    pending = coord.get_pending_signals("hardware_brain")
    print(f"  Hardware brain has {len(pending)} pending signals")

    print()
    print("Full status:")
    status = coord.status()
    print(json.dumps(status, indent=2))

    return coord


if __name__ == "__main__":
    main()
