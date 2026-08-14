#!/usr/bin/env python3
"""
Autonomous Daemon - Main loop for all autonomous operations

This daemon runs continuously and executes all autonomous tasks on schedule.
Factory-owned autonomous work is persisted through FactoryAutonomousScheduler.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from typing import Callable, List, Optional

from ai.factory.autonomous_scheduler import FactoryAutonomousScheduler

REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = Path("/var/log/hands-off")
LIVE_TRADING_ENABLED = False

LOGS_DIR.mkdir(parents=True, exist_ok=True)


class Task:
    """Represents a scheduled daemon task."""

    def __init__(self, name: str, func: Callable, interval_seconds: int, description: str, run_on_start: bool = False):
        self.name = name
        self.func = func
        self.interval = interval_seconds
        self.description = description
        self.run_on_start = run_on_start
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None

    def is_due(self) -> bool:
        if self.next_run is None:
            return self.run_on_start
        return datetime.now() >= self.next_run

    def mark_run(self, success: bool, error: Optional[str] = None):
        self.last_run = datetime.now()
        self.next_run = self.last_run + timedelta(seconds=self.interval)
        self.run_count += 1
        if not success:
            self.error_count += 1
            self.last_error = error


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] [{level}] {message}")


def run_subprocess(command: List[str], timeout: int = 300) -> tuple[bool, str]:
    """Run a subprocess with timeout."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, cwd=str(REPO_ROOT))
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


# Task implementations

def task_trading_pipeline():
    """Keep live trading unavailable until explicitly unbanned."""
    if not LIVE_TRADING_ENABLED:
        log("Trading pipeline blocked: live trading capability is temporarily disabled", "WARN")
        return False
    log("Running trading pipeline...")
    os.environ["HANDS_OFF_EXECUTOR_MODE"] = "shadow"
    success, output = run_subprocess(["python3", str(REPO_ROOT / "scripts" / "run_pipeline.py")], timeout=600)
    if success:
        log("Trading pipeline completed successfully")
    else:
        log(f"Trading pipeline failed: {output[:200]}", "ERROR")
    return success


def task_health_check():
    log("Running health check...")
    healthcheck = REPO_ROOT / "scripts" / "healthcheck.sh"
    if healthcheck.exists():
        success, output = run_subprocess(["bash", str(healthcheck)])
        if success:
            log("Health check passed")
        else:
            log(f"Health check issues: {output[:200]}", "WARN")
        return success
    log("No healthcheck script found", "WARN")
    return True


def task_phase_progression():
    log("Running phase progression check...")
    success, output = run_subprocess(["python3", str(REPO_ROOT / "scripts" / "autonomous_phase_manager.py")])
    if success:
        log("Phase progression check completed")
    else:
        log(f"Phase progression failed: {output[:200]}", "ERROR")
    return success


def task_coordination_agent():
    log("Running coordination agent...")
    success, output = run_subprocess(["python3", str(REPO_ROOT / "scripts" / "coordination_agent.py"), "--once"])
    if success:
        log("Coordination agent cycle completed")
    else:
        log(f"Coordination agent failed: {output[:200]}", "ERROR")
    return success


def task_claude_orchestrator():
    log("Running Claude orchestrator...")
    success, output = run_subprocess(["python3", str(REPO_ROOT / "scripts" / "claude_orchestrator.py")])
    if success:
        log("Claude orchestrator completed")
    else:
        log(f"Claude orchestrator failed: {output[:200]}", "ERROR")
    return success


def task_factory_scheduler():
    """Drain one persisted Factory objective through the authoritative gateway."""
    try:
        result = FactoryAutonomousScheduler().run_cycle()
        if result.get("executed"):
            log("Factory scheduler executed persisted autonomous objective")
        else:
            log("Factory scheduler idle")
        return True
    except Exception as e:
        log(f"Factory scheduler cycle failed: {e}", "ERROR")
        return False


def task_self_improvement():
    """Persist the self-improvement objective; execution happens through the Factory scheduler."""
    log("Queueing self-improvement objective through Factory scheduler...")
    try:
        scheduler = FactoryAutonomousScheduler()
        result = scheduler.schedule_task({
            "objective": "Run the Factory self-improvement cycle and apply only authorized improvements.",
            "source": "autonomous_daemon",
            "capability": "self_improvement",
        })
        log(f"Self-improvement objective persisted: {result.get('scheduled', False)}")
        return bool(result.get("scheduled"))
    except Exception as e:
        log(f"Self-improvement queueing failed: {e}", "ERROR")
        return False


def task_revenue_tracking():
    log("Running revenue tracking...")
    success, output = run_subprocess(["python3", str(REPO_ROOT / "revenue" / "master_revenue_engine.py")])
    if success:
        log("Revenue tracking completed")
    else:
        log(f"Revenue tracking failed: {output[:200]}", "ERROR")
    return success


def task_performance_metrics():
    log("Tracking performance metrics...")
    success, output = run_subprocess(["python3", str(REPO_ROOT / "scripts" / "track_performance.py")])
    if success:
        log("Performance metrics tracked")
    else:
        log(f"Performance tracking failed: {output[:200]}", "ERROR")
    return success


TASKS = [
    Task("factory_scheduler", task_factory_scheduler, 30, "Persistent Factory autonomous objective dispatcher", run_on_start=True),
    Task("coordination_agent", task_coordination_agent, 5 * 60, "Coordination agent", run_on_start=True),
    Task("health_check", task_health_check, 15 * 60, "Health monitoring"),
    Task("claude_orchestrator", task_claude_orchestrator, 30 * 60, "Claude orchestrator", run_on_start=True),
    Task("performance_metrics", task_performance_metrics, 60 * 60, "Performance metrics"),
    Task("trading_pipeline", task_trading_pipeline, 60 * 60, "Trading pipeline", run_on_start=False),
    Task("revenue_tracking", task_revenue_tracking, 4 * 60 * 60, "Revenue tracking"),
    Task("self_improvement", task_self_improvement, 6 * 60 * 60, "Queue Factory self-improvement cycle"),
    Task("phase_progression", task_phase_progression, 24 * 60 * 60, "Phase progression"),
]


class AutonomousDaemon:
    """Main daemon class."""

    def __init__(self):
        self.tasks = TASKS
        self.running = False
        self.stop_event = Event()
        self.state_file = STATE_DIR / "daemon_state.json"

    def save_state(self):
        state = {"running": self.running, "last_update": datetime.now().isoformat(), "tasks": {}}
        for task in self.tasks:
            state["tasks"][task.name] = {
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None,
                "run_count": task.run_count,
                "error_count": task.error_count,
                "last_error": task.last_error,
            }
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        if not self.state_file.exists():
            return
        try:
            with open(self.state_file) as f:
                state = json.load(f)
            for task in self.tasks:
                task_state = state.get("tasks", {}).get(task.name, {})
                if task_state.get("next_run"):
                    task.next_run = datetime.fromisoformat(task_state["next_run"])
                task.run_count = task_state.get("run_count", 0)
                task.error_count = task_state.get("error_count", 0)
        except Exception as e:
            log(f"Error loading state: {e}", "WARN")

    def run_task(self, task: Task):
        try:
            success = task.func()
            task.mark_run(success)
        except Exception as e:
            log(f"Task {task.name} exception: {e}", "ERROR")
            traceback.print_exc()
            task.mark_run(False, str(e))

    def run_loop(self):
        log("=" * 60)
        log("AUTONOMOUS DAEMON STARTING")
        log("=" * 60)
        log(f"Loaded {len(self.tasks)} tasks:")
        for task in self.tasks:
            log(f"  - {task.name}: every {task.interval // 60 if task.interval >= 60 else task.interval}s ({task.description})")
        log("=" * 60)

        self.running = True
        self.load_state()

        now = datetime.now()
        for task in self.tasks:
            if task.next_run is None:
                task.next_run = now if task.run_on_start else now + timedelta(seconds=task.interval)

        while not self.stop_event.is_set():
            try:
                for task in self.tasks:
                    if task.is_due():
                        log(f"Task due: {task.name}")
                        self.run_task(task)
                        self.save_state()
                self.stop_event.wait(30)
            except KeyboardInterrupt:
                log("Received interrupt signal")
                break
            except Exception as e:
                log(f"Loop error: {e}", "ERROR")
                traceback.print_exc()
                time.sleep(60)

        self.running = False
        self.save_state()
        log("Daemon stopped")

    def stop(self):
        log("Stopping daemon...")
        self.stop_event.set()


def main():
    parser = argparse.ArgumentParser(description="Autonomous daemon for all scheduled tasks")
    parser.add_argument("--background", action="store_true", help="Run in background")
    args = parser.parse_args()
    daemon = AutonomousDaemon()

    def signal_handler(signum, frame):
        daemon.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.background:
        pid = os.fork()
        if pid > 0:
            print(f"Daemon started in background (PID: {pid})")
            sys.exit(0)
        os.setsid()
        daemon.run_loop()
    else:
        daemon.run_loop()


if __name__ == "__main__":
    main()
