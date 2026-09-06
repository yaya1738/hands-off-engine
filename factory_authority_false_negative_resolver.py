import json
from datetime import datetime, timezone

from factory_capability_analyzer import analyze, load_report


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
    """Analyze the existing capability report in-process.

    The analyzer's CLI entrypoint also writes a derived output file and spawns
    no privileged work. This resolver only needs the returned analysis, so it
    calls the reusable library functions directly instead of starting Python.
    """
    return analyze(load_report())


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
