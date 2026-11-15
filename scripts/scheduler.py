#!/usr/bin/env python3
"""Single-instance periodic scheduler with durable per-job due times.

The scheduler is the sole cadence owner for periodic jobs. It persists each
next-run timestamp before launching a child, so a restart cannot replay a
burst of already-started jobs. Failed jobs are recorded and retried only at
their next scheduled interval.
"""
import fcntl
import json
import math
import os
import signal
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
SCHEDULER_LOG = STATE / "scheduler_log.json"
SCHEDULER_STATE = STATE / "scheduler_state.json"
SCHEDULER_HEARTBEAT = STATE / "scheduler_heartbeat.json"
SCHEDULER_LOCK = STATE / "scheduler.lock"
POLL_SECONDS = 10
TASK_TIMEOUT_SECONDS = 60
MAX_OUTPUT_CHARS = 500

TASKS = [
    {"name": "health_check", "script": "health_monitor.py", "interval_seconds": 300},
    {"name": "improvement_cycle", "script": "improvement_cycle.py", "interval_seconds": 900},
    {"name": "integrity_check", "script": "state_integrity.py", "interval_seconds": 600},
    {"name": "learning_analysis", "script": "learning_loop.py", "interval_seconds": 900},
    {"name": "github_governance_monitor", "script": "github_governance_cycle.py", "interval_seconds": 21600},
]

_RUNNING = True


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path, data, *, durable=True):
    """Atomically publish JSON; fsync durable state before reporting success."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            fd = None
            stream.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
            stream.flush()
            if durable:
                os.fsync(stream.fileno())
        os.replace(temporary, path)
        if durable:
            directory_fd = os.open(
                path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except BaseException:
        if fd is not None:
            os.close(fd)
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


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


def write_heartbeat(phase="idle", task=None, task_deadline=None):
    """Publish scheduler liveness for the supervisor watchdog; never break jobs."""
    payload = {
        "pid": os.getpid(),
        "phase": phase,
        "task": task,
        "task_deadline": task_deadline,
        "updated_at": time.time(),
        "timestamp": _timestamp(),
    }
    try:
        _atomic_write_json(SCHEDULER_HEARTBEAT, payload, durable=False)
        return True
    except OSError:
        return False


def get_due_time(job, task, now):
    """Return a valid due timestamp, repairing malformed persisted values."""
    if "next_run_at" not in job:
        job["next_run_at"] = now + task["interval_seconds"]
        return job["next_run_at"]

    raw_due = job["next_run_at"]
    # bool is an int subclass in Python; reject it before float conversion.
    # JSON true/false must never become Unix timestamps 1.0/0.0.
    if isinstance(raw_due, bool):
        due_at = now + task["interval_seconds"]
        job["next_run_at"] = due_at
        return due_at

    invalid_due = False
    try:
        due_at = float(raw_due)
        if not math.isfinite(due_at):
            raise ValueError("non-finite due timestamp")
    except (TypeError, ValueError):
        invalid_due = True
        due_at = now + task["interval_seconds"]

    if invalid_due or not isinstance(raw_due, (int, float)):
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
    """Run one child with bounded output and owned process-group cleanup."""
    from scripts.process_group import run_process

    started = _timestamp()
    outcome = run_process(
        [sys.executable, str(ROOT / "scripts" / task["script"])],
        cwd=ROOT,
        timeout=TASK_TIMEOUT_SECONDS,
        max_output_chars=MAX_OUTPUT_CHARS,
    )
    return {
        "name": task["name"],
        "success": outcome["success"],
        "returncode": outcome["returncode"],
        "output": outcome["output"],
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
        write_heartbeat()

        while _RUNNING:
            write_heartbeat()
            now = time.time()
            for task in TASKS:
                if not _RUNNING:
                    break
                job = state["jobs"].setdefault(task["name"], {})
                previous_due = job.get("next_run_at")
                due_at = get_due_time(job, task, now)
                # Persist newly initialized or repaired deadlines. Comparing
                # only the post-repair value to due_at misses both cases.
                if previous_due != job.get("next_run_at"):
                    save_state(state)
                if now < due_at:
                    continue

                # Persist the next due time before launch (at-most-once per
                # interval across crashes; a failed job is not tight-looped).
                job["last_started_at"] = now
                job["next_run_at"] = now + task["interval_seconds"]
                save_state(state)

                write_heartbeat(
                    phase="task", task=task["name"],
                    task_deadline=time.time() + TASK_TIMEOUT_SECONDS,
                )
                result = run_task(task)
                write_heartbeat()
                job["last_result"] = result
                save_state(state)
                append_log(result)
                if task["name"] in ("health_check", "integrity_check") and not result["success"]:
                    label = "health monitor" if task["name"] == "health_check" else "state integrity check"
                    _send_failure_alert(label, result.get("output", "")[:200])
                status = "OK" if result["success"] else "FAIL"
                print(f"[{result['timestamp'][:19]}] {status} {task['name']}")

            if _RUNNING:
                time.sleep(POLL_SECONDS)
        return True
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
        release_lock(lock)


def _send_failure_alert(label, detail):
    """Best-effort outbound failure alert through the real TelegramBridge API.

    The bridge itself handles the not-configured case (logged warning,
    ``{"status": "not_configured"}`` result) and Telegram delivery errors
    (logged, error result). Only genuinely unexpected errors reach this
    helper's handler, which logs instead of silently discarding them.

    Returns True when an alert was actually dispatched.
    """
    try:
        from scripts.telegram_bridge import TelegramBridge
        bridge = TelegramBridge()
        result = bridge.send_alert("Scheduled job failed", f"{label}: {detail}", severity="error")
        if isinstance(result, dict) and result.get("status") == "not_configured":
            print(f"Telegram not configured; failure alert for {label} not sent")
            return False
        return isinstance(result, dict) and result.get("status") == "sent"
    except Exception as exc:
        print(f"Telegram alert error for {label}: {exc}")
        return False


def run_once():
    """Run each configured job once for explicit diagnostics.

    Returns False when any job failed (or ownership could not be acquired),
    so callers receive a failing exit status instead of a false green.
    """
    lock = acquire_lock()
    if lock is None:
        print("Scheduler already running; refusing duplicate instance")
        return False
    try:
        any_failed = False
        for task in TASKS:
            result = run_task(task)
            append_log(result)
            status = "OK" if result["success"] else "FAIL"
            print(f"{status} {task['name']}: {result['output'][:100]}")
            if not result["success"]:
                any_failed = True
        return not any_failed
    finally:
        release_lock(lock)


def main(argv=None):
    """Return a failing exit status when the scheduler cannot acquire ownership."""
    args = sys.argv[1:] if argv is None else list(argv)
    success = run_once() if "--once" in args else run_forever()
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())