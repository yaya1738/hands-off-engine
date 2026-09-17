#!/usr/bin/env python3
"""Build bounded Factory decision context from one shared snapshot."""
from __future__ import annotations
from typing import Any, Dict

def build_factory_decision_context(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Return decision evidence already present in the shared snapshot."""
    if not isinstance(snapshot, dict):
        return {"available": False}
    health = snapshot.get("correlation_health")
    admission = snapshot.get("admission_observation")
    authority = snapshot.get("authority_decision")
    assessment = snapshot.get("factory_assessment")
    system_health = snapshot.get("system_health_observation")
    learning = snapshot.get("learning_observation")
    if not isinstance(health, dict): health = {"available": False}
    if not isinstance(admission, dict): admission = {"available": False}
    if not isinstance(authority, dict): authority = {"available": False}
    if not isinstance(assessment, dict): assessment = {"available": False}
    if not isinstance(system_health, dict): system_health = {"available": False}
    if not isinstance(learning, dict): learning = {"available": False}
    event_count = int(health.get("event_count", 0))
    correlated = int(health.get("correlated_event_count", 0))
    return {
        "available": bool(health.get("available", False)),
        "interaction": {
            "correlation_rate": correlated / event_count if event_count else 1.0,
            "orphan_reply_count": int(health.get("orphan_reply_count", 0)),
            "single_event_count": int(health.get("single_event_count", 0)),
            "task_thread_coverage": float(health.get("explicit_task_thread_coverage") or 0.0),
            "window_truncated": bool(health.get("window", {}).get("truncated", False)),
        },
        "admission": {
            "available": bool(admission.get("available", False)),
            "msg_id": admission.get("msg_id"), "reply_to": admission.get("reply_to"),
            "task_id": admission.get("task_id"), "admitted": bool(admission.get("admitted", False)),
            "reason": admission.get("reason"), "decided_at": admission.get("decided_at"),
        },
        "authority": {
            "available": bool(authority.get("available", False)),
            "msg_id": authority.get("msg_id"), "reply_to": authority.get("reply_to"),
            "task_id": authority.get("task_id"), "decision": authority.get("decision"),
            "reason": authority.get("reason"), "approval_required": bool(authority.get("approval_required", True)),
            "execution_enabled": bool(authority.get("execution_enabled", False)), "decided_at": authority.get("decided_at"),
        },
        "assessment": {
            "available": bool(assessment.get("available", False)), "health": assessment.get("health"),
            "gaps": list(assessment.get("gaps", [])), "objective": assessment.get("objective"),
        },
        "system_health": {
            "available": bool(system_health.get("available", False)),
            "status": system_health.get("status"), "generated_at": system_health.get("generated_at"),
            "component_count": int(system_health.get("component_count", 0)),
            "error_count": int(system_health.get("error_count", 0)),
            "recent_error_rate": system_health.get("recent_error_rate", 0.0),
            "most_recent_run_status": system_health.get("most_recent_run_status"),
            "latest_snapshot_age_sec": system_health.get("latest_snapshot_age_sec"),
            "latest_fetch_age_sec": system_health.get("latest_fetch_age_sec"),
        },
        "learning": {
            "available": bool(learning.get("available", False)),
            "lifecycle_entry_count": int(learning.get("lifecycle_entry_count", 0)),
            "completed_count": int(learning.get("completed_count", 0)),
            "observed_count": int(learning.get("observed_count", 0)),
            "outcome_count": int(learning.get("outcome_count", 0)),
            "success_count": int(learning.get("success_count", 0)),
            "failure_count": int(learning.get("failure_count", 0)),
            "outcome_observation_rate": learning.get("outcome_observation_rate"),
        },
    }

__all__ = ["build_factory_decision_context"]
