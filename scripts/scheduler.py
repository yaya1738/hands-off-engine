#!/usr/bin/env python3
"""Scheduler — runs periodic tasks in the background.

Replaces ad-hoc cron with a proper scheduler that respects the system's
own improvement cycle. Runs improvement_cycle.py periodically and
health checks more frequently.

Supervision support:
- Singleton file lock (state/scheduler.lock): a second instance, including a
  --once run, exits with code 75 instead of running tasks twice.
- Heartbeat (state/scheduler_heartbeat.json): records whether the scheduler is
  idle or executing a task and the deadline for that task, so a supervisor can
  tell a hung scheduler from a healthy one running a task.
- Atomic log writes (state/scheduler_log.json).
"""
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
SCHEDULER_LOG = STATE / "scheduler_log.json"
HEARTBEAT = STATE / "scheduler_heartbeat.json"
LOCK_PATH = STATE / "scheduler.lock"

EXIT_ALREADY_RUNNING = 75  # EX_TEMPFAIL: another instance owns the singleton lock
TASK_TIMEOUT_SECONDS = 60
LOG_MAX_ENTRIES = 100

TASKS = [
    {"name": "health_check", "script": "health_monitor.py", "interval_seconds": 300},
    {"name": "improvement_cycle", "script": "improvement_cycle.py", "interval_seconds": 900},
    {"name": "integrity_check", "script": "state_integrity.py", "interval_seconds": 600},
    {"name": "learning_analysis", "script": "learning_loop.py", "interval_seconds": 900},
]


def run_task(task):
    """Run a scheduled task."""
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / task["script"])],
            capture_output=True, text=True, cwd=str(ROOT), timeout=TASK_TIMEOUT_SECONDS
        )
        return {
            "name": task["name"],
            "success": r.returncode == 0,
            "output": (r.stdout + r.stderr).strip()[-200:],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "name": task["name"],
            "success": False,
            "output": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _atomic_write_text(path, text):
    """Write text atomically: temp file in the same directory, fsync, rename."""
    path = Path(path)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "w") as f:
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


def acquire_singleton_lock(path=None):
    """Return an open handle holding the exclusive scheduler lock, or None.

    The lock file is opened without truncation, so a failed attempt never
    modifies a lock file held by another instance. Closing the handle releases
    the lock.
    """
    path = Path(path or LOCK_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        os.close(fd)
        return None
    return os.fdopen(fd, "r")


def write_heartbeat(path=None, phase="idle", task=None, task_deadline=None):
    """Atomically record liveness. phase is 'idle' or 'task'. Never raises."""
    path = Path(path or HEARTBEAT)
    payload = {
        "pid": os.getpid(),
        "phase": phase,
        "task": task,
        "task_deadline": task_deadline,
        "updated_at": time.time(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(path, json.dumps(payload) + "\n")
    except OSError:
        pass


def _append_log(result, path=None):
    """Append a task result to the scheduler log (bounded, atomic write)."""
    path = Path(path or SCHEDULER_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    log = []
    if path.exists():
        try:
            log = json.loads(path.read_text())
        except Exception:
            pass
    if not isinstance(log, list):
        log = []
    log.append(result)
    if len(log) > LOG_MAX_ENTRIES:
        log = log[-LOG_MAX_ENTRIES:]
    _atomic_write_text(path, json.dumps(log, indent=2))


def run_once(lock_path=None):
    """Run every task once. Respects the singleton lock. Returns an exit code."""
    lock = acquire_singleton_lock(lock_path)
    if lock is None:
        print("Scheduler already running (singleton lock held); refusing to run --once.")
        return EXIT_ALREADY_RUNNING
    all_success = True
    try:
        for task in TASKS:
            result = run_task(task)
            succeeded = isinstance(result, dict) and result.get("success") is True
            all_success = all_success and succeeded
            status = "✅" if succeeded else "❌"
            output = result.get("output", "") if isinstance(result, dict) else "invalid task result"
            print(f"{status} {task['name']}: {str(output)[:100]}")
    finally:
        lock.close()
    return 0 if all_success else 1


def run_forever():
    """Run the scheduler forever. Returns an exit code only if it cannot start."""
    lock = acquire_singleton_lock()
    if lock is None:
        print("Scheduler already running (singleton lock held); exiting.")
        return EXIT_ALREADY_RUNNING

    print(f"Scheduler started at {datetime.now(timezone.utc).isoformat()}")
    print(f"Tasks: {', '.join(t['name'] for t in TASKS)}")
    
    last_run = {t["name"]: 0 for t in TASKS}
    
    write_heartbeat()
    while True:
        now = time.time()
        write_heartbeat()
        for task in TASKS:
            if now - last_run[task["name"]] >= task["interval_seconds"]:
                write_heartbeat(phase="task", task=task["name"],
                                task_deadline=time.time() + TASK_TIMEOUT_SECONDS)
                result = run_task(task)
                last_run[task["name"]] = now
                write_heartbeat()
                
                # Log
                _append_log(result)
                
                status = "✅" if result["success"] else "❌"
                print(f"[{result['timestamp'][:19]}] {status} {task['name']}")
        
        time.sleep(30)


if __name__ == "__main__":
    if "--once" in sys.argv:
        sys.exit(run_once())
    else:
        sys.exit(run_forever())
