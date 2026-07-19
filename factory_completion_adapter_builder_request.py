import json
import subprocess
from datetime import datetime, timezone


GOAL = "create completion registration adapter"


def run_construction_request():

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
            "error": "no_json_returned",
            "stdout": result.stdout
        }

    return json.loads(result.stdout[start:])


def run():

    lifecycle = run_construction_request()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_completion_adapter_builder_request",
        "goal": GOAL,
        "lifecycle": lifecycle
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
