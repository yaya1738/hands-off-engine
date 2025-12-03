#!/usr/bin/env python3
"""
Task Dispatch System - Distributes work to compute nodes
Per SYSTEM_BLUEPRINT.md: Heavy compute goes to workers
"""

import json
import subprocess
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
QUEUE_FILE = STATE_DIR / 'task_queue.json'
RESULTS_FILE = STATE_DIR / 'task_results.jsonl'

# Compute nodes per SYSTEM_BLUEPRINT.md
COMPUTE_NODES = [
    {"name": "ho-compute-1", "ip": "206.189.226.242"},
    {"name": "ho-compute-2a", "ip": "142.93.63.109"},
    {"name": "ho-compute-2b", "ip": "159.203.184.188"},
    {"name": "ho-scale", "ip": "162.243.175.211"},
    {"name": "ho-topdawg-4", "ip": "157.245.134.228"},
    {"name": "ho-mega-1", "ip": "147.182.172.241"},
    {"name": "ho-mega-2", "ip": "167.99.144.133"},
]

# Available tasks
TASKS = {
    "fetch_markets": {
        "cmd": "PYTHONPATH=/root/hands-off-engine timeout 60 python3 /root/hands-off-engine/scripts/fetch_fresh_markets.py",
        "description": "Fetch Polymarket markets"
    },
    "health_check": {
        "cmd": "hostname && uptime && df -h / | tail -1",
        "description": "Node health check"
    }
}

def load_queue():
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return {"tasks": [], "last_dispatch": None}

def save_queue(queue):
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, default=str))

def log_result(result):
    with open(RESULTS_FILE, 'a') as f:
        f.write(json.dumps(result, default=str) + '\n')

def dispatch_to_node(node, task_name):
    """Dispatch a task to a compute node"""
    if task_name not in TASKS:
        return {"error": f"Unknown task: {task_name}"}
    
    task = TASKS[task_name]
    cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{node['ip']} '{task['cmd']}'"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return {
            "node": node["name"],
            "ip": node["ip"],
            "task": task_name,
            "timestamp": datetime.utcnow().isoformat(),
            "success": result.returncode == 0,
            "stdout": result.stdout[:500] if result.stdout else "",
            "stderr": result.stderr[:200] if result.stderr else ""
        }
    except Exception as e:
        return {
            "node": node["name"],
            "ip": node["ip"],
            "task": task_name,
            "timestamp": datetime.utcnow().isoformat(),
            "success": False,
            "error": str(e)
        }

def dispatch_all(task_name):
    """Dispatch task to all compute nodes"""
    results = []
    for node in COMPUTE_NODES:
        print(f"Dispatching {task_name} to {node['name']}...")
        result = dispatch_to_node(node, task_name)
        results.append(result)
        log_result(result)
        status = "✓" if result.get("success") else "✗"
        print(f"  {status} {node['name']}: {result.get('stdout', '')[:50] or result.get('error', '')[:50]}")
    return results

def status():
    """Show cluster status"""
    print("=== COMPUTE CLUSTER STATUS ===")
    for node in COMPUTE_NODES:
        result = dispatch_to_node(node, "health_check")
        status = "✓" if result.get("success") else "✗"
        info = result.get("stdout", "").replace('\n', ' ')[:60] if result.get("success") else "OFFLINE"
        print(f"{status} {node['name']:15} ({node['ip']:15}): {info}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: task_dispatch.py [status|dispatch <task>|list]")
        print("Tasks:", list(TASKS.keys()))
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "status":
        status()
    elif cmd == "dispatch" and len(sys.argv) > 2:
        dispatch_all(sys.argv[2])
    elif cmd == "list":
        for name, task in TASKS.items():
            print(f"  {name}: {task['description']}")
    else:
        print("Unknown command")
