#!/usr/bin/env python3
"""
Integration tests for History & Performance Analytics module.

Tests ho_history_report.py functionality with fake snapshot data.
"""

import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from reports.ho_history_report import (
    load_snapshots,
    summarize_history,
    render_history_report,
    write_history_summary
)


class TestHistoryReport(unittest.TestCase):
    """Integration tests for history analytics."""

    def setUp(self):
        """Create temporary directory with fake snapshot data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = self.temp_dir.name

        # Create history subdirectory
        self.history_dir = Path(self.state_dir) / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def _create_snapshot(self, filename: str, data: dict):
        """Helper to write a snapshot JSON file."""
        snapshot_path = self.history_dir / filename
        with open(snapshot_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _create_sample_snapshots(self, count: int = 5):
        """Create a set of sample snapshots with realistic data."""
        base_time = datetime(2025, 11, 18, 12, 0, 0)

        for i in range(count):
            timestamp = base_time + timedelta(minutes=5 * i)
            timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_UTC.json"

            # Vary the data to create interesting metrics
            status = "ok" if i % 5 != 4 else "error"  # 1 error per 5 runs
            num_markets = 5 + i * 2
            num_orders = i
            balance = 32300.0 + i * 50.0

            data = {
                "status": status,
                "timestamp": timestamp_str,
                "components": {
                    "polymarket_alpha": "ok",
                    "polymarket_decider": "ok",
                    "polymarket_executor": "ok",
                    "polymarket_report": "ok"
                },
                "polymarket": {
                    "num_markets": num_markets,
                    "num_orders": num_orders,
                    "total_size_usd": 1000.0 + i * 100.0,
                    "current_pm_balance": balance,
                    "target_pm_balance": 35000.0,
                    "mode": "DRYRUN"
                },
                "errors": [] if status == "ok" else ["Test error message"]
            }

            self._create_snapshot(filename, data)

    def test_load_snapshots_empty_directory(self):
        """Test loading snapshots from empty history directory."""
        snapshots = load_snapshots(self.state_dir)
        self.assertEqual(len(snapshots), 0)

    def test_load_snapshots_no_history_directory(self):
        """Test loading snapshots when history directory doesn't exist."""
        # Remove history directory
        import shutil
        shutil.rmtree(self.history_dir)

        snapshots = load_snapshots(self.state_dir)
        self.assertEqual(len(snapshots), 0)

    def test_load_snapshots_valid_data(self):
        """Test loading valid snapshot data."""
        self._create_sample_snapshots(count=3)

        snapshots = load_snapshots(self.state_dir)
        self.assertEqual(len(snapshots), 3)

        # Verify snapshots are sorted by timestamp
        for i in range(len(snapshots) - 1):
            self.assertLessEqual(
                snapshots[i]["timestamp"],
                snapshots[i + 1]["timestamp"]
            )

    def test_load_snapshots_with_malformed_json(self):
        """Test that malformed JSON files are skipped gracefully."""
        # Create one good snapshot
        self._create_sample_snapshots(count=1)

        # Create a malformed JSON file
        bad_file = self.history_dir / "20251118_130000_UTC.json"
        with open(bad_file, 'w') as f:
            f.write("{invalid json")

        # Should load only the valid snapshot
        snapshots = load_snapshots(self.state_dir)
        self.assertEqual(len(snapshots), 1)

    def test_load_snapshots_missing_timestamp(self):
        """Test that snapshots without timestamp are skipped."""
        # Create a snapshot without timestamp
        self._create_snapshot("bad_snapshot.json", {
            "status": "ok",
            "polymarket": {"num_markets": 5}
        })

        snapshots = load_snapshots(self.state_dir)
        self.assertEqual(len(snapshots), 0)

    def test_summarize_history_empty(self):
        """Test summarize_history with no snapshots."""
        summary = summarize_history(self.state_dir, window_size=20)

        self.assertEqual(summary["total_runs"], 0)
        self.assertEqual(summary["status_counts"], {})
        self.assertEqual(summary["error_rate"], 0.0)
        self.assertIsNone(summary["first_timestamp"])
        self.assertIsNone(summary["last_timestamp"])
        self.assertEqual(summary["polymarket"], {})
        self.assertEqual(summary["recent"]["runs"], 0)

    def test_summarize_history_basic_metrics(self):
        """Test basic aggregation metrics."""
        self._create_sample_snapshots(count=10)

        summary = summarize_history(self.state_dir, window_size=20)

        # Verify structure
        self.assertIn("generated_at", summary)
        self.assertEqual(summary["state_dir"], self.state_dir)
        self.assertEqual(summary["total_runs"], 10)

        # Verify status counts (1 error per 5 runs = 2 errors total)
        self.assertEqual(summary["status_counts"]["ok"], 8)
        self.assertEqual(summary["status_counts"]["error"], 2)
        self.assertAlmostEqual(summary["error_rate"], 0.2, places=4)

        # Verify timestamps
        self.assertIsNotNone(summary["first_timestamp"])
        self.assertIsNotNone(summary["last_timestamp"])

    def test_summarize_history_polymarket_metrics(self):
        """Test Polymarket-specific metrics aggregation."""
        self._create_sample_snapshots(count=5)

        summary = summarize_history(self.state_dir, window_size=20)

        pm = summary["polymarket"]

        # Verify num_markets metrics (5, 7, 9, 11, 13)
        self.assertEqual(pm["num_markets_min"], 5)
        self.assertEqual(pm["num_markets_max"], 13)
        self.assertAlmostEqual(pm["num_markets_avg"], 9.0, places=1)

        # Verify num_orders metrics (0, 1, 2, 3, 4)
        self.assertEqual(pm["num_orders_min"], 0)
        self.assertEqual(pm["num_orders_max"], 4)
        self.assertAlmostEqual(pm["num_orders_avg"], 2.0, places=1)

        # Verify current_pm_balance metrics (32300, 32350, 32400, 32450, 32500)
        self.assertEqual(pm["current_pm_balance_min"], 32300.0)
        self.assertEqual(pm["current_pm_balance_max"], 32500.0)
        self.assertAlmostEqual(pm["current_pm_balance_avg"], 32400.0, places=1)

    def test_summarize_history_recent_window(self):
        """Test recent window analysis."""
        self._create_sample_snapshots(count=25)

        summary = summarize_history(self.state_dir, window_size=10)

        self.assertEqual(summary["recent_window_size"], 10)
        self.assertEqual(summary["recent"]["runs"], 10)

        # Last 10 snapshots should have 2 errors (indices 19 and 24)
        recent = summary["recent"]
        self.assertEqual(recent["status_counts"]["ok"], 8)
        self.assertEqual(recent["status_counts"]["error"], 2)
        self.assertAlmostEqual(recent["error_rate"], 0.2, places=4)

        # Balance delta: last 10 are indices 15-24
        # Balance at index 15: 32300 + 15*50 = 33050
        # Balance at index 24: 32300 + 24*50 = 33500
        # Delta: 33500 - 33050 = 450
        self.assertIsNotNone(recent["pm_balance_delta"])
        self.assertAlmostEqual(recent["pm_balance_delta"], 450.0, places=1)

    def test_summarize_history_small_dataset(self):
        """Test that recent window doesn't exceed total runs."""
        self._create_sample_snapshots(count=3)

        summary = summarize_history(self.state_dir, window_size=20)

        # Recent window should only include 3 runs, not 20
        self.assertEqual(summary["recent"]["runs"], 3)

    def test_render_history_report_empty(self):
        """Test rendering report with no snapshots."""
        report = render_history_report(self.state_dir, window_size=20)

        # Should be a string
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)

        # Should mention no snapshots
        self.assertIn("No historical snapshots", report)

    def test_render_history_report_with_data(self):
        """Test rendering report with sample data."""
        self._create_sample_snapshots(count=10)

        report = render_history_report(self.state_dir, window_size=5)

        # Should be a string
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)

        # Should contain key information
        self.assertIn("HISTORY & PERFORMANCE ANALYTICS", report)
        self.assertIn("Total runs:", report)
        self.assertIn("10", report)  # Total runs = 10
        self.assertIn("Error rate:", report)
        self.assertIn("POLYMARKET METRICS", report)
        self.assertIn("RECENT", report)

    def test_write_history_summary_creates_file(self):
        """Test that write_history_summary creates JSON file."""
        self._create_sample_snapshots(count=5)

        output_path = write_history_summary(self.state_dir, window_size=20)

        # Verify file exists
        self.assertTrue(Path(output_path).exists())

        # Verify it's valid JSON
        with open(output_path, 'r') as f:
            data = json.load(f)

        # Verify structure
        self.assertEqual(data["total_runs"], 5)
        self.assertIn("status_counts", data)
        self.assertIn("polymarket", data)
        self.assertIn("recent", data)

    def test_write_history_summary_creates_state_dir(self):
        """Test that write_history_summary creates state dir if needed."""
        # Use a fresh temp directory without state/history structure
        with tempfile.TemporaryDirectory() as new_temp:
            new_state_dir = Path(new_temp) / "new_state"

            # Should create the directory
            output_path = write_history_summary(str(new_state_dir), window_size=20)

            self.assertTrue(Path(output_path).exists())

    def test_write_history_summary_overwrites_existing(self):
        """Test that write_history_summary overwrites existing file."""
        # Create initial snapshots and write summary
        self._create_sample_snapshots(count=3)
        output_path = write_history_summary(self.state_dir, window_size=20)

        with open(output_path, 'r') as f:
            first_data = json.load(f)
        self.assertEqual(first_data["total_runs"], 3)

        # Add more snapshots with different timestamps
        base_time = datetime(2025, 11, 18, 13, 0, 0)  # Different hour
        for i in range(2):
            timestamp = base_time + timedelta(minutes=5 * i)
            timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_UTC.json"

            data = {
                "status": "ok",
                "timestamp": timestamp_str,
                "polymarket": {
                    "num_markets": 10 + i,
                    "current_pm_balance": 33000.0 + i * 50.0
                }
            }
            self._create_snapshot(filename, data)

        # Write summary again
        output_path = write_history_summary(self.state_dir, window_size=20)

        with open(output_path, 'r') as f:
            second_data = json.load(f)

        # Should have updated count (3 + 2 = 5 total)
        self.assertEqual(second_data["total_runs"], 5)

    def test_summarize_history_missing_polymarket_fields(self):
        """Test handling of snapshots with missing Polymarket fields."""
        # Create snapshots with incomplete data
        for i in range(3):
            timestamp = datetime(2025, 11, 18, 12, i, 0)
            timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_UTC.json"

            # Only include num_markets, omit other fields
            data = {
                "status": "ok",
                "timestamp": timestamp_str,
                "polymarket": {
                    "num_markets": 5 + i
                }
            }

            self._create_snapshot(filename, data)

        summary = summarize_history(self.state_dir, window_size=20)

        pm = summary["polymarket"]

        # Should have num_markets metrics
        self.assertIn("num_markets_min", pm)
        self.assertEqual(pm["num_markets_min"], 5)
        self.assertEqual(pm["num_markets_max"], 7)

        # Should not have metrics for missing fields
        self.assertNotIn("num_orders_min", pm)
        self.assertNotIn("current_pm_balance_min", pm)

    def test_recent_balance_delta_with_missing_data(self):
        """Test recent balance delta when some snapshots lack balance data."""
        # Create snapshots where only some have balance
        for i in range(5):
            timestamp = datetime(2025, 11, 18, 12, i, 0)
            timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_UTC.json"

            data = {
                "status": "ok",
                "timestamp": timestamp_str,
                "polymarket": {}
            }

            # Only first and last have balance
            if i == 0:
                data["polymarket"]["current_pm_balance"] = 1000.0
            elif i == 4:
                data["polymarket"]["current_pm_balance"] = 1500.0

            self._create_snapshot(filename, data)

        summary = summarize_history(self.state_dir, window_size=20)

        # Should compute delta from available data
        recent = summary["recent"]
        self.assertIsNotNone(recent["pm_balance_delta"])
        self.assertAlmostEqual(recent["pm_balance_delta"], 500.0, places=1)


def run_tests():
    """Run all tests."""
    unittest.main(argv=['test_history_report.py'], verbosity=2)


if __name__ == "__main__":
    run_tests()
