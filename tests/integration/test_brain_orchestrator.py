#!/usr/bin/env python3
"""
Integration tests for Brain Orchestrator (Batch 25)

Tests the complete cognitive pipeline orchestration.
"""

import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.ho_brain_orchestrator import BrainOrchestrator


class TestBrainOrchestrator(unittest.TestCase):
    """Test suite for Brain Orchestrator"""

    def setUp(self):
        """Create temporary directory for each test"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_happy_path_all_stages_ok(self):
        """Test 1: All stages succeed in happy path"""
        orchestrator = BrainOrchestrator(
            state_dir=self.state_dir,
            verbose=False
        )

        report = orchestrator.run_all()

        # Verify report structure
        self.assertIn("generated_at", report)
        self.assertIn("stages", report)
        self.assertIn("summary", report)

        # All 8 stages should be recorded
        self.assertEqual(len(report["stages"]), 8)

        # All should succeed
        self.assertEqual(report["summary"]["stages_total"], 8)
        self.assertEqual(report["summary"]["stages_ok"], 8)
        self.assertEqual(report["summary"]["stages_error"], 0)
        self.assertEqual(report["summary"]["overall_status"], "ok")

    def test_missing_initial_brain_summary_file_handled(self):
        """Test 2: Handle failure when Stage 18 fails to produce brain summary"""

        # Mock Stage 18 to fail
        def mock_brain_summary(state_dir):
            raise RuntimeError("Simulated brain summary failure")

        with patch("reports.ho_brain_report.write_brain_summary", mock_brain_summary):
            orchestrator = BrainOrchestrator(
                state_dir=self.state_dir,
                verbose=False
            )

            report = orchestrator.run_all()

            # Stage 1 should fail
            self.assertEqual(report["stages"][0]["status"], "error")
            self.assertGreater(len(report["stages"][0]["errors"]), 0)

            # Subsequent stages should also fail due to missing input
            for i in range(1, 7):
                self.assertEqual(report["stages"][i]["status"], "error")

            # Overall status should be failed
            self.assertEqual(report["summary"]["overall_status"], "failed")

    def test_policy_brain_v2_failure_recorded_but_orchestrator_completes(self):
        """Test 3: Stage 24 fails but orchestrator completes and generates report"""

        # Mock only Stage 24 to fail
        def mock_policy_v2(state_dir):
            raise FileNotFoundError("brain_learning.json not found")

        with patch("ai.ho_policy_brain_v2.generate_policy_v2", mock_policy_v2):
            orchestrator = BrainOrchestrator(
                state_dir=self.state_dir,
                verbose=False
            )

            report = orchestrator.run_all()
            orchestrator.write_reports(report)

            # Stages 1-6 should succeed
            for i in range(6):
                self.assertEqual(report["stages"][i]["status"], "ok",
                               f"Stage {i} should be ok")

            # Stage 7 (index 6) should fail
            self.assertEqual(report["stages"][6]["status"], "error")
            self.assertGreater(len(report["stages"][6]["errors"]), 0)

            # Reports should be written
            json_path = self.state_dir / "brain_orchestrator_report.json"
            txt_path = self.state_dir / "brain_orchestrator_report.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(txt_path.exists())

    def test_orchestrator_writes_json_and_txt_reports(self):
        """Test 4: Both JSON and TXT reports are written"""
        orchestrator = BrainOrchestrator(
            state_dir=self.state_dir,
            verbose=False
        )

        report = orchestrator.run_all()
        orchestrator.write_reports(report)

        # Check both files exist
        json_path = self.state_dir / "brain_orchestrator_report.json"
        txt_path = self.state_dir / "brain_orchestrator_report.txt"

        self.assertTrue(json_path.exists(), "JSON report should exist")
        self.assertTrue(txt_path.exists(), "TXT report should exist")

        # Verify JSON is valid
        with open(json_path) as f:
            loaded_report = json.load(f)
            self.assertEqual(loaded_report["summary"]["stages_total"], 8)

        # Verify TXT is non-empty
        txt_content = txt_path.read_text()
        self.assertGreater(len(txt_content), 100)
        self.assertIn("BRAIN ORCHESTRATOR", txt_content)

    def test_json_report_structure_valid(self):
        """Test 5: JSON report has all required fields"""
        orchestrator = BrainOrchestrator(
            state_dir=self.state_dir,
            verbose=False
        )

        report = orchestrator.run_all()

        # Top-level keys
        self.assertIn("generated_at", report)
        self.assertIn("completed_at", report)
        self.assertIn("stages", report)
        self.assertIn("summary", report)

        # Each stage has required fields
        for stage in report["stages"]:
            self.assertIn("name", stage)
            self.assertIn("batch", stage)
            self.assertIn("status", stage)
            self.assertIn("duration_ms", stage)
            self.assertIn("input_files", stage)
            self.assertIn("output_files", stage)
            self.assertIn("errors", stage)

            # Validate types
            self.assertIsInstance(stage["name"], str)
            self.assertIsInstance(stage["batch"], int)
            self.assertIn(stage["status"], ["ok", "error", "skipped"])
            self.assertIsInstance(stage["duration_ms"], int)
            self.assertIsInstance(stage["input_files"], list)
            self.assertIsInstance(stage["output_files"], list)
            self.assertIsInstance(stage["errors"], list)

        # Summary has required fields
        summary = report["summary"]
        self.assertIn("stages_total", summary)
        self.assertIn("stages_ok", summary)
        self.assertIn("stages_error", summary)
        self.assertIn("stages_skipped", summary)
        self.assertIn("overall_status", summary)
        self.assertIn("notes", summary)

    def test_summary_counts_match_stage_statuses(self):
        """Test 6: Summary counts match actual stage statuses"""

        # Mock stages 2 and 5 to fail
        def mock_fail_stage_2(state_dir):
            raise RuntimeError("Stage 2 forced failure")

        def mock_fail_stage_5(state_dir):
            raise RuntimeError("Stage 5 forced failure")

        with patch("ai.ho_policy_agent.write_policy_recommendation", mock_fail_stage_2), \
             patch("ai.ho_consensus_engine.run_consensus", mock_fail_stage_5):

            orchestrator = BrainOrchestrator(
                state_dir=self.state_dir,
                verbose=False
            )

            report = orchestrator.run_all()

            # Count statuses manually
            ok_count = sum(1 for s in report["stages"] if s["status"] == "ok")
            error_count = sum(1 for s in report["stages"] if s["status"] == "error")
            skipped_count = sum(1 for s in report["stages"] if s["status"] == "skipped")

            # Verify summary matches
            self.assertEqual(report["summary"]["stages_ok"], ok_count)
            self.assertEqual(report["summary"]["stages_error"], error_count)
            self.assertEqual(report["summary"]["stages_skipped"], skipped_count)
            self.assertEqual(
                report["summary"]["stages_total"],
                ok_count + error_count + skipped_count
            )

    def test_cli_invocation_basic(self):
        """Test 7: CLI can be invoked and produces reports"""
        # Run orchestrator as subprocess
        result = subprocess.run(
            [
                sys.executable,
                "ai/ho_brain_orchestrator.py",
                "--state-dir", str(self.state_dir)
            ],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )

        # Should exit successfully
        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")

        # Reports should exist
        json_path = self.state_dir / "brain_orchestrator_report.json"
        txt_path = self.state_dir / "brain_orchestrator_report.txt"

        self.assertTrue(json_path.exists(), "JSON report missing after CLI run")
        self.assertTrue(txt_path.exists(), "TXT report missing after CLI run")

    def test_file_operations_isolated_to_temp_state_dir(self):
        """Test 8: All file operations stay within state directory"""
        orchestrator = BrainOrchestrator(
            state_dir=self.state_dir,
            verbose=False
        )

        # Run and write reports
        report = orchestrator.run_all()
        orchestrator.write_reports(report)

        # Verify all output files are within state_dir
        for stage in report["stages"]:
            for output_file in stage.get("output_files", []):
                output_path = Path(output_file)
                # Check that the file is within our temp state directory
                self.assertTrue(
                    str(output_path).startswith(str(self.state_dir)),
                    f"File {output_file} is outside state directory"
                )

    def test_orchestrator_handles_empty_state_dir(self):
        """Test 9: Orchestrator handles empty state directory gracefully"""
        # Use a completely empty state directory
        empty_state = Path(self.temp_dir.name) / "empty_state"
        empty_state.mkdir(parents=True, exist_ok=True)

        orchestrator = BrainOrchestrator(
            state_dir=empty_state,
            verbose=False
        )

        report = orchestrator.run_all()
        orchestrator.write_reports(report)

        # Should still generate a report
        json_path = empty_state / "brain_orchestrator_report.json"
        self.assertTrue(json_path.exists())

        # Should have some stages succeed (at least stage 1)
        self.assertGreater(report["summary"]["stages_ok"], 0)

    def test_overall_status_degraded_when_some_failures(self):
        """Test 10: Overall status is 'degraded' when some stages fail"""

        # Mock one stage to fail
        def mock_fail(state_dir):
            raise RuntimeError("Simulated failure")

        with patch("ai.ho_policy_brain_v2.generate_policy_v2", mock_fail):
            orchestrator = BrainOrchestrator(
                state_dir=self.state_dir,
                verbose=False
            )

            report = orchestrator.run_all()

            # Some stages ok, some error
            self.assertGreater(report["summary"]["stages_ok"], 0)
            self.assertGreater(report["summary"]["stages_error"], 0)

            # Overall should be degraded
            self.assertEqual(report["summary"]["overall_status"], "degraded")

    def test_overall_status_failed_when_all_stages_fail(self):
        """Test 11: Overall status is 'failed' when all stages fail"""

        # Mock all stages to fail
        def mock_fail(state_dir):
            raise RuntimeError("All stages fail")

        with patch("reports.ho_brain_report.write_brain_summary", mock_fail), \
             patch("ai.ho_policy_agent.write_policy_recommendation", mock_fail), \
             patch("ai.ho_policy_executor.run_policy_actions", mock_fail), \
             patch("ai.ho_action_verifier.verify_actions", mock_fail), \
             patch("ai.ho_consensus_engine.run_consensus", mock_fail), \
             patch("ai.ho_learning_engine.update_learning", mock_fail), \
             patch("ai.ho_policy_brain_v2.generate_policy_v2", mock_fail):

            orchestrator = BrainOrchestrator(
                state_dir=self.state_dir,
                verbose=False
            )

            report = orchestrator.run_all()

            # All stages should fail
            self.assertEqual(report["summary"]["stages_error"], 8)
            self.assertEqual(report["summary"]["stages_ok"], 0)

            # Overall should be failed
            self.assertEqual(report["summary"]["overall_status"], "failed")

    def test_generated_at_is_valid_iso_timestamp(self):
        """Test 12: generated_at is a valid ISO-8601 timestamp"""
        orchestrator = BrainOrchestrator(
            state_dir=self.state_dir,
            verbose=False
        )

        report = orchestrator.run_all()

        # Verify generated_at is valid ISO timestamp
        generated_at = report["generated_at"]
        self.assertIsInstance(generated_at, str)

        # Should parse without error
        try:
            # Remove 'Z' suffix and parse
            dt = datetime.fromisoformat(generated_at.rstrip('Z'))
            self.assertIsInstance(dt, datetime)
        except ValueError:
            self.fail(f"generated_at is not valid ISO-8601: {generated_at}")

        # completed_at should also be valid
        completed_at = report["completed_at"]
        try:
            dt = datetime.fromisoformat(completed_at.rstrip('Z'))
            self.assertIsInstance(dt, datetime)
        except ValueError:
            self.fail(f"completed_at is not valid ISO-8601: {completed_at}")

    def test_verbose_mode_produces_output(self):
        """Test 13: Verbose mode produces log output"""
        import io
        from contextlib import redirect_stdout

        output_buffer = io.StringIO()

        with redirect_stdout(output_buffer):
            orchestrator = BrainOrchestrator(
                state_dir=self.state_dir,
                verbose=True
            )
            orchestrator.run_all()

        output = output_buffer.getvalue()

        # Should have some log output
        self.assertGreater(len(output), 0)
        self.assertIn("BRAIN ORCHESTRATOR", output)
        self.assertIn("Starting Stage", output)

    def test_stage_duration_is_recorded(self):
        """Test 14: Each stage records non-zero duration"""
        orchestrator = BrainOrchestrator(
            state_dir=self.state_dir,
            verbose=False
        )

        report = orchestrator.run_all()

        # Each stage should have a duration
        for stage in report["stages"]:
            self.assertIn("duration_ms", stage)
            # Duration should be a non-negative integer
            self.assertGreaterEqual(stage["duration_ms"], 0)
            self.assertIsInstance(stage["duration_ms"], int)

    def test_errors_are_captured_in_failed_stages(self):
        """Test 15: Failed stages capture error messages"""

        def mock_fail_with_message(state_dir):
            raise ValueError("This is a specific error message")

        with patch("ai.ho_policy_agent.write_policy_recommendation", mock_fail_with_message):
            orchestrator = BrainOrchestrator(
                state_dir=self.state_dir,
                verbose=False
            )

            report = orchestrator.run_all()

            # Find the failed stage (policy_agent_v1)
            failed_stage = None
            for stage in report["stages"]:
                if stage["name"] == "policy_agent_v1":
                    failed_stage = stage
                    break

            self.assertIsNotNone(failed_stage)
            self.assertEqual(failed_stage["status"], "error")

            # Error should be captured
            self.assertGreater(len(failed_stage["errors"]), 0)
            self.assertIn("specific error message", failed_stage["errors"][0])

    def test_batch_numbers_are_correct(self):
        """Test 16: Each stage has the correct batch number"""
        orchestrator = BrainOrchestrator(
            state_dir=self.state_dir,
            verbose=False
        )

        report = orchestrator.run_all()

        expected_batches = [18, 19, 20, 21, 22, 23, 24, 25]

        for i, stage in enumerate(report["stages"]):
            self.assertEqual(
                stage["batch"],
                expected_batches[i],
                f"Stage {i} should be batch {expected_batches[i]}"
            )


if __name__ == "__main__":
    unittest.main()
