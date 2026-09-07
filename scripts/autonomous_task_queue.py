#!/usr/bin/env python3
"""Durable task queue for the autonomous execution system.

Tasks are created by internal automation or authenticated external control
surfaces and are consumed by the governed autonomous supervisor. No consumer
AI session is required to claim, execute, or continue queued work.
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class AutonomousTaskQueue:
    """Manage durable work for the governed autonomous executor."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.queue_file = repo_root / "state" / "autonomous_task_queue.json"
        self.completed_log = repo_root / "state" / "autonomous_tasks_completed.jsonl"

    def load_queue(self) -> List[Dict]:
        if not self.queue_file.exists():
            return []
        with open(self.queue_file, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("tasks", [])

    def save_queue(self, tasks: List[Dict]):
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.queue_file.write_text(
            json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(), "tasks": tasks}, indent=2),
            encoding="utf-8",
        )

    def add_task(self, title: str, description: str, priority: str = "normal", source: str = "orchestrator", metadata: Optional[Dict] = None) -> str:
        tasks = self.load_queue()
        task = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "priority": priority,
            "source": source,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        tasks.append(task)
        self.save_queue(tasks)
        return task["id"]

    def get_next_task(self) -> Optional[Dict]:
        tasks = self.load_queue()
        if not tasks:
            return None
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        return min(tasks, key=lambda t: (priority_order.get(t.get("priority", "normal"), 2), t.get("created_at", "")))

    def get_all_tasks(self) -> List[Dict]:
        return self.load_queue()

    def complete_task(self, task_id: str, result: str = "completed"):
        tasks = self.load_queue()
        task = next((t for t in tasks if t["id"] == task_id), None)
        if not task:
            return
        self.save_queue([t for t in tasks if t["id"] != task_id])
        record = {"task": task, "completed_at": datetime.now(timezone.utc).isoformat(), "result": result}
        self.completed_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.completed_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def remove_task(self, task_id: str):
        self.save_queue([t for t in self.load_queue() if t["id"] != task_id])

    def display_queue(self):
        tasks = self.load_queue()
        if not tasks:
            print("No pending autonomous tasks")
            return
        for task in sorted(tasks, key=lambda t: t.get("created_at", "")):
            print(f"[{task['id']}] {task['priority']}: {task['title']} ({task['source']})")


def main():
    queue = AutonomousTaskQueue(Path(__file__).parent.parent)
    command = sys.argv[1] if len(sys.argv) > 1 else "list"
    if command == "list":
        queue.display_queue()
    elif command == "add" and len(sys.argv) >= 4:
        task_id = queue.add_task(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "normal", source="manual")
        print(f"Task ID: {task_id}")
    elif command == "complete" and len(sys.argv) >= 3:
        queue.complete_task(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "completed")
    elif command == "next":
        print(json.dumps(queue.get_next_task(), indent=2))
    else:
        print("Usage: autonomous_task_queue.py [list|add|complete|next]")


if __name__ == "__main__":
    main()
