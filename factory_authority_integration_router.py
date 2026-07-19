import json
from datetime import datetime, timezone

from factory_authority_false_negative_resolver import resolve


TARGETS = {
    "decision_engine": [
        "ai/factory/decision_engine.py",
        "ai/factory/runtime.py",
    ],
    "improvement_planner": [
        "ai/factory/improvement_runtime.py",
        "ai/factory/improvement_orchestrator.py",
        "ai/factory/runtime.py",
    ],
    "runtime_coordinator": [
        "ai/factory/runtime_coordinator.py",
        "ai/factory/runtime.py",
        "ai/factory/control_plane.py",
    ],
}


def classify(matches):
    if not matches:
        return {
            "action": "create_missing_capability",
            "reason": "no_existing_component_found",
        }

    return {
        "action": "reuse_existing_component",
        "reason": "existing_capability_detected",
        "components": matches,
    }


def run():
    discovery = resolve()

    authority_map = {}

    for target, expected_files in TARGETS.items():
        result = discovery.get("results", {}).get(target, {})

        matches = result.get("matches", [])

        usable = []

        for item in matches:
            files = item.get("files", [])

            overlap = [
                f for f in files
                if f in expected_files
            ]

            if overlap:
                usable.append({
                    "capability": item.get("capability"),
                    "score": item.get("score"),
                    "files": overlap,
                })

        authority_map[target] = classify(usable)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_authority_integration_router",
        "authority_map": authority_map,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
