from __future__ import annotations

import json
from typing import Any, Iterable


REQUIRED_AUTONOMOUS_CHECKS = frozenset(
    {
        "Deployment Preflight",
        "Secret Scan",
        "Factory Authority Regression",
        "Autonomous Objective Cycle",
    }
)


class AutonomousReadinessError(ValueError):
    """Raised when machine-proven readiness cannot be established."""


def evaluate_checks(
    checks: Iterable[dict[str, Any]],
    required: Iterable[str] = REQUIRED_AUTONOMOUS_CHECKS,
) -> dict[str, Any]:
    """Evaluate an independent CI quorum for the bounded autonomous lane.

    Readiness is evidence only: it never grants authority and never changes
    human approval or financial execution policy.
    """
    required_set = frozenset(required)
    if not required_set:
        raise AutonomousReadinessError("no required autonomous checks configured")

    normalized: dict[str, str] = {}
    for check in checks:
        if not isinstance(check, dict):
            continue
        name = str(check.get("name", "")).strip()
        bucket = str(check.get("bucket", "")).strip().lower()
        if name:
            normalized[name] = bucket

    missing = sorted(required_set - normalized.keys())
    failing = sorted(
        name for name in required_set
        if name in normalized and normalized[name] != "pass"
    )
    passed = sorted(name for name in required_set if normalized.get(name) == "pass")
    ready = not missing and not failing and len(passed) == len(required_set)

    return {
        "ready": ready,
        "required_checks": sorted(required_set),
        "passed_checks": passed,
        "missing_checks": missing,
        "failing_checks": failing,
    }


def evaluate_json(payload: str) -> dict[str, Any]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise AutonomousReadinessError("check payload must be a JSON array")
    return evaluate_checks(data)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Evaluate autonomous Factory CI readiness.")
    parser.add_argument("--checks-json", required=True)
    args = parser.parse_args()
    try:
        result = evaluate_json(args.checks_json)
    except (AutonomousReadinessError, json.JSONDecodeError) as exc:
        print(f"DENY: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ready"] else 1)
