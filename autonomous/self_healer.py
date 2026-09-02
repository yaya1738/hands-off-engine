#!/usr/bin/env python3
"""Read-only legacy self-healer facade.

Health observation remains available, but remediation is deliberately fail-closed.
All process/service/state remediation requests must enter FactoryAuthorityGateway.
This module is not an execution authority.
"""

import json
import os
import signal
import socket
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
LOG_DIR = BASE_DIR / "logs"
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ProcessGuard:
    name: str
    command: str
    working_dir: str = str(BASE_DIR)
    restart_delay_sec: int = 10
    max_restarts_per_hour: int = 5
    critical: bool = True
    code_file: str = ""


@dataclass
class HealingAction:
    timestamp: str
    action_type: str
    target: str
    reason: str
    success: bool
    details: Dict = field(default_factory=dict)


class SelfHealer:
    """Observe health and submit governed remediation requests only."""

    GUARDED_PROCESSES = [
        ProcessGuard(
            name="backend-loop",
            command="python3 /data/data/com.termux/files/home/hands-off-engine-forensic-jan9/autonomous/backend_loop.py",
            critical=True,
            restart_delay_sec=5,
            max_restarts_per_hour=10,
            code_file=str(BASE_DIR) + "/autonomous/backend_loop.py",
        ),
        ProcessGuard(
            name="hardware-brain",
            command="python3 /data/data/com.termux/files/home/hands-off-engine-forensic-jan9/autonomous/hardware_brain.py run",
            critical=True,
        ),
        ProcessGuard(
            name="scaling-engine",
            command="python3 /data/data/com.termux/files/home/hands-off-engine-forensic-jan9/autonomous/scaling_engine.py run",
            critical=True,
        ),
        ProcessGuard(
            name="infra-monitor",
            command="python3 /data/data/com.termux/files/home/hands-off-engine-forensic-jan9/autonomous/infra_manager.py monitor",
            critical=True,
        ),
    ]

    PROTECTED_SERVICES = [
        "hands-off-autonomous.service",
        "infra-monitor.service",
        "self-healing-agent.service",
    ]

    def __init__(self):
        self.hostname = socket.gethostname()
        self.start_time = datetime.utcnow()
        self.healing_history: List[HealingAction] = []
        self.restart_counts: Dict[str, List[datetime]] = {}
        self._shutdown = threading.Event()
        self._setup_signal_handlers()
        self._log("Self-Healer initialized", {"hostname": self.hostname})

    def _setup_signal_handlers(self):
        """Configure process-local signal handling without spawning or killing processes."""
        try:
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, self._graceful_shutdown_handler)
            signal.signal(signal.SIGINT, self._graceful_shutdown_handler)
        except (OSError, RuntimeError):
            pass

    def _graceful_shutdown_handler(self, signum, frame):
        self._log(f"Received signal {signum} - initiating graceful shutdown")
        self._shutdown.set()
        self._save_state()

    def _log(self, message: str, data: Dict = None, level: str = "info"):
        timestamp = datetime.utcnow().isoformat()
        log_line = f"[{timestamp}] [HEALER] [{level.upper()}] {message}"
        if data:
            log_line += f" | {json.dumps(data)}"
        print(log_line)
        try:
            with open(LOG_DIR / "self_healer.log", "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except OSError:
            pass

    def _save_state(self):
        state = {
            "last_save": datetime.utcnow().isoformat(),
            "hostname": self.hostname,
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            "healing_actions": [{**vars(a)} for a in self.healing_history[-100:]],
            "restart_counts": {k: [t.isoformat() for t in v] for k, v in self.restart_counts.items()},
        }
        try:
            (STATE_DIR / "self_healer_state.json").write_text(
                json.dumps(state, indent=2, default=str), encoding="utf-8"
            )
        except OSError:
            pass

    def check_process_running(self, process: ProcessGuard) -> Tuple[bool, Optional[int]]:
        """Observe process state from /proc without executing a command."""
        try:
            target = process.command.split()[1] if len(process.command.split()) > 1 else process.command
            for entry in Path("/proc").iterdir():
                if not entry.name.isdigit():
                    continue
                try:
                    cmdline = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode(errors="ignore")
                    if target in cmdline:
                        return True, int(entry.name)
                except (OSError, ValueError):
                    continue
        except OSError:
            pass
        return False, None

    def check_code_stale(self, process: ProcessGuard, pid: int) -> bool:
        if not process.code_file:
            return False
        try:
            code_path = Path(process.code_file)
            stat_path = Path(f"/proc/{pid}/stat")
            if not code_path.exists() or not stat_path.exists():
                return False
            # Linux process start time is deliberately treated as observational only.
            uptime = float(Path("/proc/uptime").read_text().split()[0])
            start_ticks = int(stat_path.read_text().split()[21])
            ticks = os.sysconf("SC_CLK_TCK")
            process_start = time.time() - uptime + start_ticks / ticks
            return code_path.stat().st_mtime > process_start
        except (OSError, ValueError, IndexError):
            return False

    def _can_restart_process(self, process: ProcessGuard) -> bool:
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        recent = [t for t in self.restart_counts.get(process.name, []) if t > hour_ago]
        self.restart_counts[process.name] = recent
        return len(recent) < process.max_restarts_per_hour

    def _request_governed_healing(self, target: str, reason: str, action: str) -> bool:
        """Submit a remediation intent to the sole authority; never execute it here."""
        self._log(
            "Legacy self-healing mutation blocked; submitting governed request",
            {"target": target, "action": action, "reason": reason},
            level="warning",
        )
        try:
            from ai.factory.authority_gateway import FactoryAuthorityGateway
            gateway = FactoryAuthorityGateway()
            gateway.submit_development_request(
                f"Self-healing request: {action} target={target} reason={reason}",
                "legacy_self_healer_governed_request",
            )
            self.healing_history.append(
                HealingAction(
                    timestamp=datetime.utcnow().isoformat(),
                    action_type="governed_request",
                    target=target,
                    reason=reason,
                    success=True,
                    details={"action": action, "authority": "FactoryAuthorityGateway"},
                )
            )
            return True
        except Exception as exc:
            self._log(f"Governed healing request failed closed: {exc}", level="error")
            self.healing_history.append(
                HealingAction(
                    timestamp=datetime.utcnow().isoformat(),
                    action_type="governed_request",
                    target=target,
                    reason=reason,
                    success=False,
                    details={"action": action, "authority": "FactoryAuthorityGateway", "error": str(exc)},
                )
            )
            return False

    def restart_process(self, process: ProcessGuard) -> bool:
        """Compatibility entrypoint: never kills or starts a process directly."""
        if not self._can_restart_process(process):
            self._log(f"Rate limit reached for {process.name}", level="warning")
            return False
        return self._request_governed_healing(process.name, "process not running or stale", "restart_process")

    def check_and_heal_processes(self) -> Dict:
        results = {"timestamp": datetime.utcnow().isoformat(), "processes": {}, "actions_taken": []}
        for process in self.GUARDED_PROCESSES:
            running, pid = self.check_process_running(process)
            status = {"running": running, "pid": pid, "critical": process.critical}
            if not running:
                status["action"] = "governed_request_pending"
                if self.restart_process(process):
                    results["actions_taken"].append(f"Requested governed restart for {process.name}")
            elif pid and self.check_code_stale(process, pid):
                status["stale"] = True
                status["action"] = "governed_request_pending"
                if self.restart_process(process):
                    results["actions_taken"].append(f"Requested governed restart for {process.name} (stale code)")
            results["processes"][process.name] = status
        return results

    def check_service_status(self, service_name: str) -> Tuple[bool, str]:
        """Observe systemd state only when exposed through a local status file; otherwise unknown."""
        unit = Path("/run/systemd/system") / service_name
        if unit.exists():
            return True, "present"
        return False, "unknown"

    def ensure_services_running(self) -> Dict:
        """Compatibility entrypoint: request governance, never invoke systemctl."""
        results = {}
        for service in self.PROTECTED_SERVICES:
            active, status = self.check_service_status(service)
            results[service] = {"active": active, "status": status}
            if not active and status != "unknown":
                results[service]["action"] = "governed_request_pending"
                self._request_governed_healing(service, f"service status={status}", "start_service")
        return results

    def check_state_files(self) -> Dict:
        """Validate state files without repairing, renaming, deleting, or overwriting them."""
        results = {}
        for filename in ["brain_state.json", "scaling_state.json", "infra_state.json", "cluster_state.json"]:
            filepath = STATE_DIR / filename
            if not filepath.exists():
                results[filename] = {"exists": False, "action": "governed_repair_required"}
                continue
            try:
                content = filepath.read_text(encoding="utf-8")
                json.loads(content)
                results[filename] = {"exists": True, "valid": bool(content.strip())}
            except (OSError, json.JSONDecodeError) as exc:
                results[filename] = {"exists": True, "valid": False, "action": "governed_repair_required", "error": str(exc)}
        return results

    def check_disk_space(self) -> Dict:
        try:
            total, used, free = os.statvfs("/").f_blocks * os.statvfs("/").f_frsize, 0, 0
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = total - free
            pct = int((used / total) * 100) if total else 0
            return {"total": total, "used": used, "available": free, "used_pct": pct, "action": "governed_cleanup_required" if pct > 90 else None}
        except OSError as exc:
            return {"error": str(exc)}

    def _cleanup_old_logs(self):
        """Compatibility entrypoint: log cleanup requires governed authority."""
        return self._request_governed_healing(str(LOG_DIR), "disk pressure", "cleanup_logs")

    def check_network(self) -> Dict:
        import socket as _socket
        results = {}
        for host, port in [("api.digitalocean.com", 443), ("github.com", 443), ("api.openai.com", 443)]:
            try:
                with _socket.create_connection((host, port), timeout=5):
                    results[host] = True
            except OSError:
                results[host] = False
        return results

    def run_healing_loop(self, interval_sec: int = 60):
        self._log("Starting governed self-healing observation loop", {"interval": interval_sec})
        iteration = 0
        while not self._shutdown.is_set():
            iteration += 1
            try:
                self.check_and_heal_processes()
                if iteration % 5 == 0:
                    self.ensure_services_running()
                if iteration % 10 == 0:
                    self.check_state_files()
                    self.check_network()
                if iteration % 30 == 0:
                    self.check_disk_space()
                self._save_state()
            except Exception as exc:
                self._log(f"Error in governed healing loop: {exc}", level="error")
            self._shutdown.wait(timeout=interval_sec)
        self._log("Self-healer shutting down")

    def status(self) -> Dict:
        return {
            "hostname": self.hostname,
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            "processes": {p.name: {"running": self.check_process_running(p)[0], "critical": p.critical} for p in self.GUARDED_PROCESSES},
            "services": {s: self.check_service_status(s) for s in self.PROTECTED_SERVICES},
            "recent_actions": len(self.healing_history),
            "network": self.check_network(),
            "disk": self.check_disk_space(),
        }


def main():
    healer = SelfHealer()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "run":
        healer.run_healing_loop(int(sys.argv[2]) if len(sys.argv) > 2 else 60)
    elif cmd == "status":
        print(json.dumps(healer.status(), indent=2, default=str))
    elif cmd == "check":
        print(json.dumps(healer.check_and_heal_processes(), indent=2, default=str))
        print(json.dumps(healer.ensure_services_running(), indent=2, default=str))
        print(json.dumps(healer.check_state_files(), indent=2, default=str))
    else:
        raise SystemExit("Commands: run [interval], status, check")


if __name__ == "__main__":
    main()
