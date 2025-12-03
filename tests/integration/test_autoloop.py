#!/usr/bin/env python3
"""
test_autoloop.py

Integration tests for the Hands-Off Autoloop orchestrator.

Tests that the autoloop orchestrator works correctly with fixture data and
produces the expected meta-summary structure.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ho_autoloop import run_all


def test_run_all_success():
    """Test that run_all executes successfully with valid fixture data."""
    # Create a temporary directory for this test
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Copy fixture files to temp state directory
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        for fixture_file in ["polymarket-model.json", "decision_output.json", "execution_plan.json"]:
            src = fixtures_dir / fixture_file
            dst = state_dir / fixture_file
            if src.exists():
                shutil.copy(src, dst)

        # Run the autoloop
        result = run_all(str(state_dir))

        # Verify return structure
        assert isinstance(result, dict), "Result should be a dict"
        assert "summary" in result, "Result should have summary"
        assert "report_text" in result, "Result should have report_text"
        assert "raw" in result, "Result should have raw data"

        print("✓ test_run_all_success: return structure verified")


def test_summary_json_created():
    """Test that hands_off_summary.json is created in state directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Copy fixtures
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        for fixture_file in ["polymarket-model.json", "decision_output.json", "execution_plan.json"]:
            src = fixtures_dir / fixture_file
            dst = state_dir / fixture_file
            if src.exists():
                shutil.copy(src, dst)

        # Run autoloop
        run_all(str(state_dir))

        # Verify JSON file was created
        summary_path = state_dir / "hands_off_summary.json"
        assert summary_path.exists(), "hands_off_summary.json should be created"

        # Verify it's valid JSON
        summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
        assert isinstance(summary_data, dict), "Summary should be a dict"

        print("✓ test_summary_json_created: JSON file verified")


def test_summary_structure():
    """Test that the meta-summary has all required keys and structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Copy fixtures
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        for fixture_file in ["polymarket-model.json", "decision_output.json", "execution_plan.json"]:
            src = fixtures_dir / fixture_file
            dst = state_dir / fixture_file
            if src.exists():
                shutil.copy(src, dst)

        # Run autoloop
        result = run_all(str(state_dir))
        summary = result["summary"]

        # Verify top-level keys
        required_top_level_keys = ["status", "timestamp", "components", "polymarket", "errors"]
        for key in required_top_level_keys:
            assert key in summary, f"Summary should have key: {key}"

        # Verify components structure
        assert isinstance(summary["components"], dict), "components should be a dict"
        required_components = [
            "polymarket_alpha",
            "polymarket_decider",
            "polymarket_executor",
            "polymarket_report"
        ]
        for component in required_components:
            assert component in summary["components"], f"components should include: {component}"

        # Verify polymarket structure
        assert isinstance(summary["polymarket"], dict), "polymarket should be a dict"
        required_polymarket_keys = [
            "num_markets",
            "num_orders",
            "total_size_usd",
            "current_pm_balance",
            "target_pm_balance",
            "mode"
        ]
        for key in required_polymarket_keys:
            assert key in summary["polymarket"], f"polymarket should have key: {key}"

        # Verify errors is a list
        assert isinstance(summary["errors"], list), "errors should be a list"

        print("✓ test_summary_structure: structure verified")


def test_successful_run_values():
    """Test that a successful run produces correct status and values."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Copy fixtures
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        for fixture_file in ["polymarket-model.json", "decision_output.json", "execution_plan.json"]:
            src = fixtures_dir / fixture_file
            dst = state_dir / fixture_file
            if src.exists():
                shutil.copy(src, dst)

        # Run autoloop
        result = run_all(str(state_dir))
        summary = result["summary"]

        # Verify status is OK
        assert summary["status"] == "ok", "Status should be 'ok' for successful run"

        # Verify mode is DRYRUN
        assert summary["polymarket"]["mode"] == "DRYRUN", "Mode should be DRYRUN"

        # Verify we have markets (from fixture)
        assert summary["polymarket"]["num_markets"] >= 1, "Should have at least 1 market"
        assert summary["polymarket"]["num_markets"] == 5, "Fixture has 5 markets"

        # Verify we have orders (from fixture)
        assert summary["polymarket"]["num_orders"] >= 1, "Should have at least 1 order"
        assert summary["polymarket"]["num_orders"] == 3, "Fixture has 3 orders"

        # Verify errors list is empty
        assert len(summary["errors"]) == 0, "errors should be empty for successful run"

        # Verify all components are OK
        for component, status in summary["components"].items():
            assert status == "ok", f"Component {component} should have status 'ok'"

        # Verify numeric values from fixtures
        assert summary["polymarket"]["total_size_usd"] == 1000.0, "Total size should match fixture"
        assert summary["polymarket"]["current_pm_balance"] == 32300.0, "Current balance should match fixture"
        assert summary["polymarket"]["target_pm_balance"] == 35000.0, "Target balance should match fixture"

        # Verify timestamp is present and looks like ISO format
        assert summary["timestamp"], "Timestamp should be present"
        assert "T" in summary["timestamp"], "Timestamp should be ISO format"

        print("✓ test_successful_run_values: values verified")


def test_error_handling():
    """Test that errors are handled gracefully and summary is still written."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Do NOT copy fixture files - this will cause the pipeline to fail gracefully
        # (It should load empty/default data rather than crash)

        # Run autoloop - with missing files it should still work but with empty data
        result = run_all(str(state_dir))
        summary = result["summary"]

        # Even with missing files, the summary should be created
        summary_path = state_dir / "hands_off_summary.json"
        assert summary_path.exists(), "Summary JSON should be written even on error"

        # Verify structure is still valid
        assert "status" in summary, "Summary should have status"
        assert "errors" in summary, "Summary should have errors list"
        assert isinstance(summary["errors"], list), "errors should be a list"

        print("✓ test_error_handling: error handling verified")


def test_report_text_included():
    """Test that report_text is included in the result."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Copy fixtures
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        for fixture_file in ["polymarket-model.json", "decision_output.json", "execution_plan.json"]:
            src = fixtures_dir / fixture_file
            dst = state_dir / fixture_file
            if src.exists():
                shutil.copy(src, dst)

        # Run autoloop
        result = run_all(str(state_dir))

        # Verify report_text is present and substantial
        report_text = result.get("report_text", "")
        assert report_text, "report_text should not be empty"
        assert len(report_text) > 100, "report_text should be substantial"
        assert "DRYRUN" in report_text, "report_text should mention DRYRUN"
        assert "Hands-Off Polymarket" in report_text, "report_text should have title"

        print("✓ test_report_text_included: report text verified")


def test_data_types():
    """Test that all fields have the correct data types."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Copy fixtures
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        for fixture_file in ["polymarket-model.json", "decision_output.json", "execution_plan.json"]:
            src = fixtures_dir / fixture_file
            dst = state_dir / fixture_file
            if src.exists():
                shutil.copy(src, dst)

        # Run autoloop
        result = run_all(str(state_dir))
        summary = result["summary"]

        # Verify types
        assert isinstance(summary["status"], str), "status should be str"
        assert isinstance(summary["timestamp"], str), "timestamp should be str"
        assert isinstance(summary["components"], dict), "components should be dict"
        assert isinstance(summary["polymarket"], dict), "polymarket should be dict"
        assert isinstance(summary["errors"], list), "errors should be list"

        # Verify polymarket field types
        pm = summary["polymarket"]
        assert isinstance(pm["num_markets"], int), "num_markets should be int"
        assert isinstance(pm["num_orders"], int), "num_orders should be int"
        assert isinstance(pm["total_size_usd"], (int, float)), "total_size_usd should be numeric"
        assert isinstance(pm["current_pm_balance"], (int, float)), "current_pm_balance should be numeric"
        assert isinstance(pm["target_pm_balance"], (int, float)), "target_pm_balance should be numeric"
        assert isinstance(pm["mode"], str), "mode should be str"

        print("✓ test_data_types: types verified")


if __name__ == "__main__":
    print("Running integration tests for ho_autoloop...")
    print("=" * 70)

    try:
        test_run_all_success()
        test_summary_json_created()
        test_summary_structure()
        test_successful_run_values()
        test_error_handling()
        test_report_text_included()
        test_data_types()

        print("=" * 70)
        print("All tests PASSED ✓")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
