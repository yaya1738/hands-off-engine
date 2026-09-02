"""Legacy task-dispatch compatibility facade.

The former implementation executed shell commands over SSH as root and
persisted queue/results state directly. Remote execution is now owned by
FactoryAuthorityGateway. This module is retained for compatibility only.
"""

import sys

COMPUTE_NODES = [
    {"name": "ho-compute-1", "ip": "206.189.226.242"},
    {"name": "ho-compute-2a", "ip": "142.93.63.109"},
    {"name": "ho-compute-2b", "ip": "159.203.184.188"},
    {"name": "ho-scale", "ip": "162.243.175.211"},
    {"name": "ho-topdawg-4", "ip": "157.245.134.228"},
    {"name": "ho-mega-1", "ip": "147.182.172.241"},
    {"name": "ho-mega-2", "ip": "167.99.144.133"},
]

TASKS = {
    "fetch_markets": {"description": "Fetch Polymarket markets"},
    "health_check": {"description": "Node health check"},
}


def load_queue():
    return {"tasks": [], "last_dispatch": None}


def save_queue(queue):
    raise RuntimeError(
        "[FACTORY-AUTHORITY] legacy queue mutation is disabled; "
        "submit through FactoryAuthorityGateway"
    )


def log_result(result):
    raise RuntimeError(
        "[FACTORY-AUTHORITY] legacy result persistence is disabled; "
        "submit through FactoryAuthorityGateway"
    )


def dispatch_to_node(node, task_name):
    if task_name not in TASKS:
        return {"error": f"Unknown task: {task_name}"}
    return {
        "node": node["name"],
        "ip": node["ip"],
        "task": task_name,
        "success": False,
        "error": "[FACTORY-AUTHORITY] remote execution is disabled; submit through FactoryAuthorityGateway",
    }


def dispatch_all(task_name):
    return [dispatch_to_node(node, task_name) for node in COMPUTE_NODES]


def status():
    print("=== COMPUTE CLUSTER STATUS (NON-AUTHORITATIVE) ===")
    for node in COMPUTE_NODES:
        result = dispatch_to_node(node, "health_check")
        print(f"✗ {node['name']:15} ({node['ip']:15}): {result['error']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: task_dispatch.py [status|dispatch <task>|list]")
        raise SystemExit(1)
    cmd = sys.argv[1]
    if cmd == "status":
        status()
    elif cmd == "dispatch" and len(sys.argv) > 2:
        print(dispatch_all(sys.argv[2]))
    elif cmd == "list":
        for name, task in TASKS.items():
            print(f"  {name}: {task['description']}")
    else:
        print("Unknown command")
