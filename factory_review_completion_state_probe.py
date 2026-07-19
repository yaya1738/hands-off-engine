import json
from pathlib import Path
from datetime import datetime, timezone


KEYWORDS = [
    "ready_for_review",
    "completion",
    "approve",
    "register",
    "artifact",
    "verification"
]


def scan_files():

    results = []

    for path in Path(".").rglob("*.py"):
        try:
            text = path.read_text(errors="ignore").lower()
        except:
            continue

        matches = [
            k for k in KEYWORDS
            if k in text
        ]

        if matches:
            results.append({
                "file": str(path),
                "matches": matches
            })

    return results


def run():

    matches = scan_files()

    completion = [
        x for x in matches
        if "completion" in x["matches"]
        or "approve" in x["matches"]
        or "register" in x["matches"]
    ]

    if completion:
        decision = {
            "decision": "existing_completion_related_components_found",
            "action": "wire_existing_components"
        }
    else:
        decision = {
            "decision": "completion_bridge_still_missing",
            "action": "extend_pipeline"
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_review_completion_state_probe",
        "matches_found": len(matches),
        "decision": decision,
        "samples": matches[:10]
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
