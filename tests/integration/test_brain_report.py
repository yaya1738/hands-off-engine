#!/usr/bin/env python3
"""
Tests for ho_brain_report.py - Unified Brain Summary module
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from reports.ho_brain_report import (
    build_brain_summary,
    write_brain_summary,
    _determine_overall_status,
    _safe_read_json
)


class TestBrainReportEmptyState(unittest.TestCase):
    """Test brain report with no existing state files"""

    def test_build_brain_summary_empty_state_dir(self):
        """Test that empty state dir produces valid structure with errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brain_summary(tmpdir)

            # Check top-level keys
            self.assertIn("generated_at", result)
            self.assertIn("state_dir", result)
            self.assertIn("status", result)
            self.assertIn("sources", result)
            self.assertIn("health", result)
            self.assertIn("polymarket", result)
            self.assertIn("loop", result)
            self.assertIn("history", result)
            self.assertIn("notes", result)
            self.assertIn("errors", result)

            # Verify sources are all marked as missing
            self.assertEqual(result["sources"]["summary"], "missing")
            self.assertEqual(result["sources"]["history"], "missing")
            self.assertEqual(result["sources"]["health"], "missing")
            self.assertEqual(result["sources"]["ai_loop"], "missing")

            # Verify errors list is populated
            self.assertGreater(len(result["errors"]), 0)
            self.assertTrue(any("not found" in err.lower() for err in result["errors"]))

            # Verify timestamp is valid ISO8601
            dt = datetime.fromisoformat(result["generated_at"])
            self.assertIsInstance(dt, datetime)


class TestBrainReportWithMinimalFiles(unittest.TestCase):
    """Test brain report with minimal valid state files"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.state_dir = self.tmpdir.name

        # Create minimal valid files
        self.health_data = {
            "overall_status": "ok",
            "error_rate": 0.05,
            "last_check_ts": datetime.now(timezone.utc).isoformat()
        }

        self.summary_data = {
            "mode": "DRYRUN",
            "markets": [{"id": "market1"}, {"id": "market2"}],
            "execution": {
                "orders": [{"id": "order1"}]
            },
            "current_pm_balance": 327.8,
            "target_pm_balance": 350.0
        }

        self.history_data = {
            "total_runs": 42,
            "error_rate": 0.0476,
            "pm_balance_delta": 25.0
        }

        self.loop_data = {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_cycles": 20
        }

        # Write files
        with open(os.path.join(self.state_dir, "hands_off_health.json"), 'w') as f:
            json.dump(self.health_data, f)

        with open(os.path.join(self.state_dir, "hands_off_summary.json"), 'w') as f:
            json.dump(self.summary_data, f)

        with open(os.path.join(self.state_dir, "hands_off_history_summary.json"), 'w') as f:
            json.dump(self.history_data, f)

        with open(os.path.join(self.state_dir, "hands_off_ai_loop.json"), 'w') as f:
            json.dump(self.loop_data, f)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_build_brain_summary_with_minimal_files(self):
        """Test that minimal valid files produce correct aggregated output"""
        result = build_brain_summary(self.state_dir)

        # Check sources all OK
        self.assertEqual(result["sources"]["summary"], "ok")
        self.assertEqual(result["sources"]["history"], "ok")
        self.assertEqual(result["sources"]["health"], "ok")
        self.assertEqual(result["sources"]["ai_loop"], "ok")

        # Check health section
        self.assertEqual(result["health"]["status"], "ok")
        self.assertEqual(result["health"]["recent_error_rate"], 0.05)
        self.assertIsNotNone(result["health"]["latest_snapshot_age_sec"])

        # Check polymarket section
        self.assertEqual(result["polymarket"]["mode"], "DRYRUN")
        self.assertEqual(result["polymarket"]["num_markets"], 2)
        self.assertEqual(result["polymarket"]["num_orders"], 1)
        self.assertEqual(result["polymarket"]["current_pm_balance"], 327.8)
        self.assertEqual(result["polymarket"]["target_pm_balance"], 350.0)

        # Check loop section
        self.assertEqual(result["loop"]["last_cycle_status"], "ok")
        self.assertEqual(result["loop"]["recent_cycles"], 20)

        # Check history section
        self.assertEqual(result["history"]["total_runs"], 42)
        self.assertEqual(result["history"]["error_rate"], 0.0476)
        self.assertEqual(result["history"]["pm_balance_delta_recent"], 25.0)

        # Check overall status (should be OK with low error rate)
        self.assertEqual(result["status"], "ok")

        # No errors expected
        self.assertEqual(len(result["errors"]), 0)


class TestMalformedFiles(unittest.TestCase):
    """Test handling of missing or malformed files"""

    def test_missing_or_malformed_files_populate_errors(self):
        """Test that malformed JSON files are handled gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a malformed JSON file
            malformed_path = os.path.join(tmpdir, "hands_off_summary.json")
            with open(malformed_path, 'w') as f:
                f.write("{this is not valid json")

            result = build_brain_summary(tmpdir)

            # Check that error was recorded
            self.assertGreater(len(result["errors"]), 0)
            self.assertTrue(
                any("malformed" in err.lower() or "json" in err.lower()
                    for err in result["errors"])
            )

            # Check that summary source is marked as error
            self.assertEqual(result["sources"]["summary"], "error")

            # Other sources should be missing
            self.assertEqual(result["sources"]["health"], "missing")
            self.assertEqual(result["sources"]["history"], "missing")
            self.assertEqual(result["sources"]["ai_loop"], "missing")

    def test_safe_read_json_missing_file(self):
        """Test _safe_read_json with missing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = os.path.join(tmpdir, "nonexistent.json")
            data, error = _safe_read_json(missing_path)

            self.assertIsNone(data)
            self.assertIsNotNone(error)
            self.assertIn("not found", error.lower())

    def test_safe_read_json_malformed_file(self):
        """Test _safe_read_json with malformed JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = os.path.join(tmpdir, "bad.json")
            with open(bad_path, 'w') as f:
                f.write("{bad json content")

            data, error = _safe_read_json(bad_path)

            self.assertIsNone(data)
            self.assertIsNotNone(error)
            self.assertIn("malformed", error.lower())


class TestWriteBrainSummary(unittest.TestCase):
    """Test write_brain_summary creates files correctly"""

    def test_write_brain_summary_creates_files(self):
        """Test that write_brain_summary creates both JSON and text files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = write_brain_summary(tmpdir)

            # Check JSON file exists
            json_path = os.path.join(tmpdir, "hands_off_brain.json")
            self.assertTrue(os.path.exists(json_path))

            # Check text file exists
            txt_path = os.path.join(tmpdir, "hands_off_brain.txt")
            self.assertTrue(os.path.exists(txt_path))

            # Verify JSON is parseable
            with open(json_path, 'r') as f:
                loaded_data = json.load(f)

            # Check top-level keys
            self.assertIn("status", loaded_data)
            self.assertIn("sources", loaded_data)
            self.assertIn("health", loaded_data)
            self.assertIn("polymarket", loaded_data)

            # Verify text file has content
            with open(txt_path, 'r') as f:
                text_content = f.read()

            self.assertIn("Hands-Off Brain Summary", text_content)
            self.assertIn("Overall Status", text_content)
            self.assertIn("Health:", text_content)
            self.assertIn("Polymarket:", text_content)

            # Return value should match what was written
            self.assertEqual(result["status"], loaded_data["status"])


class TestStatusDerivation(unittest.TestCase):
    """Test status derivation rules"""

    def test_status_derivation_rules(self):
        """Test various status derivation scenarios"""

        # Scenario 1: health.status == "error" → overall status "error"
        status = _determine_overall_status("error", 0.05)
        self.assertEqual(status, "error")

        # Scenario 2: health.status == "ok" but high error rate → "warn"
        status = _determine_overall_status("ok", 0.30)
        self.assertEqual(status, "warn")

        # Scenario 3: health.status == "ok" and low error rate → "ok"
        status = _determine_overall_status("ok", 0.05)
        self.assertEqual(status, "ok")

        # Scenario 4: health.status == None but low error rate → "ok"
        status = _determine_overall_status(None, 0.05)
        self.assertEqual(status, "ok")

        # Scenario 5: health.status == "warn" but low error rate → "ok"
        status = _determine_overall_status("warn", 0.05)
        self.assertEqual(status, "ok")

        # Scenario 6: error threshold exactly at 0.25 → "ok"
        status = _determine_overall_status("ok", 0.25)
        self.assertEqual(status, "ok")

        # Scenario 7: error threshold just above 0.25 → "warn"
        status = _determine_overall_status("ok", 0.26)
        self.assertEqual(status, "warn")

    def test_integrated_status_derivation(self):
        """Test status derivation in full build_brain_summary context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test case: error health status
            health_data = {
                "overall_status": "error",
                "error_rate": 0.05
            }
            with open(os.path.join(tmpdir, "hands_off_health.json"), 'w') as f:
                json.dump(health_data, f)

            result = build_brain_summary(tmpdir)
            self.assertEqual(result["status"], "error")

            # Test case: high error rate in history
            os.remove(os.path.join(tmpdir, "hands_off_health.json"))
            history_data = {
                "total_runs": 100,
                "error_rate": 0.35
            }
            with open(os.path.join(tmpdir, "hands_off_history_summary.json"), 'w') as f:
                json.dump(history_data, f)

            result = build_brain_summary(tmpdir)
            self.assertEqual(result["status"], "warn")


class TestCLIInvocation(unittest.TestCase):
    """Test CLI interface"""

    def test_cli_invocation_default(self):
        """Test CLI invocation with default state dir"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary test state dir
            test_state = os.path.join(tmpdir, "state")
            os.makedirs(test_state)

            # Run CLI
            result = subprocess.run(
                [sys.executable, "reports/ho_brain_report.py", "--state-dir", test_state],
                cwd=project_root,
                capture_output=True,
                text=True
            )

            # Check exit code
            self.assertEqual(result.returncode, 0)

            # Check output message
            self.assertIn("Brain summary written", result.stdout)
            self.assertIn("hands_off_brain.json", result.stdout)
            self.assertIn("status=", result.stdout)

            # Verify files were created
            self.assertTrue(os.path.exists(os.path.join(test_state, "hands_off_brain.json")))
            self.assertTrue(os.path.exists(os.path.join(test_state, "hands_off_brain.txt")))

    def test_cli_invocation_with_valid_files(self):
        """Test CLI with pre-existing valid state files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create health file
            health_data = {"overall_status": "ok", "error_rate": 0.02}
            with open(os.path.join(tmpdir, "hands_off_health.json"), 'w') as f:
                json.dump(health_data, f)

            # Run CLI
            result = subprocess.run(
                [sys.executable, "reports/ho_brain_report.py", "--state-dir", tmpdir],
                cwd=project_root,
                capture_output=True,
                text=True
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("status=ok", result.stdout)


class TestNotesGeneration(unittest.TestCase):
    """Test notes generation logic"""

    def test_notes_for_healthy_system(self):
        """Test notes when system is healthy"""
        with tempfile.TemporaryDirectory() as tmpdir:
            health_data = {"overall_status": "ok", "error_rate": 0.03}
            with open(os.path.join(tmpdir, "hands_off_health.json"), 'w') as f:
                json.dump(health_data, f)

            result = build_brain_summary(tmpdir)

            # Should have at least one note about healthy system
            self.assertGreater(len(result["notes"]), 0)
            self.assertTrue(
                any("healthy" in note.lower() or "normal" in note.lower()
                    for note in result["notes"])
            )

    def test_notes_for_high_error_rate(self):
        """Test notes when error rate is high"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_data = {"total_runs": 100, "error_rate": 0.35}
            with open(os.path.join(tmpdir, "hands_off_history_summary.json"), 'w') as f:
                json.dump(history_data, f)

            result = build_brain_summary(tmpdir)

            # Should have note about high error rate
            self.assertTrue(
                any("error rate" in note.lower() for note in result["notes"])
            )


if __name__ == "__main__":
    unittest.main()
