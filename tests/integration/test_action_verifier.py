#!/usr/bin/env python3
"""
Integration Tests for Action Verifier (Batch 21)
=================================================

This test suite verifies the Action Verifier module with comprehensive
coverage of normal operations, edge cases, and error conditions.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.ho_action_verifier import ActionVerifier


class TestActionVerifier(unittest.TestCase):
    """Comprehensive test suite for Action Verifier."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.actions_file = Path(self.test_dir) / "brain_actions.json"
        self.feedback_file = Path(self.test_dir) / "brain_feedback.json"

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_actions_file(self, data):
        """Helper to create test actions file."""
        with open(self.actions_file, 'w') as f:
            json.dump(data, f)

    def test_01_missing_actions_file(self):
        """Test 1: Graceful handling of missing brain_actions.json."""
        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        # Load should return False but not crash
        loaded = verifier.load_actions()
        self.assertFalse(loaded)

        # Should still be able to generate feedback
        feedback = verifier.generate_feedback()
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback["summary"]["actions_total"], 0)

        # Should save successfully
        saved = verifier.save_feedback()
        self.assertTrue(saved)
        self.assertTrue(self.feedback_file.exists())

    def test_02_malformed_json(self):
        """Test 2: Safe handling of malformed JSON."""
        # Write invalid JSON
        with open(self.actions_file, 'w') as f:
            f.write("{invalid json content here")

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        # Should handle gracefully
        loaded = verifier.load_actions()
        self.assertFalse(loaded)

        # Should still generate feedback with zero actions
        feedback = verifier.generate_feedback()
        self.assertEqual(feedback["summary"]["actions_total"], 0)

    def test_03_all_success_actions(self):
        """Test 3: All actions successful - correct success_rate=1.0."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {
                    "id": "action-1",
                    "type": "health-check",
                    "status": "success"
                },
                {
                    "id": "action-2",
                    "type": "polymarket-fetch",
                    "status": "success"
                },
                {
                    "id": "action-3",
                    "type": "data-sync",
                    "status": "completed"
                }
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        self.assertEqual(feedback["success_rate"], 1.0)
        self.assertEqual(feedback["summary"]["actions_total"], 3)
        self.assertEqual(feedback["summary"]["actions_successful"], 3)
        self.assertEqual(feedback["summary"]["actions_failed"], 0)
        self.assertIn("All actions successful", " ".join(feedback["recommendations"]))

    def test_04_single_failure(self):
        """Test 4: Single failure detected and reported."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {
                    "id": "action-1",
                    "type": "health-check",
                    "status": "success"
                },
                {
                    "id": "action-2",
                    "type": "polymarket-fetch",
                    "status": "failed",
                    "error": "Network timeout"
                }
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        self.assertEqual(feedback["summary"]["actions_total"], 2)
        self.assertEqual(feedback["summary"]["actions_successful"], 1)
        self.assertEqual(feedback["summary"]["actions_failed"], 1)
        self.assertEqual(feedback["success_rate"], 0.5)

        # Check failure is reported in issues
        self.assertTrue(len(feedback["issues"]) > 0)
        issue_text = " ".join(feedback["issues"])
        self.assertIn("action-2", issue_text)
        self.assertIn("Network timeout", issue_text)

    def test_05_unknown_action_types_tracked(self):
        """Test 5: Unknown action types are tracked and reported."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {
                    "id": "action-1",
                    "type": "custom-action-xyz",
                    "status": "success"
                },
                {
                    "id": "action-2",
                    "type": "another-unknown-type",
                    "status": "success"
                }
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        self.assertIn("custom-action-xyz", feedback["summary"]["unknown_types"])
        self.assertIn("another-unknown-type", feedback["summary"]["unknown_types"])

        # Should have issues about unknown types
        issues_text = " ".join(feedback["issues"])
        self.assertIn("Unknown action type", issues_text)

        # Should have recommendations
        recommendations_text = " ".join(feedback["recommendations"])
        self.assertIn("Register action types", recommendations_text)

    def test_06_stub_usage_counted(self):
        """Test 6: Stub usage correctly counted and reported."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {
                    "id": "action-1",
                    "type": "health-check",
                    "status": "success"
                },
                {
                    "id": "action-2",
                    "type": "polymarket-fetch",
                    "status": "stubbed"
                },
                {
                    "id": "action-3",
                    "type": "data-sync",
                    "status": "stubbed"
                }
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        self.assertEqual(feedback["summary"]["stub_count"], 2)

        # Should have recommendation about stubs
        recommendations_text = " ".join(feedback["recommendations"])
        self.assertIn("stubbed", recommendations_text.lower())

    def test_07_cli_invocation_works(self):
        """Test 7: CLI interface works correctly."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {
                    "id": "action-1",
                    "type": "health-check",
                    "status": "success"
                }
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=True
        )

        exit_code = verifier.run()

        self.assertEqual(exit_code, 0)
        self.assertTrue(self.feedback_file.exists())

        # Verify feedback file is valid JSON
        with open(self.feedback_file, 'r') as f:
            feedback = json.load(f)
            self.assertIn("success_rate", feedback)
            self.assertIn("summary", feedback)

    def test_08_json_structure_verified(self):
        """Test 8: Output JSON structure matches specification."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {
                    "id": "action-1",
                    "type": "health-check",
                    "status": "success"
                }
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        # Verify all required top-level fields
        self.assertIn("generated_at", feedback)
        self.assertIn("source", feedback)
        self.assertIn("success_rate", feedback)
        self.assertIn("summary", feedback)
        self.assertIn("issues", feedback)
        self.assertIn("recommendations", feedback)

        # Verify summary structure
        summary = feedback["summary"]
        self.assertIn("actions_total", summary)
        self.assertIn("actions_successful", summary)
        self.assertIn("actions_failed", summary)
        self.assertIn("stub_count", summary)
        self.assertIn("unknown_types", summary)

        # Verify types
        self.assertIsInstance(feedback["success_rate"], (int, float))
        self.assertIsInstance(feedback["issues"], list)
        self.assertIsInstance(feedback["recommendations"], list)

    def test_09_multiple_failure_reasons_aggregated(self):
        """Test 9: Multiple failure reasons correctly aggregated."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {
                    "id": "action-1",
                    "type": "health-check",
                    "status": "failed",
                    "error": "Connection refused"
                },
                {
                    "id": "action-2",
                    "type": "polymarket-fetch",
                    "status": "error",
                    "error": "API rate limit exceeded"
                },
                {
                    "id": "action-3",
                    "type": "data-sync",
                    "status": "failed",
                    "message": "Database unavailable"
                }
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        self.assertEqual(feedback["summary"]["actions_failed"], 3)
        self.assertEqual(len(feedback["issues"]), 3)

        # Verify all failures are reported
        issues_text = " ".join(feedback["issues"])
        self.assertIn("Connection refused", issues_text)
        self.assertIn("API rate limit", issues_text)
        self.assertIn("Database unavailable", issues_text)

    def test_10_file_operations_isolated(self):
        """Test 10: File operations properly isolated to test directory."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": []
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        verifier.run()

        # Verify files are in test directory
        self.assertTrue(self.actions_file.exists())
        self.assertTrue(self.feedback_file.exists())
        self.assertTrue(str(self.actions_file).startswith(self.test_dir))
        self.assertTrue(str(self.feedback_file).startswith(self.test_dir))

    def test_11_high_failure_rate_anomaly(self):
        """Test 11: High failure rate triggers anomaly detection."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {"id": "a1", "type": "health-check", "status": "success"},
                {"id": "a2", "type": "data-sync", "status": "failed", "error": "timeout"},
                {"id": "a3", "type": "market-analysis", "status": "failed", "error": "error"},
                {"id": "a4", "type": "position-update", "status": "error", "error": "error"}
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        # Should detect high failure rate anomaly
        anomalies_text = " ".join(feedback.get("anomalies", []))
        self.assertIn("failure rate", anomalies_text.lower())

    def test_12_empty_actions_list(self):
        """Test 12: Empty actions list handled gracefully."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": []
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        self.assertEqual(feedback["summary"]["actions_total"], 0)
        self.assertEqual(feedback["success_rate"], 1.0)  # No actions = no failures

        # Should recommend checking upstream components
        recommendations_text = " ".join(feedback["recommendations"])
        self.assertIn("No actions", recommendations_text)

    def test_13_high_stub_ratio_detected(self):
        """Test 13: High stub ratio triggers anomaly and recommendation."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {"id": "a1", "type": "health-check", "status": "stubbed"},
                {"id": "a2", "type": "data-sync", "status": "stubbed"},
                {"id": "a3", "type": "market-analysis", "status": "stubbed"},
                {"id": "a4", "type": "position-update", "status": "success"}
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        # Should detect high stub usage
        anomalies_text = " ".join(feedback.get("anomalies", []))
        self.assertIn("stub", anomalies_text.lower())

        recommendations_text = " ".join(feedback["recommendations"])
        self.assertIn("stub", recommendations_text.lower())

    def test_14_success_rate_calculation_excludes_stubs(self):
        """Test 14: Success rate calculation properly excludes stubs."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {"id": "a1", "type": "health-check", "status": "success"},
                {"id": "a2", "type": "data-sync", "status": "stubbed"},
                {"id": "a3", "type": "market-analysis", "status": "stubbed"},
                {"id": "a4", "type": "position-update", "status": "failed", "error": "test"}
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        # 4 total, 2 stubbed, 1 success, 1 failure
        # Success rate should be 1/2 = 0.5 (only counting non-stubbed)
        self.assertEqual(feedback["success_rate"], 0.5)

    def test_15_complete_all_failures_critical(self):
        """Test 15: All non-stub failures triggers critical anomaly."""
        data = {
            "generated_at": "2025-11-18T12:00:00Z",
            "actions": [
                {"id": "a1", "type": "health-check", "status": "failed", "error": "error"},
                {"id": "a2", "type": "data-sync", "status": "failed", "error": "error"},
                {"id": "a3", "type": "market-analysis", "status": "error", "error": "error"}
            ]
        }
        self.create_actions_file(data)

        verifier = ActionVerifier(
            actions_file=str(self.actions_file),
            output_file=str(self.feedback_file),
            verbose=False
        )

        feedback = verifier.generate_feedback()

        # Should detect critical all-failure condition
        anomalies_text = " ".join(feedback.get("anomalies", []))
        self.assertIn("CRITICAL", anomalies_text)


def run_tests():
    """Run all tests and display results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestActionVerifier)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
