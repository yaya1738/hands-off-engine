#!/usr/bin/env python3
"""
test_polymarket_report.py

Integration tests for the Polymarket DRYRUN reporting module.

Tests that the report generation functions work correctly with fixture data.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from reports.ho_polymarket_report import render_polymarket_report, run_polymarket_pipeline_and_report


def test_render_polymarket_report():
    """Test that render_polymarket_report generates valid output."""
    fixtures_dir = str(Path(__file__).parent.parent / "fixtures")

    report = render_polymarket_report(fixtures_dir)

    # Verify report is non-empty
    assert report, "Report should not be empty"
    assert len(report) > 100, "Report should be substantial"

    # Verify key sections are present
    assert "Hands-Off Polymarket DRYRUN Report" in report, "Report should have title"
    assert "DRYRUN ONLY" in report, "Report should have DRYRUN disclaimer"
    assert "DRYRUN" in report, "Report should mention DRYRUN mode"

    # Verify alpha summary section
    assert "ALPHA SUMMARY" in report, "Report should have alpha summary"
    assert "Total Markets Analyzed:" in report, "Report should show total markets"
    assert "5" in report, "Report should show correct market count (5)"

    # Verify recommendation counts
    assert "BUY YES:" in report, "Report should show BUY YES count"
    assert "BUY NO:" in report, "Report should show BUY NO count"
    assert "HOLD:" in report, "Report should show HOLD count"

    # Verify portfolio section
    assert "PORTFOLIO SUMMARY" in report, "Report should have portfolio summary"
    assert "Current Polymarket Balance:" in report, "Report should show current PM balance"
    assert "Target Polymarket Balance:" in report, "Report should show target PM balance"
    assert "32,300.00" in report, "Report should show current balance from fixture"
    assert "35,000.00" in report, "Report should show target balance from fixture"

    # Verify execution plan section
    assert "EXECUTION PLAN SUMMARY" in report, "Report should have execution plan"
    assert "Number of Orders:" in report, "Report should show order count"
    assert "Total Size (USD):" in report, "Report should show total size"
    assert "Execution Mode:" in report, "Report should show mode"

    # Verify top markets section
    assert "Top" in report and "Markets by Positive Edge" in report, "Report should show top markets"
    assert "Bitcoin" in report or "Democrats" in report, "Report should include specific market questions"

    print("✓ test_render_polymarket_report PASSED")


def test_render_report_with_missing_files():
    """Test that report handles missing files gracefully."""
    non_existent_dir = "/tmp/nonexistent_state_dir_12345"

    report = render_polymarket_report(non_existent_dir)

    # Should still generate a report, just with zeros/empty data
    assert report, "Report should be generated even with missing files"
    assert "Hands-Off Polymarket DRYRUN Report" in report, "Report should have title"
    assert "DRYRUN ONLY" in report, "Report should have disclaimer"

    print("✓ test_render_report_with_missing_files PASSED")


def test_run_polymarket_pipeline_and_report():
    """Test that run_polymarket_pipeline_and_report returns correct structure."""
    fixtures_dir = str(Path(__file__).parent.parent / "fixtures")

    result = run_polymarket_pipeline_and_report(fixtures_dir)

    # Verify return structure
    assert isinstance(result, dict), "Result should be a dict"
    assert "report_text" in result, "Result should have report_text"
    assert "summary" in result, "Result should have summary"

    # Verify report_text
    report_text = result["report_text"]
    assert isinstance(report_text, str), "report_text should be a string"
    assert len(report_text) > 100, "report_text should be substantial"
    assert "Hands-Off Polymarket DRYRUN Report" in report_text, "report_text should have title"
    assert "DRYRUN" in report_text, "report_text should mention DRYRUN"

    # Verify summary structure
    summary = result["summary"]
    assert isinstance(summary, dict), "summary should be a dict"

    # Verify all required keys are present
    required_keys = [
        "num_markets",
        "num_buy_yes",
        "num_buy_no",
        "num_hold",
        "num_orders",
        "total_size_usd",
        "current_pm_balance",
        "target_pm_balance",
        "mode"
    ]
    for key in required_keys:
        assert key in summary, f"summary should have key: {key}"

    # Verify summary values from fixtures
    assert summary["num_markets"] == 5, "Should have 5 markets from fixture"
    assert summary["num_buy_yes"] == 2, "Should have 2 BUY YES recommendations"
    assert summary["num_buy_no"] == 1, "Should have 1 BUY NO recommendation"
    assert summary["num_hold"] == 2, "Should have 2 HOLD recommendations"
    assert summary["num_orders"] == 3, "Should have 3 orders from fixture"
    assert summary["total_size_usd"] == 1000.0, "Total size should be $1000 from fixture"
    assert summary["current_pm_balance"] == 32300.0, "Current PM balance should match fixture"
    assert summary["target_pm_balance"] == 35000.0, "Target PM balance should match fixture"
    assert summary["mode"] == "DRYRUN", "Mode should be DRYRUN"

    print("✓ test_run_polymarket_pipeline_and_report PASSED")


def test_summary_types():
    """Test that summary values have correct types."""
    fixtures_dir = str(Path(__file__).parent.parent / "fixtures")

    result = run_polymarket_pipeline_and_report(fixtures_dir)
    summary = result["summary"]

    # All numeric fields should be numbers
    assert isinstance(summary["num_markets"], int), "num_markets should be int"
    assert isinstance(summary["num_buy_yes"], int), "num_buy_yes should be int"
    assert isinstance(summary["num_buy_no"], int), "num_buy_no should be int"
    assert isinstance(summary["num_hold"], int), "num_hold should be int"
    assert isinstance(summary["num_orders"], int), "num_orders should be int"
    assert isinstance(summary["total_size_usd"], (int, float)), "total_size_usd should be numeric"
    assert isinstance(summary["current_pm_balance"], (int, float)), "current_pm_balance should be numeric"
    assert isinstance(summary["target_pm_balance"], (int, float)), "target_pm_balance should be numeric"

    # Mode should be string
    assert isinstance(summary["mode"], str), "mode should be string"

    print("✓ test_summary_types PASSED")


if __name__ == "__main__":
    print("Running integration tests for ho_polymarket_report...")
    print("=" * 70)

    try:
        test_render_polymarket_report()
        test_render_report_with_missing_files()
        test_run_polymarket_pipeline_and_report()
        test_summary_types()

        print("=" * 70)
        print("All tests PASSED ✓")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
