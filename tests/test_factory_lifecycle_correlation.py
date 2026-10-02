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
