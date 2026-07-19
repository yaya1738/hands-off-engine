import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


CREATION_KEYWORDS = [
    "create",
    "build",
    "develop",
    "artifact",
    "generate",
    "constructor",
    "write",
]


NEW_COMPONENT = {
    "name": "Factory Script Creator",
    "responsibility": [
        "generate file",
        "run syntax check",
        "run tests",
        "register artifact",
    ],
    "scope": "narrow construction capability"
}


def run_capability_analyzer():
    result = subprocess.run(
        ["python", "factory_capability_analyzer.py"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    output = result.stdout

    try:
        start = output.find("{")
        data = json.loads(output[start:])
        return data

    except Exception:
        return {
            "raw_output": output,
            "parse_error": True,
        }


def find_construction_capability(report):
    matches = []

    text = json.dumps(report).lower()

    for keyword in CREATION_KEYWORDS:
        if keyword in text:
            matches.append(keyword)

    return matches


def create_missing_creator():
    return {
        "decision": "create_missing_capability",
        "capability": NEW_COMPONENT,
        "status": "planned",
    }


def run():
    report = run_capability_analyzer()

    matches = find_construction_capability(report)

    if matches:
        decision = {
            "decision": "reuse_existing_construction_organ",
            "matches": matches,
            "source": "factory_capability_analyzer",
        }
    else:
        decision = create_missing_creator()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_script_creator_capability_router",
        "decision": decision,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
