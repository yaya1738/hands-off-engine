#!/usr/bin/env python3
"""Legacy compute dispatch compatibility surface.

Historical versions opened root SSH sessions to a hard-coded compute cluster
and executed task command strings outside the Factory authority boundary.
That path is disabled. Compute work must be routed through the governed
Factory authority and its approved infrastructure provider.
"""

import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
QUEUE_FILE = STATE_DIR / "task_queue.json"
RESULTS_FILE = STATE_DIR / "task_results.jsonl"

TASKS = {
    "fetch_markets": {"description": "Fetch Polymarket markets"},
    "health_check": {"description": "Node health check"},
}


def load_queue():
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return {"tasks": [], "last_dispatch": None}


def save_queue(queue):
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, default=str))


def log_result(result):
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(result, default=str) + "\n")


def dispatch_to_node(node, task_name):
    """Refuse legacy remote execution; return a machine-readable handoff."""
    if task_name not in TASKS:
        return {"error": f"Unknown task: {task_name}"}

    return {
        "node": node.get("name"),
        "ip": node.get("ip"),
        "task": task_name,
        "timestamp": datetime.utcnow().isoformat(),
        "success": False,
        "blocked": True,
        "error": "legacy_remote_execution_disabled",
        "authority": "FactoryAuthorityGateway",
    }


def dispatch_all(task_name):
    """Refuse the legacy cluster fan-out path."""
    result = dispatch_to_node({"name": "legacy-cluster", "ip": ""}, task_name)
    log_result(result)
    return [result]


def status():
    """Report that legacy cluster probing is disabled."""
    result = dispatch_to_node({"name": "legacy-cluster", "ip": ""}, "health_check")
    print("LEGACY_REMOTE_EXECUTION_DISABLED")
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: task_dispatch.py [status|dispatch <task>|list]")
        print("Tasks:", list(TASKS.keys()))
        sys.exit(1)

    command = sys.argv[1]
    if command == "status":
        status()
    elif command == "dispatch" and len(sys.argv) > 2:
        dispatch_all(sys.argv[2])
    elif command == "list":
        for name, task in TASKS.items():
            print(f"  {name}: {task['description']}")
    else:
        print("Unknown command")
