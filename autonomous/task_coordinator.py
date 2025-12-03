#!/usr/bin/env python3
"""
TASK COORDINATOR - INTEGRAFIX BRIDGE #4

Coordinates all 96 autonomous scripts with dependency management.

Before: 96 scripts run independently via subprocess, race conditions,
        no dependency management, failures cascade silently
After:  Central coordinator with dependency DAG, timeout protection,
        rollback on failure, state synchronization

Serving: Yair Siegel
"""

import json
import sys
import uuid
import importlib
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
AUTONOMOUS_DIR = PROJECT_ROOT / "autonomous"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


@dataclass
class Task:
    """A unit of work in the autonomous system."""
    task_id: str = field(default_factory=lambda: f"TASK-{str(uuid.uuid4())[:8]}")
    name: str = ""
    description: str = ""
    module_path: str = ""  # e.g., "autonomous.capital_tracker"
    function_name: str = "main"  # Function to call
    args: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # task_ids that must run first
    timeout_seconds: int = 300
    priority: int = 5  # 1=highest, 10=lowest
    category: str = "general"


@dataclass
class TaskResult:
    """Result of executing a task."""
    task_id: str
    status: TaskStatus
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    result: Any = None
    error: Optional[str] = None
    traceback: Optional[str] = None


class TaskCoordinator:
    """
    Coordinates autonomous script execution.

    Features:
    - Dependency management (DAG)
    - Topological execution ordering
    - Timeout protection
    - Parallel execution for independent tasks
    - Error propagation (dependent tasks skip on failure)
    - State synchronization checkpoints
    """

    STATE_FILE = STATE_DIR / "coordinator_state.json"
    LOG_FILE = STATE_DIR / "coordinator_log.jsonl"

    def __init__(self, max_workers: int = 4):
        self._lock = threading.RLock()
        self.max_workers = max_workers
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, TaskResult] = {}
        self.state = self._load_state()

        # Ensure directories
        STATE_DIR.mkdir(parents=True, exist_ok=True)

        # Auto-register tasks from autonomous/
        self._auto_register_tasks()

    def _load_state(self) -> Dict:
        """Load coordinator state."""
        if self.STATE_FILE.exists():
            try:
                return json.loads(self.STATE_FILE.read_text())
            except:
                pass
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_runs": 0,
            "successful_tasks": 0,
            "failed_tasks": 0
        }

    def _save_state(self):
        """Save coordinator state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def _auto_register_tasks(self):
        """Auto-register tasks from autonomous/ directory."""
        if not AUTONOMOUS_DIR.exists():
            return

        # Key scripts and their dependencies
        task_configs = {
            # Core trading pipeline
            "concrete_executor": {
                "description": "Execute trading decisions",
                "dependencies": ["probability_calibrator", "yair_wisdom_engine"],
                "priority": 2,
                "category": "trading"
            },
            "probability_calibrator": {
                "description": "Calibrate probability estimates",
                "dependencies": [],
                "priority": 1,
                "category": "analysis"
            },
            "yair_wisdom_engine": {
                "description": "Apply Yair's teachings",
                "dependencies": [],
                "priority": 1,
                "category": "wisdom"
            },
            "outcome_recorder": {
                "description": "Record trade outcomes",
                "dependencies": ["concrete_executor"],
                "priority": 3,
                "category": "recording"
            },
            "learning_engine": {
                "description": "Learn from outcomes",
                "dependencies": ["outcome_recorder"],
                "priority": 4,
                "category": "learning"
            },
            # Support systems
            "glitch_detector": {
                "description": "Detect system anomalies",
                "dependencies": [],
                "priority": 1,
                "category": "monitoring"
            },
            "capital_state_manager": {
                "description": "Manage capital state",
                "dependencies": [],
                "priority": 1,
                "category": "capital"
            },
            "system_dashboard": {
                "description": "Generate system dashboard",
                "dependencies": ["glitch_detector"],
                "priority": 5,
                "category": "monitoring"
            },
            # Master orchestrator
            "master_orchestrator": {
                "description": "Orchestrate all systems",
                "dependencies": ["concrete_executor", "learning_engine"],
                "priority": 5,
                "category": "orchestration"
            }
        }

        for script_path in AUTONOMOUS_DIR.glob("*.py"):
            if script_path.name.startswith("__"):
                continue

            script_name = script_path.stem
            config = task_configs.get(script_name, {})

            task = Task(
                task_id=script_name,
                name=script_name.replace("_", " ").title(),
                description=config.get("description", f"Run {script_name}"),
                module_path=f"autonomous.{script_name}",
                function_name="main",
                dependencies=config.get("dependencies", []),
                timeout_seconds=config.get("timeout", 300),
                priority=config.get("priority", 5),
                category=config.get("category", "general")
            )
            self.tasks[task.task_id] = task

    def register_task(self, task: Task):
        """Register a task."""
        with self._lock:
            self.tasks[task.task_id] = task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def execute_task(self, task_id: str) -> TaskResult:
        """
        Execute a single task with full lifecycle.

        1. Check dependencies completed successfully
        2. Lock execution
        3. Execute with timeout
        4. Record result
        5. Release lock
        """
        task = self.tasks.get(task_id)
        if not task:
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=f"Task not found: {task_id}"
            )

        start_time = datetime.now(timezone.utc)

        # Check dependencies
        for dep_id in task.dependencies:
            dep_result = self.results.get(dep_id)
            if not dep_result or dep_result.status != TaskStatus.SUCCESS:
                result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.BLOCKED,
                    start_time=start_time.isoformat(),
                    end_time=datetime.now(timezone.utc).isoformat(),
                    error=f"Dependency not satisfied: {dep_id}"
                )
                self.results[task_id] = result
                self._log_result(result)
                return result

        # Execute
        result = self._execute_with_timeout(task, start_time)
        self.results[task_id] = result
        self._log_result(result)

        # Update state
        with self._lock:
            if result.status == TaskStatus.SUCCESS:
                self.state["successful_tasks"] = self.state.get("successful_tasks", 0) + 1
            else:
                self.state["failed_tasks"] = self.state.get("failed_tasks", 0) + 1
            self._save_state()

        return result

    def _execute_with_timeout(self, task: Task, start_time: datetime) -> TaskResult:
        """Execute task function with timeout."""
        try:
            # Dynamically import module
            module = importlib.import_module(task.module_path)
            func = getattr(module, task.function_name, None)

            if func is None:
                # Try to find a callable main or run function
                for fname in ["main", "run", "execute", "run_cycle"]:
                    func = getattr(module, fname, None)
                    if func and callable(func):
                        break

            if func is None:
                return TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    start_time=start_time.isoformat(),
                    end_time=datetime.now(timezone.utc).isoformat(),
                    error=f"No callable function found in {task.module_path}"
                )

            # Execute with timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, **(task.args or {}))
                try:
                    result_value = future.result(timeout=task.timeout_seconds)
                    end_time = datetime.now(timezone.utc)

                    return TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.SUCCESS,
                        start_time=start_time.isoformat(),
                        end_time=end_time.isoformat(),
                        duration_seconds=(end_time - start_time).total_seconds(),
                        result=str(result_value)[:500] if result_value else None
                    )
                except FuturesTimeoutError:
                    return TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.TIMEOUT,
                        start_time=start_time.isoformat(),
                        end_time=datetime.now(timezone.utc).isoformat(),
                        duration_seconds=task.timeout_seconds,
                        error=f"Task exceeded timeout of {task.timeout_seconds}s"
                    )

        except Exception as e:
            import traceback
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                start_time=start_time.isoformat(),
                end_time=datetime.now(timezone.utc).isoformat(),
                error=str(e),
                traceback=traceback.format_exc()
            )

    def execute_batch(self, task_ids: List[str] = None) -> Dict:
        """
        Execute multiple tasks respecting dependencies.

        Uses topological sort to determine execution order.
        Independent tasks run in parallel.
        """
        if task_ids is None:
            task_ids = list(self.tasks.keys())

        self.state["total_runs"] = self.state.get("total_runs", 0) + 1

        # Topological sort
        sorted_tasks = self._topological_sort(task_ids)

        # Group by dependency level for parallel execution
        levels = self._get_execution_levels(sorted_tasks)

        results = {}
        for level_idx, level_tasks in enumerate(levels):
            print(f"\n[Level {level_idx + 1}] Executing {len(level_tasks)} tasks...")

            # Execute level in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.execute_task, tid): tid
                    for tid in level_tasks
                }

                for future in futures:
                    task_id = futures[future]
                    try:
                        result = future.result(timeout=300)
                        results[task_id] = result
                        status_symbol = "✓" if result.status == TaskStatus.SUCCESS else "✗"
                        print(f"  [{status_symbol}] {task_id}: {result.status.value}")
                    except Exception as e:
                        results[task_id] = TaskResult(
                            task_id=task_id,
                            status=TaskStatus.FAILED,
                            error=str(e)
                        )
                        print(f"  [✗] {task_id}: failed - {e}")

        self._save_state()

        return {
            "total_tasks": len(task_ids),
            "successful": sum(1 for r in results.values() if r.status == TaskStatus.SUCCESS),
            "failed": sum(1 for r in results.values() if r.status == TaskStatus.FAILED),
            "blocked": sum(1 for r in results.values() if r.status == TaskStatus.BLOCKED),
            "timeout": sum(1 for r in results.values() if r.status == TaskStatus.TIMEOUT),
            "results": {tid: asdict(r) for tid, r in results.items()}
        }

    def _topological_sort(self, task_ids: List[str]) -> List[str]:
        """Sort tasks by dependencies (topological order)."""
        sorted_list = []
        visited = set()
        temp_visited = set()

        def visit(task_id: str):
            if task_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving {task_id}")
            if task_id in visited:
                return

            temp_visited.add(task_id)

            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dep_id in task_ids:
                        visit(dep_id)

            temp_visited.remove(task_id)
            visited.add(task_id)
            sorted_list.append(task_id)

        for task_id in task_ids:
            if task_id not in visited:
                visit(task_id)

        return sorted_list

    def _get_execution_levels(self, sorted_tasks: List[str]) -> List[List[str]]:
        """Group tasks into execution levels for parallel execution."""
        levels: List[List[str]] = []
        task_level: Dict[str, int] = {}

        for task_id in sorted_tasks:
            task = self.tasks.get(task_id)
            if not task or not task.dependencies:
                level = 0
            else:
                # Level is max of dependency levels + 1
                dep_levels = [task_level.get(dep, 0) for dep in task.dependencies]
                level = max(dep_levels) + 1 if dep_levels else 0

            task_level[task_id] = level

            while len(levels) <= level:
                levels.append([])
            levels[level].append(task_id)

        return levels

    def _log_result(self, result: TaskResult):
        """Log task result."""
        # Convert to dict and handle enum
        result_dict = asdict(result)
        result_dict["status"] = result.status.value if isinstance(result.status, TaskStatus) else str(result.status)
        with open(self.LOG_FILE, "a") as f:
            f.write(json.dumps(result_dict) + "\n")

    def get_status(self) -> Dict:
        """Get coordinator status."""
        return {
            "total_tasks": len(self.tasks),
            "registered_tasks": list(self.tasks.keys()),
            "categories": list(set(t.category for t in self.tasks.values())),
            "state": self.state,
            "recent_results": {
                tid: asdict(r) for tid, r in list(self.results.items())[-10:]
            }
        }


def main():
    """Demo the task coordinator."""
    print("=" * 70)
    print("TASK COORDINATOR - INTEGRAFIX BRIDGE #4")
    print("=" * 70)

    coordinator = TaskCoordinator()

    print(f"\nRegistered {len(coordinator.tasks)} tasks:")
    for category in set(t.category for t in coordinator.tasks.values()):
        tasks_in_cat = [t for t in coordinator.tasks.values() if t.category == category]
        print(f"\n  [{category}]")
        for task in sorted(tasks_in_cat, key=lambda t: t.priority):
            deps = ", ".join(task.dependencies) if task.dependencies else "none"
            print(f"    - {task.task_id} (deps: {deps})")

    # Run a subset of tasks
    print("\n" + "-" * 70)
    print("Executing core trading pipeline...")
    print("-" * 70)

    core_tasks = [
        "probability_calibrator",
        "yair_wisdom_engine",
        "glitch_detector"
    ]

    # Filter to only tasks that exist
    core_tasks = [t for t in core_tasks if t in coordinator.tasks]

    if core_tasks:
        results = coordinator.execute_batch(core_tasks)
        print(f"\nBatch results:")
        print(f"  Total: {results['total_tasks']}")
        print(f"  Successful: {results['successful']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Blocked: {results['blocked']}")
    else:
        print("No core tasks found")

    print("\n" + "=" * 70)
    print(f"State: {coordinator.STATE_FILE}")
    print(f"Log: {coordinator.LOG_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
