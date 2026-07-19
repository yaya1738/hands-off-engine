import json
import subprocess
from datetime import datetime, timezone


TARGET = "create factory construction lifecycle controller"


def run_router(goal):
    result = subprocess.run(
        ["python", "factory_construction_router.py", goal],
        capture_output=True,
        text=True
    )

    output = result.stdout
    start = output.find("{")

    if start == -1:
        return {
            "error": "router produced no json",
            "stdout": output,
            "stderr": result.stderr
        }

    return json.loads(output[start:])


def analyze(result):

    text = json.dumps(result).lower()

    if "ready_for_review" in text:
        return {
            "decision": "construction_pipeline_available",
            "action": "use_existing_pipeline"
        }

    if "new_construction_pipeline" in text:
        return {
            "decision": "construction_route_exists",
            "action": "continue_existing_route"
        }

    return {
        "decision": "construction_gap_detected",
        "action": "create_missing_lifecycle_controller"
    }


def run():

    router_result = run_router(TARGET)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_construction_autonomy_controller",
        "router_result": router_result,
        "decision": analyze(router_result)
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
