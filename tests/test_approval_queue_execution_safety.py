"""ApprovalQueue must not turn an approval ID into arbitrary host execution."""
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from ai.approval_queue import ApprovalQueue


def make_queue(tmp_path):
    root = tmp_path / "repo"
    (root / "state").mkdir(parents=True)
    return ApprovalQueue(repo_root=root), root


def queue_and_approve(queue, action, title="test change"):
    change_id = queue.add_change(
        title=title,
        description="reviewed test proposal",
        change_type="code",
        files_affected=["config/test.json"],
        proposed_action=action,
        risk_level="high",
    )
    assert queue.approve(change_id)
    return change_id


def test_arbitrary_bash_command_is_never_executed(tmp_path):
    queue, root = make_queue(tmp_path)
    change_id = queue_and_approve(queue, {
        "type": "bash_command",
        "command": "touch /tmp/approval-queue-pwned",
    })
    with patch("subprocess.run") as run:
        result = queue.execute_approved(change_id)
    assert not result["success"]
    assert "disabled" in result["error"]
    run.assert_not_called()
    assert not Path("/tmp/approval-queue-pwned").exists()


def test_edit_file_rejects_absolute_path_outside_repo(tmp_path):
    queue, root = make_queue(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("safe")
    change_id = queue_and_approve(queue, {
        "type": "edit_file", "file_path": str(outside),
        "old_content": "safe", "new_content": "owned",
    })
    result = queue.execute_approved(change_id)
    assert not result["success"]
    assert "inside the repository root" in result["error"]
    assert outside.read_text() == "safe"


def test_write_file_rejects_path_traversal(tmp_path):
    queue, root = make_queue(tmp_path)
    change_id = queue_and_approve(queue, {
        "type": "write_file", "file_path": "../outside.txt", "content": "owned",
    })
    result = queue.execute_approved(change_id)
    assert not result["success"]
    assert "inside the repository root" in result["error"]
    assert not (tmp_path / "outside.txt").exists()


def test_file_actions_reject_symlink_escape(tmp_path):
    queue, root = make_queue(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("safe")
    link = root / "escape.txt"
    link.symlink_to(outside)
    change_id = queue_and_approve(queue, {
        "type": "edit_file", "file_path": "escape.txt",
        "old_content": "safe", "new_content": "owned",
    })
    result = queue.execute_approved(change_id)
    assert not result["success"]
    assert "inside the repository root" in result["error"]
    assert outside.read_text() == "safe"


def test_edit_file_is_limited_to_existing_repo_file_and_exact_old_content(tmp_path):
    queue, root = make_queue(tmp_path)
    target = root / "config.json"
    target.write_text('{"limit": 10}')
    change_id = queue_and_approve(queue, {
        "type": "edit_file", "file_path": "config.json",
        "old_content": '"limit": 10', "new_content": '"limit": 20',
    })
    result = queue.execute_approved(change_id)
    assert result["success"]
    assert target.read_text() == '{"limit": 20}'


def test_edit_file_refuses_empty_or_nonmatching_old_content(tmp_path):
    queue, root = make_queue(tmp_path)
    target = root / "config.json"
    target.write_text('{"limit": 10}')
    change_id = queue_and_approve(queue, {
        "type": "edit_file", "file_path": "config.json",
        "old_content": "", "new_content": "owned",
    })
    result = queue.execute_approved(change_id)
    assert not result["success"]
    assert "non-empty exact match" in result["error"]
    assert target.read_text() == '{"limit": 10}'


def test_edit_file_refuses_ambiguous_multiple_matches(tmp_path):
    queue, root = make_queue(tmp_path)
    target = root / "config.json"
    target.write_text('{"limit": 10, "backup_limit": 10}')
    change_id = queue_and_approve(queue, {
        "type": "edit_file", "file_path": "config.json",
        "old_content": "10", "new_content": "20",
    })
    result = queue.execute_approved(change_id)
    assert not result["success"]
    assert "match exactly once" in result["error"]
    assert target.read_text() == '{"limit": 10, "backup_limit": 10}'

def test_approved_action_tampering_fails_closed(tmp_path):
    queue, root = make_queue(tmp_path)
    target = root / "config.json"
    target.write_text('{"limit": 10}')
    change_id = queue_and_approve(queue, {
        "type": "edit_file", "file_path": "config.json",
        "old_content": '"limit": 10', "new_content": '"limit": 20',
    })
    persisted = json.loads(queue.queue_file.read_text())
    persisted["approved"][0]["proposed_action"]["new_content"] = '"limit": 999'
    queue.queue_file.write_text(json.dumps(persisted))
    result = queue.execute_approved(change_id)
    assert not result["success"]
    assert "changed after approval" in result["error"]
    assert target.read_text() == '{"limit": 10}'


def test_approval_is_one_shot_even_if_file_is_restored(tmp_path):
    queue, root = make_queue(tmp_path)
    target = root / "config.json"
    original = '{"limit": 10}'
    target.write_text(original)
    change_id = queue_and_approve(queue, {
        "type": "edit_file", "file_path": "config.json",
        "old_content": '"limit": 10', "new_content": '"limit": 20',
    })
    first = queue.execute_approved(change_id)
    assert first["success"]
    assert target.read_text() == '{"limit": 20}'
    target.write_text(original)
    second = queue.execute_approved(change_id)
    assert not second["success"]
    assert "not executable" in second["error"]
    assert target.read_text() == original

def test_write_file_is_create_only_inside_repo(tmp_path):
    queue, root = make_queue(tmp_path)
    change_id = queue_and_approve(queue, {
        "type": "write_file", "file_path": "new.txt", "content": "hello",
    })
    result = queue.execute_approved(change_id)
    assert result["success"]
    assert (root / "new.txt").read_text() == "hello"

    existing_id = queue_and_approve(queue, {
        "type": "write_file", "file_path": "new.txt", "content": "overwrite",
    }, title="overwrite attempt")
    result = queue.execute_approved(existing_id)
    assert not result["success"]
    assert "create-only" in result["error"]
    assert (root / "new.txt").read_text() == "hello"


def test_unapproved_change_cannot_execute(tmp_path):
    queue, root = make_queue(tmp_path)
    change_id = queue.add_change(
        title="pending", description="not approved", change_type="code",
        files_affected=[], proposed_action={
            "type": "write_file", "file_path": "new.txt", "content": "no",
        },
    )
    result = queue.execute_approved(change_id)
    assert not result["success"]
    assert result["error"] == "Change not approved"
    assert not (root / "new.txt").exists()


def test_approval_preview_discloses_action_type_and_target_without_content(tmp_path):
    queue, root = make_queue(tmp_path)
    change = {
        "description": "Update a config value",
        "files_affected": ["config.json"],
        "proposed_action": {
            "type": "edit_file",
            "file_path": "config.json",
            "old_content": "secret-old-value",
            "new_content": "secret-new-value",
        },
    }
    preview = queue.format_change_preview(change)
    assert "Description: Update a config value" in preview
    assert "Action type: edit_file" in preview
    assert "Target: config.json" in preview
    assert "secret-old-value" not in preview
    assert "secret-new-value" not in preview


def test_approval_preview_marks_shell_command_as_blocked(tmp_path):
    queue, root = make_queue(tmp_path)
    preview = queue.format_change_preview({
        "description": "Run arbitrary shell",
        "files_affected": [],
        "proposed_action": {"type": "bash_command", "command": "echo unsafe"},
    })
    assert "BLOCKED" in preview
    assert "echo unsafe" not in preview


def test_both_telegram_pending_views_show_action_type_and_target():
    import importlib
    from unittest.mock import Mock, patch

    change = {
        "id": "a1b2c3d4",
        "title": "Config adjustment",
        "description": "Update one config field",
        "change_type": "configuration",
        "risk_level": "high",
        "files_affected": ["config/risk.json"],
        "proposed_action": {"type": "edit_file", "file_path": "config/risk.json"},
    }
    for module_name in ("scripts.telegram_command_bot", "telegram.telegram_command_bot"):
        module = importlib.import_module(module_name)
        bot = module.TelegramCommandBot.__new__(module.TelegramCommandBot)
        fake_queue = Mock()
        fake_queue.get_pending.return_value = [change]
        fake_queue.format_change_preview.return_value = (
            "Action type: edit_file\nTarget: config/risk.json"
        )
        with patch.object(module, "ApprovalQueue", return_value=fake_queue):
            output = bot.cmd_pending([])
        assert "Action type: edit_file" in output
        assert "Target: config/risk.json" in output
