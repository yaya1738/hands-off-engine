import json
import subprocess
from datetime import datetime, timezone


TARGETS = {
    "decision_engine": [
        "decision",
        "engine",
        "policy",
        "adaptive",
    ],
    "improvement_planner": [
        "improvement",
        "planner",
        "optimizer",
        "strategy",
    ],
    "runtime_coordinator": [
        "runtime",
        "coordinator",
        "orchestrator",
        "control",
    ],
}


def run_capability_analyzer():

    result = subprocess.run(
        ["python", "factory_capability_analyzer.py"],
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


def resolve():

    report = run_capability_analyzer()

    capabilities = report.get(
        "capabilities",
        {}
    )

    results = {}

    for target, keywords in TARGETS.items():

        matches = []

        for capability, data in capabilities.items():

            files = " ".join(
                data.get("files", [])
            ).lower()

            combined = capability.lower() + " " + files

            score = sum(
                1
                for keyword in keywords
                if keyword in combined
            )

            if score:
                matches.append(
                    {
                        "capability": capability,
                        "score": score,
                        "files": data.get("files", [])[:5],
                    }
                )

        if matches:
            results[target] = {
                "status": "found_under_existing_capability",
                "action": "reuse",
                "matches": sorted(
                    matches,
                    key=lambda x: x["score"],
                    reverse=True
                ),
            }
        else:
            results[target] = {
                "status": "not_found",
                "action": "candidate_for_creation",
            }


    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_authority_false_negative_resolver",
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(resolve(), indent=2))
