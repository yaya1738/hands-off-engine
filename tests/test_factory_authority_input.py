from scripts.factory_authority_input import build_authority_input


def test_builds_dryrun_authority_input_with_explicit_identity():
    result = build_authority_input({
        "available": True,
        "admission": {"msg_id": "m-1", "task_id": "t-1", "reply_to": "m-0"},
        "authority": {"msg_id": "m-1", "task_id": "t-1", "reply_to": "m-0"},
        "assessment": {"objective": "continue", "health": 0.9},
    })
    assert result["available"] is True
    command = result["command"]
    assert command["id"] == "m-1"
    assert command["mode"] == "DRYRUN"
    assert command["approval_status"] == "pending"
    assert command["correlation"] == {"msg_id": "m-1", "task_id": "t-1", "reply_to": "m-0"}


def test_missing_objective_or_identity_fails_closed():
    assert build_authority_input({"available": True, "assessment": {}}) == {"available": False}
    assert build_authority_input({"available": True, "assessment": {"objective": "continue"}}) == {"available": False}


def test_does_not_copy_execution_authority_or_secrets():
    result = build_authority_input({
        "available": True,
        "authority": {"msg_id": "m-1", "execution_enabled": True, "secret": "hidden"},
        "assessment": {"objective": "continue", "secret": "hidden"},
    })
    command = result["command"]
    assert command["mode"] == "DRYRUN"
    assert "execution_enabled" not in command
    assert "secret" not in str(result)
