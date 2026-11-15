#!/usr/bin/env python3
"""Single-instance periodic scheduler with durable per-job due times.

The scheduler is the sole cadence owner for periodic jobs. It persists each
next-run timestamp before launching a child, so a restart cannot replay a
burst of already-started jobs. Failed jobs are recorded and retried only at
their next scheduled interval.
"""
import fcntl
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
SCHEDULER_LOG = STATE / "scheduler_log.json"
SCHEDULER_STATE = STATE / "scheduler_state.json"
SCHEDULER_LOCK = STATE / "scheduler.lock"
POLL_SECONDS = 10
TASK_TIMEOUT_SECONDS = 60
MAX_OUTPUT_CHARS = 500

TASKS = [
    {"name": "health_check", "script": "health_monitor.py", "interval_seconds": 300},
    {"name": "improvement_cycle", "script": "improvement_cycle.py", "interval_seconds": 900},
    {"name": "integrity_check", "script": "state_integrity.py", "interval_seconds": 600},
    {"name": "learning_analysis", "script": "learning_loop.py", "interval_seconds": 900},
]

_RUNNING = True


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def load_state():
    """Load durable job schedule, falling back safely on malformed state."""
    if SCHEDULER_STATE.exists():
        try:
            data = json.loads(SCHEDULER_STATE.read_text())
            if isinstance(data, dict) and isinstance(data.get("jobs"), dict):
                data["jobs"] = {
                    name: job for name, job in data["jobs"].items()
                    if isinstance(name, str) and isinstance(job, dict)
                }
                return data
        except (OSError, ValueError, TypeError):
            pass
    return {"jobs": {}}


def initialize_state(now=None):
    """Stagger first-run jobs; later restarts reuse persisted due times."""
    now = time.time() if now is None else float(now)
    jobs = {}
    for index, task in enumerate(TASKS):
        jobs[task["name"]] = {
            "next_run_at": now + index * POLL_SECONDS,
            "last_started_at": None,
            "last_result": None,
        }
    return {"jobs": jobs, "updated_at": _timestamp()}


def save_state(state):
    state["updated_at"] = _timestamp()
    _atomic_write_json(SCHEDULER_STATE, state)


def get_due_time(job, task, now):
    """Return a valid due timestamp, repairing malformed persisted values."""
    try:
        return float(job.get("next_run_at", now + task["interval_seconds"]))
    except (TypeError, ValueError):
        due_at = now + task["interval_seconds"]
        job["next_run_at"] = due_at
        return due_at


def acquire_lock():
    """Return an exclusively locked file handle, or None if already running."""
    STATE.mkdir(parents=True, exist_ok=True)
    handle = SCHEDULER_LOCK.open("a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, OSError):
        handle.close()
        return None
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def release_lock(handle):
    if handle is None:
        return
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def run_task(task):
    """Run one bounded child and return a structured result."""
    started = _timestamp()
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / task["script"])],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=TASK_TIMEOUT_SECONDS,
        )
        output = (result.stdout + result.stderr).strip()
        return {
            "name": task["name"],
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "output": output[-MAX_OUTPUT_CHARS:],
            "started_at": started,
            "timestamp": _timestamp(),
        }
    except Exception as exc:
        return {
            "name": task["name"],
            "success": False,
            "returncode": None,
            "output": str(exc)[-MAX_OUTPUT_CHARS:],
            "started_at": started,
            "timestamp": _timestamp(),
        }


def append_log(result):
    STATE.mkdir(parents=True, exist_ok=True)
    entries = []
    if SCHEDULER_LOG.exists():
        try:
            loaded = json.loads(SCHEDULER_LOG.read_text())
            if isinstance(loaded, list):
                entries = loaded
        except (OSError, ValueError, TypeError):
            pass
    entries.append(result)
    _atomic_write_json(SCHEDULER_LOG, entries[-100:])


def _handle_signal(signum, frame):
    global _RUNNING
    _RUNNING = False


def run_forever():
    """Run periodic jobs until signalled; one process owns the schedule."""
    global _RUNNING
    lock = acquire_lock()
    if lock is None:
        print("Scheduler already running; refusing duplicate instance")
        return False

    previous_handlers = {}
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous_handlers[sig] = signal.signal(sig, _handle_signal)

        state = load_state()
        if not state["jobs"]:
            state = initialize_state()
            save_state(state)

        print(f"Scheduler started at {_timestamp()}")
        print(f"Tasks: {', '.join(task['name'] for task in TASKS)}")
        _RUNNING = True

        while _RUNNING:
            now = time.time()
            for task in TASKS:
                if not _RUNNING:
                    break
                job = state["jobs"].setdefault(task["name"], {})
                due_at = get_due_time(job, task, now)
                if "next_run_at" not in job or not isinstance(job["next_run_at"], (int, float)):
                    save_state(state)
                if now < due_at:
                    continue

                # Persist the next due time before launch (at-most-once per
                # interval across crashes; a failed job is not tight-looped).
                job["last_started_at"] = now
                job["next_run_at"] = now + task["interval_seconds"]
                save_state(state)

                result = run_task(task)
                job["last_result"] = result
                save_state(state)
                append_log(result)
                if task["name"] == "integrity_check" and not result["success"]:
                    try:
                        from scripts.telegram_bridge import send_message
                        send_message("⚠️ Scheduled state integrity check failed")
                    except Exception:
                        pass
                status = "OK" if result["success"] else "FAIL"
                print(f"[{result['timestamp'][:19]}] {status} {task['name']}")

            if _RUNNING:
                time.sleep(POLL_SECONDS)
        return True
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
        release_lock(lock)


def run_once():
    """Run each configured job once for explicit diagnostics."""
    lock = acquire_lock()
    if lock is None:
        print("Scheduler already running; refusing duplicate instance")
        return False
    try:
        for task in TASKS:
            result = run_task(task)
            append_log(result)
            status = "OK" if result["success"] else "FAIL"
            print(f"{status} {task['name']}: {result['output'][:100]}")
        return True
    finally:
        release_lock(lock)


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        run_forever()
