import json
import subprocess
from datetime import datetime, timezone


TARGETS = [
    "register",
    "artifact",
    "verification",
    "complete",
]


def get_introspection():

    result = subprocess.run(
        ["python", "factory_introspection_extension_adapter.py"],
        capture_output=True,
        text=True
    )

    start = result.stdout.find("{")

    if start == -1:
        return {}

    return json.loads(result.stdout[start:])


def resolve(data):

    text = json.dumps(data).lower()

    matches = []

    for target in TARGETS:
        if target in text:
            matches.append(target)

    if "register" in matches and "artifact" in matches:
        return {
            "decision": "reuse_registration_organ",
            "action": "wire_pipeline_completion_to_registry",
            "matches": matches
        }

    return {
        "decision": "completion_adapter_required",
        "action": "extend_existing_pipeline",
        "matches": matches
    }


def run():

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_completion_registration_resolver",
        "decision": resolve(get_introspection())
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
