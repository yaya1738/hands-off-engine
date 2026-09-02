from scripts import task_dispatch


def test_legacy_task_dispatch_is_fail_closed():
    result = task_dispatch.dispatch_to_node(
        {"name": "example", "ip": "127.0.0.1"},
        "health_check",
    )

    assert result["blocked"] is True
    assert result["success"] is False
    assert result["error"] == "legacy_remote_execution_disabled"
    assert result["authority"] == "FactoryAuthorityGateway"
