import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent


def reconcile():
    income_file = ROOT / "state/income_engine.json"
    bridge_file = ROOT / "state/capital_bridge.json"

    income = json.loads(income_file.read_text())
    bridge = json.loads(bridge_file.read_text()) if bridge_file.exists() else {}

    events = income.get("capital_events", [])

    ids = [
        e.get("id")
        for e in events
        if e.get("id")
    ]

    duplicates = [
        k for k, v in Counter(ids).items()
        if v > 1
    ]

    missing_injection = [
        e for e in events
        if not e.get("capital_bridge_injected", False)
    ]

    return {
        "events": len(events),
        "total_event_value": sum(
            e.get("amount_usd", 0)
            for e in events
        ),
        "injected_events": len([
            e for e in events
            if e.get("capital_bridge_injected")
        ]),
        "missing_injection_events": len(missing_injection),
        "duplicate_event_ids": duplicates,
        "capital_bridge_exists": bridge_file.exists(),
        "health": (
            "healthy"
            if not duplicates and not missing_injection
            else "attention_required"
        )
    }


if __name__ == "__main__":
    print(json.dumps(reconcile(), indent=2))
