from messaging.human_participant_router import build_contact_proposal


def _event():
    return {
        "event_type": "blocker",
        "event_id": "evt-9",
        "correlation_id": "task-9",
        "context": {"task_id": "task-9"},
    }


def _task():
    return {
        "task_id": "task-9",
        "requires_human_input": True,
        "human_contact_reason": "external_blocker",
        "summary": "The implementation is blocked on a domain decision.",
        "human_question": "Which of these two maintenance approaches do you prefer?",
        "human_question_impact": "The answer determines which design Factory implements.",
    }


def test_explicit_human_blocker_builds_non_sending_proposal():
    result = build_contact_proposal(_event(), _task(), "aharon")
    assert result["status"] == "proposal_ready"
    assert result["participant_id"] == "aharon"
    assert result["payload"]["task_id"] == "task-9"
    assert result["payload"]["correlation_id"] == "task-9"
    assert result["send_authorized"] is False
    assert result["requires_policy_check"] is True


def test_heartbeat_never_becomes_a_contact_proposal():
    event = {**_event(), "event_type": "heartbeat"}
    task = {**_task(), "human_contact_reason": ""}
    assert build_contact_proposal(event, task, "aharon")["reason"] == "human_relevance_not_explicit"


def test_generic_blocker_requires_explicit_human_input_flag():
    task = {**_task(), "requires_human_input": False, "human_contact_reason": ""}
    assert build_contact_proposal(_event(), task, "aharon")["reason"] == "human_relevance_not_explicit"


def test_missing_context_never_gets_invented():
    task = {**_task(), "human_question": ""}
    assert build_contact_proposal(_event(), task, "aharon")["reason"] == "task_question_context_incomplete"


def test_missing_correlation_prevents_proposal():
    event = {**_event(), "correlation_id": ""}
    assert build_contact_proposal(event, _task(), "aharon")["reason"] == "task_or_correlation_missing"

def test_factory_decision_evidence_alone_never_infers_human_contact():
    # Shared decision/health evidence is evidence, not a contact instruction.
    # A producer must attach an explicit, task-scoped human_contact request.
    task = {
        "task_id": "task-9",
        "summary": "The system has an assessment gap.",
        "factory_decision_context": {
            "available": True,
            "assessment": {"available": True, "gaps": ["missing context"]},
            "authority": {"available": True, "decision": "pending", "approval_required": True},
            "system_health": {"available": True, "status": "warn"},
        },
    }
    result = build_contact_proposal(_event(), task, "aharon")
    assert result["status"] == "not_eligible"
    assert result["reason"] == "human_relevance_not_explicit"
    assert result.get("send_authorized") is not True
