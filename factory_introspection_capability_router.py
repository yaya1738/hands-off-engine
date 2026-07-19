import json
import subprocess
from datetime import datetime, timezone


KEYWORDS = [
    "inspect",
    "introspect",
    "contract",
    "probe",
    "reflection",
]


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
        return {
            "raw_output": output,
            "parse_error": True,
        }


def find_existing_probe_tools(report):
    matches = []

    tools = report.get("available_tools", [])

    for tool in tools:
        name = tool.get("tool", "").lower()

        exports = " ".join(
            tool.get("exports", [])
        ).lower()

        combined = name + " " + exports

        found = [
            keyword
            for keyword in KEYWORDS
            if keyword in combined
        ]

        if found:
            matches.append({
                "tool": tool.get("tool"),
                "matches": found,
                "exports": tool.get("exports", [])
            })

    return matches


def run():
    report = run_forensic_engine()

    existing = find_existing_probe_tools(report)

    if existing:
        decision = {
            "decision": "reuse_existing_probe_capability",
            "tools": existing,
        }

    else:
        decision = {
            "decision": "create_missing_probe_utility",
            "capability": {
                "name": "Factory Introspection Probe",
                "responsibility": [
                    "discover modules",
                    "discover classes",
                    "discover functions",
                    "inspect signatures",
                    "return JSON contracts",
                ],
            },
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_introspection_capability_router",
        "decision": decision,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
