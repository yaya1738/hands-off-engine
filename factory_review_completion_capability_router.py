import json
import subprocess
from datetime import datetime, timezone


KEYWORDS = [
    "review",
    "approve",
    "complete",
    "finalize",
    "validate",
    "merge",
    "commit",
]


def forensic():

    result = subprocess.run(
        ["python", "factory_introspection_execution_adapter.py"],
        capture_output=True,
        text=True
    )

    start = result.stdout.find("{")

    if start == -1:
        return {}

    return json.loads(result.stdout[start:])


def analyze(data):

    text = json.dumps(data).lower()

    found = [
        k for k in KEYWORDS
        if k in text
    ]

    if found:
        return {
            "decision": "reuse_existing_completion_capability",
            "matches": found
        }

    return {
        "decision": "missing_completion_authority",
        "action": "extend_existing_pipeline"
    }


def run():

    report = forensic()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_review_completion_capability_router",
        "decision": analyze(report)
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
