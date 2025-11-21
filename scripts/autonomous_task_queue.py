#!/usr/bin/env python3
"""
Autonomous Task Queue System

Enables continuous Claude Code engagement without requiring manual prompts:

1. Orchestrator/monitors detect needs → add tasks to queue
2. Claude Code sessions (like this one) → read queue and execute tasks autonomously
3. Tasks completed → documented and removed from queue

This achieves "always working" behavior where Claude Code is continuously
engaged in serving user Yair Siegel, even across session boundaries.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
import uuid


class AutonomousTaskQueue:
    """Manage autonomous tasks for Claude Code to execute"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.queue_file = repo_root / 'state' / 'autonomous_task_queue.json'
        self.completed_log = repo_root / 'state' / 'autonomous_tasks_completed.jsonl'

    def load_queue(self) -> List[Dict]:
        """Load current task queue"""
        if not self.queue_file.exists():
            return []

        with open(self.queue_file) as f:
            data = json.load(f)
            return data.get('tasks', [])

    def save_queue(self, tasks: List[Dict]):
        """Save task queue"""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'tasks': tasks
        }

        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_task(
        self,
        title: str,
        description: str,
        priority: str = 'normal',
        source: str = 'orchestrator',
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add a new autonomous task.

        Args:
            title: Short task title
            description: Detailed task description for Claude
            priority: 'critical', 'high', 'normal', 'low'
            source: What created this task (orchestrator, healthcheck, etc.)
            metadata: Additional context

        Returns:
            task_id
        """
        tasks = self.load_queue()

        task = {
            'id': str(uuid.uuid4()),
            'title': title,
            'description': description,
            'priority': priority,
            'source': source,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {}
        }

        tasks.append(task)
        self.save_queue(tasks)

        print(f"✓ Added autonomous task: {title}")
        return task['id']

    def get_next_task(self) -> Optional[Dict]:
        """
        Get highest priority pending task.

        Priority order: critical > high > normal > low
        Within same priority: oldest first
        """
        tasks = self.load_queue()
        if not tasks:
            return None

        # Sort by priority then age
        priority_order = {'critical': 0, 'high': 1, 'normal': 2, 'low': 3}

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                priority_order.get(t.get('priority', 'normal'), 2),
                t.get('created_at', '')
            )
        )

        return sorted_tasks[0] if sorted_tasks else None

    def get_all_tasks(self) -> List[Dict]:
        """Get all pending tasks"""
        return self.load_queue()

    def complete_task(self, task_id: str, result: str = "completed"):
        """
        Mark task as completed and remove from queue.

        Args:
            task_id: Task ID to complete
            result: Completion result/notes
        """
        tasks = self.load_queue()

        # Find and remove task
        task = None
        remaining_tasks = []

        for t in tasks:
            if t['id'] == task_id:
                task = t
            else:
                remaining_tasks.append(t)

        if not task:
            print(f"Warning: Task {task_id} not found in queue")
            return

        # Save updated queue
        self.save_queue(remaining_tasks)

        # Log completion
        completion_record = {
            'task': task,
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'result': result
        }

        self.completed_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.completed_log, 'a') as f:
            f.write(json.dumps(completion_record) + '\n')

        print(f"✓ Completed task: {task['title']}")

    def remove_task(self, task_id: str):
        """Remove task from queue without completing (if no longer relevant)"""
        tasks = self.load_queue()
        remaining = [t for t in tasks if t['id'] != task_id]
        self.save_queue(remaining)
        print(f"✓ Removed task {task_id} from queue")

    def display_queue(self):
        """Display current queue for Claude Code session"""
        tasks = self.load_queue()

        if not tasks:
            print("○ No pending autonomous tasks")
            return

        print(f"\n{'='*60}")
        print(f"AUTONOMOUS TASK QUEUE ({len(tasks)} pending)")
        print('='*60)

        # Group by priority
        for priority in ['critical', 'high', 'normal', 'low']:
            priority_tasks = [t for t in tasks if t.get('priority') == priority]

            if priority_tasks:
                print(f"\n{priority.upper()} PRIORITY:")
                for task in priority_tasks:
                    age = self._get_task_age(task)
                    print(f"\n  [{task['id'][:8]}...] {task['title']}")
                    print(f"  Source: {task['source']} | Age: {age}")
                    print(f"  {task['description'][:150]}...")

        print(f"\n{'='*60}\n")

    def _get_task_age(self, task: Dict) -> str:
        """Get human-readable task age"""
        created = task.get('created_at', '')
        if not created:
            return "unknown"

        try:
            created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
            age = datetime.now(timezone.utc) - created_dt

            hours = age.total_seconds() / 3600
            if hours < 1:
                return f"{int(age.total_seconds() / 60)}m"
            elif hours < 24:
                return f"{int(hours)}h"
            else:
                return f"{int(hours / 24)}d"
        except:
            return "unknown"


def main():
    """CLI interface for task queue management"""
    import sys

    repo_root = Path(__file__).parent.parent
    queue = AutonomousTaskQueue(repo_root)

    if len(sys.argv) < 2:
        queue.display_queue()
        return

    command = sys.argv[1]

    if command == 'list':
        queue.display_queue()

    elif command == 'add':
        if len(sys.argv) < 4:
            print("Usage: autonomous_task_queue.py add <title> <description> [priority]")
            return

        title = sys.argv[2]
        description = sys.argv[3]
        priority = sys.argv[4] if len(sys.argv) > 4 else 'normal'

        task_id = queue.add_task(title, description, priority, source='manual')
        print(f"Task ID: {task_id}")

    elif command == 'complete':
        if len(sys.argv) < 3:
            print("Usage: autonomous_task_queue.py complete <task_id> [result]")
            return

        task_id = sys.argv[2]
        result = sys.argv[3] if len(sys.argv) > 3 else "completed"
        queue.complete_task(task_id, result)

    elif command == 'next':
        task = queue.get_next_task()
        if task:
            print(json.dumps(task, indent=2))
        else:
            print("No pending tasks")

    else:
        print(f"Unknown command: {command}")
        print("Commands: list, add, complete, next")


if __name__ == '__main__':
    main()
