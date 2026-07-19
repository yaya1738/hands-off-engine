import json
import subprocess
from datetime import datetime, timezone


def run_controller():

    result = subprocess.run(
        [
            "python",
            "factory_construction_autonomy_controller.py"
        ],
        capture_output=True,
        text=True
    )

    start = result.stdout.find("{")

    if start == -1:
        return {}

    return json.loads(result.stdout[start:])


def inspect_state(data):

    text = json.dumps(data).lower()

    return {
        "ready_for_review_found": "ready_for_review" in text,
        "validation_found": "validation" in text,
        "registration_found": "register" in text,
        "completion_found": "complete" in text
    }


def run():

    result = run_controller()
    state = inspect_state(result)

    if (
        state["ready_for_review_found"]
        and not state["completion_found"]
    ):
        decision = {
            "decision": "missing_review_completion_bridge",
            "action": "extend_existing_pipeline"
        }
    else:
        decision = {
            "decision": "completion_path_detected",
            "action": "reuse_existing_components"
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_completion_flow_verifier",
        "state": state,
        "decision": decision
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
