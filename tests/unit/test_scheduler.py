"""
Unit tests for scheduler module

Tests the task scheduling system components:
- ScheduledTask dataclass
- Scheduler core functionality
- TaskRunner execution
"""

import json
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from scheduler.core import Scheduler, ScheduledTask
from scheduler.runner import TaskRunner, TaskLock
from scheduler.tasks import REGISTERED_TASKS, get_task_handler


@pytest.fixture
def temp_schedule_file(tmp_path):
    """Fixture that provides a temporary schedule file"""
    schedule_file = tmp_path / "schedule.json"
    return schedule_file


@pytest.fixture
def temp_history_file(tmp_path):
    """Fixture that provides a temporary history file"""
    history_file = tmp_path / "history.jsonl"
    return history_file


@pytest.fixture
def temp_lock_dir(tmp_path):
    """Fixture that provides a temporary lock directory"""
    lock_dir = tmp_path / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return lock_dir


class TestScheduledTask:
    """Tests for ScheduledTask dataclass"""
    
    def test_scheduled_task_creation(self):
        """Test creating a ScheduledTask"""
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
            timeout_seconds=300,
        )
        
        assert task.task_id == "test_task"
        assert task.task_name == "Test Task"
        assert task.cron_expression == "*/5 * * * *"
        assert task.enabled is True
        assert task.timeout_seconds == 300
        assert task.dependencies == []
    
    def test_scheduled_task_to_dict(self):
        """Test converting task to dictionary"""
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["task_id"] == "test_task"
        assert task_dict["task_name"] == "Test Task"
        assert task_dict["cron_expression"] == "*/5 * * * *"
        assert "handler" not in task_dict  # Handler is removed
    
    def test_scheduled_task_from_dict(self):
        """Test creating task from dictionary"""
        task_data = {
            "task_id": "test_task",
            "task_name": "Test Task",
            "cron_expression": "*/5 * * * *",
            "enabled": True,
            "timeout_seconds": 300,
        }
        
        task = ScheduledTask.from_dict(task_data, handler="test_handler")
        
        assert task.task_id == "test_task"
        assert task.task_name == "Test Task"
        assert task.handler == "test_handler"
    
    def test_should_run_never_run_before(self):
        """Test that task should run if never run before"""
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        assert task.should_run(last_run=None) is True
    
    def test_should_run_disabled(self):
        """Test that disabled task should not run"""
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=False,
        )
        
        assert task.should_run(last_run=None) is False


class TestScheduler:
    """Tests for Scheduler core functionality"""
    
    def test_scheduler_creation(self, temp_schedule_file):
        """Test creating a scheduler"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        
        assert scheduler.schedule_file == temp_schedule_file
        assert len(scheduler.tasks) == 0
    
    def test_add_task(self, temp_schedule_file):
        """Test adding a task"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        scheduler.add_task(task)
        
        assert "test_task" in scheduler.tasks
        assert scheduler.tasks["test_task"].task_name == "Test Task"
    
    def test_remove_task(self, temp_schedule_file):
        """Test removing a task"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        scheduler.add_task(task)
        assert "test_task" in scheduler.tasks
        
        result = scheduler.remove_task("test_task")
        assert result is True
        assert "test_task" not in scheduler.tasks
    
    def test_enable_disable_task(self, temp_schedule_file):
        """Test enabling and disabling a task"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        scheduler.add_task(task)
        
        # Disable
        scheduler.disable_task("test_task")
        assert scheduler.tasks["test_task"].enabled is False
        
        # Enable
        scheduler.enable_task("test_task")
        assert scheduler.tasks["test_task"].enabled is True
    
    def test_list_tasks(self, temp_schedule_file):
        """Test listing tasks"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        
        task1 = ScheduledTask(
            task_id="task1",
            task_name="Task 1",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        task2 = ScheduledTask(
            task_id="task2",
            task_name="Task 2",
            cron_expression="*/10 * * * *",
            handler="test_handler",
            enabled=False,
        )
        
        scheduler.add_task(task1)
        scheduler.add_task(task2)
        
        all_tasks = scheduler.list_tasks()
        assert len(all_tasks) == 2
        
        enabled_tasks = scheduler.list_tasks(enabled_only=True)
        assert len(enabled_tasks) == 1
        assert enabled_tasks[0].task_id == "task1"
    
    def test_mark_task_run(self, temp_schedule_file):
        """Test marking a task as run"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        scheduler.add_task(task)
        
        run_time = datetime.now(timezone.utc).replace(tzinfo=None)
        scheduler.mark_task_run("test_task", run_time)
        
        assert "test_task" in scheduler.last_runs
        assert scheduler.last_runs["test_task"] == run_time
    
    def test_one_time_task_disabled_after_run(self, temp_schedule_file):
        """Test that one-time tasks are disabled after running"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
            one_time=True,
        )
        
        scheduler.add_task(task)
        assert scheduler.tasks["test_task"].enabled is True
        
        scheduler.mark_task_run("test_task")
        assert scheduler.tasks["test_task"].enabled is False
    
    def test_save_and_load_schedule(self, temp_schedule_file):
        """Test saving and loading schedule"""
        scheduler1 = Scheduler(schedule_file=temp_schedule_file)
        
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        scheduler1.add_task(task)
        scheduler1.mark_task_run("test_task")
        
        # Load into new scheduler
        scheduler2 = Scheduler(schedule_file=temp_schedule_file)
        
        assert "test_task" in scheduler2.tasks
        assert scheduler2.tasks["test_task"].task_name == "Test Task"
        assert "test_task" in scheduler2.last_runs


class TestTaskLock:
    """Tests for TaskLock file-based locking"""
    
    def test_lock_acquire_and_release(self, temp_lock_dir):
        """Test acquiring and releasing a lock"""
        lock = TaskLock(temp_lock_dir, "test_task")
        
        # Lock should not exist initially
        assert not lock.lock_file.exists()
        
        # Acquire lock
        result = lock.acquire()
        assert result is True
        assert lock.lock_file.exists()
        
        # Release lock
        lock.release()
        assert not lock.lock_file.exists()
    
    def test_lock_prevents_double_acquisition(self, temp_lock_dir):
        """Test that lock prevents double acquisition"""
        lock1 = TaskLock(temp_lock_dir, "test_task")
        lock2 = TaskLock(temp_lock_dir, "test_task")
        
        # First lock should succeed
        assert lock1.acquire() is True
        
        # Second lock should fail (no timeout)
        assert lock2.acquire(timeout=0) is False
        
        # Release first lock
        lock1.release()
        
        # Now second lock should succeed
        assert lock2.acquire() is True
        lock2.release()
    
    def test_lock_context_manager(self, temp_lock_dir):
        """Test using lock as context manager"""
        lock = TaskLock(temp_lock_dir, "test_task")
        
        with lock:
            assert lock.lock_file.exists()
        
        assert not lock.lock_file.exists()


class TestTaskRunner:
    """Tests for TaskRunner execution"""
    
    def test_task_runner_creation(self, temp_schedule_file, temp_history_file, temp_lock_dir):
        """Test creating a task runner"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        runner = TaskRunner(
            scheduler=scheduler,
            history_file=temp_history_file,
            lock_dir=temp_lock_dir,
        )
        
        assert runner.scheduler == scheduler
        assert runner.history_file == temp_history_file
        assert runner.lock_dir == temp_lock_dir
    
    @patch('scheduler.runner.get_task_handler')
    def test_execute_task_success(self, mock_get_handler, temp_schedule_file, temp_history_file, temp_lock_dir):
        """Test successful task execution"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        runner = TaskRunner(
            scheduler=scheduler,
            history_file=temp_history_file,
            lock_dir=temp_lock_dir,
        )
        
        # Mock task handler
        mock_handler = Mock(return_value={"status": "success", "result": "test"})
        mock_get_handler.return_value = mock_handler
        
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
        )
        
        scheduler.add_task(task)
        
        result = runner.execute_task(task, skip_lock=True)
        
        assert result["status"] == "success"
        assert "task_result" in result
        assert mock_handler.called
    
    @patch('scheduler.runner.get_task_handler')
    def test_execute_task_with_retry(self, mock_get_handler, temp_schedule_file, temp_history_file, temp_lock_dir):
        """Test task execution with retry on failure"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        runner = TaskRunner(
            scheduler=scheduler,
            history_file=temp_history_file,
            lock_dir=temp_lock_dir,
        )
        
        # Mock task handler that fails twice then succeeds
        mock_handler = Mock(
            side_effect=[
                Exception("First failure"),
                Exception("Second failure"),
                {"status": "success"}
            ]
        )
        mock_get_handler.return_value = mock_handler
        
        task = ScheduledTask(
            task_id="test_task",
            task_name="Test Task",
            cron_expression="*/5 * * * *",
            handler="test_handler",
            enabled=True,
            retry_count=3,
            retry_delay_seconds=0,  # No delay for testing
        )
        
        scheduler.add_task(task)
        
        result = runner.execute_task(task, skip_lock=True)
        
        assert result["status"] == "success"
        assert result["attempts"] == 3
        assert mock_handler.call_count == 3
    
    def test_history_logging(self, temp_schedule_file, temp_history_file, temp_lock_dir):
        """Test that task execution is logged to history"""
        scheduler = Scheduler(schedule_file=temp_schedule_file)
        runner = TaskRunner(
            scheduler=scheduler,
            history_file=temp_history_file,
            lock_dir=temp_lock_dir,
        )
        
        # Use a real task from registered tasks
        task = ScheduledTask(
            task_id="health_check",
            task_name="Health Check",
            cron_expression="*/5 * * * *",
            handler="health_check",
            enabled=True,
        )
        
        scheduler.add_task(task)
        
        result = runner.execute_task(task, skip_lock=True)
        
        # Check history file exists and has content
        assert temp_history_file.exists()
        
        with open(temp_history_file, 'r') as f:
            lines = f.readlines()
        
        # Should have at least 2 lines (started and completed)
        assert len(lines) >= 2
        
        # Parse and verify
        events = [json.loads(line) for line in lines]
        assert any(e["event"] == "started" for e in events)
        assert any(e["event"] == "completed" for e in events)


class TestRegisteredTasks:
    """Tests for registered tasks"""
    
    def test_registered_tasks_exist(self):
        """Test that all required tasks are registered"""
        required_tasks = [
            "fetch_markets",
            "calculate_alpha",
            "generate_report",
            "backup_state",
            "health_check",
        ]
        
        for task_id in required_tasks:
            assert task_id in REGISTERED_TASKS
    
    def test_get_task_handler(self):
        """Test getting task handlers"""
        handler = get_task_handler("health_check")
        assert handler is not None
        assert callable(handler)
    
    def test_health_check_task(self):
        """Test that health_check task runs"""
        handler = get_task_handler("health_check")
        result = handler()
        
        assert result["status"] in ["success", "warning"]
        assert "checks" in result
        assert "overall_status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
