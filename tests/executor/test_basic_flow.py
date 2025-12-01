"""
Basic flow tests for the executor module.

Tests:
1. DRYRUN mode returns success without executing
2. Unsafe commands are rejected
3. Safe commands pass safety checks
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor.task_protocol import ExecutionTask, ExecutionResult
from executor.command_executor import CommandExecutor
from executor.safety_rules import SafetyAuditor


# Test configuration
TEST_CONFIG = {
    "mode": "DRYRUN",
    "allowed_commands": ["python", "python3", "pytest", "ls", "git", "echo", "cat"],
    "blocked_substrings": ["rm -rf", "sudo", ":(){ :|:& };:", "mkfs", "dd if="],
    "protected_paths": [".ssh", ".env", "id_rsa", "termux"],
    "max_timeout_sec": 120,
    "workspace_root_only": True
}


def test_dryrun_returns_success():
    """Test that DRYRUN mode returns success without executing the command."""
    executor = CommandExecutor(TEST_CONFIG)

    task = ExecutionTask(
        task_id="test-001",
        command=["ls", "-la"],
        working_dir=".",
        mode="DRYRUN",
        timeout_sec=60
    )

    result = executor.execute(task)

    # Assertions
    assert result.status == "success", f"Expected status 'success', got '{result.status}'"
    assert result.reason == "Dry run simulation", f"Expected reason 'Dry run simulation', got '{result.reason}'"
    assert result.mode == "DRYRUN", f"Expected mode 'DRYRUN', got '{result.mode}'"
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}"
    assert "[DRYRUN]" in result.stdout, f"Expected '[DRYRUN]' in stdout, got: {result.stdout}"


def test_unsafe_command_rejected():
    """Test that unsafe commands are rejected by the SafetyAuditor."""
    executor = CommandExecutor(TEST_CONFIG)

    # Test 1: Command not in whitelist
    task = ExecutionTask(
        task_id="test-002",
        command=["rm", "-rf", "/"],
        working_dir=".",
        mode="DRYRUN"
    )

    result = executor.execute(task)
    assert result.status == "rejected", f"Expected status 'rejected', got '{result.status}'"
    assert "not whitelisted" in result.reason, f"Expected 'not whitelisted' in reason, got: {result.reason}"


def test_blocked_substring_rejected():
    """Test that commands with blocked substrings are rejected."""
    executor = CommandExecutor(TEST_CONFIG)

    task = ExecutionTask(
        task_id="test-003",
        command=["echo", "sudo", "apt-get", "install"],
        working_dir=".",
        mode="DRYRUN"
    )

    result = executor.execute(task)
    assert result.status == "rejected", f"Expected status 'rejected', got '{result.status}'"
    assert "banned pattern" in result.reason, f"Expected 'banned pattern' in reason, got: {result.reason}"


def test_safe_command_passes_audit():
    """Test that safe commands pass the safety audit."""
    auditor = SafetyAuditor(TEST_CONFIG)

    task = ExecutionTask(
        task_id="test-004",
        command=["python", "-c", "print('Hello, World!')"],
        working_dir=".",
        mode="DRYRUN"
    )

    is_safe, reason = auditor.audit_task(task)
    assert is_safe is True, f"Expected safe command to pass audit, got reason: {reason}"
    assert reason == "Safe", f"Expected reason 'Safe', got: {reason}"


def test_empty_command_rejected():
    """Test that empty commands are rejected."""
    auditor = SafetyAuditor(TEST_CONFIG)

    task = ExecutionTask(
        task_id="test-005",
        command=[],
        working_dir=".",
        mode="DRYRUN"
    )

    is_safe, reason = auditor.audit_task(task)
    assert is_safe is False, "Expected empty command to be rejected"
    assert reason == "Empty command", f"Expected reason 'Empty command', got: {reason}"


def test_path_traversal_rejected():
    """Test that path traversal attempts are rejected."""
    auditor = SafetyAuditor(TEST_CONFIG)

    task = ExecutionTask(
        task_id="test-006",
        command=["ls"],
        working_dir="../../../../etc",
        mode="DRYRUN"
    )

    is_safe, reason = auditor.audit_task(task)
    assert is_safe is False, "Expected path traversal to be rejected"
    assert "escapes repo root" in reason, f"Expected 'escapes repo root' in reason, got: {reason}"


def test_result_to_json():
    """Test that ExecutionResult can be serialized to JSON."""
    result = ExecutionResult(
        task_id="test-007",
        status="success",
        exit_code=0,
        stdout="test output",
        stderr="",
        reason=None,
        started_at="2025-01-01T00:00:00",
        finished_at="2025-01-01T00:00:01",
        mode="DRYRUN"
    )

    json_data = result.to_json()

    assert json_data["task_id"] == "test-007"
    assert json_data["status"] == "success"
    assert json_data["exit_code"] == 0
    assert json_data["mode"] == "DRYRUN"


if __name__ == "__main__":
    # Run tests manually
    print("Running executor tests...")
    print()

    tests = [
        ("DRYRUN returns success", test_dryrun_returns_success),
        ("Unsafe command rejected", test_unsafe_command_rejected),
        ("Blocked substring rejected", test_blocked_substring_rejected),
        ("Safe command passes audit", test_safe_command_passes_audit),
        ("Empty command rejected", test_empty_command_rejected),
        ("Path traversal rejected", test_path_traversal_rejected),
        ("Result to JSON", test_result_to_json),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
