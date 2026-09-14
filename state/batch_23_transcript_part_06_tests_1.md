# Batch 23 Implementation Transcript - Part 6: Test Suite (Part 1/2)

## File: tests/integration/test_learning_engine.py (Lines 1-350)

```python
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
        """Create a sample consensus file for testing."""
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
```

*Continued in Part 7...*
