"""Fail-closed integrity audit for the durable Factory execution journal."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TERMINAL = {"COMPLETED", "FAILED", "CANCELLED"}
ALLOWED_TRANSITIONS = {
    None: {"STARTED"},
    "STARTED": {"COMPLETED", "FAILED", "CANCELLED"},
    "COMPLETED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
}


def audit(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"valid": True, "entries": 0, "interrupted": 0, "errors": [], "missing": True}
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "entries": 0, "interrupted": 0, "errors": [f"journal unreadable: {exc}"]}

    if not isinstance(payload, list):
        errors.append("journal root must be a list")
        payload = []

    latest: dict[str, str] = {}
    seen: set[str] = set()
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            errors.append(f"entry {index} is not an object")
            continue
        execution_id = entry.get("execution_id")
        state = entry.get("state")
        timestamp = entry.get("ts")
        if not isinstance(execution_id, str) or not execution_id.strip():
            errors.append(f"entry {index} has invalid execution_id")
            continue
        if not isinstance(state, str) or state not in ALLOWED_TRANSITIONS:
            errors.append(f"entry {index} has invalid state: {state!r}")
            continue
        if not isinstance(timestamp, str) or not timestamp.strip():
            errors.append(f"entry {index} has invalid ts")
        if not isinstance(entry.get("intent", {}), dict):
            errors.append(f"entry {index} intent must be an object")

        previous = latest.get(execution_id)
        if previous is None and execution_id in seen:
            errors.append(f"entry {index} follows malformed execution history for {execution_id}")
        allowed = ALLOWED_TRANSITIONS.get(previous, set())
        if state not in allowed:
            errors.append(f"entry {index} invalid transition {previous!r} -> {state!r} for {execution_id}")
        latest[execution_id] = state
        seen.add(execution_id)

    interrupted = sum(state not in TERMINAL for state in latest.values())
    return {
        "valid": not errors,
        "entries": len(payload),
        "executions": len(latest),
        "interrupted": interrupted,
        "errors": errors,
        "missing": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="state/factory_execution_journal.json")
    args = parser.parse_args()
    result = audit(Path(args.path))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
