"""
Task Runner - Execute scheduled tasks with retries and logging

Handles:
- Task execution in background
- Retry logic with exponential backoff
- Task locking to prevent overlapping runs
- Execution history logging
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import signal

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger
from scheduler.core import Scheduler, ScheduledTask
from scheduler.tasks import get_task_handler


class TaskLock:
    """Simple file-based task lock to prevent concurrent execution"""
    
    def __init__(self, lock_dir: Path, task_id: str):
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.lock_dir / f"{task_id}.lock"
        self.task_id = task_id
        self.acquired = False
    
    def acquire(self, timeout: int = 0) -> bool:
        """
        Try to acquire lock.
        
        Args:
            timeout: How long to wait for lock in seconds (0 = don't wait)
        
        Returns:
            True if lock acquired, False otherwise
        """
        start_time = time.time()
        
        while True:
            if not self.lock_file.exists():
                try:
                    # Create lock file with PID and timestamp
                    lock_data = {
                        "task_id": self.task_id,
                        "pid": os.getpid(),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    with open(self.lock_file, 'w') as f:
                        json.dump(lock_data, f)
                    self.acquired = True
                    return True
                except Exception:
                    pass  # Lock file might have been created by another process
            
            # Check if we should keep waiting
            if timeout == 0:
                return False
            
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return False
            
            # Wait a bit before retrying
            time.sleep(0.1)
    
    def release(self):
        """Release the lock"""
        if self.acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                self.acquired = False
            except Exception:
                pass  # Lock file might have been removed already
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock for task {self.task_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class TaskRunner:
    """
    Executes scheduled tasks with retry logic and logging.
    """
    
    def __init__(
        self,
        scheduler: Scheduler,
        history_file: Optional[Path] = None,
        lock_dir: Optional[Path] = None,
    ):
        """
        Initialize task runner
        
        Args:
            scheduler: Scheduler instance
            history_file: Path to execution history log (JSONL)
            lock_dir: Directory for task lock files
        """
        self.scheduler = scheduler
        self.audit = get_audit_logger(component="scheduler.runner")
        
        # Set up history file
        if history_file is None:
            history_file = Path(__file__).parent.parent / "state" / "scheduler" / "history.jsonl"
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up lock directory
        if lock_dir is None:
            lock_dir = Path(__file__).parent.parent / "state" / "scheduler" / "locks"
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        
        self.running = False
        self.run_thread = None
    
    def _log_history(self, task_id: str, event: str, data: Dict[str, Any]):
        """Log task execution event to history file"""
        try:
            history_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task_id,
                "event": event,
                "data": data,
            }
            
            with open(self.history_file, 'a') as f:
                f.write(json.dumps(history_entry) + '\n')
        except Exception as e:
            print(f"Warning: Failed to log history: {e}", file=sys.stderr)
    
    def execute_task(
        self,
        task: ScheduledTask,
        skip_lock: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a single task
        
        Args:
            task: Task to execute
            skip_lock: Skip lock acquisition (for manual runs)
        
        Returns:
            Result dictionary with status and details
        """
        start_time = time.time()
        result = {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "unknown",
        }
        
        # Try to acquire lock
        lock = TaskLock(self.lock_dir, task.task_id)
        if not skip_lock:
            if not lock.acquire(timeout=0):
                result["status"] = "skipped"
                result["message"] = "Task already running (lock held)"
                result["duration_seconds"] = time.time() - start_time
                
                self._log_history(task.task_id, "skipped", result)
                return result
        
        try:
            # Get task handler
            handler = get_task_handler(task.task_id)
            if handler is None:
                raise ValueError(f"No handler registered for task: {task.task_id}")
            
            # Log execution start
            self.audit.log_action(
                action_type="task_execution_start",
                action_data={
                    "task_id": task.task_id,
                    "task_name": task.task_name,
                },
                session_id="scheduler"
            )
            self._log_history(task.task_id, "started", {})
            
            # Execute with retries
            last_error = None
            for attempt in range(task.retry_count + 1):
                try:
                    # Run the task handler
                    task_result = handler()
                    
                    # Task succeeded
                    result["status"] = "success"
                    result["task_result"] = task_result
                    result["attempts"] = attempt + 1
                    break
                
                except Exception as e:
                    last_error = e
                    
                    # Log the error
                    self.audit.log_error(
                        error_type="task_execution_error",
                        error_message=str(e),
                        stack_trace=traceback.format_exc(),
                        context={
                            "task_id": task.task_id,
                            "attempt": attempt + 1,
                            "max_attempts": task.retry_count + 1,
                        },
                        session_id="scheduler"
                    )
                    
                    # If not last attempt, wait and retry
                    if attempt < task.retry_count:
                        time.sleep(task.retry_delay_seconds)
                    else:
                        # All retries exhausted
                        result["status"] = "failed"
                        result["error"] = str(e)
                        result["attempts"] = attempt + 1
            
            # If we still have an error, task failed
            if last_error and result["status"] == "unknown":
                result["status"] = "failed"
                result["error"] = str(last_error)
            
            # Mark task as run in scheduler
            self.scheduler.mark_task_run(task.task_id)
            
        except Exception as e:
            # Unexpected error during execution setup
            result["status"] = "failed"
            result["error"] = str(e)
            
            self.audit.log_error(
                error_type="task_runner_error",
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                context={"task_id": task.task_id},
                session_id="scheduler"
            )
        
        finally:
            # Release lock
            if not skip_lock:
                lock.release()
            
            # Record completion
            result["end_time"] = datetime.now(timezone.utc).isoformat()
            result["duration_seconds"] = time.time() - start_time
            
            # Log to history
            self._log_history(task.task_id, "completed", result)
            
            # Log to audit
            self.audit.log_action(
                action_type="task_execution_complete",
                action_data={
                    "task_id": task.task_id,
                    "task_name": task.task_name,
                    "status": result["status"],
                    "duration_seconds": result["duration_seconds"],
                },
                result=result["status"],
                session_id="scheduler"
            )
        
        return result
    
    def run_once(self) -> Dict[str, Any]:
        """
        Run one iteration of the scheduler - check and execute due tasks.
        
        Returns:
            Summary of execution
        """
        due_tasks = self.scheduler.get_due_tasks()
        
        results = []
        for task in due_tasks:
            result = self.execute_task(task)
            results.append(result)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tasks_checked": len(self.scheduler.list_tasks(enabled_only=True)),
            "tasks_executed": len(results),
            "results": results,
        }
    
    def run_loop(self, check_interval: int = 60):
        """
        Run scheduler loop continuously
        
        Args:
            check_interval: Seconds between checks for due tasks
        """
        self.running = True
        
        print(f"Scheduler started. Checking for tasks every {check_interval} seconds.")
        print(f"Press Ctrl+C to stop.")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\nStopping scheduler...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running:
                try:
                    summary = self.run_once()
                    
                    if summary["tasks_executed"] > 0:
                        print(f"[{summary['timestamp']}] Executed {summary['tasks_executed']} tasks")
                        for result in summary["results"]:
                            status_icon = "✓" if result["status"] == "success" else "✗"
                            print(f"  {status_icon} {result['task_name']} - {result['status']}")
                
                except Exception as e:
                    print(f"Error in scheduler loop: {e}", file=sys.stderr)
                    self.audit.log_error(
                        error_type="scheduler_loop_error",
                        error_message=str(e),
                        stack_trace=traceback.format_exc(),
                        session_id="scheduler"
                    )
                
                # Wait for next check
                time.sleep(check_interval)
        
        finally:
            print("Scheduler stopped.")
    
    def start_background(self, check_interval: int = 60):
        """Start scheduler in background thread"""
        if self.run_thread and self.run_thread.is_alive():
            print("Scheduler already running in background")
            return False
        
        self.run_thread = threading.Thread(
            target=self.run_loop,
            args=(check_interval,),
            daemon=True
        )
        self.run_thread.start()
        return True
    
    def stop(self):
        """Stop background scheduler"""
        self.running = False
        if self.run_thread:
            self.run_thread.join(timeout=5)
