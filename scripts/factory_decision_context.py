#!/usr/bin/env python3
"""Read-only decision context derived from the shared Control Room snapshot."""
from __future__ import annotations

from typing import Any, Dict


def build_factory_decision_context(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Return bounded evidence suitable for Factory decision-making; fail closed."""
    if not isinstance(snapshot, dict):
        return {"available": False}

    health = snapshot.get("correlation_health")
    admission = snapshot.get("admission_observation")
    assessment = snapshot.get("factory_assessment")

    if not isinstance(health, dict):
        health = {"available": False}
    if not isinstance(admission, dict):
        admission = {"available": False}
    if not isinstance(assessment, dict):
        assessment = {"available": False}

    return {
        "available": bool(health.get("available", False)),
        "interaction": {
            "correlation_rate": (
                float(health.get("correlated_event_count", 0)) /
                int(health.get("event_count", 0))
                if int(health.get("event_count", 0)) else 1.0
            ),
            "orphan_reply_count": int(health.get("orphan_reply_count", 0)),
            "single_event_count": int(health.get("single_event_count", 0)),
            "task_thread_coverage": float(health.get("explicit_task_thread_coverage", 0.0)),
            "window_truncated": bool(health.get("window", {}).get("truncated", False)),
        },
        "admission": {
            "available": bool(admission.get("available", False)),
            "msg_id": admission.get("msg_id"),
            "reply_to": admission.get("reply_to"),
            "task_id": admission.get("task_id"),
            "admitted": bool(admission.get("admitted", False)),
            "reason": admission.get("reason"),
            "decided_at": admission.get("decided_at"),
        },
        "assessment": {
            "available": bool(assessment.get("available", False)),
            "health": assessment.get("health"),
            "gaps": list(assessment.get("gaps", [])),
            "objective": assessment.get("objective"),
        },
    }


__all__ = ["build_factory_decision_context"]
