from scripts.factory_lifecycle_correlation import correlate_lifecycle


def test_lifecycle_correlates_explicit_msg_id_and_task_id():
    result = correlate_lifecycle(
        {"proposal": {"msg_id": "m-1", "task_id": "t-1"}},
        {"msg_id": "m-1", "task_id": "t-1", "reply_to": "m-0", "status": "completed"},
    )
    assert result["correlated"] is True
    assert result["msg_id_match"] is True
    assert result["task_id_match"] is True
    assert result["reply_to"] == "m-0"


def test_unrelated_lifecycle_does_not_correlate():
    result = correlate_lifecycle(
        {"proposal": {"msg_id": "m-1"}},
        {"msg_id": "m-2", "task_id": "t-2"},
    )
    assert result["correlated"] is False


def test_missing_identity_fails_closed():
    assert correlate_lifecycle({"proposal": {}}, {}) == {"available": False}


def test_projection_preserves_explicit_identity():
    state = {}
    from scripts.lifecycle_projection import apply_message

    changed = apply_message(
        state,
        {
            "id": "m-9",
            "type": "task_result",
            "from": "factory",
            "to": "system_internal",
            "timestamp": "2026-09-17T15:00:00+00:00",
            "context": {"task_id": "t-9", "reply_to": "m-8", "status": "completed"},
        },
    )
    assert changed is True
    assert state["t-9"]["msg_id"] == "m-9"
    assert state["t-9"]["reply_to"] == "m-8"
    assert "secret" not in state["t-9"]
