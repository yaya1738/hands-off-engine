import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


KEYWORDS = [
    "inspect",
    "introspect",
    "contract",
    "probe",
    "reflection",
]


MISSING_UTILITY = {
    "name": "factory_introspection_probe.py",
    "responsibility": [
        "discover modules",
        "discover classes",
        "discover functions",
        "inspect signatures",
        "return JSON contracts",
    ],
}


def run_forensic_engine():
    result = subprocess.run(
        ["python", "factory_forensic_engine.py"],
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


def find_existing_capability(report):
    matches = []

    for tool in report.get("available_tools", []):
        name = tool.get("tool", "").lower()
        exports = " ".join(
            tool.get("exports", [])
        ).lower()

        combined = name + " " + exports

        found = [
            k for k in KEYWORDS
            if k in combined
        ]

        if found:
            matches.append({
                "tool": tool.get("tool"),
                "matches": found,
            })

    return matches


def connect_existing(matches):
    return {
        "action": "connect_existing_tool",
        "tools": matches,
    }


def create_missing():
    return {
        "action": "create_missing_utility",
        "utility": MISSING_UTILITY,
    }


def run():

    report = run_forensic_engine()

    existing = find_existing_capability(report)

    if existing:
        result = connect_existing(existing)

    else:
        result = create_missing()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "controller": "factory_introspection_controller",
        "decision": result,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
