#!/usr/bin/env python3
"""
Integration tests for Batch 19 - Policy Agent

Tests the ho_policy_agent module with comprehensive coverage:
1. Fallback behavior when brain file is missing
2. Mock LLM integration
3. Malformed LLM output handling
4. CLI invocation
5. Required fields validation
6. Robust parsing of bullet points
7. No external network calls
"""

import json
import os
import sys
import tempfile
import shutil
import subprocess
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai.ho_policy_agent import (
    build_policy_recommendation,
    write_policy_recommendation,
    load_brain_state,
    build_llm_prompt,
    parse_llm_response
)


class TestPolicyAgent:
    """Test suite for Policy Agent (Batch 19)"""

    def setup_method(self):
        """Create temporary test directory for each test"""
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = os.path.join(self.test_dir, "state")
        os.makedirs(self.state_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up temporary test directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_policy_minimal_fallback(self):
        """
        Test 1: Minimal fallback when brain file is missing and llm_fn is None

        Verifies:
        - Missing brain file is handled gracefully
        - No LLM function returns fallback policy
        - Policy file is written successfully
        - Contains minimal safe action
        """
        # Ensure brain file does NOT exist
        brain_path = os.path.join(self.state_dir, "hands_off_brain.json")
        assert not os.path.exists(brain_path)

        # Call without LLM function
        policy = write_policy_recommendation(
            state_dir=self.state_dir,
            llm_fn=None,
            model_name="test-fallback"
        )

        # Verify policy structure
        assert "generated_at" in policy
        assert "model_name" in policy
        assert policy["model_name"] == "none (fallback)"
        assert "proposed_actions" in policy
        assert isinstance(policy["proposed_actions"], list)
        assert len(policy["proposed_actions"]) > 0
        assert "errors" in policy
        assert len(policy["errors"]) > 0  # Should have error about missing brain file

        # Verify file was written
        policy_path = os.path.join(self.state_dir, "brain_policy.json")
        assert os.path.exists(policy_path)

        # Verify file contents
        with open(policy_path, 'r') as f:
            saved_policy = json.load(f)
        assert saved_policy["model_name"] == "none (fallback)"
        assert saved_policy["proposed_actions"] == [{"type": "summary"}]

        print("✓ Test 1 passed: Minimal fallback works")

    def test_policy_with_mock_llm(self):
        """
        Test 2: Policy generation with mock LLM returning valid JSON

        Verifies:
        - Mock LLM function is called correctly
        - Valid JSON response is parsed
        - Actions list is extracted
        """
        # Create a brain file
        brain_data = {
            "status": "healthy",
            "health": {"cpu": "ok", "memory": "ok"},
            "summary": {"tasks_completed": 5}
        }
        brain_path = os.path.join(self.state_dir, "hands_off_brain.json")
        with open(brain_path, 'w') as f:
            json.dump(brain_data, f)

        # Mock LLM that returns valid JSON
        def mock_llm(prompt: str) -> str:
            assert "Policy Brain" in prompt
            return json.dumps({
                "brain_status": "ok",
                "proposed_actions": [
                    {"type": "summary"},
                    {"type": "health-check"},
                    {"type": "autoloop", "mode": "DRYRUN"}
                ],
                "notes": ["System is healthy", "Proceeding with standard actions"]
            })

        # Build policy with mock LLM
        policy = build_policy_recommendation(
            state_dir=self.state_dir,
            llm_fn=mock_llm,
            model_name="mock-model"
        )

        # Verify policy
        assert policy["model_name"] == "mock-model"
        assert policy["brain_status"] == "ok"
        assert len(policy["proposed_actions"]) == 3
        assert policy["proposed_actions"][0]["type"] == "summary"
        assert policy["proposed_actions"][1]["type"] == "health-check"
        assert policy["proposed_actions"][2]["type"] == "autoloop"
        assert policy["proposed_actions"][2]["mode"] == "DRYRUN"
        assert len(policy["notes"]) == 2

        print("✓ Test 2 passed: Mock LLM integration works")

    def test_policy_bad_llm_json(self):
        """
        Test 3: Graceful handling of malformed LLM output

        Verifies:
        - Garbage LLM output doesn't crash
        - Fallback policy is generated
        - Errors are logged
        """
        # Create brain file
        brain_path = os.path.join(self.state_dir, "hands_off_brain.json")
        with open(brain_path, 'w') as f:
            json.dump({"status": "ok"}, f)

        # Mock LLM that returns garbage
        def garbage_llm(prompt: str) -> str:
            return "This is not JSON at all! Just random text with no structure."

        # Build policy
        policy = build_policy_recommendation(
            state_dir=self.state_dir,
            llm_fn=garbage_llm,
            model_name="garbage-model"
        )

        # Verify fallback behavior
        assert "proposed_actions" in policy
        assert isinstance(policy["proposed_actions"], list)
        assert len(policy["proposed_actions"]) > 0
        assert policy["proposed_actions"][0]["type"] == "summary"  # Fallback action
        assert len(policy["errors"]) > 0  # Should log parsing error

        print("✓ Test 3 passed: Malformed LLM output handled gracefully")

    def test_cli_invocation(self):
        """
        Test 4: CLI can be invoked and writes policy file

        Verifies:
        - CLI runs without errors
        - Exit code is 0
        - Policy file is created
        """
        # Run CLI
        result = subprocess.run(
            [
                sys.executable,
                "ai/ho_policy_agent.py",
                "--state-dir", self.state_dir,
                "--model", "test-cli-model"
            ],
            cwd=os.path.join(os.path.dirname(__file__), '..', '..'),
            capture_output=True,
            text=True
        )

        # Verify exit code
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Verify policy file was created
        policy_path = os.path.join(self.state_dir, "brain_policy.json")
        assert os.path.exists(policy_path)

        # Verify file contents
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        assert "generated_at" in policy
        assert "proposed_actions" in policy

        print("✓ Test 4 passed: CLI invocation successful")

    def test_policy_contains_required_fields(self):
        """
        Test 5: Policy output contains all required fields

        Verifies:
        - generated_at (ISO timestamp)
        - model_name (string)
        - proposed_actions (list)
        - errors (list)
        - brain_status
        - notes
        """
        # Create brain file
        brain_path = os.path.join(self.state_dir, "hands_off_brain.json")
        with open(brain_path, 'w') as f:
            json.dump({"status": "ok"}, f)

        # Mock LLM
        def mock_llm(prompt: str) -> str:
            return '{"brain_status": "ok", "proposed_actions": [], "notes": []}'

        # Build policy
        policy = build_policy_recommendation(
            state_dir=self.state_dir,
            llm_fn=mock_llm,
            model_name="test-model"
        )

        # Verify all required fields
        required_fields = [
            "generated_at",
            "model_name",
            "brain_status",
            "proposed_actions",
            "notes",
            "errors"
        ]

        for field in required_fields:
            assert field in policy, f"Missing required field: {field}"

        # Verify types
        assert isinstance(policy["generated_at"], str)
        assert isinstance(policy["model_name"], str)
        assert isinstance(policy["proposed_actions"], list)
        assert isinstance(policy["errors"], list)
        assert isinstance(policy["notes"], list)

        # Verify timestamp format (ISO 8601)
        assert "T" in policy["generated_at"]
        assert "Z" in policy["generated_at"]

        print("✓ Test 5 passed: All required fields present")

    def test_policy_robust_parsing(self):
        """
        Test 6: Robust parsing of bullet-point format LLM output

        Verifies:
        - Bullet points are converted to structured actions
        - Different bullet styles are recognized
        - Fallback actions are added if needed
        """
        # Create brain file
        brain_path = os.path.join(self.state_dir, "hands_off_brain.json")
        with open(brain_path, 'w') as f:
            json.dump({"status": "ok"}, f)

        # Mock LLM that returns bullet points
        def bullet_llm(prompt: str) -> str:
            return """
Based on the system state, I recommend:

- run autoloop in DRYRUN mode
- refresh summary
- health check the system
- analyze history data

These actions will help maintain system health.
"""

        # Build policy
        policy = build_policy_recommendation(
            state_dir=self.state_dir,
            llm_fn=bullet_llm,
            model_name="bullet-model"
        )

        # Verify parsing
        assert "proposed_actions" in policy
        actions = policy["proposed_actions"]
        assert len(actions) > 0

        # Check that we parsed the bullet points
        action_types = [a["type"] for a in actions]
        assert "autoloop" in action_types or "summary" in action_types

        # Verify DRYRUN mode was preserved for autoloop
        autoloop_actions = [a for a in actions if a["type"] == "autoloop"]
        if autoloop_actions:
            assert autoloop_actions[0].get("mode") == "DRYRUN"

        print("✓ Test 6 passed: Robust parsing of bullet points works")

    def test_no_external_calls(self):
        """
        Test 7: Verify no HTTP/network calls occur in policy module

        Verifies:
        - Module doesn't import requests/urllib
        - No network connections are made
        - All operations are file-based
        """
        # Read the module source
        module_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'ai', 'ho_policy_agent.py'
        )
        with open(module_path, 'r') as f:
            source = f.read()

        # Check for network-related imports
        forbidden_imports = ['requests', 'urllib', 'http.client', 'socket']
        for imp in forbidden_imports:
            assert f'import {imp}' not in source, f"Found forbidden import: {imp}"
            assert f'from {imp}' not in source, f"Found forbidden import: from {imp}"

        # Create brain file
        brain_path = os.path.join(self.state_dir, "hands_off_brain.json")
        with open(brain_path, 'w') as f:
            json.dump({"status": "ok"}, f)

        # Mock LLM (no network needed)
        call_count = [0]

        def local_llm(prompt: str) -> str:
            call_count[0] += 1
            return '{"brain_status": "ok", "proposed_actions": [{"type": "summary"}], "notes": []}'

        # Build policy - should work offline
        policy = build_policy_recommendation(
            state_dir=self.state_dir,
            llm_fn=local_llm,
            model_name="offline-model"
        )

        # Verify LLM was called (locally)
        assert call_count[0] == 1

        # Verify policy was built successfully (no network needed)
        assert policy["model_name"] == "offline-model"
        assert len(policy["proposed_actions"]) > 0

        print("✓ Test 7 passed: No external network calls detected")


def run_all_tests():
    """Run all tests and report results"""
    test_suite = TestPolicyAgent()
    tests = [
        ("Test 1: Minimal fallback", test_suite.test_policy_minimal_fallback),
        ("Test 2: Mock LLM", test_suite.test_policy_with_mock_llm),
        ("Test 3: Bad LLM JSON", test_suite.test_policy_bad_llm_json),
        ("Test 4: CLI invocation", test_suite.test_cli_invocation),
        ("Test 5: Required fields", test_suite.test_policy_contains_required_fields),
        ("Test 6: Robust parsing", test_suite.test_policy_robust_parsing),
        ("Test 7: No external calls", test_suite.test_no_external_calls),
    ]

    passed = 0
    failed = 0

    print("\n" + "=" * 60)
    print("BATCH 19 POLICY AGENT - TEST SUITE")
    print("=" * 60 + "\n")

    for test_name, test_func in tests:
        try:
            test_suite.setup_method()
            test_func()
            test_suite.teardown_method()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
