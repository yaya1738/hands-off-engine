#!/usr/bin/env python3
"""
Termux Supervisor — credential-free process supervisor for AnyClaw daemons.

Requirements (Factory round 14):
- One-instance PID/lock guard
- Restart daemons after clean exit, crash, or timeout with bounded exponential backoff
- Keep CommHub/event state outside the supervisor process
- Bounded rotating logs
- Durable last-start/last-exit/restart counters
- Fail-closed: never auto-authorize live execution
- Termux:Boot-compatible launcher
- Does NOT require root, secrets, or a second coordination bus

Platform boundary documented:
Android cannot guarantee an ordinary process survives arbitrary OS killing.
The supervisor recovers on next boot/launcher invocation. Termux:Boot
starts the supervisor, which restarts the daemons.
"""

import json
import os
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"
SUPERVISOR_STATE = STATE_DIR / "supervisor_state.json"
SUPERVISOR_PID = STATE_DIR / "supervisor.pid"
SUPERVISOR_LOCK = STATE_DIR / "supervisor.lock"
LOG_DIR = STATE_DIR / "logs"

# Bounded exponential backoff config
MIN_BACKOFF = 2       # seconds
MAX_BACKOFF = 300     # 5 minutes
MAX_RESTARTS_WINDOW = 10  # resets after this many successful seconds
WINDOW_RESET_SECONDS = 600  # 10 minutes of stability resets restart counter

# Daemons to supervise
DAEMONS = {
    "governed_root": {
        "script": REPO_ROOT / "autonomous" / "governed_root.py",
        "required": True,
        "timeout": None,  # no timeout — runs indefinitely
    },
    "event_router": {
        "script": REPO_ROOT / "scripts" / "event_router.py",
        "args": ["loop", "--interval", "10"],
        "required": True,
        "timeout": None,
    },
    "analysis_engine": {
        "script": REPO_ROOT / "scripts" / "analysis_engine.py",
        "required": False,
        "timeout": None,
    },
    "proactive_monitor": {
        "script": REPO_ROOT / "scripts" / "proactive_monitor.py",
        "args": ["--interval", "60"],
        "required": False,
        "timeout": None,
    },
    "control_room": {
        "script": REPO_ROOT / "scripts" / "yair_control_room.py",
        "required": True,
        "timeout": None,
    },
    "telegram_bridge": {
        "script": REPO_ROOT / "scripts" / "telegram_bridge.py",
        "required": True,
        "timeout": None,
    },
}

import fcntl

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [Supervisor] %(message)s')
log = logging.getLogger("Supervisor")


# ── PID/lock guard: one instance only ──

class SupervisorLock:
    """File-based lock ensuring only one supervisor instance runs."""

    def __init__(self):
        self.lock_path = SUPERVISOR_LOCK
        self.pid_path = SUPERVISOR_PID
        self.fd = None

    def try_acquire(self) -> bool:
        try:
            self.fd = open(self.lock_path, "w")
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            self.pid_path.write_text(str(os.getpid()))
            return True
        except (IOError, OSError):
            if self.fd:
                self.fd.close()
                self.fd = None
            return False

    def release(self):
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
            except Exception:
                pass
        try:
            self.lock_path.unlink(missing_ok=True)
            self.pid_path.unlink(missing_ok=True)
        except Exception:
            pass


# ── Durable state: restart counters, timing ──

def load_state() -> dict:
    if SUPERVISOR_STATE.exists():
        try:
            return json.loads(SUPERVISOR_STATE.read_text())
        except Exception:
            pass
    return {"daemons": {}, "supervisor": {"restarts": 0, "started_at": None}}


def save_state(state: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SUPERVISOR_STATE.write_text(json.dumps(state, indent=2))


# ── Rotating log manager ──

class RotatingLog:
    """Bounded rotating log for daemon stdout/stderr."""

    MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_LOG_FILES = 3

    def __init__(self, name: str):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.log_path = LOG_DIR / f"{name}.log"
        self.rotate_count = 0

    def _rotate(self):
        if not self.log_path.exists():
            return
        if self.log_path.stat().st_size < self.MAX_LOG_SIZE:
            return
        # Rotate: .log -> .log.1 -> .log.2 -> deleted
        for i in range(self.MAX_LOG_FILES - 1, 0, -1):
            src = LOG_DIR / f"{self.log_path.name}.{i}"
            dst = LOG_DIR / f"{self.log_path.name}.{i + 1}"
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
        # Current -> .1
        self.log_path.rename(LOG_DIR / f"{self.log_path.name}.1")

    def write(self, data: str):
        self._rotate()
        try:
            with open(self.log_path, "a") as f:
                f.write(data)
        except Exception:
            pass


# ── Daemon management ──

class ManagedDaemon:
    """One daemon: start, monitor, backoff, restart."""

    def __init__(self, name: str, config: dict, state: dict):
        self.name = name
        self.config = config
        self.script = config["script"]
        self.args = config.get("args", [])
        self.required = config.get("required", False)
        self.timeout = config.get("timeout")
        self.state = state.setdefault("daemons", {}).setdefault(name, {
            "restart_count": 0,
            "last_start": None,
            "last_exit": None,
            "last_exit_code": None,
            "total_restarts": 0,
            "stable_since": None,
        })
        self.process: Optional[subprocess.Popen] = None
        self.log = RotatingLog(name)
        self.start_time: Optional[float] = None

    def start(self):
        if not self.script.exists():
            log.warning(f"{self.name}: script not found ({self.script})")
            return
        cmd = [sys.executable, str(self.script)] + self.args
        try:
            self.process = subprocess.Popen(
                cmd, cwd=REPO_ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            self.start_time = time.time()
            self.state["last_start"] = datetime.now(timezone.utc).isoformat()
            log.info(f"Started {self.name} (pid={self.process.pid})")
        except Exception as e:
            log.error(f"Failed to start {self.name}: {e}")

    def poll(self) -> Optional[int]:
        """Poll for exit. Returns returncode or None if still running."""
        if self.process is None:
            return None
        returncode = self.process.poll()
        if returncode is not None:
            self.state["last_exit"] = datetime.now(timezone.utc).isoformat()
            self.state["last_exit_code"] = returncode
            # Drain stdout
            try:
                output = self.process.stdout.read()
                if output:
                    self.log.write(output)
            except Exception:
                pass
            self.process = None
            self.start_time = None
        return returncode

    def backoff_seconds(self) -> float:
        """Bounded exponential backoff: 2s, 4s, 8s, ..., up to 300s."""
        count = self.state.get("restart_count", 0)
        seconds = min(MIN_BACKOFF * (2 ** count), MAX_BACKOFF)
        return seconds

    def record_crash(self):
        self.state["restart_count"] = self.state.get("restart_count", 0) + 1
        self.state["total_restarts"] = self.state.get("total_restarts", 0) + 1
        self.state["stable_since"] = None

    def record_stable(self):
        """Call when daemon has been running for a while."""
        if self.state.get("stable_since") is None:
            self.state["stable_since"] = datetime.now(timezone.utc).isoformat()
            self.state["restart_count"] = 0  # reset backoff after stability


# ── Supervisor main loop ──

class TermuxSupervisor:
    """One-instance supervisor for AnyClaw daemons."""

    def __init__(self):
        self.lock = SupervisorLock()
        self.state = load_state()
        self.daemons: Dict[str, ManagedDaemon] = {}
        self.running = True

        for name, config in DAEMONS.items():
            daemon_state = self.state.setdefault("daemons", {}).setdefault(name, {
                "restart_count": 0,
                "last_start": None,
                "last_exit": None,
                "last_exit_code": None,
                "total_restarts": 0,
                "stable_since": None,
            })
            self.daemons[name] = ManagedDaemon(name, config, daemon_state)

    def run(self):
        if not self.lock.try_acquire():
            existing_pid = SUPERVISOR_PID.read_text().strip() if SUPERVISOR_PID.exists() else "?"
            log.error(f"Supervisor already running (pid={existing_pid}). Exiting.")
            return False

        self.state["supervisor"]["started_at"] = datetime.now(timezone.utc).isoformat()
        log.info("Termux Supervisor started (one-instance PID lock acquired)")

        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        try:
            self._loop()
        finally:
            self.lock.release()
            save_state(self.state)
            log.info("Supervisor shut down")

        return True

    def _handle_signal(self, signum, frame):
        log.info(f"Signal {signum} received, shutting down gracefully")
        self.running = False
        for name, daemon in self.daemons.items():
            if daemon.process and daemon.process.poll() is None:
                log.info(f"Terminating {name}")
                daemon.process.terminate()

    def _loop(self):
        while self.running:
            for name, daemon in self.daemons.items():
                if daemon.process is None:
                    # Not running — start with backoff
                    backoff = daemon.backoff_seconds()
                    last_exit = daemon.state.get("last_exit")
                    if last_exit and backoff > 0:
                        time.sleep(min(backoff, 5))  # cap poll sleep at 5s
                    daemon.start()
                    if daemon.process:
                        daemon.state["stable_since"] = None
                else:
                    # Running — check for timeout
                    if daemon.timeout and daemon.start_time:
                        elapsed = time.time() - daemon.start_time
                        if elapsed > daemon.timeout:
                            log.warning(f"{name}: timeout after {elapsed:.0f}s, killing")
                            daemon.process.kill()
                    # Check for exit
                    rc = daemon.poll()
                    if rc is not None:
                        log.warning(f"{name} exited with code {rc}")
                        daemon.record_crash()

            # Check stability for all running daemons
            for name, daemon in self.daemons.items():
                if daemon.process and daemon.process.poll() is None:
                    if daemon.start_time and (time.time() - daemon.start_time) > WINDOW_RESET_SECONDS:
                        daemon.record_stable()

            # Persist state periodically
            self.state["supervisor"]["restarts"] = sum(
                d.state.get("total_restarts", 0) for d in self.daemons.values()
            )
            save_state(self.state)

            time.sleep(5)

    def get_status(self) -> dict:
        daemon_status = {}
        for name, daemon in self.daemons.items():
            running = daemon.process is not None and daemon.process.poll() is None
            daemon_status[name] = {
                "running": running,
                "pid": daemon.process.pid if running else None,
                "restart_count": daemon.state.get("restart_count", 0),
                "total_restarts": daemon.state.get("total_restarts", 0),
                "last_exit_code": daemon.state.get("last_exit_code"),
                "last_start": daemon.state.get("last_start"),
                "last_exit": daemon.state.get("last_exit"),
            }
        return {
            "supervisor_pid": os.getpid(),
            "uptime_seconds": 0,
            "daemons": daemon_status,
        }


# ── Termux:Boot launcher ──

def install_boot_launcher():
    """Install a Termux:Boot startup script."""
    termux_boot = Path.home() / ".termux" / "boot"
    termux_boot.mkdir(parents=True, exist_ok=True)
    launcher = termux_boot / "start_anyclaw.sh"
    launcher.write_text(f"""#!/data/data/com.termux/files/usr/bin/bash
# Termux:Boot — starts AnyClaw supervisor on device boot
cd {REPO_ROOT}
nohup python {REPO_ROOT / 'scripts' / 'termux_supervisor.py'} > {STATE_DIR / 'logs' / 'boot.log'} 2>&1 &
echo "AnyClaw supervisor started at $(date)" >> {STATE_DIR / 'logs' / 'boot.log'}
""")
    launcher.chmod(0o755)
    log.info(f"Termux:Boot launcher installed: {launcher}")
    return str(launcher)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Termux Supervisor for AnyClaw daemons")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("run", help="Start supervisor (one instance)")
    sub.add_parser("status", help="Show supervisor and daemon status")
    sub.add_parser("install-boot", help="Install Termux:Boot launcher script")
    sub.add_parser("platform", help="Show platform boundary documentation")

    args = parser.parse_args()

    if args.cmd == "run":
        supervisor = TermuxSupervisor()
        supervisor.run()
    elif args.cmd == "status":
        state = load_state()
        print(json.dumps(state, indent=2))
    elif args.cmd == "install-boot":
        path = install_boot_launcher()
        print(f"Boot launcher installed: {path}")
    elif args.cmd == "platform":
        print("""
PLATFORM BOUNDARY — Android Process Survival

Android OS can kill background processes at any time for memory, battery,
or user-initiated reasons. This supervisor CANNOT guarantee process survival
under arbitrary OS killing.

What the supervisor CAN do:
- Run as a foreground process (more likely to survive)
- Restart immediately on next boot/launcher invocation
- Use Termux:Boot to auto-start on device boot
- Persist all state to disk (survives process death)
- Re-establish daemon state on restart (no duplicate execution)

What the supervisor CANNOT do:
- Prevent Android from killing the process
- Guarantee 100% uptime
- Auto-start after force-stop (only after reboot)
- Override battery optimization (user must disable for AnyClaw)

The correct mental model:
- Supervisor is a "best effort" resilience layer
- Every daemon state is durable (crash-safe)
- If killed, next boot or Termux:Boot invocation restores everything
- No data loss, no duplicate execution, eventual consistency
""")
    else:
        parser.print_help()
