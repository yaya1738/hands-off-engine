from scripts.authority_decision_observability import latest_authority_decision


def test_latest_explicit_authority_decision_wins():
    events = [
        {"payload": {"event_type": "authority_decision", "decision": {"msg_id": "old", "decision": "denied"}}},
        {"payload": {"event_type": "unrelated", "decision": {"msg_id": "noise"}}},
        {"payload": {"event_type": "authority_decision", "decision": {"msg_id": "new", "reply_to": "req-1", "task_id": "task-1", "decision": "approved", "reason": "reviewed", "approval_required": False, "execution_enabled": False, "secret": "no"}}},
    ]
    result = latest_authority_decision(events)
    assert result == {
        "available": True,
        "msg_id": "new",
        "reply_to": "req-1",
        "task_id": "task-1",
        "decision": "approved",
        "reason": "reviewed",
        "approval_required": False,
        "execution_enabled": False,
        "decided_at": None,
    }


def test_malformed_or_unrelated_decisions_fail_closed():
    assert latest_authority_decision([
        {"payload": {"event_type": "authority_decision", "decision": {"decision": "approved"}}},
        {"payload": {"event_type": "task_result", "decision": {"msg_id": "m"}}},
    ]) == {"available": False}
