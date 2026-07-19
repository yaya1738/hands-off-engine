import json
import subprocess
from datetime import datetime, timezone


TARGETS = {
    "capability_router": [
        "capability",
        "router",
        "routing",
    ],
    "decision_engine": [
        "decision",
        "engine",
    ],
    "build_controller": [
        "controller",
        "builder",
        "constructor",
    ],
    "improvement_planner": [
        "improvement",
        "planner",
    ],
    "runtime_coordinator": [
        "runtime",
        "coordinator",
    ],
}


def run_forensic_engine():
    result = subprocess.run(
        ["python", "factory_forensic_engine.py"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    start = result.stdout.find("{")

    if start == -1:
        return {}

    try:
        return json.loads(result.stdout[start:])
    except Exception:
        return {}


def discover():

    report = run_forensic_engine()

    found = {}

    for category, keywords in TARGETS.items():
        matches = []

        for tool in report.get("available_tools", []):
            name = tool.get("tool", "").lower()

            exports = " ".join(
                tool.get("exports", [])
            ).lower()

            combined = name + " " + exports

            score = sum(
                1
                for keyword in keywords
                if keyword in combined
            )

            if score:
                matches.append({
                    "tool": tool.get("tool"),
                    "score": score,
                })

        found[category] = matches


    decisions = {}

    for category, matches in found.items():

        if matches:
            decisions[category] = {
                "status": "existing",
                "action": "reuse",
                "matches": matches,
            }
        else:
            decisions[category] = {
                "status": "missing",
                "action": "create_only_if_required",
            }


    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_authority_layer_discovery",
        "decisions": decisions,
    }


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2))
