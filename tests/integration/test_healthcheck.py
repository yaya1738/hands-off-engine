"""
Integration tests for Hands-Off Engine health check system.

These tests verify the complete health monitoring functionality
without requiring external network calls or live services.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from health.ho_healthcheck import (
    gather_health,
    render_health_text,
    write_health_json,
    _check_summary_file,
    _check_polymarket_fetch,
    _check_snapshot_history,
    _extract_status_from_snapshot,
    _calculate_error_rate,
    _determine_overall_status,
)


class TestHealthCheckEmptyState(unittest.TestCase):
    """Test health check behavior with empty or missing state directory."""

    def test_health_empty_state_dir(self):
        """Test health check when state directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent_state"

            health = gather_health(state_dir=str(nonexistent))

            # Should report error status
            self.assertEqual(health["status"], "error")
            self.assertIn("does not exist", " ".join(health["errors"]))

            # All components should be error or unknown
            self.assertEqual(health["components"]["polymarket_fetch"], "error")
            self.assertEqual(health["components"]["polymarket_pipeline"], "error")
            self.assertEqual(health["components"]["history"], "error")

    def test_health_missing_summary(self):
        """Test health check when hands_off_summary.json is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()

            health = gather_health(state_dir=str(state_dir))

            # Pipeline component should be error
            self.assertEqual(health["components"]["polymarket_pipeline"], "error")
            self.assertIn("hands_off_summary.json", " ".join(health["errors"]))

    def test_health_missing_snapshot_dir(self):
        """Test health check when history/ directory is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()

            # Create valid summary and compact files
            self._create_valid_summary(state_dir)
            self._create_valid_compact(state_dir)

            health = gather_health(state_dir=str(state_dir))

            # History component should be error
            self.assertEqual(health["components"]["history"], "error")
            self.assertIn("history/", " ".join(health["errors"]))

    @staticmethod
    def _create_valid_summary(state_dir: Path):
        """Helper: create a valid summary file."""
        summary_file = state_dir / "hands_off_summary.json"
        summary_file.write_text(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ok",
        }))

    @staticmethod
    def _create_valid_compact(state_dir: Path, age_sec: int = 60):
        """Helper: create a valid compact file with specific age."""
        compact_file = state_dir / "polymarket-compact.json"
        compact_file.write_text(json.dumps({
            "markets": [
                {"id": "test-market-1", "question": "Test market?"}
            ]
        }))

        # Set file modification time to simulate age
        now = datetime.now(timezone.utc).timestamp()
        mtime = now - age_sec
        compact_file.touch()
        import os
        os.utime(compact_file, (mtime, mtime))


class TestHealthCheckValidState(unittest.TestCase):
    """Test health check with valid state data."""

    def test_health_valid_snapshot_and_summary(self):
        """Test health check with valid summary and snapshot files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()
            history_dir = state_dir / "history"
            history_dir.mkdir()

            # Create valid files
            self._create_valid_summary(state_dir)
            self._create_valid_compact(state_dir, age_sec=60)
            self._create_snapshot(history_dir, "snapshot_001.json", status="ok", age_sec=30)

            health = gather_health(state_dir=str(state_dir))

            # Should be healthy
            self.assertEqual(health["status"], "ok")
            self.assertEqual(health["components"]["polymarket_pipeline"], "ok")
            self.assertEqual(health["components"]["polymarket_fetch"], "ok")
            self.assertEqual(health["components"]["history"], "ok")

            # Check values
            self.assertEqual(health["checks"]["num_snapshots"], 1)
            self.assertIsNotNone(health["checks"]["latest_snapshot_age_sec"])
            self.assertEqual(health["checks"]["recent_error_rate"], 0.0)

    def test_recent_error_rate_calculation(self):
        """Test error rate calculation from multiple snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()
            history_dir = state_dir / "history"
            history_dir.mkdir()

            # Create valid summary and compact
            self._create_valid_summary(state_dir)
            self._create_valid_compact(state_dir)

            # Create 20 snapshots: 6 errors, 14 ok (error rate = 0.30)
            for i in range(20):
                status = "error" if i < 6 else "ok"
                self._create_snapshot(
                    history_dir,
                    f"snapshot_{i:03d}.json",
                    status=status,
                    age_sec=100 + i
                )

            health = gather_health(state_dir=str(state_dir))

            # Error rate should be 6/20 = 0.30
            self.assertAlmostEqual(health["checks"]["recent_error_rate"], 0.30, places=2)

            # Status should be warn (error rate > 0.25)
            self.assertEqual(health["status"], "warn")

    def test_snapshot_age_and_timestamp_parsing(self):
        """Test snapshot age calculation and status parsing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()
            history_dir = state_dir / "history"
            history_dir.mkdir()

            self._create_valid_summary(state_dir)
            self._create_valid_compact(state_dir)

            # Create snapshot with known age
            age_sec = 120
            self._create_snapshot(history_dir, "snapshot_001.json", status="ok", age_sec=age_sec)

            health = gather_health(state_dir=str(state_dir))

            # Age should be approximately correct (allow 5 second tolerance)
            actual_age = health["checks"]["latest_snapshot_age_sec"]
            self.assertIsNotNone(actual_age)
            self.assertAlmostEqual(actual_age, age_sec, delta=5)

            # Status should be parsed correctly
            self.assertEqual(health["checks"]["most_recent_run_status"], "ok")

    @staticmethod
    def _create_valid_summary(state_dir: Path):
        """Helper: create a valid summary file."""
        summary_file = state_dir / "hands_off_summary.json"
        summary_file.write_text(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ok",
            "metrics": {"total_runs": 100}
        }))

    @staticmethod
    def _create_valid_compact(state_dir: Path, age_sec: int = 60):
        """Helper: create a valid compact file with specific age."""
        compact_file = state_dir / "polymarket-compact.json"
        compact_file.write_text(json.dumps({
            "markets": [
                {"id": "test-market-1", "question": "Test market?"},
                {"id": "test-market-2", "question": "Another market?"}
            ]
        }))

        # Set file modification time
        now = datetime.now(timezone.utc).timestamp()
        mtime = now - age_sec
        import os
        os.utime(compact_file, (mtime, mtime))

    @staticmethod
    def _create_snapshot(history_dir: Path, filename: str, status: str, age_sec: int):
        """Helper: create a snapshot file with specific status and age."""
        snapshot_file = history_dir / filename
        snapshot_file.write_text(json.dumps({
            "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=age_sec)).isoformat(),
            "status": status,
            "pipeline_result": "completed" if status == "ok" else "failed",
            "errors": [] if status == "ok" else ["Test error"]
        }))

        # Set file modification time
        now = datetime.now(timezone.utc).timestamp()
        mtime = now - age_sec
        import os
        os.utime(snapshot_file, (mtime, mtime))


class TestHealthCheckPolymarketFetch(unittest.TestCase):
    """Test health checks for Polymarket fetch component."""

    def test_missing_or_malformed_polymarket_compact(self):
        """Test handling of missing or malformed polymarket-compact.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()

            # Test missing file
            health = gather_health(state_dir=str(state_dir))
            self.assertEqual(health["components"]["polymarket_fetch"], "error")
            self.assertIn("polymarket-compact.json", " ".join(health["errors"]))

            # Test malformed JSON
            compact_file = state_dir / "polymarket-compact.json"
            compact_file.write_text("{ invalid json }")

            health = gather_health(state_dir=str(state_dir))
            self.assertEqual(health["components"]["polymarket_fetch"], "error")
            self.assertIn("malformed", " ".join(health["errors"]))

    def test_health_detects_old_data(self):
        """Test detection of stale polymarket data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()
            history_dir = state_dir / "history"
            history_dir.mkdir()

            self._create_valid_summary(state_dir)
            self._create_snapshot(history_dir, "snapshot_001.json", "ok", 60)

            # Create compact file that's 10 minutes old (> 5 minute threshold)
            compact_file = state_dir / "polymarket-compact.json"
            compact_file.write_text(json.dumps({
                "markets": [{"id": "test", "question": "Test?"}]
            }))

            # Set to 10 minutes old
            import os
            now = datetime.now(timezone.utc).timestamp()
            old_time = now - 600  # 10 minutes
            os.utime(compact_file, (old_time, old_time))

            health = gather_health(state_dir=str(state_dir))

            # Fetch should be warn due to stale data
            self.assertEqual(health["components"]["polymarket_fetch"], "warn")
            self.assertIn("stale", " ".join(health["errors"]))

    def test_polymarket_compact_no_markets(self):
        """Test detection of empty markets in polymarket-compact.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()

            # Create compact with empty markets list
            compact_file = state_dir / "polymarket-compact.json"
            compact_file.write_text(json.dumps({"markets": []}))

            health = gather_health(state_dir=str(state_dir))

            # Should be warn (no markets)
            self.assertEqual(health["components"]["polymarket_fetch"], "warn")
            self.assertIn("no markets", " ".join(health["errors"]))

    @staticmethod
    def _create_valid_summary(state_dir: Path):
        """Helper: create a valid summary file."""
        summary_file = state_dir / "hands_off_summary.json"
        summary_file.write_text(json.dumps({"status": "ok"}))

    @staticmethod
    def _create_snapshot(history_dir: Path, filename: str, status: str, age_sec: int):
        """Helper: create a snapshot file."""
        snapshot_file = history_dir / filename
        snapshot_file.write_text(json.dumps({
            "status": status,
            "errors": [] if status == "ok" else ["Error"]
        }))

        import os
        now = datetime.now(timezone.utc).timestamp()
        mtime = now - age_sec
        os.utime(snapshot_file, (mtime, mtime))


class TestHealthCheckStatusRules(unittest.TestCase):
    """Test overall status determination rules."""

    def test_top_level_status_rules(self):
        """Test that overall status follows error > warn > ok precedence."""
        # All OK
        components = {
            "polymarket_fetch": "ok",
            "polymarket_pipeline": "ok",
            "history": "ok",
            "scheduler": "unknown"
        }
        self.assertEqual(_determine_overall_status(components), "ok")

        # One warn
        components["history"] = "warn"
        self.assertEqual(_determine_overall_status(components), "warn")

        # One error (should override warn)
        components["polymarket_fetch"] = "error"
        self.assertEqual(_determine_overall_status(components), "error")

        # All errors
        components = {k: "error" for k in components}
        self.assertEqual(_determine_overall_status(components), "error")

    def test_health_detects_pipeline_error_status(self):
        """Test detection of pipeline error status from snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()
            history_dir = state_dir / "history"
            history_dir.mkdir()

            self._create_valid_summary(state_dir)
            self._create_valid_compact(state_dir)

            # Create 20 snapshots: 12 errors (60% error rate)
            for i in range(20):
                status = "error" if i < 12 else "ok"
                self._create_snapshot(
                    history_dir,
                    f"snapshot_{i:03d}.json",
                    status=status,
                    age_sec=200 - i
                )

            health = gather_health(state_dir=str(state_dir))

            # Error rate > 0.50, so should be error
            self.assertEqual(health["components"]["history"], "error")
            self.assertEqual(health["status"], "error")
            self.assertGreater(health["checks"]["recent_error_rate"], 0.50)

    @staticmethod
    def _create_valid_summary(state_dir: Path):
        """Helper: create a valid summary file."""
        summary_file = state_dir / "hands_off_summary.json"
        summary_file.write_text(json.dumps({"status": "ok"}))

    @staticmethod
    def _create_valid_compact(state_dir: Path):
        """Helper: create a valid compact file."""
        compact_file = state_dir / "polymarket-compact.json"
        compact_file.write_text(json.dumps({
            "markets": [{"id": "test", "question": "Test?"}]
        }))

    @staticmethod
    def _create_snapshot(history_dir: Path, filename: str, status: str, age_sec: int):
        """Helper: create a snapshot file."""
        snapshot_file = history_dir / filename
        snapshot_file.write_text(json.dumps({
            "status": status,
            "errors": [] if status == "ok" else ["Error"]
        }))

        import os
        now = datetime.now(timezone.utc).timestamp()
        mtime = now - age_sec
        os.utime(snapshot_file, (mtime, mtime))


class TestHealthCheckRendering(unittest.TestCase):
    """Test health report rendering and output."""

    def test_render_health_text(self):
        """Test rendering of health data to human-readable text."""
        health = {
            "generated_at": "2025-11-18T15:42:12Z",
            "state_dir": "state",
            "status": "ok",
            "components": {
                "polymarket_fetch": "ok",
                "polymarket_pipeline": "ok",
                "history": "ok",
                "scheduler": "unknown"
            },
            "checks": {
                "latest_snapshot_age_sec": 12,
                "latest_fetch_age_sec": 60,
                "num_snapshots": 42,
                "recent_error_rate": 0.05,
                "most_recent_run_status": "ok"
            },
            "errors": []
        }

        text = render_health_text(health)

        # Verify key elements are present
        self.assertIn("Hands-Off System Health Report", text)
        self.assertIn("Status:", text)
        self.assertIn("OK", text)
        self.assertIn("Components:", text)
        self.assertIn("polymarket_fetch: ok", text)
        self.assertIn("Checks:", text)
        self.assertIn("Latest snapshot age: 12s", text)
        self.assertIn("Total snapshots: 42", text)
        self.assertIn("Recent error rate", text)
        self.assertIn("5.00%", text)
        self.assertIn("No errors detected", text)

    def test_render_health_text_with_errors(self):
        """Test rendering of health data with errors."""
        health = {
            "generated_at": "2025-11-18T15:42:12Z",
            "state_dir": "state",
            "status": "error",
            "components": {
                "polymarket_fetch": "error",
                "polymarket_pipeline": "ok",
                "history": "warn",
                "scheduler": "unknown"
            },
            "checks": {
                "latest_snapshot_age_sec": None,
                "latest_fetch_age_sec": None,
                "num_snapshots": 0,
                "recent_error_rate": 0.0,
                "most_recent_run_status": None
            },
            "errors": [
                "polymarket-compact.json does not exist",
                "No snapshots found"
            ]
        }

        text = render_health_text(health)

        # Verify error rendering
        self.assertIn("ERROR", text)
        self.assertIn("Errors:", text)
        self.assertIn("polymarket-compact.json does not exist", text)
        self.assertIn("No snapshots found", text)

    def test_write_health_json_creates_file(self):
        """Test that write_health_json creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"

            health = {
                "generated_at": "2025-11-18T15:42:12Z",
                "state_dir": str(state_dir),
                "status": "ok",
                "components": {},
                "checks": {},
                "errors": []
            }

            output_path = write_health_json(str(state_dir), health)

            # Verify file was created
            self.assertTrue(Path(output_path).exists())
            self.assertEqual(Path(output_path).name, "hands_off_health.json")

            # Verify content is valid JSON
            with open(output_path, "r") as f:
                loaded = json.load(f)

            self.assertEqual(loaded["status"], "ok")
            self.assertEqual(loaded["generated_at"], "2025-11-18T15:42:12Z")


class TestHealthCheckSnapshotParsing(unittest.TestCase):
    """Test snapshot status extraction and parsing."""

    def test_extract_status_from_snapshot_various_formats(self):
        """Test status extraction from different snapshot formats."""
        # Standard status field
        snapshot1 = {"status": "ok"}
        self.assertEqual(_extract_status_from_snapshot(snapshot1), "ok")

        snapshot2 = {"status": "error"}
        self.assertEqual(_extract_status_from_snapshot(snapshot2), "error")

        # Alternative field names
        snapshot3 = {"run_status": "success"}
        self.assertEqual(_extract_status_from_snapshot(snapshot3), "ok")

        snapshot4 = {"pipeline_status": "failed"}
        self.assertEqual(_extract_status_from_snapshot(snapshot4), "error")

        # Errors field
        snapshot5 = {"errors": ["something went wrong"]}
        self.assertEqual(_extract_status_from_snapshot(snapshot5), "error")

        snapshot6 = {"errors": []}
        self.assertEqual(_extract_status_from_snapshot(snapshot6), "ok")

        # No clear status (default to ok)
        snapshot7 = {"data": "some data"}
        self.assertEqual(_extract_status_from_snapshot(snapshot7), "ok")


if __name__ == "__main__":
    unittest.main()
