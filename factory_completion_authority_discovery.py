import json
import subprocess
from datetime import datetime, timezone

KEYWORDS = [
    "approve",
    "finalize",
    "complete",
    "commit",
    "promote",
    "publish",
    "register",
    "verify",
]


def run_probe():
    result = subprocess.run(
        ["python", "factory_introspection_extension_adapter.py"],
        capture_output=True,
        text=True
    )

    start = result.stdout.find("{")

    if start == -1:
        return {}

    return json.loads(result.stdout[start:])


def search(data):

    text = json.dumps(data).lower()

    matches = [
        word for word in KEYWORDS
        if word in text
    ]

    if matches:
        return {
            "decision": "existing_completion_capability_detected",
            "matches": matches,
            "action": "reuse_existing_component"
        }

    return {
        "decision": "completion_capability_missing",
        "action": "extend_existing_pipeline"
    }


def run():

    report = run_probe()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_completion_authority_discovery",
        "decision": search(report)
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
