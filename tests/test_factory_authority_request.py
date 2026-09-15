from ai.factory.authority_request import FactoryAuthorityRequest


def test_builds_bounded_dryrun_request_with_explicit_correlation():
    result = FactoryAuthorityRequest.build(
        {"goal": "improve interaction reliability", "priority": 0.8},
        msg_id="m-1",
        task_id="t-1",
    )
    command = result["command"]
    assert result["available"] is True
    assert command["id"] == "m-1"
    assert command["mode"] == "DRYRUN"
    assert command["approval_status"] == "pending"
    assert command["correlation"] == {"msg_id": "m-1", "task_id": "t-1"}
    assert "message" not in command


def test_missing_plan_or_objective_fails_closed():
    assert FactoryAuthorityRequest.build(None) == {"available": False}
    assert FactoryAuthorityRequest.build({"priority": 0.8}) == {"available": False}


def test_request_never_grants_live_execution():
    result = FactoryAuthorityRequest.build({"goal": "improve", "priority": 0.2}, task_id="t-2")
    assert result["command"]["mode"] == "DRYRUN"
    assert result["command"]["approval_status"] == "pending"
