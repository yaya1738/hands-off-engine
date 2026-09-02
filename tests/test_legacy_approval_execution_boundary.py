from ai.approval_queue import ApprovalQueue


def test_legacy_approval_records_authority_without_executing(tmp_path, monkeypatch):
    queue_file = tmp_path / "approval_queue.json"
    monkeypatch.setattr("ai.approval_queue.QUEUE_FILE", queue_file)

    queue = ApprovalQueue()
    change_id = queue.add_change(
        title="boundary test",
        description="must never execute through legacy queue",
        change_type="configuration",
        files_affected=["config/example.json"],
        proposed_action={
            "type": "bash_command",
            "command": "touch SHOULD_NOT_EXIST",
        },
        risk_level="high",
    )

    assert queue.approve(change_id) is True
    result = queue.execute_approved(change_id)

    assert result["success"] is False
    assert result["blocked"] is True
    assert result["error"] == "legacy_execution_authority_disabled"
    assert queue.get_change(change_id)["execution_authority"] == "factory_authority_gateway"
