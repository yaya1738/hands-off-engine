#!/usr/bin/env python3
"""
Integration tests for Hands-Off Learning Engine (Batch 23)

Test coverage:
1. Missing brain_consensus.json
2. Malformed JSON
3. New learning file creation
4. Updating existing learning file
5. Issue recurrence tracking
6. Stable hashing correctness
7. Agent performance scoring
8. Learning weight normalization
9. Trend calculation
10. CLI invocation
11. File isolation
12. Large-history performance behavior
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.ho_learning_engine import LearningEngine


class TestLearningEngine(unittest.TestCase):
    """Integration tests for the Learning Engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.test_dir) / "state"
        self.state_dir.mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def create_sample_consensus(self, num_issues=3, agents=None):
        """
        Create a sample consensus file for testing.

        Args:
            num_issues: Number of issues to include
            agents: Dict of agent data (uses defaults if None)
        """
        if agents is None:
            agents = {
                "rules": {
                    "issues": [
                        {"severity": "high", "message": "Critical error detected", "confidence": 0.9}
                    ]
                },
                "llm_1": {
                    "issues": [
                        {"severity": "high", "message": "Critical error detected", "confidence": 0.85}
                    ]
                },
                "llm_2": {
                    "issues": [
                        {"severity": "medium", "message": "Warning: potential issue", "confidence": 0.7}
                    ]
                },
                "heuristics": {
                    "issues": [
                        {"severity": "high", "message": "Critical error found", "confidence": 0.88}
                    ]
                }
            }

        consensus = {
            "generated_at": "2025-11-19T00:00:00Z",
            "source": "test",
            "agents": agents,
            "issues": [
                {
                    "severity": "high",
                    "message": "Critical error detected",
                    "confidence": 0.88,
                    "agent_agreement": 0.75
                },
                {
                    "severity": "medium",
                    "message": "Warning: potential issue",
                    "confidence": 0.7,
                    "agent_agreement": 0.5
                },
                {
                    "severity": "low",
                    "message": "Minor optimization opportunity",
                    "confidence": 0.6,
                    "agent_agreement": 0.25
                }
            ][:num_issues]
        }

        consensus_path = self.state_dir / "brain_consensus.json"
        with open(consensus_path, 'w') as f:
            json.dump(consensus, f, indent=2)

        return consensus

    def test_01_missing_consensus_file(self):
        """Test 1: Missing brain_consensus.json"""
        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        with self.assertRaises(FileNotFoundError):
            engine.update()

    def test_02_malformed_json(self):
        """Test 2: Malformed JSON"""
        consensus_path = self.state_dir / "brain_consensus.json"
        with open(consensus_path, 'w') as f:
            f.write("{invalid json content")

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        with self.assertRaises(json.JSONDecodeError):
            engine.update()

    def test_03_new_learning_file_creation(self):
        """Test 3: New learning file creation"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)
        learning_state = engine.update()

        # Verify learning file was created
        learning_path = self.state_dir / "brain_learning.json"
        self.assertTrue(learning_path.exists())

        # Verify structure
        self.assertIn('run_count', learning_state)
        self.assertEqual(learning_state['run_count'], 1)
        self.assertIn('issue_history', learning_state)
        self.assertIn('agent_performance', learning_state)
        self.assertIn('trend_metrics', learning_state)
        self.assertIn('learning_weights', learning_state)
        self.assertIn('recommendations', learning_state)

    def test_04_updating_existing_learning_file(self):
        """Test 4: Updating existing learning file"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        # First run
        state1 = engine.update()
        self.assertEqual(state1['run_count'], 1)

        # Second run
        state2 = engine.update()
        self.assertEqual(state2['run_count'], 2)

        # Third run
        state3 = engine.update()
        self.assertEqual(state3['run_count'], 3)

        # Verify persistence
        loaded_state = engine.load_learning_state()
        self.assertEqual(loaded_state['run_count'], 3)

    def test_05_issue_recurrence_tracking(self):
        """Test 5: Issue recurrence tracking"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        # Run multiple times
        for i in range(5):
            engine.update()

        # Check that issues have been tracked
        learning_state = engine.load_learning_state()
        issue_history = learning_state['issue_history']

        self.assertGreater(len(issue_history), 0)

        # Find the critical error issue
        critical_issue = next(
            (issue for issue in issue_history
             if "Critical error" in issue.get('message', '')),
            None
        )

        self.assertIsNotNone(critical_issue)
        self.assertEqual(critical_issue['occurrences'], 5)
        self.assertEqual(critical_issue['severity'], 'high')

    def test_06_stable_hashing_correctness(self):
        """Test 6: Stable hashing correctness"""
        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        # Same input should produce same hash
        hash1 = engine.generate_issue_hash("high", "Critical error")
        hash2 = engine.generate_issue_hash("high", "Critical error")
        self.assertEqual(hash1, hash2)

        # Different input should produce different hash
        hash3 = engine.generate_issue_hash("low", "Critical error")
        self.assertNotEqual(hash1, hash3)

        hash4 = engine.generate_issue_hash("high", "Different error")
        self.assertNotEqual(hash1, hash4)

    def test_07_agent_performance_scoring(self):
        """Test 7: Agent performance scoring"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)
        learning_state = engine.update()

        # Verify agent performance was calculated
        agent_perf = learning_state['agent_performance']
        self.assertGreater(len(agent_perf), 0)

        # Check that all agents have required fields
        for agent_name, perf in agent_perf.items():
            self.assertIn('accuracy', perf)
            self.assertIn('runs', perf)
            self.assertGreaterEqual(perf['accuracy'], 0.0)
            self.assertLessEqual(perf['accuracy'], 1.0)
            self.assertEqual(perf['runs'], 1)

    def test_08_learning_weight_normalization(self):
        """Test 8: Learning weight normalization"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)
        learning_state = engine.update()

        # Verify weights are normalized
        weights = learning_state['learning_weights']
        self.assertGreater(len(weights), 0)

        # Check that weights sum to approximately 1.0
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=1)

        # Check that all weights are between 0 and 1
        for agent_name, weight in weights.items():
            self.assertGreaterEqual(weight, 0.0)
            self.assertLessEqual(weight, 1.0)

    def test_09_trend_calculation(self):
        """Test 9: Trend calculation"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        # Run multiple times
        for i in range(3):
            learning_state = engine.update()

        # Verify trend metrics
        trends = learning_state['trend_metrics']
        self.assertIn('error_rate_mean', trends)
        self.assertIn('error_rate_std', trends)
        self.assertIn('consensus_mean', trends)
        self.assertIn('consensus_trend', trends)

        # Check trend direction is valid
        self.assertIn(trends['consensus_trend'], ['up', 'down', 'flat'])

        # Check metrics are in valid range
        self.assertGreaterEqual(trends['error_rate_mean'], 0.0)
        self.assertLessEqual(trends['error_rate_mean'], 1.0)
        self.assertGreaterEqual(trends['consensus_mean'], 0.0)
        self.assertLessEqual(trends['consensus_mean'], 1.0)

    def test_10_cli_invocation(self):
        """Test 10: CLI invocation"""
        self.create_sample_consensus()

        # Test CLI with verbose flag
        result = subprocess.run(
            [
                sys.executable,
                'ai/ho_learning_engine.py',
                '--state-dir', str(self.state_dir),
                '--verbose'
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn('LEARNING ENGINE SUMMARY', result.stdout)
        self.assertIn('Run count:', result.stdout)

    def test_11_file_isolation(self):
        """Test 11: File isolation"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)
        engine.update()

        # Verify only expected files were created
        state_files = list(self.state_dir.glob('*'))
        state_filenames = [f.name for f in state_files]

        self.assertIn('brain_consensus.json', state_filenames)
        self.assertIn('brain_learning.json', state_filenames)

        # No files should be created outside state directory
        root_files_before = set(Path(self.test_dir).glob('*'))
        engine.update()
        root_files_after = set(Path(self.test_dir).glob('*'))

        # Only state directory should exist at root level
        self.assertEqual(root_files_before, root_files_after)

    def test_12_large_history_performance(self):
        """Test 12: Large-history performance behavior"""
        # Create learning state with large history
        large_history = []
        for i in range(1000):
            large_history.append({
                "hash": f"hash_{i:04d}",
                "first_seen": "2025-11-01T00:00:00Z",
                "last_seen": "2025-11-19T00:00:00Z",
                "occurrences": i % 10 + 1,
                "severity": ["low", "medium", "high"][i % 3],
                "confidence": 0.5 + (i % 50) / 100.0,
                "message": f"Issue message {i}"
            })

        learning_state = {
            "generated_at": "2025-11-19T00:00:00Z",
            "source": "state/brain_consensus.json",
            "run_count": 100,
            "issue_history": large_history,
            "agent_performance": {
                "rules": {"accuracy": 0.91, "runs": 100, "total_accuracy": 91.0},
                "llm_1": {"accuracy": 0.87, "runs": 100, "total_accuracy": 87.0},
                "llm_2": {"accuracy": 0.77, "runs": 100, "total_accuracy": 77.0},
                "heuristics": {"accuracy": 0.89, "runs": 100, "total_accuracy": 89.0}
            },
            "trend_metrics": {
                "error_rate_mean": 0.08,
                "error_rate_std": 0.02,
                "consensus_mean": 0.63,
                "consensus_trend": "up"
            },
            "learning_weights": {
                "rules": 0.31,
                "llm_1": 0.28,
                "llm_2": 0.16,
                "heuristics": 0.25
            },
            "recommendations": []
        }

        learning_path = self.state_dir / "brain_learning.json"
        with open(learning_path, 'w') as f:
            json.dump(learning_state, f)

        # Create consensus and run update
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        # Should complete without issues even with large history
        updated_state = engine.update()

        self.assertEqual(updated_state['run_count'], 101)
        self.assertGreaterEqual(len(updated_state['issue_history']), 1000)

    def test_13_recommendations_generation(self):
        """Test 13: Recommendations generation"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        # Run enough times to trigger recurring issue detection
        for i in range(5):
            learning_state = engine.update()

        # Verify recommendations were generated
        recommendations = learning_state['recommendations']
        self.assertGreater(len(recommendations), 0)
        self.assertIsInstance(recommendations, list)
        for rec in recommendations:
            self.assertIsInstance(rec, str)

    def test_14_malformed_existing_learning_state(self):
        """Test 14: Malformed existing learning state"""
        self.create_sample_consensus()

        # Create malformed learning state
        learning_path = self.state_dir / "brain_learning.json"
        with open(learning_path, 'w') as f:
            f.write("{invalid json")

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        # Should handle gracefully and create new state
        learning_state = engine.update()

        self.assertEqual(learning_state['run_count'], 1)

    def test_15_empty_consensus_issues(self):
        """Test 15: Empty consensus issues"""
        consensus = self.create_sample_consensus(num_issues=0)

        # Remove all issues
        consensus['issues'] = []
        for agent_data in consensus['agents'].values():
            agent_data['issues'] = []

        consensus_path = self.state_dir / "brain_consensus.json"
        with open(consensus_path, 'w') as f:
            json.dump(consensus, f, indent=2)

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)
        learning_state = engine.update()

        # Should handle empty issues gracefully
        self.assertEqual(learning_state['run_count'], 1)
        self.assertEqual(len(learning_state['issue_history']), 0)


def main():
    """Run tests."""
    # Run with verbose output
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
