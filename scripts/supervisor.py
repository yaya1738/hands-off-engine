#!/usr/bin/env python3
"""Process Supervisor — keeps all runtime services alive with bounded backoff.

Supervises:
- node1_runtime.py (task worker + event router + intake + improvements)
- yair_control_room.py (Control Room API on port 8787)
- scheduler.py (periodic health / integrity / improvement / learning tasks)

Design:
- Bounded exponential backoff (max 5 min), applied before restarts
- Max 10 consecutive restarts before cooldown (10 min)
- Restart counters, backoff and cooldown persist in state/supervisor_state.json
- Idempotent: only one supervisor instance (file lock, never truncated)
- PID file is written only after the lock is held and removed only by its owner
- Heartbeat watchdog for services that declare one (scheduler): an idle
  heartbeat that stops refreshing, or a task that overruns its declared
  deadline, triggers an orderly restart; a healthy service running a task
  within its deadline is left alone
- Exit code 75 from a singleton service is harmless only when a healthy
  external owner (lock held, live PID, fresh heartbeat) is verified
- Orderly shutdown: terminate children, wait, kill only after the grace period
- Logs to state/logs/supervisor.log
"""
import fcntl
import json
import math
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
    {
        "name": "factory_scheduler",
        "cmd": [sys.executable, str(ROOT / "scripts" / "scheduler.py")],
        "cwd": str(ROOT),
        "log": LOG_DIR / "factory_scheduler_supervised.log",
    },
]

MAX_BACKOFF = 300  # 5 minutes
INITIAL_BACKOFF = 5
MAX_CONSECUTIVE = 10
COOLDOWN_DURATION = 600  # 10 minutes
EXIT_ALREADY_RUNNING = 75  # singleton service found another instance running
ALREADY_RUNNING_RETRY = 60
STOP_GRACE = 10  # seconds between terminate and kill
HEARTBEAT_IDLE_MAX_AGE = 120  # idle heartbeat older than this => stale
TASK_OVERRUN_GRACE = 30  # seconds past a declared task deadline => hung
HEARTBEAT_MAX_TASK_SECONDS = 60  # must match scheduler.TASK_TIMEOUT_SECONDS
HEARTBEAT_STARTUP_GRACE = 120  # time a new process has to write its first heartbeat


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
    _atomic_write_text(WATCHDOG_STATE, json.dumps(state, indent=2) + "\n")


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


def _atomic_write_text(path, text):
    """Write text atomically: temp file in the same directory, fsync, rename."""
    path = Path(path)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def _acquire_lock(path):
    """Return an fd holding an exclusive flock on path, or None if it is held.

    The file is opened without truncation, so a failed attempt never modifies
    a lock file owned by another process. os.close(fd) releases the lock.
    """
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        os.close(fd)
        return None
    return fd


def _lock_is_held(path):
    """True if some process currently holds the flock on path (never creates it)."""
    try:
        fd = os.open(path, os.O_RDWR)
    except OSError:
        return False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def _write_pid_file():
    """Write this process's PID. Call only while holding the supervisor lock."""
    _atomic_write_text(SUPERVISOR_PID, str(os.getpid()))


def _release_pid_file():
    """Remove the PID file only if it still names this process."""
    try:
        if SUPERVISOR_PID.read_text().strip() == str(os.getpid()):
            SUPERVISOR_PID.unlink()
    except (OSError, ValueError):
        pass


def _is_supervisor_process(pid):
    """Verify /proc identifies PID as this repository's supervisor.py process."""
    proc = Path("/proc") / str(pid)
    try:
        args = (proc / "cmdline").read_bytes().split(b"\0")
        cwd = Path(os.readlink(proc / "cwd")).resolve()
    except OSError:
        return False
    expected = (ROOT / "scripts" / "supervisor.py").resolve()
    for arg in args[1:]:
        if not arg or not arg.endswith(b"supervisor.py"):
            continue
        candidate = Path(os.fsdecode(arg))
        if not candidate.is_absolute():
            candidate = cwd / candidate
        try:
            if candidate.resolve() == expected:
                return True
        except OSError:
            continue
    return False


def _can_signal_supervisor(pid):
    """Only signal a live process matching this repo's supervisor while lock is held."""
    try:
        registered_pid = int(SUPERVISOR_PID.read_text().strip())
    except (OSError, ValueError):
        return False
    return (type(pid) is int and pid > 0 and pid != os.getpid()
            and pid == registered_pid
            and _is_process_alive(pid) and _lock_is_held(SUPERVISOR_LOCK)
            and _is_supervisor_process(pid))


def _read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None


def _finite_timestamp(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _heartbeat_verdict(path, now, started_at=None, expected_pid=None):
    """Classify a service heartbeat: 'ok', 'stale' or 'hung'. Reject malformed or future data."""
    data = _read_json(path)
    if not isinstance(data, dict):
        usable = False
    else:
        pid = data.get("pid")
        usable = type(pid) is int and pid > 0 and (expected_pid is None or pid == expected_pid)

    if not usable:
        if (_finite_timestamp(started_at) and started_at <= now + 5
                and now - started_at <= HEARTBEAT_STARTUP_GRACE):
            return "ok"
        return "stale"

    updated = data.get("updated_at")
    if not _finite_timestamp(updated) or updated > now + 5:
        return "stale"

    phase = data.get("phase")
    if phase == "task":
        deadline = data.get("task_deadline")
        task = data.get("task")
        if (not isinstance(task, str) or not task.strip()
                or not _finite_timestamp(deadline) or deadline < updated
                or deadline > updated + HEARTBEAT_MAX_TASK_SECONDS + 5):
            return "stale"
        return "hung" if now > deadline + TASK_OVERRUN_GRACE else "ok"
    if phase == "idle":
        return "stale" if now - updated > HEARTBEAT_IDLE_MAX_AGE else "ok"
    return "stale"


def _external_owner_healthy(svc, now):
    """Verify that exit code 75 means a healthy instance really owns the service.

    Requires all of: the singleton lock is currently held, the heartbeat names a
    live PID other than this supervisor, and that heartbeat is fresh/healthy.
    """
    lock, hb = svc.get("singleton_lock"), svc.get("heartbeat")
    if not lock or not hb or not _lock_is_held(lock):
        return False
    data = _read_json(hb)
    if not isinstance(data, dict):
        return False
    pid = data.get("pid")
    if not isinstance(pid, int) or pid <= 0 or pid == os.getpid() or not _is_process_alive(pid):
        return False
    return _heartbeat_verdict(hb, now, expected_pid=pid) == "ok"


def _shutdown_children(procs, grace=None):
    """Terminate children, wait for them, kill only after the grace period.

    Returns the names of children that had to be killed. Clears procs.
    """
    grace = STOP_GRACE if grace is None else grace
    live = [(n, p) for n, p in procs.items() if p.poll() is None]
    for n, p in live:
        try:
            p.terminate()
        except Exception:
            pass
    deadline = time.monotonic() + grace
    killed = []
    for n, p in live:
        try:
            p.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            _log(f"{n} did not exit within {grace}s of SIGTERM; killing")
            killed.append(n)
            try:
                p.kill()
                p.wait(timeout=grace)
            except Exception:
                pass
        except Exception:
            pass
    procs.clear()
    return killed


def _stop_process(p):
    """Orderly stop of a single child (terminate, wait, kill after grace)."""
    return _shutdown_children({"process": p})


def _new_stats():
    return {
        "consecutive_failures": 0,
        "last_success": None,
        "backoff": INITIAL_BACKOFF,
        "cooldown_until": None,
        "next_start_at": 0,
        "started_at": None,
    }


def _restore_stats(state):
    """Rebuild restart counters / backoff / cooldown persisted by a prior run.

    Timestamps are wall-clock epoch seconds, so they stay meaningful across a
    supervisor restart. They are clamped so a clock jump cannot block a
    service for longer than one cooldown.
    """
    stats = {}
    saved_all = state.get("services") if isinstance(state, dict) else None
    if not isinstance(saved_all, dict):
        return stats
    now = time.time()
    ceiling = now + COOLDOWN_DURATION
    for svc in SERVICES:
        saved = saved_all.get(svc["name"])
        if not isinstance(saved, dict):
            continue
        st = _new_stats()
        try:
            st["consecutive_failures"] = max(0, int(saved.get("consecutive_failures") or 0))
            st["backoff"] = min(MAX_BACKOFF, max(INITIAL_BACKOFF, int(saved.get("backoff") or INITIAL_BACKOFF)))
            cu = saved.get("cooldown_until")
            st["cooldown_until"] = min(float(cu), ceiling) if cu else None
            st["next_start_at"] = min(float(saved.get("next_start_at") or 0), ceiling)
        except (TypeError, ValueError):
            st = _new_stats()
        st["last_success"] = saved.get("last_success")
        stats[svc["name"]] = st
    return stats


def _services_snapshot(procs, stats):
    snap = {}
    for svc in SERVICES:
        n = svc["name"]
        s = stats.get(n, {})
        alive = n in procs and procs[n].poll() is None
        snap[n] = {
            "pid": procs[n].pid if alive else None,
            "consecutive_failures": s.get("consecutive_failures", 0),
            "backoff": s.get("backoff", INITIAL_BACKOFF),
            "cooldown_until": s.get("cooldown_until"),
            "next_start_at": s.get("next_start_at", 0),
            "last_success": s.get("last_success"),
        }
    return snap


def run(max_loops=None):
    lock_fd = _acquire_lock(SUPERVISOR_LOCK)
    if lock_fd is None:
        _log("Another supervisor is already running")
        return

    # PID is written only after the lock is held, so a duplicate supervisor
    # can never overwrite the active supervisor's PID.
    _write_pid_file()

    state = _load_state()
    procs = {}  # name -> subprocess.Popen
    stats = _restore_stats(state)  # name -> restart / backoff / cooldown bookkeeping

    _log(f"Supervisor started (pid={os.getpid()})")

    def shutdown(sig, frame):
        _log("Supervisor shutting down")
        sys.exit(0)  # cleanup runs in the finally block below

    old_handlers = {
        signal.SIGTERM: signal.signal(signal.SIGTERM, shutdown),
        signal.SIGINT: signal.signal(signal.SIGINT, shutdown),
    }

    try:
        loops = 0
        while True:
            for svc in SERVICES:
                name = svc["name"]
                if name not in stats:
                    stats[name] = _new_stats()
                s = stats[name]

                running = name in procs and procs[name].poll() is None

                # Heartbeat watchdog (services that declare a heartbeat)
                if running and svc.get("heartbeat") and s["started_at"] is not None:
                    verdict = _heartbeat_verdict(
                        svc["heartbeat"], time.time(),
                        started_at=s["started_at"], expected_pid=procs[name].pid,
                    )
                    if verdict != "ok":
                        _log(f"{name} heartbeat {verdict}; restarting")
                        _stop_process(procs[name])
                        running = False

                if not running:
                    # Clean up dead process
                    if name in procs:
                        rc = procs[name].returncode
                        if rc == 0:
                            s["consecutive_failures"] = 0
                            s["backoff"] = INITIAL_BACKOFF
                            s["next_start_at"] = 0
                            _log(f"{name} exited cleanly (rc=0)")
                        elif rc == EXIT_ALREADY_RUNNING and _external_owner_healthy(svc, time.time()):
                            s["next_start_at"] = time.time() + ALREADY_RUNNING_RETRY
                            _log(f"{name} exit 75: healthy external owner verified; retry in {ALREADY_RUNNING_RETRY}s")
                        else:
                            if rc == EXIT_ALREADY_RUNNING:
                                _log(f"{name} exit 75 but no healthy external owner verified; counting as failure")
                            s["consecutive_failures"] += 1
                            s["backoff"] = _get_backoff(s["consecutive_failures"], s["backoff"])
                            s["next_start_at"] = time.time() + s["backoff"]
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
                    if time.time() < s["next_start_at"]:
                        continue

                    # Start
                    _log(f"Starting {name}")
                    try:
                        with open(svc["log"], "a") as log_file:
                            p = subprocess.Popen(
                                svc["cmd"],
                                cwd=svc["cwd"],
                                stdout=log_file,
                                stderr=subprocess.STDOUT,
                            )
                        procs[name] = p
                        s["started_at"] = time.time()
                        _log(f"{name} started (pid={p.pid})")
                    except Exception as e:
                        _log(f"Failed to start {name}: {e}")
                        s["consecutive_failures"] += 1
                        s["backoff"] = _get_backoff(s["consecutive_failures"], s["backoff"])
                        s["next_start_at"] = time.time() + s["backoff"]
                else:
                    # Process is alive — reset failure tracking
                    if s["consecutive_failures"] > 0:
                        _log(f"{name} recovered (was {s['consecutive_failures']} consecutive failures)")
                        s["consecutive_failures"] = 0
                        s["backoff"] = INITIAL_BACKOFF
                    s["last_success"] = datetime.now(timezone.utc).isoformat()

            state["last_check"] = datetime.now(timezone.utc).isoformat()
            state["services"] = _services_snapshot(procs, stats)
            _save_state(state)

            loops += 1
            if max_loops is not None and loops >= max_loops:
                break
            time.sleep(10)
    finally:
        # Orderly shutdown: terminate children, wait, kill only after the grace
        # period, then release only the resources this process owns.
        _shutdown_children(procs)
        state["services"] = _services_snapshot(procs, stats)
        try:
            _save_state(state)
        except Exception:
            pass
        _release_pid_file()
        for sig, handler in old_handlers.items():
            if handler is not None:
                signal.signal(sig, handler)
        os.close(lock_fd)


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
            try:
                pid = int(SUPERVISOR_PID.read_text().strip())
            except (OSError, ValueError):
                pid = 0
            if not _can_signal_supervisor(pid):
                print(f"Supervisor not verified (pid={pid}); not signalling")
            else:
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"Sent SIGTERM to verified supervisor (pid={pid})")
                except ProcessLookupError:
                    print("Supervisor already exited; not signalling")
                except OSError as exc:
                    print(f"Could not signal supervisor: {exc}")
    else:
        # run() takes the lock first, then writes the PID file
        run()
