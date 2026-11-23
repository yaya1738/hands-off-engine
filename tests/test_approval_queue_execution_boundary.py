from ai.approval_queue import ApprovalQueue


def _approved_queue(tmp_path, action):
    queue = ApprovalQueue()
    queue.queue_file = tmp_path / "approval_queue.json"
    change_id = queue.add_change(
        title="test change",
        description="security regression",
        change_type="code",
        files_affected=[],
        proposed_action=action,
    )
    assert queue.approve(change_id)
    return queue, change_id


def test_approved_edit_file_action_is_not_executed(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("original")
    queue, change_id = _approved_queue(
        tmp_path,
        {
            "type": "edit_file",
            "file_path": str(target),
            "old_content": "original",
            "new_content": "modified",
        },
    )

    result = queue.execute_approved(change_id)

    assert result["success"] is False
    assert "Execution blocked" in result["error"]
    assert target.read_text() == "original"


def test_approved_write_file_action_is_not_executed(tmp_path):
    target = tmp_path / "new-file.txt"
    queue, change_id = _approved_queue(
        tmp_path,
        {"type": "write_file", "file_path": str(target), "content": "owned"},
    )

    result = queue.execute_approved(change_id)

    assert result["success"] is False
    assert "Execution blocked" in result["error"]
    assert not target.exists()


def test_approved_shell_action_is_not_executed(tmp_path):
    marker = tmp_path / "shell-ran"
    queue, change_id = _approved_queue(
        tmp_path,
        {"type": "bash_command", "command": f"touch {marker}"},
    )

    result = queue.execute_approved(change_id)

    assert result["success"] is False
    assert "Execution blocked" in result["error"]
    assert not marker.exists()


def test_pending_change_cannot_be_executed(tmp_path):
    queue = ApprovalQueue()
    queue.queue_file = tmp_path / "approval_queue.json"
    change_id = queue.add_change(
        title="pending",
        description="not approved",
        change_type="code",
        files_affected=[],
        proposed_action={"type": "bash_command", "command": "false"},
    )

    result = queue.execute_approved(change_id)

    assert result == {"success": False, "error": "Change not approved"}
