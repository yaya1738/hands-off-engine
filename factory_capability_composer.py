import json
from datetime import datetime

from pathlib import Path

TARGETS = [
    "factory_capability_constructor.py",
    "factory_workflow_executor.py",
    "ai/factory/workflow_engine.py",
    "ai/factory/development_orchestrator.py",
    "ai/factory/development_executor.py",
]

def detect_connections():
    found = {}

    for target in TARGETS:
        found[target] = Path(target).exists()

    return found


def compose(goal):
    connections = detect_connections()

    required = [
        "ai/factory/workflow_engine.py",
        "ai/factory/development_orchestrator.py",
    ]

    if all(connections.get(x) for x in required):
        decision = "reuse_existing_pipeline"
        next_step = "bind_capability_request_to_workflow_execution"
    else:
        decision = "missing_execution_bridge"
        next_step = "create_minimal_adapter"

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "goal": goal,
        "connections": connections,
        "decision": decision,
        "next_step": next_step,
    }


if __name__ == "__main__":
    import sys

    goal = " ".join(sys.argv[1:]) or "unknown"

    print(json.dumps(
        compose(goal),
        indent=2
    ))
