from ai.autonomous_change import propose_change


def test_propose_change_never_executes_legacy_action(tmp_path, monkeypatch):
    queue_file = tmp_path / "approval_queue.json"
    monkeypatch.setattr("ai.approval_queue.QUEUE_FILE", queue_file)

    result = propose_change(
        title="boundary test",
        description="must remain governed",
        change_type="documentation",
        files=["README.md"],
        action={"type": "bash_command", "command": "touch SHOULD_NOT_EXIST"},
        risk_level="low",
    )

    assert result["applied"] is False
    assert result["status"] == "pending_governed_execution"
    assert result["execution_authority"] == "factory_authority_gateway"
