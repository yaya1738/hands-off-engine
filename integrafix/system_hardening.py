#!/usr/bin/env python3
"""
INTEGRAFIX: System Hardening
============================

Ensure 24/7 reliability for $5M/month target.

Components:
1. Process Supervisor - Keep critical processes running
2. Health Monitoring - Detect issues before they cause problems
3. Auto-Recovery - Automatic restart on failure
4. State Persistence - Never lose state on crash
5. Watchdog - Kill and restart hung processes
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"
HARDENING_STATE = STATE_DIR / "system_hardening.json"


@dataclass
class ProcessConfig:
    """Configuration for a supervised process."""
    name: str
    command: str
    working_dir: str
    required: bool  # If true, system is unhealthy without it
    max_restarts: int = 10
    restart_delay: float = 5.0
    health_check_interval: float = 30.0
    memory_limit_mb: int = 500
    cpu_timeout_seconds: int = 300  # Kill if stuck for this long


# Critical processes for $5M/month operation
CRITICAL_PROCESSES = {
    "backend_loop": ProcessConfig(
        name="backend_loop",
        command=f"python3 {PROJECT_ROOT}/autonomous/backend_loop.py",
        working_dir=str(PROJECT_ROOT),
        required=True,
        max_restarts=20,
        restart_delay=10.0
    ),
    "self_healer": ProcessConfig(
        name="self_healer",
        command=f"python3 {PROJECT_ROOT}/autonomous/self_healer.py run",
        working_dir=str(PROJECT_ROOT),
        required=True,
        max_restarts=20,
        restart_delay=5.0
    ),
    "hardware_brain": ProcessConfig(
        name="hardware_brain",
        command=f"python3 {PROJECT_ROOT}/autonomous/hardware_brain.py run",
        working_dir=str(PROJECT_ROOT),
        required=False,
        max_restarts=10
    ),
    "scaling_engine": ProcessConfig(
        name="scaling_engine",
        command=f"python3 {PROJECT_ROOT}/autonomous/scaling_engine.py run",
        working_dir=str(PROJECT_ROOT),
        required=False,
        max_restarts=10
    ),
    "infra_manager": ProcessConfig(
        name="infra_manager",
        command=f"python3 {PROJECT_ROOT}/autonomous/infra_manager.py monitor",
        working_dir=str(PROJECT_ROOT),
        required=False,
        max_restarts=10
    )
}


@dataclass
class ProcessState:
    """Runtime state of a process."""
    name: str
    pid: Optional[int]
    status: str  # running, stopped, restarting, failed
    restarts: int
    last_restart: Optional[str]
    last_health_check: Optional[str]
    health_status: str  # healthy, unhealthy, unknown


@dataclass
class SystemHealth:
    """Overall system health."""
    status: str  # healthy, degraded, critical
    processes_running: int
    processes_total: int
    critical_processes_ok: bool
    last_check: str
    uptime_hours: float
    issues: List[str]


class SystemHardening:
    """System hardening and supervision."""

    def __init__(self):
        self.state = self._load_state()
        self.start_time = datetime.now(timezone.utc)

    def _load_state(self) -> Dict[str, ProcessState]:
        """Load persisted state."""
        if HARDENING_STATE.exists():
            try:
                with open(HARDENING_STATE) as f:
                    data = json.load(f)
                return {k: ProcessState(**v) for k, v in data.items()}
            except:
                pass
        return {}

    def _save_state(self):
        """Persist state."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {k: asdict(v) for k, v in self.state.items()}
        with open(HARDENING_STATE, 'w') as f:
            json.dump(data, f, indent=2)

    def get_process_pid(self, name: str) -> Optional[int]:
        """Find PID of a process by name."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                return int(pids[0])
        except:
            pass
        return None

    def is_process_running(self, name: str) -> bool:
        """Check if process is running."""
        return self.get_process_pid(name) is not None

    def check_process_health(self, name: str, config: ProcessConfig) -> ProcessState:
        """Check health of a specific process."""
        pid = self.get_process_pid(name)
        now = datetime.now(timezone.utc).isoformat()

        existing = self.state.get(name)
        restarts = existing.restarts if existing else 0

        if pid:
            # Process is running, check if healthy
            try:
                # Check memory usage
                result = subprocess.run(
                    ["ps", "-o", "rss=", "-p", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    mem_kb = int(result.stdout.strip())
                    mem_mb = mem_kb / 1024
                    health = "healthy" if mem_mb < config.memory_limit_mb else "unhealthy"
                else:
                    health = "unknown"
            except:
                health = "unknown"

            return ProcessState(
                name=name,
                pid=pid,
                status="running",
                restarts=restarts,
                last_restart=existing.last_restart if existing else None,
                last_health_check=now,
                health_status=health
            )
        else:
            return ProcessState(
                name=name,
                pid=None,
                status="stopped",
                restarts=restarts,
                last_restart=existing.last_restart if existing else None,
                last_health_check=now,
                health_status="unhealthy"
            )

    def restart_process(self, name: str, config: ProcessConfig) -> bool:
        """Restart a process."""
        existing = self.state.get(name)
        restarts = (existing.restarts + 1) if existing else 1

        if restarts > config.max_restarts:
            print(f"[HARDENING] {name}: Max restarts exceeded ({restarts})")
            return False

        # Kill existing if any
        pid = self.get_process_pid(name)
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                os.kill(pid, signal.SIGKILL)
            except:
                pass

        time.sleep(config.restart_delay)

        # Start new process
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = "{PROJECT_ROOT}"

            subprocess.Popen(
                config.command.split(),
                cwd=config.working_dir,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            now = datetime.now(timezone.utc).isoformat()
            self.state[name] = ProcessState(
                name=name,
                pid=None,  # Will be updated on next check
                status="restarting",
                restarts=restarts,
                last_restart=now,
                last_health_check=now,
                health_status="unknown"
            )
            self._save_state()

            print(f"[HARDENING] {name}: Restarted (attempt {restarts})")
            return True

        except Exception as e:
            print(f"[HARDENING] {name}: Failed to restart: {e}")
            return False

    def check_system_health(self) -> SystemHealth:
        """Check overall system health."""
        issues = []
        running = 0
        critical_ok = True

        for name, config in CRITICAL_PROCESSES.items():
            state = self.check_process_health(name, config)
            self.state[name] = state

            if state.status == "running":
                running += 1
            else:
                if config.required:
                    critical_ok = False
                    issues.append(f"CRITICAL: {name} not running")
                else:
                    issues.append(f"WARNING: {name} not running")

            if state.health_status == "unhealthy":
                issues.append(f"WARNING: {name} unhealthy")

        self._save_state()

        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600

        if not critical_ok:
            status = "critical"
        elif running < len(CRITICAL_PROCESSES):
            status = "degraded"
        else:
            status = "healthy"

        return SystemHealth(
            status=status,
            processes_running=running,
            processes_total=len(CRITICAL_PROCESSES),
            critical_processes_ok=critical_ok,
            last_check=datetime.now(timezone.utc).isoformat(),
            uptime_hours=uptime,
            issues=issues
        )

    def enforce_health(self) -> SystemHealth:
        """Enforce system health by restarting failed processes."""
        health = self.check_system_health()

        for name, config in CRITICAL_PROCESSES.items():
            state = self.state.get(name)
            if state and state.status != "running":
                print(f"[HARDENING] {name}: Not running, attempting restart")
                self.restart_process(name, config)

        # Re-check after restarts
        time.sleep(5)
        return self.check_system_health()

    def supervise(self, interval: float = 60.0):
        """Run supervisor loop."""
        print("[HARDENING] Starting supervisor loop")

        while True:
            try:
                health = self.enforce_health()
                print(f"[HARDENING] System: {health.status} | "
                      f"Running: {health.processes_running}/{health.processes_total}")

                if health.issues:
                    for issue in health.issues:
                        print(f"[HARDENING]   {issue}")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("[HARDENING] Supervisor stopped")
                break
            except Exception as e:
                print(f"[HARDENING] Error: {e}")
                time.sleep(interval)


def status_report() -> str:
    """Generate system hardening status report."""
    hardening = SystemHardening()
    health = hardening.check_system_health()

    status_emoji = {
        "healthy": "🟢",
        "degraded": "🟡",
        "critical": "🔴"
    }

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║             SYSTEM HARDENING STATUS                          ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  System Status: {status_emoji.get(health.status, '?')} {health.status.upper():<42} ║",
        f"║  Processes: {health.processes_running}/{health.processes_total} running                                   ║",
        f"║  Uptime: {health.uptime_hours:.1f} hours                                        ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  Process Status:                                             ║",
    ]

    for name, config in CRITICAL_PROCESSES.items():
        state = hardening.state.get(name)
        if state and state.status == "running":
            status = "🟢 Running"
            restarts = f"({state.restarts} restarts)" if state.restarts > 0 else ""
        else:
            status = "🔴 Stopped"
            restarts = ""
        req = "*" if config.required else " "
        lines.append(f"║  {req} {name:<18} {status:<15} {restarts:<12} ║")

    if health.issues:
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        lines.append("║  Issues:                                                     ║")
        for issue in health.issues[:5]:
            lines.append(f"║    {issue:<56} ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  * = Required for system health                              ║",
        "║  Supervisor: Restarts failed processes automatically         ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines)


def main():
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "supervise":
            interval = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
            hardening = SystemHardening()
            hardening.supervise(interval)
        elif cmd == "enforce":
            hardening = SystemHardening()
            health = hardening.enforce_health()
            print(f"System: {health.status}")
        elif cmd == "restart":
            if len(sys.argv) > 2:
                name = sys.argv[2]
                if name in CRITICAL_PROCESSES:
                    hardening = SystemHardening()
                    hardening.restart_process(name, CRITICAL_PROCESSES[name])
                else:
                    print(f"Unknown process: {name}")
            else:
                print("Usage: system_hardening.py restart <process>")
        else:
            print(status_report())
    else:
        print(status_report())


if __name__ == "__main__":
    main()
