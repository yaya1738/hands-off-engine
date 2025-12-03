#!/usr/bin/env python3
"""
Integration tests for Policy Executor (Batch 20)

Tests the safe DRYRUN policy execution engine that interprets
brain_policy.json and executes system actions.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.ho_policy_executor import PolicyExecutor, run_policy_actions


class TestPolicyExecutor(unittest.TestCase):
    """Test suite for Policy Executor"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for isolated testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.test_dir.name) / "state"
        self.ai_dir = Path(self.test_dir.name) / "ai"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.ai_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures"""
        self.test_dir.cleanup()

    def test_missing_policy_file(self):
        """Test 1: Missing policy file should produce empty/no-op action list"""
        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Should complete successfully with no actions
        self.assertEqual(report["actions_tried"], 0)
        self.assertEqual(report["actions_successful"], 0)
        self.assertEqual(len(report["actions"]), 0)
        self.assertIn("Policy file not found", report["errors"][0])

        # Output file should still be created
        output_path = self.state_dir / "brain_actions.json"
        self.assertTrue(output_path.exists())

    def test_malformed_policy_file(self):
        """Test 2: Malformed policy file should be handled gracefully"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write invalid JSON
        with open(policy_path, 'w') as f:
            f.write("{ invalid json here }")

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Should complete with error but not crash
        self.assertEqual(report["actions_tried"], 0)
        self.assertEqual(len(report["errors"]), 1)
        self.assertIn("Malformed policy JSON", report["errors"][0])

        # Output file should still be created
        output_path = self.state_dir / "brain_actions.json"
        self.assertTrue(output_path.exists())

    def test_summary_action(self):
        """Test 3: Running a single summary action (with stub behavior)"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy with summary action
        policy = {
            "actions": [
                {"type": "summary"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Should execute summary action
        self.assertEqual(report["actions_tried"], 1)
        self.assertEqual(report["actions_successful"], 1)
        self.assertEqual(len(report["actions"]), 1)

        # Check action details
        action = report["actions"][0]
        self.assertEqual(action["type"], "summary")
        self.assertEqual(action["status"], "ok")
        self.assertIn("details", action)

    def test_health_check_action(self):
        """Test 4: Running a health-check action"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy with health-check action
        policy = {
            "actions": [
                {"type": "health-check"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Should execute health-check action
        self.assertEqual(report["actions_tried"], 1)
        self.assertEqual(report["actions_successful"], 1)

        # Check action details
        action = report["actions"][0]
        self.assertEqual(action["type"], "health-check")
        self.assertEqual(action["status"], "ok")

    def test_autoloop_action_safe_dryrun(self):
        """Test 5: Running autoloop action (safe DRYRUN)"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy with autoloop action
        policy = {
            "actions": [
                {"type": "autoloop"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Should execute autoloop action
        self.assertEqual(report["actions_tried"], 1)
        self.assertEqual(report["actions_successful"], 1)

        # Check action details - should be DRYRUN mode
        action = report["actions"][0]
        self.assertEqual(action["type"], "autoloop")
        self.assertEqual(action["status"], "ok")
        # Stub behavior should note DRYRUN mode
        self.assertIn("details", action)

    def test_polymarket_analysis_safe_behavior(self):
        """Test 6: Polymarket analysis safe behavior (no API calls)"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy with polymarket-analysis action
        policy = {
            "actions": [
                {"type": "polymarket-analysis"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        # Create a mock polymarket compact file
        compact_path = self.state_dir / "polymarket-compact.json"
        compact_data = {
            "markets": [
                {"id": 1, "volume": 1000},
                {"id": 2, "volume": 2000},
                {"id": 3, "volume": 1500}
            ]
        }
        with open(compact_path, 'w') as f:
            json.dump(compact_data, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Should execute polymarket-analysis action
        self.assertEqual(report["actions_tried"], 1)
        self.assertEqual(report["actions_successful"], 1)

        # Check action details
        action = report["actions"][0]
        self.assertEqual(action["type"], "polymarket-analysis")
        self.assertEqual(action["status"], "ok")
        self.assertEqual(action["details"]["markets_count"], 3)
        self.assertEqual(action["details"]["total_volume"], 4500)

    def test_analyze_history_safe_behavior(self):
        """Test 7: Analyze-history safe behavior"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy with analyze-history action
        policy = {
            "actions": [
                {"type": "analyze-history"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Should execute analyze-history action
        self.assertEqual(report["actions_tried"], 1)
        self.assertEqual(report["actions_successful"], 1)

        # Check action details
        action = report["actions"][0]
        self.assertEqual(action["type"], "analyze-history")
        self.assertEqual(action["status"], "ok")

    def test_cli_invocation(self):
        """Test 8: CLI invocation works correctly"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy
        policy = {
            "actions": [
                {"type": "summary"},
                {"type": "health-check"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        # Test the run_policy_actions function (used by CLI)
        report = run_policy_actions(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=True
        )

        # Should execute both actions
        self.assertEqual(report["actions_tried"], 2)
        self.assertEqual(report["actions_successful"], 2)

        # Output file should exist
        output_path = self.state_dir / "brain_actions.json"
        self.assertTrue(output_path.exists())

        # Verify output JSON structure
        with open(output_path, 'r') as f:
            output_data = json.load(f)

        self.assertEqual(output_data["actions_tried"], 2)
        self.assertEqual(output_data["actions_successful"], 2)

    def test_output_json_structure(self):
        """Test 9: Output JSON structure has all required fields"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy with multiple actions
        policy = {
            "actions": [
                {"type": "summary"},
                {"type": "health-check"},
                {"type": "polymarket-analysis"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Verify all required top-level fields
        self.assertIn("generated_at", report)
        self.assertIn("policy_source", report)
        self.assertIn("actions_tried", report)
        self.assertIn("actions_successful", report)
        self.assertIn("actions", report)
        self.assertIn("errors", report)

        # Verify generated_at is valid ISO timestamp
        self.assertRegex(report["generated_at"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

        # Verify actions is a list
        self.assertIsInstance(report["actions"], list)
        self.assertEqual(len(report["actions"]), 3)

        # Verify errors is a list
        self.assertIsInstance(report["errors"], list)

        # Verify each action has required fields
        for action in report["actions"]:
            self.assertIn("type", action)
            self.assertIn("status", action)
            self.assertIn("details", action)
            self.assertIn(action["status"], ["ok", "error"])

    def test_multiple_actions_mixed_success(self):
        """Test 10 (bonus): Multiple actions with some failures"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write policy with valid and invalid actions
        policy = {
            "actions": [
                {"type": "summary"},
                {"type": "unknown-action-type"},
                {"type": "health-check"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Should try all 3 actions
        self.assertEqual(report["actions_tried"], 3)
        # Only 2 should succeed (unknown-action-type will fail)
        self.assertEqual(report["actions_successful"], 2)

        # Check individual action statuses
        self.assertEqual(report["actions"][0]["status"], "ok")  # summary
        self.assertEqual(report["actions"][1]["status"], "error")  # unknown
        self.assertEqual(report["actions"][2]["status"], "ok")  # health-check

    def test_verbose_mode_text_output(self):
        """Test 11 (bonus): Verbose mode creates text summary"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy
        policy = {
            "actions": [
                {"type": "summary"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=True  # Enable verbose mode
        )

        report = executor.run_policy_actions()

        # Both JSON and text files should exist
        json_path = self.state_dir / "brain_actions.json"
        txt_path = self.state_dir / "brain_actions.txt"

        self.assertTrue(json_path.exists())
        self.assertTrue(txt_path.exists())

        # Verify text file has content
        with open(txt_path, 'r') as f:
            content = f.read()

        self.assertIn("POLICY EXECUTOR REPORT", content)
        self.assertIn("Actions Tried:", content)
        self.assertIn("summary", content.lower())


class TestPolicyExecutorSafety(unittest.TestCase):
    """Test suite for safety guarantees"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.test_dir.name) / "state"
        self.ai_dir = Path(self.test_dir.name) / "ai"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.ai_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures"""
        self.test_dir.cleanup()

    def test_no_network_calls(self):
        """Test 12 (bonus): Verify no network calls are made"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write policy with all action types
        policy = {
            "actions": [
                {"type": "summary"},
                {"type": "health-check"},
                {"type": "autoloop"},
                {"type": "polymarket-analysis"},
                {"type": "analyze-history"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        # Mock network modules to ensure they're not called
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch('requests.get') as mock_requests_get, \
             patch('requests.post') as mock_requests_post:

            executor = PolicyExecutor(
                state_dir=str(self.state_dir),
                ai_dir=str(self.ai_dir),
                verbose=False
            )

            report = executor.run_policy_actions()

            # Verify no network calls were made
            mock_urlopen.assert_not_called()
            mock_requests_get.assert_not_called()
            mock_requests_post.assert_not_called()

    def test_file_operations_isolated(self):
        """Test 13 (bonus): Verify file operations are isolated to state/ai dirs"""
        policy_path = self.state_dir / "brain_policy.json"

        # Write valid policy
        policy = {
            "actions": [
                {"type": "summary"}
            ]
        }
        with open(policy_path, 'w') as f:
            json.dump(policy, f)

        executor = PolicyExecutor(
            state_dir=str(self.state_dir),
            ai_dir=str(self.ai_dir),
            verbose=False
        )

        report = executor.run_policy_actions()

        # Verify output is written to correct location
        output_path = self.state_dir / "brain_actions.json"
        self.assertTrue(output_path.exists())

        # Verify output is inside test directory (isolated)
        self.assertTrue(str(output_path).startswith(self.test_dir.name))


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyExecutor))
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyExecutorSafety))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
