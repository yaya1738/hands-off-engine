import json
import subprocess
from datetime import datetime, timezone


GOAL = "create factory review completion bridge adapter"


def run():

    result = subprocess.run(
        [
            "python",
            "factory_construction_router.py",
            GOAL
        ],
        capture_output=True,
        text=True
    )

    start = result.stdout.find("{")

    if start == -1:
        return {
            "error": "no_json",
            "stdout": result.stdout
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_completion_bridge_builder_request",
        "goal": GOAL,
        "result": json.loads(result.stdout[start:])
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
