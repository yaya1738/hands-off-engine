import json
import subprocess
from datetime import datetime, timezone


KEYWORDS = [
    "review",
    "approve",
    "validate",
    "verification",
    "complete",
    "accept",
]


def probe():

    result = subprocess.run(
        ["python", "factory_introspection_extension_adapter.py"],
        capture_output=True,
        text=True
    )

    start = result.stdout.find("{")

    if start == -1:
        return {}

    return json.loads(result.stdout[start:])


def find(data):

    text = json.dumps(data).lower()

    matches = []

    for word in KEYWORDS:
        if word in text:
            matches.append(word)

    return matches


def run():

    matches = find(probe())

    if matches:
        decision = {
            "decision": "existing_review_authority_candidates_found",
            "matches": matches,
            "action": "reuse_or_adapt"
        }
    else:
        decision = {
            "decision": "review_authority_missing",
            "action": "extend_pipeline"
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_review_authority_resolver",
        "decision": decision
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
