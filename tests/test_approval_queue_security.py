import ai.approval_queue as approval_module
from ai.approval_queue import ApprovalQueue


def _approved_queue(tmp_path, monkeypatch, action):
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(approval_module, "REPO_ROOT", root)
    monkeypatch.setattr(approval_module, "QUEUE_FILE", tmp_path / "approval_queue.json")
    queue = ApprovalQueue()
    change_id = queue.add_change(
        title="test change",
        description="security regression test",
        change_type="code",
        files_affected=[],
        proposed_action=action,
    )
    assert queue.approve(change_id)
    return queue, change_id, root


def test_approval_queue_allows_repository_relative_write(tmp_path, monkeypatch):
    queue, change_id, root = _approved_queue(
        tmp_path, monkeypatch,
        {"type": "write_file", "file_path": "docs/generated.md", "content": "safe"},
    )

    result = queue.execute_approved(change_id)

    assert result["success"] is True
    assert (root / "docs/generated.md").read_text() == "safe"


def test_approval_queue_rejects_path_traversal(tmp_path, monkeypatch):
    queue, change_id, _ = _approved_queue(
        tmp_path, monkeypatch,
        {"type": "write_file", "file_path": "../outside.txt", "content": "unsafe"},
    )

    result = queue.execute_approved(change_id)

    assert result["success"] is False
    assert "escapes the repository root" in result["error"]


def test_approval_queue_rejects_absolute_paths(tmp_path, monkeypatch):
    outside = tmp_path / "outside.txt"
    queue, change_id, _ = _approved_queue(
        tmp_path, monkeypatch,
        {"type": "write_file", "file_path": str(outside), "content": "unsafe"},
    )

    result = queue.execute_approved(change_id)

    assert result["success"] is False
    assert "repository-relative" in result["error"]
    assert not outside.exists()


def test_approval_queue_protects_credentials_and_runtime_state(tmp_path, monkeypatch):
    for protected in [".env", ".env.production", "state/credentials.json", ".ssh/authorized_keys"]:
        queue, change_id, _ = _approved_queue(
            tmp_path, monkeypatch,
            {"type": "write_file", "file_path": protected, "content": "unsafe"},
        )

        result = queue.execute_approved(change_id)

        assert result["success"] is False
        assert "Protected" in result["error"] or "credential" in result["error"]


def test_approval_queue_disables_arbitrary_shell_commands(tmp_path, monkeypatch):
    queue, change_id, _ = _approved_queue(
        tmp_path, monkeypatch,
        {"type": "bash_command", "command": "touch SHOULD_NOT_EXIST"},
    )

    result = queue.execute_approved(change_id)

    assert result["success"] is False
    assert "Arbitrary shell execution is disabled" in result["error"]
