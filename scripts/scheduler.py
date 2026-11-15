#!/usr/bin/env python3
"""Scheduler — runs periodic tasks in the background.

Replaces ad-hoc cron with a proper scheduler that respects the system's
own improvement cycle. Runs improvement_cycle.py periodically and
health checks more frequently.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
SCHEDULER_LOG = STATE / "scheduler_log.json"

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
            capture_output=True, text=True, cwd=str(ROOT), timeout=60
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


def run_forever():
    """Run the scheduler forever."""
    print(f"Scheduler started at {datetime.now(timezone.utc).isoformat()}")
    print(f"Tasks: {', '.join(t['name'] for t in TASKS)}")
    
    last_run = {t["name"]: 0 for t in TASKS}
    
    while True:
        now = time.time()
        for task in TASKS:
            if now - last_run[task["name"]] >= task["interval_seconds"]:
                result = run_task(task)
                last_run[task["name"]] = now
                
                # Log
                STATE.mkdir(parents=True, exist_ok=True)
                log = []
                if SCHEDULER_LOG.exists():
                    try:
                        log = json.loads(SCHEDULER_LOG.read_text())
                    except Exception:
                        pass
                log.append(result)
                if len(log) > 100:
                    log = log[-100:]
                SCHEDULER_LOG.write_text(json.dumps(log, indent=2))
                
                status = "✅" if result["success"] else "❌"
                print(f"[{result['timestamp'][:19]}] {status} {task['name']}")
        
        time.sleep(30)


def run_once():
    """Run every task once. Returns the number of failed tasks."""
    failures = 0
    for task in TASKS:
        result = run_task(task)
        status = "✅" if result["success"] else "❌"
        print(f"{status} {task['name']}: {result['output'][:100]}")
        if not result["success"]:
            failures += 1
    return failures


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--once" in argv:
        # Exit non-zero when any scheduled task fails, so callers
        # (supervisor, CI, cron) can detect failure instead of a
        # silently green run.
        failures = run_once()
        sys.exit(1 if failures else 0)
    run_forever()


if __name__ == "__main__":
    main()
