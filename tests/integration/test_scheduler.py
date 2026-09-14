#!/usr/bin/env python3
"""
Integration tests for Hands-Off Scheduler (Batch 11)

Tests validate:
1. Scheduler runs once successfully (using --once)
2. Scheduler writes a history snapshot file
3. Scheduler handles errors without stopping
4. Interval parser works correctly
5. Snapshot JSON has the correct structure and types
6. --once stops after one cycle
"""

import os
import sys
import json
import time
import tempfile
import subprocess
from pathlib import Path

# Add scheduler to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scheduler"))

import ho_scheduler
import ho_autoloop


def test_interval_parser():
    """Test interval parsing for various formats."""
    print("Testing interval parser...")

    # Valid intervals
    assert ho_scheduler.parse_interval("30s") == 30
    assert ho_scheduler.parse_interval("5m") == 300
    assert ho_scheduler.parse_interval("2h") == 7200
    assert ho_scheduler.parse_interval("1s") == 1
    assert ho_scheduler.parse_interval("1m") == 60
    assert ho_scheduler.parse_interval("1h") == 3600

    # Test case insensitivity
    assert ho_scheduler.parse_interval("30S") == 30
    assert ho_scheduler.parse_interval("5M") == 300
    assert ho_scheduler.parse_interval("2H") == 7200

    # Test with whitespace
    assert ho_scheduler.parse_interval("  30s  ") == 30

    # Test invalid intervals
    try:
        ho_scheduler.parse_interval("invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        ho_scheduler.parse_interval("30x")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        ho_scheduler.parse_interval("0s")
        assert False, "Should have raised ValueError for zero"
    except ValueError:
        pass

    try:
        ho_scheduler.parse_interval("-5s")
        assert False, "Should have raised ValueError for negative"
    except ValueError:
        pass

    try:
        ho_scheduler.parse_interval("")
        assert False, "Should have raised ValueError for empty"
    except ValueError:
        pass

    print("✓ Interval parser tests passed")


def test_autoloop_run_all():
    """Test the autoloop run_all() function."""
    print("Testing autoloop run_all()...")

    with tempfile.TemporaryDirectory() as tmpdir:
        result = ho_autoloop.run_all(tmpdir)

        # Validate result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "timestamp" in result, "Result should have timestamp"
        assert "status" in result, "Result should have status"
        assert "pipelines" in result, "Result should have pipelines"
        assert "total_execution_time_sec" in result, "Result should have execution time"
        assert "summary" in result, "Result should have summary"

        # Validate types
        assert isinstance(result["timestamp"], str), "Timestamp should be string"
        assert isinstance(result["status"], str), "Status should be string"
        assert isinstance(result["pipelines"], dict), "Pipelines should be dict"
        assert isinstance(result["total_execution_time_sec"], (int, float)), "Execution time should be numeric"
        assert isinstance(result["summary"], str), "Summary should be string"

        # Validate status values
        assert result["status"] in ["success", "error", "partial"], "Status should be valid"

        # Validate pipelines structure
        assert "polymarket" in result["pipelines"], "Should have polymarket pipeline"
        pm_result = result["pipelines"]["polymarket"]
        assert isinstance(pm_result, dict), "Pipeline result should be dict"
        assert "status" in pm_result, "Pipeline should have status"

        print("✓ Autoloop run_all() tests passed")


def test_scheduler_once_mode():
    """Test scheduler runs once successfully with --once flag."""
    print("Testing scheduler --once mode...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run scheduler in once mode
        ho_scheduler.run_scheduler(
            state_dir=tmpdir,
            every="60s",
            once=True,
            log=False
        )

        # Verify summary file was created
        summary_path = os.path.join(tmpdir, "hands_off_summary.json")
        assert os.path.exists(summary_path), "Summary file should exist"

        # Verify history snapshot was created
        history_dir = os.path.join(tmpdir, "history")
        assert os.path.exists(history_dir), "History directory should exist"

        history_files = list(Path(history_dir).glob("*.json"))
        assert len(history_files) == 1, "Should have exactly one history snapshot"

        # Verify summary content
        with open(summary_path, 'r') as f:
            summary = json.load(f)

        assert isinstance(summary, dict), "Summary should be a dictionary"
        assert "timestamp" in summary, "Summary should have timestamp"
        assert "status" in summary, "Summary should have status"
        assert "pipelines" in summary, "Summary should have pipelines"

        # Verify history snapshot content
        with open(history_files[0], 'r') as f:
            snapshot = json.load(f)

        assert isinstance(snapshot, dict), "Snapshot should be a dictionary"
        assert "timestamp" in snapshot, "Snapshot should have timestamp"
        assert "status" in snapshot, "Snapshot should have status"

        # Verify summary and snapshot match
        assert summary == snapshot, "Summary and snapshot should match"

        print("✓ Scheduler --once mode tests passed")


def test_history_snapshot_structure():
    """Test that history snapshots have the correct structure and types."""
    print("Testing history snapshot structure...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run one cycle
        result = ho_scheduler.run_cycle(tmpdir, log=False, cycle_num=1)

        # Find the history snapshot
        history_dir = os.path.join(tmpdir, "history")
        history_files = list(Path(history_dir).glob("*.json"))
        assert len(history_files) == 1, "Should have exactly one history snapshot"

        # Load snapshot
        with open(history_files[0], 'r') as f:
            snapshot = json.load(f)

        # Validate required fields and types
        required_fields = {
            "timestamp": str,
            "status": str,
            "pipelines": dict,
            "total_execution_time_sec": (int, float),
            "summary": str
        }

        for field, expected_type in required_fields.items():
            assert field in snapshot, f"Snapshot missing required field: {field}"
            assert isinstance(snapshot[field], expected_type), \
                f"Field '{field}' has wrong type. Expected {expected_type}, got {type(snapshot[field])}"

        # Validate timestamp format (should be ISO 8601)
        timestamp = snapshot["timestamp"]
        assert "T" in timestamp, "Timestamp should be ISO 8601 format"
        assert timestamp.endswith("Z") or "+" in timestamp or "-" in timestamp[-6:], \
            "Timestamp should include timezone"

        # Validate status values
        assert snapshot["status"] in ["success", "error", "partial"], \
            f"Invalid status: {snapshot['status']}"

        # Validate pipelines structure
        assert isinstance(snapshot["pipelines"], dict), "Pipelines should be dict"
        for pipeline_name, pipeline_result in snapshot["pipelines"].items():
            assert isinstance(pipeline_name, str), "Pipeline name should be string"
            assert isinstance(pipeline_result, dict), "Pipeline result should be dict"
            assert "status" in pipeline_result, f"Pipeline '{pipeline_name}' missing status"

        print("✓ History snapshot structure tests passed")


def test_multiple_cycles():
    """Test scheduler runs multiple cycles and creates multiple snapshots."""
    print("Testing multiple scheduler cycles...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run multiple cycles manually
        num_cycles = 3
        for i in range(num_cycles):
            ho_scheduler.run_cycle(tmpdir, log=False, cycle_num=i+1)
            # Delay to ensure different timestamps (snapshots use second precision)
            if i < num_cycles - 1:  # Don't sleep after last cycle
                time.sleep(1.1)

        # Verify multiple history snapshots were created
        history_dir = os.path.join(tmpdir, "history")
        history_files = list(Path(history_dir).glob("*.json"))
        assert len(history_files) == num_cycles, \
            f"Should have {num_cycles} history snapshots, found {len(history_files)}"

        # Verify each snapshot is valid
        for snapshot_file in history_files:
            with open(snapshot_file, 'r') as f:
                snapshot = json.load(f)
            assert isinstance(snapshot, dict), "Snapshot should be dict"
            assert "timestamp" in snapshot, "Snapshot should have timestamp"

        print("✓ Multiple cycles tests passed")


def test_error_handling():
    """Test that scheduler handles errors without stopping."""
    print("Testing error handling...")

    # This test verifies that even if there's an error in the pipeline,
    # the scheduler still writes snapshots and continues

    with tempfile.TemporaryDirectory() as tmpdir:
        # The autoloop is designed to handle errors gracefully
        # Even if there's an internal error, it should return a result
        # with status="error"

        # Run a cycle - it should complete even if there are errors
        result = ho_scheduler.run_cycle(tmpdir, log=False, cycle_num=1)

        # Verify the result exists (not None)
        assert result is not None, "Should return a result even on error"

        # Verify snapshot was written even if there was an error
        history_dir = os.path.join(tmpdir, "history")
        history_files = list(Path(history_dir).glob("*.json"))
        assert len(history_files) >= 1, "Should write snapshot even on error"

        # Summary should exist
        summary_path = os.path.join(tmpdir, "hands_off_summary.json")
        assert os.path.exists(summary_path), "Should write summary even on error"

    print("✓ Error handling tests passed")


def test_summary_and_history_match():
    """Test that hands_off_summary.json and latest history snapshot match."""
    print("Testing summary and history match...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run one cycle
        ho_scheduler.run_cycle(tmpdir, log=False, cycle_num=1)

        # Load summary
        summary_path = os.path.join(tmpdir, "hands_off_summary.json")
        with open(summary_path, 'r') as f:
            summary = json.load(f)

        # Load history snapshot
        history_dir = os.path.join(tmpdir, "history")
        history_files = sorted(Path(history_dir).glob("*.json"))
        with open(history_files[-1], 'r') as f:
            snapshot = json.load(f)

        # They should be identical
        assert summary == snapshot, "Summary and latest snapshot should match"

    print("✓ Summary and history match tests passed")


def test_cli_once_flag():
    """Test CLI --once flag stops after one cycle."""
    print("Testing CLI --once flag...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run scheduler CLI with --once flag
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "..", "..", "scheduler", "ho_scheduler.py"),
            "--once",
            tmpdir
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Should complete successfully
        assert result.returncode == 0, f"CLI should exit cleanly. stderr: {result.stderr}"

        # Should have created one snapshot
        history_dir = os.path.join(tmpdir, "history")
        history_files = list(Path(history_dir).glob("*.json"))
        assert len(history_files) == 1, "Should have exactly one snapshot with --once"

        # Verify output mentions single cycle
        assert "--once mode" in result.stdout or "Single cycle completed" in result.stdout, \
            "Output should mention --once mode"

    print("✓ CLI --once flag tests passed")


def test_dryrun_mode_safety():
    """Test that DRYRUN mode is enforced."""
    print("Testing DRYRUN mode safety...")

    with tempfile.TemporaryDirectory() as tmpdir:
        result = ho_autoloop.run_all(tmpdir)

        # Verify DRYRUN mode is indicated
        assert "mode" in result, "Result should have mode field"
        assert result["mode"] == "DRYRUN", "Mode should be DRYRUN"

        # Verify pipelines are also in DRYRUN mode
        for pipeline_name, pipeline_result in result["pipelines"].items():
            if "mode" in pipeline_result:
                assert pipeline_result["mode"] == "DRYRUN", \
                    f"Pipeline '{pipeline_name}' should be in DRYRUN mode"

    print("✓ DRYRUN mode safety tests passed")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("Running Batch 11 Scheduler Integration Tests")
    print("="*70 + "\n")

    tests = [
        test_interval_parser,
        test_autoloop_run_all,
        test_scheduler_once_mode,
        test_history_snapshot_structure,
        test_multiple_cycles,
        test_error_handling,
        test_summary_and_history_match,
        test_cli_once_flag,
        test_dryrun_mode_safety
    ]

    failed_tests = []

    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"✗ {test_func.__name__} FAILED: {e}")
            failed_tests.append((test_func.__name__, e))
        print()

    print("="*70)
    if failed_tests:
        print(f"FAILED: {len(failed_tests)}/{len(tests)} tests failed\n")
        for test_name, error in failed_tests:
            print(f"  ✗ {test_name}: {error}")
        return False
    else:
        print(f"SUCCESS: All {len(tests)} tests passed!")
        return True
    print("="*70 + "\n")


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
