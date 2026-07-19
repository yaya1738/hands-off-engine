import json
import subprocess
from datetime import datetime, timezone


KEYWORDS = [
    "controller",
    "gateway",
    "service",
    "request",
    "lifecycle",
    "workflow",
    "manager"
]


def run():

    result = subprocess.run(
        ["python", "factory_forensic_engine.py"],
        capture_output=True,
        text=True
    )

    output = result.stdout

    start = output.find("{")

    if start == -1:
        return {"error": "no forensic output"}

    report = json.loads(output[start:])

    matches = []

    for tool in report.get("available_tools", []):
        combined = (
            tool.get("tool","") +
            " " +
            " ".join(tool.get("exports",[]))
        ).lower()

        found = [
            k for k in KEYWORDS
            if k in combined
        ]

        if found:
            matches.append({
                "tool": tool.get("tool"),
                "matches": found,
                "exports": tool.get("exports",[])
            })

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_lifecycle_authority_probe",
        "matches": matches
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
