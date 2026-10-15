"""Shadow-only bridge from Node 1 persisted observations to routing evidence.

No dispatch or scheduler integration is performed here. Callers may log the
result beside an existing governed route decision for comparison.
"""
from datetime import datetime, timezone

from scripts.device_condition_trends import summarize_device_condition


def assess_node_routing_shadow(node_state, task_class="routine", now=None,
                               manual_reports=(), thermal_event_threshold=2):
    """Produce an explainable advisory without granting execution authority."""
    if not isinstance(node_state, dict):
        node_state = {}
    history = node_state.get("device_condition_history")
    if not isinstance(history, list):
        history = []
    summary = summarize_device_condition(
        history, now=now, manual_reports=manual_reports,
    )
    reasons = []
    if summary["status"] == "unknown":
        reasons.append("device_condition_unknown")
    elif summary["status"] == "stale":
        reasons.append("device_condition_stale")
    if summary["thermal_events_in_window"] >= thermal_event_threshold:
        reasons.append("recurring_thermal_pressure")
    if summary["resource_pressure_events_in_window"]:
        reasons.append("recurring_resource_pressure")
    if summary["manual_defects"]:
        reasons.append("reported_device_defect")

    if summary["status"] != "fresh":
        recommendation = "collect_fresh_observations"
    elif reasons:
        recommendation = "consider_alternate_capable_node"
    else:
        recommendation = "no_condition_based_objection"

    if task_class not in {"routine", "intensive", "optional_intensive"}:
        reasons.append("unknown_task_class")
        recommendation = "manual_policy_review"

    return {
        "node_id": node_state.get("node_id", "unknown"),
        "task_class": task_class,
        "runtime_heartbeat": node_state.get("last_heartbeat"),
        "runtime_health": node_state.get("health"),
        "device_condition": summary,
        "recommendation": recommendation,
        "reasons": reasons or ["no_adverse_fresh_evidence"],
        "decision_mode": "shadow",
        "dispatch_changed": False,
        "authorization_changed": False,
        "evaluated_at": (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
    }
