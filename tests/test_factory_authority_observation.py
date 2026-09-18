from scripts.factory_authority_observation import project_factory_authority_observation


def test_authority_observation_exposes_only_explicit_correlation():
    result = project_factory_authority_observation(
        {"proposal": {"msg_id": "m-1", "task_id": "t-1"}},
        {"msg_id": "m-1", "task_id": "t-1", "decision": "dryrun_only", "secret": "x"},
    )
    assert result["available"] is True
    assert result["correlated"] is True
    assert result["msg_id_match"] is True
    assert result["task_id_match"] is True
    assert "secret" not in result


def test_unrelated_decision_is_not_correlated():
    result = project_factory_authority_observation(
        {"proposal": {"msg_id": "m-1"}},
        {"msg_id": "m-2", "task_id": "t-2"},
    )
    assert result["correlated"] is False


def test_malformed_inputs_fail_closed():
    assert project_factory_authority_observation(None, {}) == {"available": False}
