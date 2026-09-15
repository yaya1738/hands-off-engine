#!/usr/bin/env python3
"""Project bounded system-health evidence into Factory decision context."""
from __future__ import annotations

from typing import Any, Dict

from scripts.system_health_observability import project_system_health


def project_factory_health_context(health: Dict[str, Any]) -> Dict[str, Any]:
    """Return health evidence suitable for reasoning, never execution authority."""
    observation = project_system_health(health)
    if not observation.get("available", False):
        return {"available": False}

    checks = observation.get("checks", {})
    if not isinstance(checks, dict):
        checks = {}
    return {
        "available": True,
        "status": observation.get("status"),
        "generated_at": observation.get("generated_at"),
        "component_count": len(observation.get("components", {})),
        "error_count": int(observation.get("error_count", 0)),
        "recent_error_rate": checks.get("recent_error_rate", 0.0),
        "most_recent_run_status": checks.get("most_recent_run_status"),
        "latest_snapshot_age_sec": checks.get("latest_snapshot_age_sec"),
        "latest_fetch_age_sec": checks.get("latest_fetch_age_sec"),
    }


__all__ = ["project_factory_health_context"]
