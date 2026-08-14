"""
Basic flow tests for the legacy executor compatibility surface.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor.task_protocol import ExecutionTask, ExecutionResult
from executor.command_executor import CommandExecutor
from executor.safety_rules import SafetyAuditor

TEST_CONFIG = {
    "mode": "DRYRUN",
    "allowed_commands": ["python", "python3", "pytest", "ls", "git", "echo", "cat"],
    "blocked_substrings": ["rm -rf", "sudo", ":(){ :|:& };:", "mkfs", "dd if="],
    "protected_paths": [".ssh", ".env", "id_rsa", "termux"],
    "max_timeout_sec": 120,
    "workspace_root_only": True,
}


def test_dryrun_returns_success():
    executor = CommandExecutor(TEST_CONFIG)
    task = ExecutionTask(task_id="test-001", command=["ls", "-la"], working_dir=".", mode="DRYRUN", timeout_sec=60)
    result = executor.execute(task)
    assert result.status == "success"
    assert result.reason == "Dry run simulation"
    assert result.mode == "DRYRUN"
    assert result.exit_code == 0
    assert "[DRYRUN]" in result.stdout


def test_live_mode_is_fail_closed():
    """Legacy executor must never spawn a subprocess in LIVE mode."""
    executor = CommandExecutor(TEST_CONFIG)
    task = ExecutionTask(task_id="test-live", command=["echo", "must-not-run"], working_dir=".", mode="LIVE", timeout_sec=60)
    result = executor.execute(task)
    assert result.status == "rejected"
    assert result.exit_code is None
    assert "FactoryAuthorityGateway" in result.reason
    assert result.mode == "LIVE"
    assert result.stdout == ""


def test_unsafe_command_rejected():
    executor = CommandExecutor(TEST_CONFIG)
    task = ExecutionTask(task_id="test-002", command=["rm", "-rf", "/"], working_dir=".", mode="DRYRUN")
    result = executor.execute(task)
    assert result.status == "rejected"
    assert "not whitelisted" in result.reason


def test_blocked_substring_rejected():
    executor = CommandExecutor(TEST_CONFIG)
    task = ExecutionTask(task_id="test-003", command=["echo", "sudo", "apt-get", "install"], working_dir=".", mode="DRYRUN")
    result = executor.execute(task)
    assert result.status == "rejected"
    assert "banned pattern" in result.reason


def test_safe_command_passes_audit():
    auditor = SafetyAuditor(TEST_CONFIG)
    task = ExecutionTask(task_id="test-004", command=["python", "-c", "print('Hello, World!')"], working_dir=".", mode="DRYRUN")
    is_safe, reason = auditor.audit_task(task)
    assert is_safe is True
    assert reason == "Safe"


def test_empty_command_rejected():
    auditor = SafetyAuditor(TEST_CONFIG)
    task = ExecutionTask(task_id="test-005", command=[], working_dir=".", mode="DRYRUN")
    is_safe, reason = auditor.audit_task(task)
    assert is_safe is False
    assert reason == "Empty command"


def test_path_traversal_rejected():
    auditor = SafetyAuditor(TEST_CONFIG)
    task = ExecutionTask(task_id="test-006", command=["ls"], working_dir="../../../../etc", mode="DRYRUN")
    is_safe, reason = auditor.audit_task(task)
    assert is_safe is False
    assert "escapes repo root" in reason


def test_result_to_json():
    result = ExecutionResult(
        task_id="test-007", status="success", exit_code=0, stdout="test output", stderr="",
        reason=None, started_at="2025-01-01T00:00:00", finished_at="2025-01-01T00:00:01", mode="DRYRUN"
    )
    json_data = result.to_json()
    assert json_data["task_id"] == "test-007"
    assert json_data["status"] == "success"
    assert json_data["exit_code"] == 0
    assert json_data["mode"] == "DRYRUN"
