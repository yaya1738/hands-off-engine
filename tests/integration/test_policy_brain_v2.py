#!/usr/bin/env python3
"""
Comprehensive test suite for Policy Brain v2

Tests cover:
- Input validation
- Weight computation
- Priority calculation
- Trend influence
- Recurrence handling
- Deterministic output
- CLI invocation
- JSON contract validation
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.ho_policy_brain_v2 import PolicyBrainV2, PolicyAction


class TestPolicyBrainV2Basic(unittest.TestCase):
    """Basic functionality tests."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.test_dir) / "state"
        self.state_dir.mkdir()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_01_initialization(self):
        """Test PolicyBrainV2 initialization."""
        brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        self.assertEqual(brain.state_dir, self.state_dir)
        self.assertEqual(brain.verbose, False)
        self.assertEqual(brain.errors, [])
        self.assertEqual(brain.notes, [])

    def test_02_initialization_with_defaults(self):
        """Test PolicyBrainV2 initialization with default state_dir."""
        brain = PolicyBrainV2()
        self.assertEqual(brain.state_dir, Path("state"))
        self.assertEqual(brain.verbose, False)

    def test_03_load_missing_consensus_file(self):
        """Test loading missing consensus file."""
        brain = PolicyBrainV2(state_dir=self.state_dir)
        result = brain.load_consensus_state()
        self.assertIsNone(result)
        self.assertEqual(len(brain.errors), 1)
        self.assertIn("brain_consensus.json", brain.errors[0])

    def test_04_load_missing_learning_file(self):
        """Test loading missing learning file."""
        brain = PolicyBrainV2(state_dir=self.state_dir)
        result = brain.load_learning_state()
        self.assertIsNone(result)
        self.assertEqual(len(brain.errors), 1)
        self.assertIn("brain_learning.json", brain.errors[0])

    def test_05_load_invalid_json(self):
        """Test loading invalid JSON file."""
        # Create invalid JSON file
        invalid_json = self.state_dir / "brain_consensus.json"
        with open(invalid_json, 'w') as f:
            f.write("{ invalid json }")

        brain = PolicyBrainV2(state_dir=self.state_dir)
        result = brain.load_consensus_state()
        self.assertIsNone(result)
        self.assertEqual(len(brain.errors), 1)
        self.assertIn("Invalid JSON", brain.errors[0])


class TestPolicyBrainV2WeightComputation(unittest.TestCase):
    """Weight computation tests."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.test_dir) / "state"
        self.state_dir.mkdir()
        self.brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_06_compute_learning_weight_default(self):
        """Test learning weight computation with default values."""
        learning_state = {
            "weights": {
                "test_agent": {
                    "base_weight": 0.5,
                    "accuracy": 0.5,
                    "trend": 0.0
                }
            }
        }
        weight = self.brain.compute_learning_weight("test_agent", learning_state)
        # Expected: 0.5 * (0.5 + 0.5) * 1.0 = 0.5
        self.assertAlmostEqual(weight, 0.5, places=2)

    def test_07_compute_learning_weight_high_accuracy(self):
        """Test learning weight with high accuracy."""
        learning_state = {
            "weights": {
                "high_accuracy_agent": {
                    "base_weight": 0.7,
                    "accuracy": 0.9,
                    "trend": 0.1
                }
            }
        }
        weight = self.brain.compute_learning_weight("high_accuracy_agent", learning_state)
        # Expected: 0.7 * (0.5 + 0.9) * (1.0 + 0.1*0.2) = 0.7 * 1.4 * 1.02 ≈ 0.999
        self.assertGreater(weight, 0.8)
        self.assertLessEqual(weight, 1.0)

    def test_08_compute_learning_weight_low_accuracy(self):
        """Test learning weight with low accuracy."""
        learning_state = {
            "weights": {
                "low_accuracy_agent": {
                    "base_weight": 0.6,
                    "accuracy": 0.2,
                    "trend": -0.3
                }
            }
        }
        weight = self.brain.compute_learning_weight("low_accuracy_agent", learning_state)
        # Lower weight due to low accuracy and negative trend
        self.assertLess(weight, 0.6)

    def test_09_compute_learning_weight_missing_agent(self):
        """Test learning weight for non-existent agent."""
        learning_state = {"weights": {}}
        weight = self.brain.compute_learning_weight("missing_agent", learning_state)
        # Should return default weight
        self.assertEqual(weight, 0.5)

    def test_10_compute_learning_weight_bounds(self):
        """Test that learning weights are bounded to [0.0, 1.0]."""
        learning_state = {
            "weights": {
                "extreme_agent": {
                    "base_weight": 1.0,
                    "accuracy": 1.0,
                    "trend": 1.0
                }
            }
        }
        weight = self.brain.compute_learning_weight("extreme_agent", learning_state)
        self.assertLessEqual(weight, 1.0)
        self.assertGreaterEqual(weight, 0.0)


class TestPolicyBrainV2PriorityComputation(unittest.TestCase):
    """Priority computation tests."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.test_dir) / "state"
        self.state_dir.mkdir()
        self.brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_11_compute_action_priority_high_consensus(self):
        """Test priority computation with high consensus."""
        action = {
            "type": "risk-reduction",
            "consensus_score": 0.9,
            "agents": ["agent1", "agent2"]
        }
        consensus_state = {}
        learning_state = {
            "weights": {
                "agent1": {"base_weight": 0.7, "accuracy": 0.8, "trend": 0.1},
                "agent2": {"base_weight": 0.7, "accuracy": 0.8, "trend": 0.1}
            },
            "issue_history": {
                "risk-reduction": {"count": 5}
            },
            "trend_metrics": {
                "risk-reduction": {"trend": 0.0}
            }
        }

        priority, reasoning = self.brain.compute_action_priority(
            action, consensus_state, learning_state
        )

        # High consensus should result in high priority
        self.assertGreater(priority, 0.6)
        self.assertIsInstance(reasoning, list)
        self.assertGreater(len(reasoning), 0)

    def test_12_compute_action_priority_recurrence_boost(self):
        """Test that high recurrence increases priority."""
        action_low_recurrence = {
            "type": "rare-issue",
            "consensus_score": 0.5,
            "agents": ["agent1"]
        }
        action_high_recurrence = {
            "type": "common-issue",
            "consensus_score": 0.5,
            "agents": ["agent1"]
        }
        consensus_state = {}
        learning_state = {
            "weights": {
                "agent1": {"base_weight": 0.5, "accuracy": 0.5, "trend": 0.0}
            },
            "issue_history": {
                "rare-issue": {"count": 1},
                "common-issue": {"count": 20}
            },
            "trend_metrics": {
                "rare-issue": {"trend": 0.0},
                "common-issue": {"trend": 0.0}
            }
        }

        priority_low, _ = self.brain.compute_action_priority(
            action_low_recurrence, consensus_state, learning_state
        )
        priority_high, _ = self.brain.compute_action_priority(
            action_high_recurrence, consensus_state, learning_state
        )

        # High recurrence should increase priority
        self.assertGreater(priority_high, priority_low)

    def test_13_compute_action_priority_trend_influence(self):
        """Test that negative trend increases priority."""
        action = {
            "type": "degrading-issue",
            "consensus_score": 0.5,
            "agents": ["agent1"]
        }
        consensus_state = {}
        learning_state_positive_trend = {
            "weights": {
                "agent1": {"base_weight": 0.5, "accuracy": 0.5, "trend": 0.0}
            },
            "issue_history": {"degrading-issue": {"count": 5}},
            "trend_metrics": {"degrading-issue": {"trend": 0.5}}  # Improving
        }
        learning_state_negative_trend = {
            "weights": {
                "agent1": {"base_weight": 0.5, "accuracy": 0.5, "trend": 0.0}
            },
            "issue_history": {"degrading-issue": {"count": 5}},
            "trend_metrics": {"degrading-issue": {"trend": -0.5}}  # Degrading
        }

        priority_pos, _ = self.brain.compute_action_priority(
            action, consensus_state, learning_state_positive_trend
        )
        priority_neg, _ = self.brain.compute_action_priority(
            action, consensus_state, learning_state_negative_trend
        )

        # Negative trend (degrading) should increase priority
        self.assertGreater(priority_neg, priority_pos)

    def test_14_determine_confidence_levels(self):
        """Test confidence level determination."""
        self.assertEqual(self.brain.determine_confidence(0.9), "high")
        self.assertEqual(self.brain.determine_confidence(0.7), "high")
        self.assertEqual(self.brain.determine_confidence(0.5), "medium")
        self.assertEqual(self.brain.determine_confidence(0.4), "medium")
        self.assertEqual(self.brain.determine_confidence(0.3), "low")
        self.assertEqual(self.brain.determine_confidence(0.0), "low")


class TestPolicyBrainV2Integration(unittest.TestCase):
    """Integration tests with full pipeline."""

    def setUp(self):
        """Set up test environment with sample data."""
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.test_dir) / "state"
        self.state_dir.mkdir()

        # Create sample consensus data
        self.consensus_data = {
            "final_recommendations": [
                {
                    "type": "risk-reduction",
                    "consensus_score": 0.88,
                    "agents": ["risk_analyzer", "trend_detector"],
                    "triggers": ["high_volatility"],
                    "next_step": "Reduce positions"
                },
                {
                    "type": "monitoring",
                    "consensus_score": 0.65,
                    "agents": ["sentiment_monitor"],
                    "triggers": ["sentiment_shift"],
                    "next_step": "Monitor closely"
                }
            ]
        }

        # Create sample learning data
        self.learning_data = {
            "weights": {
                "risk_analyzer": {"base_weight": 0.75, "accuracy": 0.82, "trend": 0.15},
                "trend_detector": {"base_weight": 0.65, "accuracy": 0.68, "trend": -0.05},
                "sentiment_monitor": {"base_weight": 0.55, "accuracy": 0.71, "trend": 0.08}
            },
            "issue_history": {
                "risk-reduction": {"count": 8},
                "monitoring": {"count": 25}
            },
            "trend_metrics": {
                "risk-reduction": {"trend": 0.12},
                "monitoring": {"trend": -0.01}
            }
        }

        # Write to files
        with open(self.state_dir / "brain_consensus.json", 'w') as f:
            json.dump(self.consensus_data, f)

        with open(self.state_dir / "brain_learning.json", 'w') as f:
            json.dump(self.learning_data, f)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_15_full_pipeline_execution(self):
        """Test full pipeline execution."""
        brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        success = brain.run()

        self.assertTrue(success)
        self.assertTrue((self.state_dir / "brain_policy_v2.json").exists())

    def test_16_output_json_contract(self):
        """Test that output matches expected JSON contract."""
        brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        brain.run()

        # Load output
        with open(self.state_dir / "brain_policy_v2.json", 'r') as f:
            output = json.load(f)

        # Validate contract
        self.assertIn("generated_at", output)
        self.assertIn("source_consensus", output)
        self.assertIn("source_learning", output)
        self.assertIn("weights_used", output)
        self.assertIn("actions", output)
        self.assertIn("notes", output)
        self.assertIn("errors", output)

        # Validate actions structure
        for action in output["actions"]:
            self.assertIn("type", action)
            self.assertIn("priority", action)
            self.assertIn("confidence", action)
            self.assertIn("reasoning", action)
            self.assertIn("triggers", action)
            self.assertIn("recommended_next_step", action)
            self.assertIn("source_agents", action)
            self.assertIn("learning_weight", action)

    def test_17_deterministic_output(self):
        """Test that output is deterministic for same input."""
        brain1 = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        brain1.run()

        with open(self.state_dir / "brain_policy_v2.json", 'r') as f:
            output1 = json.load(f)

        # Run again
        brain2 = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        brain2.run()

        with open(self.state_dir / "brain_policy_v2.json", 'r') as f:
            output2 = json.load(f)

        # Compare actions (excluding timestamp)
        self.assertEqual(len(output1["actions"]), len(output2["actions"]))

        for i in range(len(output1["actions"])):
            action1 = output1["actions"][i]
            action2 = output2["actions"][i]

            self.assertEqual(action1["type"], action2["type"])
            self.assertAlmostEqual(action1["priority"], action2["priority"], places=3)
            self.assertEqual(action1["confidence"], action2["confidence"])

    def test_18_priority_sorting(self):
        """Test that actions are sorted by priority (descending)."""
        brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        brain.run()

        with open(self.state_dir / "brain_policy_v2.json", 'r') as f:
            output = json.load(f)

        # Check that priorities are in descending order
        priorities = [action["priority"] for action in output["actions"]]
        self.assertEqual(priorities, sorted(priorities, reverse=True))

    def test_19_cli_invocation(self):
        """Test CLI invocation."""
        from ai.ho_policy_brain_v2 import main

        test_args = [
            "ho_policy_brain_v2.py",
            "--state-dir", str(self.state_dir),
            "--verbose"
        ]

        with patch.object(sys, 'argv', test_args):
            try:
                main()
                success = True
            except SystemExit as e:
                success = (e.code == 0)

        self.assertTrue(success)
        self.assertTrue((self.state_dir / "brain_policy_v2.json").exists())

    def test_20_malformed_input_consensus(self):
        """Test handling of malformed consensus input."""
        # Overwrite with malformed data
        malformed_consensus = {"wrong_structure": "invalid"}
        with open(self.state_dir / "brain_consensus.json", 'w') as f:
            json.dump(malformed_consensus, f)

        brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        consensus_state = brain.load_consensus_state()
        learning_state = brain.load_learning_state()

        # Should handle gracefully
        actions = brain.generate_policy_actions(consensus_state, learning_state)
        self.assertEqual(len(actions), 0)  # No actions from malformed data

    def test_21_malformed_input_learning(self):
        """Test handling of malformed learning input."""
        # Overwrite with malformed data
        malformed_learning = {"incorrect": "structure"}
        with open(self.state_dir / "brain_learning.json", 'w') as f:
            json.dump(malformed_learning, f)

        brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        consensus_state = brain.load_consensus_state()
        learning_state = brain.load_learning_state()

        # Should handle gracefully with defaults
        actions = brain.generate_policy_actions(consensus_state, learning_state)
        # Should still generate actions but with default weights
        self.assertIsInstance(actions, list)


class TestPolicyBrainV2EdgeCases(unittest.TestCase):
    """Edge case tests."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.test_dir) / "state"
        self.state_dir.mkdir()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_22_empty_recommendations(self):
        """Test handling of empty recommendations."""
        consensus_data = {"final_recommendations": []}
        learning_data = {"weights": {}, "issue_history": {}, "trend_metrics": {}}

        with open(self.state_dir / "brain_consensus.json", 'w') as f:
            json.dump(consensus_data, f)
        with open(self.state_dir / "brain_learning.json", 'w') as f:
            json.dump(learning_data, f)

        brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        success = brain.run()

        self.assertTrue(success)

        # Check output
        with open(self.state_dir / "brain_policy_v2.json", 'r') as f:
            output = json.load(f)

        self.assertEqual(len(output["actions"]), 0)

    def test_23_missing_optional_fields(self):
        """Test handling of missing optional fields in recommendations."""
        consensus_data = {
            "final_recommendations": [
                {
                    "type": "minimal-action",
                    "consensus_score": 0.5
                    # Missing: agents, triggers, next_step
                }
            ]
        }
        learning_data = {"weights": {}, "issue_history": {}, "trend_metrics": {}}

        with open(self.state_dir / "brain_consensus.json", 'w') as f:
            json.dump(consensus_data, f)
        with open(self.state_dir / "brain_learning.json", 'w') as f:
            json.dump(learning_data, f)

        brain = PolicyBrainV2(state_dir=self.state_dir, verbose=False)
        success = brain.run()

        self.assertTrue(success)

        # Should handle missing fields with defaults
        with open(self.state_dir / "brain_policy_v2.json", 'r') as f:
            output = json.load(f)

        self.assertEqual(len(output["actions"]), 1)
        action = output["actions"][0]
        self.assertEqual(action["type"], "minimal-action")
        self.assertIsInstance(action["source_agents"], list)
        self.assertIsInstance(action["triggers"], list)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyBrainV2Basic))
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyBrainV2WeightComputation))
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyBrainV2PriorityComputation))
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyBrainV2Integration))
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyBrainV2EdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
