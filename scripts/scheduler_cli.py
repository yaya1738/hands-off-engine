#!/usr/bin/env python3
"""
Scheduler CLI - Command-line interface for scheduler management

Commands:
- start: Start scheduler daemon
- stop: Stop scheduler daemon
- status: Show scheduler status
- list: List all scheduled tasks
- run: Manually run a task
- add: Add a new task
- enable/disable: Enable or disable a task
- history: View task execution history
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheduler.core import Scheduler, ScheduledTask
from scheduler.runner import TaskRunner
from scheduler.tasks import REGISTERED_TASKS


def cmd_start(args):
    """Start the scheduler daemon"""
    scheduler = Scheduler()
    runner = TaskRunner(scheduler)
    
    print("Starting scheduler...")
    print(f"Check interval: {args.interval} seconds")
    
    # Run in foreground (daemon mode would require more setup)
    try:
        runner.run_loop(check_interval=args.interval)
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")


def cmd_status(args):
    """Show scheduler status"""
    scheduler = Scheduler()
    
    tasks = scheduler.list_tasks()
    enabled_tasks = [t for t in tasks if t.enabled]
    
    print(f"Scheduler Status")
    print("=" * 60)
    print(f"Total tasks: {len(tasks)}")
    print(f"Enabled tasks: {len(enabled_tasks)}")
    print(f"Disabled tasks: {len(tasks) - len(enabled_tasks)}")
    print()
    
    if enabled_tasks:
        print("Next scheduled runs:")
        for task in enabled_tasks:
            next_run = scheduler.get_next_run(task.task_id)
            if next_run:
                print(f"  {task.task_name}: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")


def cmd_list(args):
    """List all scheduled tasks"""
    scheduler = Scheduler()
    
    tasks = scheduler.list_tasks()
    
    if not tasks:
        print("No scheduled tasks found.")
        print("\nTo add default tasks, run: scheduler_cli.py init")
        return
    
    print(f"Scheduled Tasks")
    print("=" * 80)
    
    for task in tasks:
        status = "✓ Enabled" if task.enabled else "✗ Disabled"
        print(f"\n{task.task_name} ({task.task_id})")
        print(f"  Status: {status}")
        print(f"  Schedule: {task.cron_expression}")
        print(f"  Timeout: {task.timeout_seconds}s")
        print(f"  Retries: {task.retry_count}")
        
        if task.dependencies:
            print(f"  Dependencies: {', '.join(task.dependencies)}")
        
        next_run = scheduler.get_next_run(task.task_id)
        if next_run:
            print(f"  Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if task.task_id in scheduler.last_runs:
            last_run = scheduler.last_runs[task.task_id]
            print(f"  Last run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")


def cmd_run(args):
    """Manually run a task"""
    scheduler = Scheduler()
    runner = TaskRunner(scheduler)
    
    task = scheduler.get_task(args.task_id)
    if not task:
        print(f"Error: Task '{args.task_id}' not found")
        return 1
    
    print(f"Running task: {task.task_name}")
    print(f"Task ID: {task.task_id}")
    print()
    
    result = runner.execute_task(task, skip_lock=args.force)
    
    print(f"Status: {result['status']}")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    
    if result['status'] == 'success':
        if 'task_result' in result:
            print("\nTask result:")
            print(json.dumps(result['task_result'], indent=2))
    else:
        if 'error' in result:
            print(f"\nError: {result['error']}")
    
    return 0 if result['status'] == 'success' else 1


def cmd_init(args):
    """Initialize scheduler with default tasks"""
    scheduler = Scheduler()
    
    print("Initializing scheduler with default tasks...")
    
    for task_id, task_info in REGISTERED_TASKS.items():
        # Check if task already exists
        if scheduler.get_task(task_id):
            print(f"  - {task_id}: Already exists, skipping")
            continue
        
        # Create task
        task = ScheduledTask(
            task_id=task_id,
            task_name=task_id.replace('_', ' ').title(),
            cron_expression=task_info["cron"],
            handler=task_id,  # Store task_id as handler reference
            enabled=True,
            timeout_seconds=task_info.get("timeout", 300),
            retry_count=3,
            retry_delay_seconds=60,
        )
        
        scheduler.add_task(task)
        print(f"  ✓ {task_id}: Added")
    
    print(f"\nScheduler initialized with {len(REGISTERED_TASKS)} tasks")
    print(f"Schedule saved to: {scheduler.schedule_file}")


def cmd_enable(args):
    """Enable a task"""
    scheduler = Scheduler()
    
    if scheduler.enable_task(args.task_id):
        print(f"Task '{args.task_id}' enabled")
        return 0
    else:
        print(f"Error: Task '{args.task_id}' not found")
        return 1


def cmd_disable(args):
    """Disable a task"""
    scheduler = Scheduler()
    
    if scheduler.disable_task(args.task_id):
        print(f"Task '{args.task_id}' disabled")
        return 0
    else:
        print(f"Error: Task '{args.task_id}' not found")
        return 1


def cmd_history(args):
    """View task execution history"""
    history_file = Path(__file__).parent.parent / "state" / "scheduler" / "history.jsonl"
    
    if not history_file.exists():
        print("No execution history found")
        return
    
    # Read history
    entries = []
    with open(history_file, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                pass
    
    # Filter by task_id if specified
    if args.task_id:
        entries = [e for e in entries if e.get('task_id') == args.task_id]
    
    # Get last N entries
    if args.last:
        entries = entries[-args.last:]
    
    if not entries:
        print("No history entries found")
        return
    
    print(f"Task Execution History")
    print("=" * 80)
    
    for entry in entries:
        timestamp = entry.get('timestamp', 'Unknown')
        task_id = entry.get('task_id', 'Unknown')
        event = entry.get('event', 'Unknown')
        data = entry.get('data', {})
        
        print(f"\n[{timestamp}] {task_id} - {event}")
        
        if event == 'completed':
            status = data.get('status', 'Unknown')
            duration = data.get('duration_seconds', 0)
            print(f"  Status: {status}")
            print(f"  Duration: {duration:.2f}s")
            
            if 'error' in data:
                print(f"  Error: {data['error']}")


def cmd_remove(args):
    """Remove a task"""
    scheduler = Scheduler()
    
    if scheduler.remove_task(args.task_id):
        print(f"Task '{args.task_id}' removed")
        return 0
    else:
        print(f"Error: Task '{args.task_id}' not found")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Scheduler CLI - Manage scheduled tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # start command
    start_parser = subparsers.add_parser('start', help='Start scheduler daemon')
    start_parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    
    # status command
    subparsers.add_parser('status', help='Show scheduler status')
    
    # list command
    subparsers.add_parser('list', help='List all scheduled tasks')
    
    # run command
    run_parser = subparsers.add_parser('run', help='Manually run a task')
    run_parser.add_argument('task_id', help='Task ID to run')
    run_parser.add_argument(
        '--force',
        action='store_true',
        help='Force run even if task is already running'
    )
    
    # init command
    subparsers.add_parser('init', help='Initialize scheduler with default tasks')
    
    # enable command
    enable_parser = subparsers.add_parser('enable', help='Enable a task')
    enable_parser.add_argument('task_id', help='Task ID to enable')
    
    # disable command
    disable_parser = subparsers.add_parser('disable', help='Disable a task')
    disable_parser.add_argument('task_id', help='Task ID to disable')
    
    # history command
    history_parser = subparsers.add_parser('history', help='View task execution history')
    history_parser.add_argument('--task-id', help='Filter by task ID')
    history_parser.add_argument('--last', type=int, help='Show last N entries')
    
    # remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a task')
    remove_parser.add_argument('task_id', help='Task ID to remove')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Dispatch to command handler
    command_map = {
        'start': cmd_start,
        'status': cmd_status,
        'list': cmd_list,
        'run': cmd_run,
        'init': cmd_init,
        'enable': cmd_enable,
        'disable': cmd_disable,
        'history': cmd_history,
        'remove': cmd_remove,
    }
    
    handler = command_map.get(args.command)
    if handler:
        return handler(args) or 0
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
