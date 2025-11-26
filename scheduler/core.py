"""
Scheduler Core - Cron-like task scheduling engine

Provides:
- Cron-like syntax for scheduling tasks
- Support for one-time and recurring tasks
- Task dependency management
- In-memory and persistent schedules
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from croniter import croniter


@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    task_id: str
    task_name: str
    cron_expression: str  # Cron syntax: "*/15 * * * *" for every 15 minutes
    handler: str  # Module path to handler function, e.g., "scheduler.tasks.fetch_markets"
    enabled: bool = True
    dependencies: List[str] = None  # List of task_ids that must complete first
    timeout_seconds: int = 300  # 5 minutes default
    retry_count: int = 3
    retry_delay_seconds: int = 60
    one_time: bool = False  # If True, task runs once and is disabled
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Remove handler from serialization - it's loaded from REGISTERED_TASKS
        data.pop('handler', None)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], handler: Optional[Callable] = None) -> 'ScheduledTask':
        """Create from dictionary"""
        # Handler is looked up separately from REGISTERED_TASKS
        task_data = {k: v for k, v in data.items() if k != 'handler'}
        task = cls(**task_data, handler=handler or "")
        return task
    
    def should_run(self, last_run: Optional[datetime] = None) -> bool:
        """Check if task should run now based on cron expression"""
        if not self.enabled:
            return False
        
        if last_run is None:
            return True  # First run
        
        try:
            cron = croniter(self.cron_expression, last_run)
            next_run = cron.get_next(datetime)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            return now >= next_run
        except Exception:
            # If cron parsing fails, don't run
            return False


class Scheduler:
    """
    Task scheduler with cron-like functionality.
    Manages task schedules and determines when tasks should run.
    """
    
    def __init__(self, schedule_file: Optional[Path] = None):
        """
        Initialize scheduler
        
        Args:
            schedule_file: Path to schedule JSON file. Defaults to state/scheduler/schedule.json
        """
        if schedule_file is None:
            schedule_file = Path(__file__).parent.parent / "state" / "scheduler" / "schedule.json"
        
        self.schedule_file = Path(schedule_file)
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.tasks: Dict[str, ScheduledTask] = {}
        self.last_runs: Dict[str, datetime] = {}  # task_id -> last run time
        
        # Load existing schedule if available
        self._load_schedule()
    
    def _load_schedule(self):
        """Load schedule from file"""
        if not self.schedule_file.exists():
            return
        
        try:
            with open(self.schedule_file, 'r') as f:
                data = json.load(f)
            
            # Load tasks
            for task_data in data.get('tasks', []):
                task = ScheduledTask.from_dict(task_data)
                self.tasks[task.task_id] = task
            
            # Load last runs
            last_runs = data.get('last_runs', {})
            for task_id, timestamp_str in last_runs.items():
                try:
                    self.last_runs[task_id] = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    pass  # Skip invalid timestamps
        
        except Exception as e:
            print(f"Warning: Failed to load schedule from {self.schedule_file}: {e}")
    
    def _save_schedule(self):
        """Save schedule to file"""
        try:
            # Convert tasks to dict
            tasks_data = [task.to_dict() for task in self.tasks.values()]
            
            # Convert last runs to ISO strings
            last_runs_data = {
                task_id: dt.isoformat()
                for task_id, dt in self.last_runs.items()
            }
            
            data = {
                'tasks': tasks_data,
                'last_runs': last_runs_data,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Atomic write
            tmp_file = self.schedule_file.with_suffix('.tmp')
            with open(tmp_file, 'w') as f:
                json.dump(data, f, indent=2)
            tmp_file.replace(self.schedule_file)
        
        except Exception as e:
            print(f"Error: Failed to save schedule to {self.schedule_file}: {e}")
    
    def add_task(self, task: ScheduledTask) -> None:
        """Add or update a scheduled task"""
        self.tasks[task.task_id] = task
        self._save_schedule()
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            if task_id in self.last_runs:
                del self.last_runs[task_id]
            self._save_schedule()
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._save_schedule()
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_schedule()
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """List all tasks"""
        tasks = list(self.tasks.values())
        if enabled_only:
            tasks = [t for t in tasks if t.enabled]
        return tasks
    
    def get_due_tasks(self) -> List[ScheduledTask]:
        """Get tasks that are due to run now"""
        due_tasks = []
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            last_run = self.last_runs.get(task.task_id)
            if task.should_run(last_run):
                # Check dependencies
                if self._dependencies_satisfied(task):
                    due_tasks.append(task)
        
        return due_tasks
    
    def _dependencies_satisfied(self, task: ScheduledTask) -> bool:
        """Check if all task dependencies have run recently"""
        if not task.dependencies:
            return True
        
        for dep_task_id in task.dependencies:
            # Dependency must have run at least once
            if dep_task_id not in self.last_runs:
                return False
            
            # For now, just check that dependency has run at some point
            # Could add more sophisticated checks (e.g., must have run in last N minutes)
        
        return True
    
    def mark_task_run(self, task_id: str, run_time: Optional[datetime] = None) -> None:
        """Mark a task as having run"""
        if run_time is None:
            run_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        self.last_runs[task_id] = run_time
        
        # If one-time task, disable it
        if task_id in self.tasks and self.tasks[task_id].one_time:
            self.tasks[task_id].enabled = False
        
        self._save_schedule()
    
    def get_next_run(self, task_id: str) -> Optional[datetime]:
        """Get the next scheduled run time for a task"""
        task = self.tasks.get(task_id)
        if not task or not task.enabled:
            return None
        
        last_run = self.last_runs.get(task_id)
        if last_run is None:
            # Never run, so next run is now
            return datetime.now(timezone.utc).replace(tzinfo=None)
        
        try:
            cron = croniter(task.cron_expression, last_run)
            return cron.get_next(datetime)
        except Exception:
            return None
