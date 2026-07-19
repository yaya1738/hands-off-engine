import json
import sys
from datetime import datetime, timezone

from factory_autonomous_capability_loop import run as lifecycle_run


def register_capability(goal, lifecycle):
    registry_entry = {
        "capability": goal,
        "created": datetime.now(timezone.utc).isoformat(),
        "status": lifecycle.get("status"),
        "validated": (
            lifecycle
            .get("records", {})
            .get("orchestrator", {})
            .get("validation", [{}])[0]
            .get("validated", False)
        ),
        "source": "factory_autonomous_capability_loop",
    }

    with open("factory_capability_registry_runtime.json", "a") as f:
        f.write(json.dumps(registry_entry) + "\n")

    return registry_entry


def run(goal):
    lifecycle = lifecycle_run(goal)

    if lifecycle.get("status") != "completed":
        return {
            "decision": "not_registered",
            "lifecycle": lifecycle,
        }

    capability = register_capability(
        goal,
        lifecycle
    )

    return {
        "goal": goal,
        "decision": "registered",
        "capability": capability,
        "lifecycle": lifecycle,
    }


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:])

    if not goal:
        goal = "create automatic program builder"

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
