from scripts.factory_decision_context import build_factory_decision_context


def test_context_projects_shared_observation_without_extra_fields():
    result = build_factory_decision_context({
        "correlation_health": {"available": True, "event_count": 2, "correlated_event_count": 1, "orphan_reply_count": 1, "single_event_count": 0, "explicit_task_thread_coverage": 0.5, "window": {"truncated": False}},
        "admission_observation": {"available": True, "msg_id": "m-1", "reply_to": "m-0", "task_id": "t-1", "admitted": True, "reason": "accepted", "decided_at": "now", "secret": "no"},
        "authority_decision": {"available": True, "msg_id": "m-1", "reply_to": "m-0", "task_id": "t-1", "decision": "approved", "reason": "reviewed", "approval_required": False, "execution_enabled": False, "decided_at": "now", "secret": "no"},
        "factory_assessment": {"available": True, "health": 0.9, "gaps": [], "objective": "continue", "secret": "no"},
    })
    assert result["authority"]["msg_id"] == "m-1"
    assert result["authority"]["task_id"] == "t-1"
    assert result["authority"]["execution_enabled"] is False
    assert result["interaction"]["correlation_rate"] == 0.5
    assert "secret" not in str(result)


def test_missing_snapshot_fails_closed():
    assert build_factory_decision_context(None) == {"available": False}
