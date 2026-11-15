#!/usr/bin/env python3
"""Process Supervisor — keeps all runtime services alive with bounded backoff.

Supervises:
- node1_runtime.py (task worker + event router + intake + improvements)
- yair_control_room.py (Control Room API on port 8787)

Design:
- Bounded exponential backoff between restarts (capped at MAX_BACKOFF=300s).
  The cooldown after MAX_CONSECUTIVE failures is a separate, longer
  COOLDOWN_DURATION=600s pause — backoff and cooldown are distinct bounds.
- Max 10 consecutive restarts before cooldown (10 min)
- Idempotent: only one supervisor instance (file lock)
- Heartbeat validation rejects future timestamps (clock skew/tampering) and
  stale heartbeats past their deadline.
- `stop` only signals a PID verified to be the process holding the
  supervisor lock — a stale or mismatched PID file is never trusted.
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

MAX_BACKOFF = 300  # 5 minutes — cap for exponential restart backoff
INITIAL_BACKOFF = 5
MAX_CONSECUTIVE = 10
COOLDOWN_DURATION = 600  # 10 minutes — separate from MAX_BACKOFF

# Heartbeat validation bounds. The supervisor loop sleeps 10s, so a healthy
# heartbeat is at most ~10s old; 120s allows for slow devices.
HEARTBEAT_MAX_AGE_S = 120
# Tolerance for clock skew when comparing heartbeat timestamps to now.
# Anything further in the future is rejected (tampering / wrong clock).
HEARTBEAT_MAX_FUTURE_SKEW_S = 60


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


def _get_backoff(consecutive):
    """Bounded exponential backoff between restarts.

    Distinct bounds: restart backoff is capped at MAX_BACKOFF (300s). Only
    after MAX_CONSECUTIVE consecutive failures does the separate, longer
    COOLDOWN_DURATION (600s) apply.
    """
    if consecutive >= MAX_CONSECUTIVE:
        return COOLDOWN_DURATION
    return min(INITIAL_BACKOFF * (2 ** min(consecutive, 6)), MAX_BACKOFF)


def _parse_timestamp(value):
    """Parse an ISO-8601 timestamp to an aware datetime (UTC if naive).

    Returns None when missing or unparseable.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def validate_heartbeat(record, now=None,
                       max_future_skew_s=HEARTBEAT_MAX_FUTURE_SKEW_S,
                       max_age_s=HEARTBEAT_MAX_AGE_S):
    """Validate a heartbeat record (dict with a `last_check`-style timestamp).

    Fail-closed validation:
    - missing / unparseable timestamp -> invalid
    - timestamp in the future beyond max_future_skew_s -> invalid
      (clock skew or tampering; future heartbeats must never look healthy)
    - timestamp older than max_age_s -> invalid (deadline exceeded)

    Returns {"valid": bool, "reason": str, "age_s": float|None}.
    """
    if not isinstance(record, dict):
        return {"valid": False, "reason": "record is not a dict", "age_s": None}
    ts = _parse_timestamp(record.get("last_check"))
    if ts is None:
        return {"valid": False, "reason": "missing or unparseable timestamp", "age_s": None}
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    age_s = (now - ts).total_seconds()
    if age_s < -max_future_skew_s:
        return {"valid": False,
                "reason": f"timestamp is {-age_s:.0f}s in the future (beyond {max_future_skew_s}s skew)",
                "age_s": age_s}
    if age_s > max_age_s:
        return {"valid": False,
                "reason": f"heartbeat is {age_s:.0f}s old (deadline {max_age_s}s)",
                "age_s": age_s}
    return {"valid": True, "reason": "ok", "age_s": age_s}


def _lock_is_held_by_other(lock_file=None):
    """True when another process currently holds the supervisor lock."""
    import fcntl
    lock_file = Path(lock_file) if lock_file else SUPERVISOR_LOCK
    try:
        fd = open(lock_file, "a")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
            return False
        finally:
            fd.close()
    except (IOError, OSError):
        return True


def _pid_is_supervisor(pid):
    """Best-effort verification that pid is a supervisor.py process.

    Checks /proc/<pid>/cmdline when available; refuses (False) when the
    check cannot be performed, so an unverifiable PID is never signaled.
    """
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline = f.read().decode("utf-8", "replace")
        return "supervisor.py" in cmdline
    except (OSError, ValueError):
        return False


def stop_supervisor(pid_file=None, lock_file=None):
    """Stop the supervisor, signaling only a verified lock owner.

    Fail-closed decision order:
    1. No pid file -> nothing to stop.
    2. Corrupt pid file -> refuse to signal anything.
    3. Lock not held by any process -> pid file is stale; remove it, never
       signal (PID reuse could kill an unrelated process).
    4. Lock held but pid in file is dead -> refuse (file names a dead pid).
    5. Lock held but pid does not verify as a supervisor.py process ->
       refuse (file may name an unrelated process).
    6. Only then send SIGTERM.

    Returns (stopped: bool, message: str).
    """
    pid_file = Path(pid_file) if pid_file else SUPERVISOR_PID
    lock_file = Path(lock_file) if lock_file else SUPERVISOR_LOCK

    if not pid_file.exists():
        return False, "Supervisor not running (no pid file)"

    try:
        pid = int(pid_file.read_text().strip())
    except (OSError, ValueError):
        return False, "Supervisor pid file is corrupt; refusing to signal"

    if not _lock_is_held_by_other(lock_file):
        try:
            pid_file.unlink()
        except OSError:
            pass
        return False, "Supervisor not running (stale pid file, lock not held)"

    if not _is_process_alive(pid):
        return False, "Supervisor not running (lock held by another instance; pid in file is dead)"

    if not _pid_is_supervisor(pid):
        return False, (f"Refusing to signal pid={pid}: "
                       "not verified as the supervisor holding the lock")

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as e:
        return False, f"Failed to signal supervisor (pid={pid}): {e}"
    return True, f"Sent SIGTERM to supervisor (pid={pid})"


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
    stats = {}  # name -> {consecutive_failures, last_success, backoff, restart_not_before}
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
                stats[name] = {"consecutive_failures": 0, "last_success": None,
                               "backoff": INITIAL_BACKOFF, "restart_not_before": 0.0}

            s = stats[name]
            running = name in procs and procs[name].poll() is None

            if not running:
                # Clean up dead process
                if name in procs:
                    rc = procs[name].returncode
                    if rc == 0:
                        s["consecutive_failures"] = 0
                        s["backoff"] = INITIAL_BACKOFF
                        s["restart_not_before"] = 0.0
                        _log(f"{name} exited cleanly (rc=0)")
                    else:
                        s["consecutive_failures"] += 1
                        s["backoff"] = _get_backoff(s["consecutive_failures"])
                        s["restart_not_before"] = time.time() + s["backoff"]
                        _log(f"{name} exited with rc={rc}, consecutive_failures={s['consecutive_failures']}, next_backoff={s['backoff']}s")
                    del procs[name]

                # Apply cooldown after too many consecutive failures
                if s["consecutive_failures"] >= MAX_CONSECUTIVE:
                    if s.get("cooldown_until") is None:
                        s["cooldown_until"] = time.time() + COOLDOWN_DURATION
                        _log(f"{name} entering cooldown for {COOLDOWN_DURATION}s after {MAX_CONSECUTIVE} consecutive failures")
                    if time.time() < s["cooldown_until"]:
                        continue
                    else:
                        s["cooldown_until"] = None
                        s["consecutive_failures"] = 0
                        s["restart_not_before"] = 0.0

                # Apply bounded backoff before restarting
                if time.time() < s.get("restart_not_before", 0.0):
                    continue

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
                    s["backoff"] = _get_backoff(s["consecutive_failures"])
                    s["restart_not_before"] = time.time() + s["backoff"]

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
            try:
                pid = int(SUPERVISOR_PID.read_text().strip())
            except ValueError:
                pid = None
            alive = pid is not None and _is_process_alive(pid)
            lock_held = _lock_is_held_by_other()
            if alive and lock_held and _pid_is_supervisor(pid):
                print(f"Supervisor: RUNNING (pid={pid})")
            elif alive and not lock_held:
                print(f"Supervisor: STALE PID FILE (pid={pid} alive but no supervisor lock held)")
            elif alive:
                print(f"Supervisor: UNVERIFIED (pid={pid} alive, lock held, PID not verified as lock owner)")
            else:
                print(f"Supervisor: DEAD (stale pid={pid})")
        else:
            print("Supervisor: NOT STARTED")
        if WATCHDOG_STATE.exists():
            try:
                heartbeat = json.loads(WATCHDOG_STATE.read_text())
                check = validate_heartbeat(heartbeat)
                print(f"Heartbeat: {'VALID' if check['valid'] else 'INVALID'} ({check['reason']})")
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                print("Heartbeat: INVALID (state file unreadable)")
            print(json.dumps(json.loads(WATCHDOG_STATE.read_text()), indent=1)[:400])
    elif args.action == "stop":
        stopped, message = stop_supervisor()
        print(message)
        if not stopped:
            sys.exit(1)
    else:
        # Write PID and run
        SUPERVISOR_PID.write_text(str(os.getpid()))
        run()
