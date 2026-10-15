"""Convert explicit Factory lifecycle signals into reviewable contact proposals.

No transport is called here. Missing task context, an ambiguous reason, or an
unsuitable participant produces no proposal. A separate caller must pass the
proposal through CommHub's enforced send boundary.
"""
from copy import deepcopy

from messaging.human_participant_policy import ELIGIBLE_REASON_CODES

EVENT_REASON_MAP = {
    "blocker": "external_blocker",
    "human_context_gap": "human_context_gap",
    "material_ambiguity": "material_ambiguity",
    "stakeholder_validation": "stakeholder_validation",
    "requested_update": "requested_update",
}


def build_contact_proposal(event, task, participant_id):
    """Build a proposal only from explicit lifecycle/task fields; never send."""
    if not isinstance(event, dict) or not isinstance(task, dict):
        return {"status": "not_eligible", "reason": "event_and_task_must_be_objects"}
    if not isinstance(participant_id, str) or not participant_id.strip():
        return {"status": "not_eligible", "reason": "participant_not_specified"}

    event_type = str(event.get("event_type", "")).strip().casefold()
    context = event.get("context") if isinstance(event.get("context"), dict) else {}
    task_id = str(task.get("task_id") or context.get("task_id") or "").strip()
    correlation_id = str(event.get("correlation_id") or context.get("correlation_id") or "").strip()
    if not task_id or not correlation_id:
        return {"status": "not_eligible", "reason": "task_or_correlation_missing"}

    # Prefer an explicit reason code. Map a generic blocker only when task data
    # explicitly marks that the blocker requires a human participant.
    reason = str(task.get("human_contact_reason") or context.get("human_contact_reason") or "").strip()
    if not reason and event_type in EVENT_REASON_MAP and task.get("requires_human_input") is True:
        reason = EVENT_REASON_MAP[event_type]
    if reason not in ELIGIBLE_REASON_CODES:
        return {"status": "not_eligible", "reason": "human_relevance_not_explicit"}

    question = str(task.get("human_question") or "").strip()
    why = str(task.get("human_question_impact") or "").strip()
    summary = str(task.get("summary") or task.get("objective") or "").strip()
    if not question or not why or not summary:
        return {"status": "not_eligible", "reason": "task_question_context_incomplete"}

    payload = {
        "task_id": task_id,
        "correlation_id": correlation_id,
        "reason_code": reason,
        "context": summary[:2000],
        "question": question[:2000],
        "why_it_matters": why[:1000],
        "subject": str(task.get("human_email_subject") or "A question about your input")[:180],
        "source_event_id": str(event.get("event_id") or event.get("msg_id") or "")[:200],
    }
    return {
        "status": "proposal_ready",
        "participant_id": participant_id.strip(),
        "task_id": task_id,
        "correlation_id": correlation_id,
        "payload": deepcopy(payload),
        "send_authorized": False,
        "requires_policy_check": True,
    }
