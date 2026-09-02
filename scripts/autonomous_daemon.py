#!/usr/bin/env python3
"""Autonomous daemon coordinator.

This daemon owns scheduling only. Legacy direct subprocess execution has been
removed; operational work is persisted through FactoryAutonomousScheduler so
approval, policy, audit, and execution remain centralized.
"""

import argparse
import json
import os
import signal
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event
from typing import Callable, List, Optional

from ai.factory.autonomous_scheduler import FactoryAutonomousScheduler
from ai.finance.polymarket_rules_gate import PolymarketRulesGate

REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = Path("/var/log/hands-off")
LIVE_TRADING_ENABLED = False
POLYMARKET_RULES_GATE = PolymarketRulesGate()

try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass


class Task:
    def __init__(self, name: str, func: Callable, interval_seconds: int, description: str, run_on_start: bool = False):
        self.name, self.func, self.interval, self.description = name, func, interval_seconds, description
        self.run_on_start = run_on_start
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None

    def is_due(self) -> bool:
        return self.run_on_start if self.next_run is None else datetime.now() >= self.next_run

    def mark_run(self, success: bool, error: Optional[str] = None):
        self.last_run = datetime.now()
        self.next_run = self.last_run + timedelta(seconds=self.interval)
        self.run_count += 1
        if not success:
            self.error_count += 1
            self.last_error = error


def log(message: str, level: str = "INFO"):
    print(f"[{datetime.now().isoformat()}] [{level}] {message}")


def run_subprocess(command: List[str], timeout: int = 300) -> tuple[bool, str]:
    """Deprecated compatibility hook: direct process execution is forbidden."""
    log(f"Blocked legacy subprocess request: {command!r}", "WARN")
    return False, "[FACTORY-AUTHORITY] direct subprocess execution is disabled"


def queue_objective(objective: str, capability: str, source: str = "autonomous_daemon") -> bool:
    try:
        result = FactoryAutonomousScheduler().schedule_task({"objective": objective, "source": source, "capability": capability})
        return bool(result.get("scheduled"))
    except Exception as e:
        log(f"Failed to persist objective: {e}", "ERROR")
        return False


def task_trading_pipeline():
    if not LIVE_TRADING_ENABLED:
        log("Trading pipeline blocked: live trading capability is disabled", "WARN")
        return False
    snapshot_raw = os.environ.get("POLYMARKET_RULES_SNAPSHOT_JSON")
    if not snapshot_raw:
        log("Trading pipeline blocked: no current rules snapshot", "WARN")
        return False
    try:
        snapshot = json.loads(snapshot_raw)
    except (TypeError, ValueError):
        log("Trading pipeline blocked: invalid current rules snapshot", "WARN")
        return False
    decision = POLYMARKET_RULES_GATE.check(snapshot, live_trading_enabled=True, now=datetime.now(timezone.utc))
    if not decision.allowed:
        log(f"Trading pipeline blocked by rules gate: {decision.reason}", "WARN")
        return False
    return queue_objective("Run the trading pipeline only within the authorized live-trading policy.", "trading_pipeline")


def task_health_check(): return queue_objective("Run the authoritative health check and persist its result.", "health_check")
def task_phase_progression(): return queue_objective("Evaluate autonomous phase progression through the Factory authority.", "phase_progression")
def task_coordination_agent(): return queue_objective("Run one coordination-agent cycle through the Factory authority.", "coordination")
def task_claude_orchestrator(): return queue_objective("Run the Claude orchestration objective through the Factory authority.", "claude_orchestration")


def task_factory_scheduler():
    try:
        result = FactoryAutonomousScheduler().run_cycle()
        log("Factory scheduler cycle completed")
        return bool(result.get("executed") or result.get("scheduled") or result.get("idle", True))
    except Exception as e:
        log(f"Factory scheduler cycle failed: {e}", "ERROR")
        return False


def task_self_improvement(): return queue_objective("Run the Factory self-improvement cycle and apply only authorized improvements.", "self_improvement")
def task_revenue_tracking(): return queue_objective("Run revenue tracking through the Factory authority.", "revenue_tracking")
def task_performance_metrics(): return queue_objective("Collect performance metrics through the Factory authority.", "performance_metrics")


TASKS = [
    Task("factory_scheduler", task_factory_scheduler, 30, "Persistent Factory autonomous objective dispatcher", True),
    Task("coordination_agent", task_coordination_agent, 300, "Coordination agent", True),
    Task("health_check", task_health_check, 900, "Health monitoring"),
    Task("claude_orchestrator", task_claude_orchestrator, 1800, "Claude orchestrator", True),
    Task("performance_metrics", task_performance_metrics, 3600, "Performance metrics"),
    Task("trading_pipeline", task_trading_pipeline, 3600, "Trading pipeline"),
    Task("revenue_tracking", task_revenue_tracking, 14400, "Revenue tracking"),
    Task("self_improvement", task_self_improvement, 21600, "Queue Factory self-improvement cycle"),
    Task("phase_progression", task_phase_progression, 86400, "Phase progression"),
]


class AutonomousDaemon:
    def __init__(self):
        self.tasks = TASKS
        self.running = False
        self.stop_event = Event()
        self.state_file = STATE_DIR / "daemon_state.json"

    def save_state(self):
        state = {"running": self.running, "last_update": datetime.now().isoformat(), "tasks": {}}
        for task in self.tasks:
            state["tasks"][task.name] = {"last_run": task.last_run.isoformat() if task.last_run else None,
                                         "next_run": task.next_run.isoformat() if task.next_run else None,
                                         "run_count": task.run_count, "error_count": task.error_count,
                                         "last_error": task.last_error}
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, indent=2))

    def load_state(self):
        if not self.state_file.exists(): return
        try:
            state = json.loads(self.state_file.read_text())
            for task in self.tasks:
                saved = state.get("tasks", {}).get(task.name, {})
                if saved.get("next_run"): task.next_run = datetime.fromisoformat(saved["next_run"])
                task.run_count, task.error_count = saved.get("run_count", 0), saved.get("error_count", 0)
        except Exception as e:
            log(f"Error loading state: {e}", "WARN")

    def run_task(self, task: Task):
        try: task.mark_run(bool(task.func()))
        except Exception as e:
            log(f"Task {task.name} exception: {e}", "ERROR")
            task.mark_run(False, str(e))

    def run_loop(self):
        log("AUTONOMOUS DAEMON STARTING")
        self.running = True
        self.load_state()
        now = datetime.now()
        for task in self.tasks:
            if task.next_run is None: task.next_run = now if task.run_on_start else now + timedelta(seconds=task.interval)
        while not self.stop_event.is_set():
            try:
                for task in self.tasks:
                    if task.is_due():
                        log(f"Task due: {task.name}")
                        self.run_task(task)
                        self.save_state()
                self.stop_event.wait(30)
            except KeyboardInterrupt: break
            except Exception as e:
                log(f"Loop error: {e}", "ERROR")
                traceback.print_exc()
                self.stop_event.wait(60)
        self.running = False
        self.save_state()
        log("Daemon stopped")

    def stop(self): self.stop_event.set()


def main():
    parser = argparse.ArgumentParser(description="Factory-authorized autonomous scheduler")
    parser.add_argument("--background", action="store_true")
    args = parser.parse_args()
    daemon = AutonomousDaemon()
    signal.signal(signal.SIGTERM, lambda signum, frame: daemon.stop())
    signal.signal(signal.SIGINT, lambda signum, frame: daemon.stop())
    if args.background:
        pid = os.fork()
        if pid > 0:
            print(f"Daemon started in background (PID: {pid})")
            sys.exit(0)
        os.setsid()
    daemon.run_loop()


if __name__ == "__main__": main()
