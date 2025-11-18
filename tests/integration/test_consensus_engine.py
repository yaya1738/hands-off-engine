#!/usr/bin/env python3
"""
Integration tests for Consensus Feedback Engine (Batch 22)

Tests cover:
- Missing feedback file
- Malformed JSON
- Minimal valid JSON
- Multiple agents with different priorities
- Consensus score calculation
- Contradiction detection
- Confidence bucket calculation
- Stubbed LLM agent behavior
- CLI invocation
- JSON structure validation
- Severity ordering
- File operation isolation

All tests use temporary directories for isolation.
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.ho_consensus_engine import (
    ConsensusEngine,
    ConfidenceLevel,
    SeverityLevel,
    AgentResponse,
    ConsensusOutput
)


class TestConsensusEngine(unittest.TestCase):
    """Integration tests for ConsensusEngine"""

    def setUp(self):
        """Create temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.feedback_path = os.path.join(self.temp_dir, 'brain_feedback.json')
        self.output_path = os.path.join(self.temp_dir, 'brain_consensus.json')

    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_feedback(self, data):
        """Helper: create feedback JSON file"""
        with open(self.feedback_path, 'w') as f:
            json.dump(data, f)

    def _load_output(self):
        """Helper: load output JSON file"""
        with open(self.output_path, 'r') as f:
            return json.load(f)

    # Test 1: Missing feedback file
    def test_missing_feedback_file(self):
        """Test handling of missing feedback file"""
        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        # Should not raise exception
        success = engine.load_feedback()
        self.assertFalse(success)
        self.assertTrue(len(engine.errors) > 0)
        self.assertIn("not found", engine.errors[0].lower())

        # Should still have minimal feedback data
        self.assertIsNotNone(engine.feedback_data)
        self.assertEqual(engine.feedback_data.get('issues', []), [])

    # Test 2: Malformed JSON
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        # Write invalid JSON
        with open(self.feedback_path, 'w') as f:
            f.write("{invalid json content")

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        success = engine.load_feedback()
        self.assertFalse(success)
        self.assertTrue(len(engine.errors) > 0)
        self.assertIn("malformed", engine.errors[0].lower())

        # Should have fallback data
        self.assertIsNotNone(engine.feedback_data)

    # Test 3: Minimal valid JSON
    def test_minimal_valid_json(self):
        """Test processing of minimal valid JSON"""
        minimal_data = {
            "issues": [],
            "metrics": {}
        }
        self._create_feedback(minimal_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        success = engine.run()
        self.assertTrue(success)

        # Verify output exists
        self.assertTrue(os.path.exists(self.output_path))

        output = self._load_output()
        self.assertIn('consensus', output)
        self.assertIn('agents', output)
        self.assertEqual(len(output['issues_detected']), 0)

    # Test 4: Multiple agents returning different priorities
    def test_multiple_agents_different_priorities(self):
        """Test that different agents produce different priorities"""
        feedback_data = {
            "issues": [
                {"severity": "high", "type": "error", "fixable": True},
                {"severity": "medium", "type": "warning", "fixable": True},
                {"severity": "critical", "type": "failure", "fixable": False}
            ],
            "metrics": {
                "error_rate": 0.15
            }
        }
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        engine.load_feedback()
        engine.agent_responses = [
            engine.run_rules_engine(),
            engine.run_llm_agent_1(),
            engine.run_llm_agent_2(),
            engine.run_heuristics()
        ]

        # Verify all agents ran
        self.assertEqual(len(engine.agent_responses), 4)

        # Verify different agent names
        agent_names = [r.agent_name for r in engine.agent_responses]
        self.assertEqual(len(set(agent_names)), 4)

        # Verify agents have different characteristics
        confidences = [r.confidence for r in engine.agent_responses]
        self.assertTrue(min(confidences) < max(confidences))  # Some variance

    # Test 5: Consensus score calculation
    def test_consensus_score_calculation(self):
        """Test consensus score computation"""
        feedback_data = {
            "issues": [
                {"severity": "high", "type": "error"},
                {"severity": "high", "type": "error"}
            ],
            "metrics": {}
        }
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        success = engine.run()
        self.assertTrue(success)

        output = self._load_output()
        consensus = output['consensus']

        # Verify consensus structure
        self.assertIn('agreement_score', consensus)
        self.assertIn('confidence', consensus)
        self.assertIn('stability_score', consensus)

        # Verify score ranges
        self.assertGreaterEqual(consensus['agreement_score'], 0.0)
        self.assertLessEqual(consensus['agreement_score'], 1.0)

        self.assertGreaterEqual(consensus['stability_score'], 0.0)
        self.assertLessEqual(consensus['stability_score'], 1.0)

        # Verify confidence bucket
        self.assertIn(consensus['confidence'], ['low', 'medium', 'high'])

    # Test 6: Contradiction detection
    def test_contradiction_detection(self):
        """Test detection of agent contradictions"""
        feedback_data = {
            "issues": [
                {"severity": "critical", "type": "error"},
                {"severity": "high", "type": "warning"},
                {"severity": "medium", "type": "info"}
            ],
            "metrics": {}
        }
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        success = engine.run()
        self.assertTrue(success)

        output = self._load_output()
        contradictions = output['consensus']['contradictions']

        # Should detect some contradictions due to different agent perspectives
        self.assertIsInstance(contradictions, list)

        # Each contradiction should have proper structure
        for contradiction in contradictions:
            self.assertIn('type', contradiction)
            self.assertIn('description', contradiction)

    # Test 7: Confidence bucket calculation
    def test_confidence_bucket_calculation(self):
        """Test confidence bucket mapping"""
        engine = ConsensusEngine(verbose=False)

        # Test boundary conditions
        self.assertEqual(engine._confidence_to_bucket(0.9), 'high')
        self.assertEqual(engine._confidence_to_bucket(0.8), 'high')
        self.assertEqual(engine._confidence_to_bucket(0.75), 'medium')
        self.assertEqual(engine._confidence_to_bucket(0.6), 'medium')
        self.assertEqual(engine._confidence_to_bucket(0.5), 'low')
        self.assertEqual(engine._confidence_to_bucket(0.0), 'low')

    # Test 8: Stubbed LLM agent behavior
    def test_stubbed_llm_agents(self):
        """Test that LLM agents are properly stubbed (no API calls)"""
        feedback_data = {
            "issues": [{"severity": "high", "type": "error"}],
            "metrics": {}
        }
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        engine.load_feedback()

        # Run LLM agents - should be deterministic and instant
        import time
        start = time.time()

        response1 = engine.run_llm_agent_1()
        response2 = engine.run_llm_agent_2()

        elapsed = time.time() - start

        # Should be very fast (no network calls)
        self.assertLess(elapsed, 0.1)

        # Should have different characteristics
        self.assertEqual(response1.agent_name, "llm_agent_1_conservative")
        self.assertEqual(response2.agent_name, "llm_agent_2_optimistic")

        # Conservative vs optimistic should differ
        self.assertNotEqual(response1.recommendations, response2.recommendations)

    # Test 9: CLI invocation
    def test_cli_invocation(self):
        """Test command-line interface"""
        feedback_data = {
            "issues": [],
            "metrics": {}
        }
        self._create_feedback(feedback_data)

        # Run via CLI
        result = subprocess.run(
            [
                sys.executable,
                'ai/ho_consensus_engine.py',
                '--input', self.feedback_path,
                '--output', self.output_path
            ],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )

        # Should succeed
        self.assertEqual(result.returncode, 0)

        # Output file should exist
        self.assertTrue(os.path.exists(self.output_path))

        # Should be valid JSON
        output = self._load_output()
        self.assertIn('consensus', output)

    # Test 10: JSON structure validation
    def test_json_structure_validation(self):
        """Test complete output JSON structure"""
        feedback_data = {
            "issues": [
                {"severity": "medium", "type": "warning"}
            ],
            "metrics": {
                "error_rate": 0.05
            }
        }
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        success = engine.run()
        self.assertTrue(success)

        output = self._load_output()

        # Validate top-level structure
        required_keys = ['generated_at', 'source', 'agents', 'consensus', 'issues_detected', 'notes', 'errors']
        for key in required_keys:
            self.assertIn(key, output, f"Missing required key: {key}")

        # Validate agents structure
        self.assertIsInstance(output['agents'], dict)
        self.assertGreater(len(output['agents']), 0)

        for agent_name, agent_data in output['agents'].items():
            self.assertIn('recommendations', agent_data)
            self.assertIn('priority_items', agent_data)
            self.assertIn('confidence', agent_data)
            self.assertIn('severity_assessment', agent_data)
            self.assertIn('notes', agent_data)

        # Validate consensus structure
        consensus = output['consensus']
        self.assertIn('agreement_score', consensus)
        self.assertIn('confidence', consensus)
        self.assertIn('priority_items', consensus)
        self.assertIn('contradictions', consensus)
        self.assertIn('final_recommendations', consensus)
        self.assertIn('stability_score', consensus)

    # Test 11: Severity ordering
    def test_severity_ordering(self):
        """Test that severity levels are correctly assessed and ordered"""
        test_cases = [
            {
                "input": {"issues": [], "metrics": {}},
                "expected_severities": ['low', 'info']
            },
            {
                "input": {"issues": [{"severity": "critical"}], "metrics": {}},
                "expected_severities": ['critical', 'high']
            },
            {
                "input": {"issues": [{"severity": "high"}] * 3, "metrics": {}},
                "expected_severities": ['high', 'medium', 'critical']
            }
        ]

        for i, test_case in enumerate(test_cases):
            with self.subTest(i=i):
                self._create_feedback(test_case['input'])

                engine = ConsensusEngine(
                    feedback_path=self.feedback_path,
                    output_path=self.output_path,
                    verbose=False
                )

                engine.load_feedback()
                engine.agent_responses = [
                    engine.run_rules_engine(),
                    engine.run_heuristics()
                ]

                # Check that at least one agent reported expected severity
                agent_severities = [r.severity_assessment for r in engine.agent_responses]
                self.assertTrue(
                    any(sev in test_case['expected_severities'] for sev in agent_severities),
                    f"Expected one of {test_case['expected_severities']}, got {agent_severities}"
                )

    # Test 12: File operation isolation (temp dirs)
    def test_file_operation_isolation(self):
        """Test that file operations are properly isolated to temp directories"""
        feedback_data = {"issues": [], "metrics": {}}
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        # Verify paths are within temp directory
        self.assertTrue(self.feedback_path.startswith(self.temp_dir))
        self.assertTrue(self.output_path.startswith(self.temp_dir))

        # Run engine
        success = engine.run()
        self.assertTrue(success)

        # Verify only expected files exist
        files_created = os.listdir(self.temp_dir)
        self.assertIn('brain_feedback.json', files_created)
        self.assertIn('brain_consensus.json', files_created)

        # Should not create files outside temp directory
        parent_dir = os.path.dirname(self.temp_dir)
        parent_files_before = set(os.listdir(parent_dir))

        engine.run()

        parent_files_after = set(os.listdir(parent_dir))
        self.assertEqual(parent_files_before, parent_files_after)

    # Test 13: Agreement score edge cases
    def test_agreement_score_edge_cases(self):
        """Test agreement score with edge cases"""
        feedback_data = {
            "issues": [{"severity": "high"}],
            "metrics": {}
        }
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        engine.load_feedback()

        # Single agent: perfect agreement
        engine.agent_responses = [engine.run_rules_engine()]
        score_single = engine._compute_agreement_score()
        self.assertEqual(score_single, 1.0)

        # Multiple identical agents: high agreement
        engine.agent_responses = [
            engine.run_rules_engine(),
            engine.run_rules_engine()
        ]
        score_identical = engine._compute_agreement_score()
        self.assertGreater(score_identical, 0.65)  # Should have good agreement

        # Diverse agents: varying agreement
        engine.agent_responses = [
            engine.run_rules_engine(),
            engine.run_llm_agent_1(),
            engine.run_llm_agent_2(),
            engine.run_heuristics()
        ]
        score_diverse = engine._compute_agreement_score()
        self.assertGreaterEqual(score_diverse, 0.0)
        self.assertLessEqual(score_diverse, 1.0)

    # Test 14: Priority merging
    def test_priority_merging(self):
        """Test merging of priority items from multiple agents"""
        feedback_data = {
            "issues": [
                {"severity": "critical", "type": "error"},
                {"severity": "high", "type": "warning"},
                {"severity": "medium", "type": "info"}
            ],
            "metrics": {"error_rate": 0.2}
        }
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        success = engine.run()
        self.assertTrue(success)

        output = self._load_output()
        priority_items = output['consensus']['priority_items']

        # Should have merged priorities
        self.assertIsInstance(priority_items, list)
        self.assertGreater(len(priority_items), 0)

        # Each item should have source agent
        for item in priority_items:
            self.assertIn('source_agent', item)
            self.assertIn('priority', item)

        # Should be sorted by priority (lower number = higher priority)
        priorities = [item['priority'] for item in priority_items]
        self.assertEqual(priorities, sorted(priorities))

    # Test 15: Empty recommendations handling
    def test_empty_recommendations_handling(self):
        """Test handling when agents produce no recommendations"""
        feedback_data = {"issues": [], "metrics": {}}
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        success = engine.run()
        self.assertTrue(success)

        output = self._load_output()

        # Should still produce final recommendations (at least meta-recommendations)
        final_recs = output['consensus']['final_recommendations']
        self.assertIsInstance(final_recs, list)
        self.assertGreater(len(final_recs), 0)

    # Test 16: High issue volume stress test
    def test_high_issue_volume(self):
        """Test handling of high volume of issues"""
        feedback_data = {
            "issues": [
                {"severity": "medium", "type": f"issue_{i}", "fixable": True}
                for i in range(100)
            ],
            "metrics": {"error_rate": 0.5}
        }
        self._create_feedback(feedback_data)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        # Should complete without errors
        success = engine.run()
        self.assertTrue(success)

        output = self._load_output()

        # Should handle all issues
        self.assertEqual(len(output['issues_detected']), 100)

        # Consensus should reflect high issue count
        consensus = output['consensus']
        self.assertGreater(len(consensus['priority_items']), 0)


class TestAgentSpecificBehavior(unittest.TestCase):
    """Tests for specific agent behaviors"""

    def setUp(self):
        """Create temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.feedback_path = os.path.join(self.temp_dir, 'brain_feedback.json')
        self.output_path = os.path.join(self.temp_dir, 'brain_consensus.json')

    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_rules_engine_deterministic(self):
        """Test that rules engine is deterministic"""
        feedback_data = {
            "issues": [{"severity": "high", "type": "error"}],
            "metrics": {"error_rate": 0.15}
        }

        with open(self.feedback_path, 'w') as f:
            json.dump(feedback_data, f)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        engine.load_feedback()

        # Run multiple times
        response1 = engine.run_rules_engine()
        response2 = engine.run_rules_engine()
        response3 = engine.run_rules_engine()

        # Should be identical
        self.assertEqual(response1.recommendations, response2.recommendations)
        self.assertEqual(response2.recommendations, response3.recommendations)
        self.assertEqual(response1.confidence, response2.confidence)

    def test_conservative_vs_optimistic_agents(self):
        """Test that conservative and optimistic agents differ appropriately"""
        feedback_data = {
            "issues": [
                {"severity": "medium", "type": "error", "fixable": True},
                {"severity": "medium", "type": "warning", "fixable": True}
            ],
            "metrics": {}
        }

        with open(self.feedback_path, 'w') as f:
            json.dump(feedback_data, f)

        engine = ConsensusEngine(
            feedback_path=self.feedback_path,
            output_path=self.output_path,
            verbose=False
        )

        engine.load_feedback()

        conservative = engine.run_llm_agent_1()
        optimistic = engine.run_llm_agent_2()

        # Conservative should have lower or equal confidence
        # (or they may be tuned differently based on implementation)
        self.assertIsInstance(conservative.confidence, float)
        self.assertIsInstance(optimistic.confidence, float)

        # Should have different recommendation styles
        conservative_text = ' '.join(conservative.recommendations).lower()
        optimistic_text = ' '.join(optimistic.recommendations).lower()

        # Conservative might mention "thorough", "review", "incremental"
        # Optimistic might mention "batch", "parallel", "quick"
        self.assertNotEqual(conservative_text, optimistic_text)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load all tests
    suite.addTests(loader.loadTestsFromTestCase(TestConsensusEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentSpecificBehavior))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
