from scripts.factory_authority_correlation import correlate_authority_decision


def test_explicit_msg_id_correlates():
    result = correlate_authority_decision(
        {"proposal": {"msg_id": "m-1"}},
        {"msg_id": "m-1", "task_id": "t-1"},
    )
    assert result["correlated"] is True
    assert result["msg_id_match"] is True


def test_explicit_task_id_correlates():
    result = correlate_authority_decision(
        {"proposal": {"task_id": "t-1"}},
        {"msg_id": "m-1", "task_id": "t-1"},
    )
    assert result["correlated"] is True
    assert result["task_id_match"] is True


def test_mismatch_does_not_correlate():
    result = correlate_authority_decision(
        {"proposal": {"msg_id": "m-1", "task_id": "t-1"}},
        {"msg_id": "m-2", "task_id": "t-2"},
    )
    assert result["correlated"] is False


def test_missing_identity_fails_closed():
    assert correlate_authority_decision({"proposal": {}}, {}) == {"available": False}
