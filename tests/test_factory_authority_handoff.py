from scripts.factory_authority_handoff import build_authority_input


def test_authority_adapter_forces_dryrun_and_preserves_correlation():
    result = build_authority_input({
        "available": True,
        "handoff": {
            "requires_governance": True,
            "objective": "improve interaction reliability",
            "msg_id": "m-1",
            "reply_to": "m-0",
            "task_id": "t-1",
        },
    })
    command = result["command"]
    assert command["mode"] == "DRYRUN"
    assert command["approval_status"] == "pending"
    assert command["id"] == "m-1"
    assert command["correlation"]["task_id"] == "t-1"


def test_missing_objective_fails_closed():
    assert build_authority_input({
        "available": True,
        "handoff": {"requires_governance": True},
    }) == {"available": False}


def test_missing_handoff_fails_closed():
    assert build_authority_input(None) == {"available": False}
