import json
import subprocess
from datetime import datetime, timezone


GOAL = "create factory review authority adapter"


def request():

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

    return json.loads(result.stdout[start:])


def run():

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_review_authority_builder_request",
        "goal": GOAL,
        "construction_request": request()
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
