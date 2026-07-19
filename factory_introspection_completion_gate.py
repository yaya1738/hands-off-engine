import json
import subprocess
from datetime import datetime, timezone


EXPECTED_DECISION = "introspection_capability_complete"


def run_verifier():

    result = subprocess.run(
        [
            "python",
            "factory_introspection_capability_completion_verifier.py",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    output = result.stdout

    start = output.find("{")

    if start == -1:
        return {}

    try:
        return json.loads(output[start:])
    except Exception:
        return {}


def run():

    result = run_verifier()

    verification = result.get("verification", {})

    if isinstance(verification, dict):
        decision_value = verification.get("decision")
    else:
        decision_value = verification

    if isinstance(decision_value, dict):
        actual = decision_value.get("decision")
    else:
        actual = decision_value

    if actual == EXPECTED_DECISION:

        status = {
            "status": "PASS",
            "action": "reuse_existing_introspection_system",
        }

    else:

        status = {
            "status": "FAIL",
            "action": "inspect_missing_capabilities",
            "expected": EXPECTED_DECISION,
            "actual": actual,
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_introspection_completion_gate",
        "verification": status,
        "raw_result": result,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
