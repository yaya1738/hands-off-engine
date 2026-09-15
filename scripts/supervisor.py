#!/usr/bin/env python3
"""Process Supervisor — keeps all runtime services alive with bounded backoff.

Supervises:
- node1_runtime.py (task worker + event router + intake + improvements)
- yair_control_room.py (Control Room API on port 8787)

Design:
- Bounded exponential backoff (max 5 min)
- Max 10 consecutive restarts before cooldown (10 min)
- Idempotent: only one supervisor instance (file lock)
- Logs to state/logs/supervisor.log
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
LOG_DIR = STATE / "logs"
SUPERVISOR_PID = STATE / "supervisor.pid"
SUPERVISOR_LOCK = STATE / "supervisor.lock"
SUPERVISOR_LOG = LOG_DIR / "supervisor.log"
WATCHDOG_STATE = STATE / "supervisor_state.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)

SERVICES = [
    {
        "name": "node1_runtime",
        "cmd": [sys.executable, str(ROOT / "scripts" / "node1_runtime.py"), "run"],
        "cwd": str(ROOT),
        "log": LOG_DIR / "node1_supervised.log",
    },
    {
        "name": "control_room",
        "cmd": [sys.executable, str(ROOT / "scripts" / "yair_control_room.py")],
        "cwd": str(ROOT),
        "log": LOG_DIR / "control_room_supervised.log",
    },
]

MAX_BACKOFF = 300  # 5 minutes
INITIAL_BACKOFF = 5
MAX_CONSECUTIVE = 10
COOLDOWN_DURATION = 600  # 10 minutes


def _log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    try:
        with SUPERVISOR_LOG.open("a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load_state():
    if WATCHDOG_STATE.exists():
        try:
            return json.loads(WATCHDOG_STATE.read_text())
        except Exception:
            pass
    return {}


def _save_state(state):
    WATCHDOG_STATE.write_text(json.dumps(state, indent=2) + "\n")


def _is_process_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _get_backoff(consecutive, backoff):
    """Bounded exponential backoff with reset on success."""
    if consecutive >= MAX_CONSECUTIVE:
        return COOLDOWN_DURATION
    return min(INITIAL_BACKOFF * (2 ** min(consecutive, 6)), MAX_BACKOFF)


def run():
    import fcntl
    try:
        lock_fd = open(SUPERVISOR_LOCK, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        _log("Another supervisor is already running")
        return

    state = _load_state()
    procs = {}  # name -> subprocess.Popen
    stats = {}  # name -> {consecutive_failures, last_success, backoff}
    _log(f"Supervisor started (pid={os.getpid()})")

    def shutdown(sig, frame):
        _log("Supervisor shutting down")
        for name, p in procs.items():
            try:
                p.terminate()
            except Exception:
                pass
        _save_state(state)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    while True:
        for svc in SERVICES:
            name = svc["name"]
            if name not in stats:
                stats[name] = {"consecutive_failures": 0, "last_success": None, "backoff": INITIAL_BACKOFF}

            s = stats[name]
            running = name in procs and procs[name].poll() is None

            if not running:
                # Clean up dead process
                if name in procs:
                    rc = procs[name].returncode
                    if rc == 0:
                        s["consecutive_failures"] = 0
                        s["backoff"] = INITIAL_BACKOFF
                        _log(f"{name} exited cleanly (rc=0)")
                    else:
                        s["consecutive_failures"] += 1
                        s["backoff"] = _get_backoff(s["consecutive_failures"], s["backoff"])
                        _log(f"{name} exited with rc={rc}, consecutive_failures={s['consecutive_failures']}, next_backoff={s['backoff']}s")
                    del procs[name]

                # Apply backoff / cooldown
                if s["consecutive_failures"] >= MAX_CONSECUTIVE:
                    if s.get("cooldown_until") is None:
                        s["cooldown_until"] = time.time() + COOLDOWN_DURATION
                        _log(f"{name} entering cooldown for {COOLDOWN_DURATION}s after {MAX_CONSECUTIVE} consecutive failures")
                    if time.time() < s["cooldown_until"]:
                        continue
                    else:
                        s["cooldown_until"] = None
                        s["consecutive_failures"] = 0

                # Start
                _log(f"Starting {name}")
                try:
                    log_file = open(svc["log"], "a")
                    p = subprocess.Popen(
                        svc["cmd"],
                        cwd=svc["cwd"],
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                    )
                    procs[name] = p
                    _log(f"{name} started (pid={p.pid})")
                except Exception as e:
                    _log(f"Failed to start {name}: {e}")
                    s["consecutive_failures"] += 1

            else:
                # Process is alive — reset failure tracking
                if s["consecutive_failures"] > 0:
                    _log(f"{name} recovered (was {s['consecutive_failures']} consecutive failures)")
                s["consecutive_failures"] = 0
                s["backoff"] = INITIAL_BACKOFF
                s["last_success"] = datetime.now(timezone.utc).isoformat()

        state["last_check"] = datetime.now(timezone.utc).isoformat()
        state["services"] = {
            name: {
                "pid": procs[name].pid if name in procs and procs[name].poll() is None else None,
                "consecutive_failures": stats.get(name, {}).get("consecutive_failures", 0),
            }
            for name in [s["name"] for s in SERVICES]
        }
        _save_state(state)
        time.sleep(10)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs="?", default="run", choices=["run", "status", "stop"])
    args = parser.parse_args()

    if args.action == "status":
        if SUPERVISOR_PID.exists():
            pid = int(SUPERVISOR_PID.read_text().strip())
            alive = _is_process_alive(pid)
            print(f"Supervisor: {'RUNNING' if alive else 'DEAD'} (pid={pid})")
        else:
            print("Supervisor: NOT STARTED")
        if WATCHDOG_STATE.exists():
            print(json.dumps(json.loads(WATCHDOG_STATE.read_text()), indent=1)[:400])
    elif args.action == "stop":
        if SUPERVISOR_PID.exists():
            pid = int(SUPERVISOR_PID.read_text().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Sent SIGTERM to supervisor (pid={pid})")
            except Exception:
                print("Supervisor not running")
    else:
        # Write PID and run
        SUPERVISOR_PID.write_text(str(os.getpid()))
        run()
