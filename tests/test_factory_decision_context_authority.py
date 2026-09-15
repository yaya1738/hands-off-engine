from scripts.factory_decision_context import build_factory_decision_context


def test_factory_context_uses_shared_authority_observation_only():
    snapshot = {
        "correlation_health": {"available": True, "event_count": 2, "correlated_event_count": 2, "orphan_reply_count": 0, "single_event_count": 0, "explicit_task_thread_coverage": 1.0, "window": {"truncated": False}},
        "admission_observation": {"available": True, "msg_id": "m-1", "task_id": "t-1", "admitted": True},
        "authority_decision": {"available": True, "msg_id": "m-1", "reply_to": "m-0", "task_id": "t-1", "decision": "approved", "reason": "reviewed", "approval_required": False, "execution_enabled": False, "decided_at": "now", "secret": "must-not-escape"},
        "factory_assessment": {"available": True, "health": 0.9, "gaps": [], "objective": "continue"},
    }
    result = build_factory_decision_context(snapshot)
    assert result["authority"] == {
        "available": True,
        "msg_id": "m-1",
        "reply_to": "m-0",
        "task_id": "t-1",
        "decision": "approved",
        "reason": "reviewed",
        "approval_required": False,
        "execution_enabled": False,
        "decided_at": "now",
    }
    assert "secret" not in str(result)


def test_missing_authority_observation_fails_closed():
    result = build_factory_decision_context({"correlation_health": {"available": True}})
    assert result["authority"] == {"available": False}
