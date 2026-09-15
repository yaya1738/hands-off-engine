#!/usr/bin/env python3
"""Project an already-produced system health report for shared observation.

The legacy health monitors remain producers of health data. This adapter is a
bounded, read-only projection so Factory/Control Room consumers can use those
signals without creating another state store or coupling health checks to
execution.
"""
from __future__ import annotations

from typing import Any, Dict


def project_system_health(health: Dict[str, Any]) -> Dict[str, Any]:
    """Return a bounded health observation; malformed input fails closed."""
    if not isinstance(health, dict):
        return {"available": False}

    components = health.get("components")
    if not isinstance(components, dict):
        components = {}

    checks = health.get("checks")
    if not isinstance(checks, dict):
        checks = {}

    errors = health.get("errors")
    if not isinstance(errors, list):
        errors = []

    return {
        "available": True,
        "status": health.get("status"),
        "generated_at": health.get("generated_at"),
        "components": {str(key): str(value) for key, value in components.items()},
        "checks": {
            "latest_snapshot_age_sec": checks.get("latest_snapshot_age_sec"),
            "latest_fetch_age_sec": checks.get("latest_fetch_age_sec"),
            "num_snapshots": checks.get("num_snapshots", 0),
            "recent_error_rate": checks.get("recent_error_rate", 0.0),
            "most_recent_run_status": checks.get("most_recent_run_status"),
        },
        "error_count": len(errors),
    }


__all__ = ["project_system_health"]
