from scripts.admission_observability import latest_admission_decision


def test_latest_explicit_admission_decision_is_correlated():
    events = [
        {
            "type": "inbound_from_agent",
            "payload": {
                "event_type": "task_admission",
                "decision": {
                    "msg_id": "req-1",
                    "reply_to": "req-1",
                    "task_id": "task-1",
                    "admitted": True,
                    "reason": "ok",
                    "decided_at": "2026-09-15T00:00:00Z",
                    "secret": "must-not-leak",
                },
            },
        }
    ]

    observed = latest_admission_decision(events)

    assert observed == {
        "available": True,
        "msg_id": "req-1",
        "reply_to": "req-1",
        "task_id": "task-1",
        "admitted": True,
        "reason": "ok",
        "decided_at": "2026-09-15T00:00:00Z",
    }
    assert "secret" not in observed


def test_latest_explicit_admission_decision_wins():
    events = [
        {"payload": {"event_type": "task_admission", "decision": {"msg_id": "old", "admitted": False}}},
        {"payload": {"event_type": "task_admission", "decision": {"msg_id": "new", "reply_to": "new", "admitted": True}}},
    ]

    assert latest_admission_decision(events)["msg_id"] == "new"


def test_malformed_or_unrelated_events_fail_closed():
    events = [
        {"type": "task_request", "msg_id": "req-1"},
        {"payload": {"event_type": "task_admission", "decision": {"admitted": True}}},
        {"payload": {"event_type": "other", "decision": {"msg_id": "req-2", "admitted": True}}},
    ]

    assert latest_admission_decision(events) == {"available": False}
