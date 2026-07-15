"""
Comprehensive test suite for Batch 17: Continuous Autonomous AI Loop

Tests all required functionality:
1. Single cycle success
2. Summary file writing
3. History file writing
4. Graceful handling of missing/malformed health
5. Graceful handling of component failures
6. Error threshold behavior
7. Interval parsing
8. CLI --once mode
9. SIGINT handling
"""

import json
import os
import signal
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the module under test
from ai.ho_ai_loop import (
    invoke_ai_runner,
    invoke_task_generator,
    load_health,
    parse_interval,
    run_ai_loop,
    run_single_cycle,
    sleep_interruptible,
    write_loop_summary,
)


@pytest.fixture
def temp_dirs():
    """Create temporary state and ai directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = os.path.join(tmpdir, "state")
        ai_dir = os.path.join(tmpdir, "ai")
        os.makedirs(state_dir, exist_ok=True)
        os.makedirs(ai_dir, exist_ok=True)
        yield {"state_dir": state_dir, "ai_dir": ai_dir, "tmpdir": tmpdir}


# Test 1: Single cycle success
def test_single_cycle_success(temp_dirs):
    """Test that a single cycle completes successfully."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    # Mock the component invocations
    with patch("ai.ho_ai_loop.invoke_task_generator") as mock_tg, \
         patch("ai.ho_ai_loop.invoke_ai_runner") as mock_runner:

        mock_tg.return_value = {"status": "success", "result": {"tasks": 5}, "error": None}
        mock_runner.return_value = {"status": "success", "result": {"executed": 3}, "error": None}

        result = run_single_cycle(
            state_dir=state_dir,
            ai_dir=ai_dir,
            cycle=1,
            interval="30s",
            verbose=False
        )

        assert result["status"] == "ok"
        assert result["cycle"] == 1
        assert len(result["errors"]) == 0
        mock_tg.assert_called_once()
        mock_runner.assert_called_once()


# Test 2: Loop writes summary file
def test_loop_writes_summary(temp_dirs):
    """Test that the loop writes the latest summary file."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    health = {"status": "ok"}
    tg_result = {"status": "success", "result": {"tasks": 5}, "error": None}
    runner_result = {"status": "success", "result": {"executed": 3}, "error": None}

    write_loop_summary(
        state_dir=state_dir,
        cycle=1,
        interval="30s",
        health=health,
        task_generator_result=tg_result,
        ai_runner_result=runner_result,
        errors=[],
        verbose=False
    )

    # Check that summary file exists
    summary_path = Path(state_dir) / "hands_off_ai_loop.json"
    assert summary_path.exists()

    # Verify contents
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    assert summary["cycle"] == 1
    assert summary["interval"] == "30s"
    assert summary["health"] == "ok"
    assert summary["status"] == "ok"
    assert summary["task_generator"]["status"] == "success"
    assert summary["ai_runner"]["status"] == "success"


# Test 3: Loop writes history file
def test_loop_writes_history_file(temp_dirs):
    """Test that the loop writes per-cycle history files."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    health = {"status": "ok"}
    tg_result = {"status": "success", "result": {"tasks": 5}, "error": None}
    runner_result = {"status": "success", "result": {"executed": 3}, "error": None}

    write_loop_summary(
        state_dir=state_dir,
        cycle=42,
        interval="1m",
        health=health,
        task_generator_result=tg_result,
        ai_runner_result=runner_result,
        errors=[],
        verbose=False
    )

    # Check that history directory exists
    history_dir = Path(state_dir) / "history"
    assert history_dir.exists()

    # Check that at least one history file exists
    history_files = list(history_dir.glob("ai_loop_*.json"))
    assert len(history_files) >= 1

    # Verify contents of latest history file
    with open(history_files[0], 'r') as f:
        history = json.load(f)

    assert history["cycle"] == 42
    assert history["interval"] == "1m"


# Test 4: Health missing handled gracefully
def test_health_missing_handled_gracefully(temp_dirs):
    """Test that missing health file is handled gracefully."""
    state_dir = temp_dirs["state_dir"]

    # Don't create health file
    health = load_health(state_dir)

    assert health["status"] == "unknown"
    assert "reason" in health
    assert "not found" in health["reason"].lower()


# Test 5: Malformed health handled gracefully
def test_malformed_health_handled_gracefully(temp_dirs):
    """Test that malformed health file is handled gracefully."""
    state_dir = temp_dirs["state_dir"]

    # Create malformed health file
    health_path = Path(state_dir) / "hands_off_health.json"
    with open(health_path, 'w') as f:
        f.write("this is not valid JSON {{{")

    health = load_health(state_dir)

    assert health["status"] == "unknown"
    assert "reason" in health
    assert "malformed" in health["reason"].lower()


# Test 6: Task generator failure does not crash loop
def test_task_generator_failure_does_not_crash_loop(temp_dirs):
    """Test that task generator failure does not crash the loop."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    # Mock task generator to fail
    with patch("ai.ho_ai_loop.invoke_task_generator") as mock_tg, \
         patch("ai.ho_ai_loop.invoke_ai_runner") as mock_runner:

        mock_tg.return_value = {"status": "error", "result": None, "error": "TG failed"}
        mock_runner.return_value = {"status": "success", "result": {"executed": 0}, "error": None}

        result = run_single_cycle(
            state_dir=state_dir,
            ai_dir=ai_dir,
            cycle=1,
            interval="30s",
            verbose=False
        )

        # Loop should complete but with error status
        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert result["errors"][0]["component"] == "task_generator"

        # Verify summary was written despite error
        summary_path = Path(state_dir) / "hands_off_ai_loop.json"
        assert summary_path.exists()


# Test 7: AI runner failure does not crash loop
def test_ai_runner_failure_does_not_crash_loop(temp_dirs):
    """Test that AI runner failure does not crash the loop."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    # Mock AI runner to fail
    with patch("ai.ho_ai_loop.invoke_task_generator") as mock_tg, \
         patch("ai.ho_ai_loop.invoke_ai_runner") as mock_runner:

        mock_tg.return_value = {"status": "success", "result": {"tasks": 5}, "error": None}
        mock_runner.return_value = {"status": "error", "result": None, "error": "Runner crashed"}

        result = run_single_cycle(
            state_dir=state_dir,
            ai_dir=ai_dir,
            cycle=1,
            interval="30s",
            verbose=False
        )

        # Loop should complete but with error status
        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert result["errors"][0]["component"] == "ai_runner"

        # Verify summary was written despite error
        summary_path = Path(state_dir) / "hands_off_ai_loop.json"
        assert summary_path.exists()


# Test 8: Error threshold stops loop
def test_error_threshold_stops_loop(temp_dirs):
    """Test that exceeding max_errors stops the loop."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    # Mock both components to fail
    with patch("ai.ho_ai_loop.invoke_task_generator") as mock_tg, \
         patch("ai.ho_ai_loop.invoke_ai_runner") as mock_runner:

        mock_tg.return_value = {"status": "error", "result": None, "error": "Always fails"}
        mock_runner.return_value = {"status": "error", "result": None, "error": "Always fails"}

        # Run loop with max_errors=3 and once=False
        # Since we can't easily test infinite loop, we'll test the logic in a controlled way
        exit_code = run_ai_loop(
            state_dir=state_dir,
            ai_dir=ai_dir,
            interval="1s",
            max_errors=3,
            verbose=False,
            once=False
        )

        # Should exit with error code after exceeding max_errors
        assert exit_code == 1

        # Verify final summary was written
        summary_path = Path(state_dir) / "hands_off_ai_loop.json"
        assert summary_path.exists()

        with open(summary_path, 'r') as f:
            summary = json.load(f)

        # Should have fatal error in summary
        assert "errors" in summary
        assert len(summary["errors"]) > 0


# Test 9: Interval parser
def test_interval_parser():
    """Test interval parsing for various formats."""
    # Test seconds
    assert parse_interval("10s") == 10
    assert parse_interval("30s") == 30
    assert parse_interval("1s") == 1

    # Test minutes
    assert parse_interval("1m") == 60
    assert parse_interval("5m") == 300
    assert parse_interval("10m") == 600

    # Test hours
    assert parse_interval("1h") == 3600
    assert parse_interval("2h") == 7200

    # Test case insensitivity
    assert parse_interval("10S") == 10
    assert parse_interval("5M") == 300
    assert parse_interval("1H") == 3600

    # Test whitespace handling
    assert parse_interval(" 30s ") == 30

    # Test invalid formats
    with pytest.raises(ValueError):
        parse_interval("invalid")

    with pytest.raises(ValueError):
        parse_interval("10")

    with pytest.raises(ValueError):
        parse_interval("")


# Test 10: CLI --once mode
def test_cli_once_mode(temp_dirs):
    """Test that --once mode runs exactly one cycle."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    # Mock both components
    with patch("ai.ho_ai_loop.invoke_task_generator") as mock_tg, \
         patch("ai.ho_ai_loop.invoke_ai_runner") as mock_runner:

        mock_tg.return_value = {"status": "success", "result": {"tasks": 5}, "error": None}
        mock_runner.return_value = {"status": "success", "result": {"executed": 3}, "error": None}

        # Run with once=True
        exit_code = run_ai_loop(
            state_dir=state_dir,
            ai_dir=ai_dir,
            interval="30s",
            max_errors=50,
            verbose=False,
            once=True
        )

        # Should exit successfully
        assert exit_code == 0

        # Should have called each component exactly once
        assert mock_tg.call_count == 1
        assert mock_runner.call_count == 1

        # Should have written summary
        summary_path = Path(state_dir) / "hands_off_ai_loop.json"
        assert summary_path.exists()

        with open(summary_path, 'r') as f:
            summary = json.load(f)

        # Should be cycle 1
        assert summary["cycle"] == 1


# Test 11: SIGINT handling
def test_sigint_handling(temp_dirs):
    """Test that SIGINT is handled gracefully."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    # Mock the components
    with patch("ai.ho_ai_loop.invoke_task_generator") as mock_tg, \
         patch("ai.ho_ai_loop.invoke_ai_runner") as mock_runner, \
         patch("ai.ho_ai_loop.sleep_interruptible") as mock_sleep:

        mock_tg.return_value = {"status": "success", "result": {"tasks": 5}, "error": None}
        mock_runner.return_value = {"status": "success", "result": {"executed": 3}, "error": None}

        # Make sleep_interruptible return True (shutdown requested) after first call
        mock_sleep.return_value = True

        # Run the loop
        exit_code = run_ai_loop(
            state_dir=state_dir,
            ai_dir=ai_dir,
            interval="30s",
            max_errors=50,
            verbose=False,
            once=False
        )

        # Should exit successfully
        assert exit_code == 0

        # Should have completed at least one cycle
        assert mock_tg.call_count >= 1
        assert mock_runner.call_count >= 1


# Additional test: Sleep interruptible
def test_sleep_interruptible():
    """Test that sleep_interruptible can be interrupted."""
    import ai.ho_ai_loop as loop_module

    # Test normal sleep (very short)
    loop_module._shutdown_requested = False
    result = sleep_interruptible(1, verbose=False)
    assert result is False  # No shutdown requested

    # Test interrupted sleep
    loop_module._shutdown_requested = True
    result = sleep_interruptible(10, verbose=False)
    assert result is True  # Shutdown was requested

    # Reset global state
    loop_module._shutdown_requested = False


# Additional test: Component invocation with missing modules
def test_invoke_task_generator_missing_module(temp_dirs):
    """Test task generator invocation when module is missing."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    # The module doesn't exist, so it should handle gracefully
    result = invoke_task_generator(state_dir, ai_dir, verbose=False)

    assert result["status"] == "error"
    assert result["error"] is not None
    assert "not available" in result["error"] or "No module" in result["error"]


def test_invoke_ai_runner_available(temp_dirs):
    """Test AI runner invocation when module is available."""
    state_dir = temp_dirs["state_dir"]
    ai_dir = temp_dirs["ai_dir"]

    result = invoke_ai_runner(state_dir, ai_dir, verbose=False)

    assert result["status"] == "success"
    assert result["result"] is not None
    assert result["error"] is None


# Additional test: Status determination in summary
def test_summary_status_determination(temp_dirs):
    """Test that summary status is determined correctly."""
    state_dir = temp_dirs["state_dir"]

    # Test error status (both failed)
    write_loop_summary(
        state_dir=state_dir,
        cycle=1,
        interval="30s",
        health={"status": "ok"},
        task_generator_result={"status": "error", "error": "failed"},
        ai_runner_result={"status": "error", "error": "failed"},
        errors=[],
        verbose=False
    )

    with open(Path(state_dir) / "hands_off_ai_loop.json", 'r') as f:
        summary = json.load(f)
    assert summary["status"] == "error"

    # Test partial status (success but with errors list)
    write_loop_summary(
        state_dir=state_dir,
        cycle=2,
        interval="30s",
        health={"status": "ok"},
        task_generator_result={"status": "success"},
        ai_runner_result={"status": "success"},
        errors=[{"warning": "something"}],
        verbose=False
    )

    with open(Path(state_dir) / "hands_off_ai_loop.json", 'r') as f:
        summary = json.load(f)
    assert summary["status"] == "partial"

    # Test ok status
    write_loop_summary(
        state_dir=state_dir,
        cycle=3,
        interval="30s",
        health={"status": "ok"},
        task_generator_result={"status": "success"},
        ai_runner_result={"status": "success"},
        errors=[],
        verbose=False
    )

    with open(Path(state_dir) / "hands_off_ai_loop.json", 'r') as f:
        summary = json.load(f)
    assert summary["status"] == "ok"
