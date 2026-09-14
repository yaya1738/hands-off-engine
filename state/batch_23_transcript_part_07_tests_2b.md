# Batch 23 Implementation Transcript - Part 7B: Test Suite (Part 3/3)

## File: tests/integration/test_learning_engine.py (Lines 451-end)

```python
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

        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)
        updated_state = engine.update()

        self.assertEqual(updated_state['run_count'], 101)
        self.assertGreaterEqual(len(updated_state['issue_history']), 1000)

    def test_13_recommendations_generation(self):
        """Test 13: Recommendations generation"""
        self.create_sample_consensus()

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)

        for i in range(5):
            learning_state = engine.update()

        recommendations = learning_state['recommendations']
        self.assertGreater(len(recommendations), 0)

    def test_14_malformed_existing_learning_state(self):
        """Test 14: Malformed existing learning state"""
        self.create_sample_consensus()

        learning_path = self.state_dir / "brain_learning.json"
        with open(learning_path, 'w') as f:
            f.write("{invalid json")

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)
        learning_state = engine.update()

        self.assertEqual(learning_state['run_count'], 1)

    def test_15_empty_consensus_issues(self):
        """Test 15: Empty consensus issues"""
        consensus = self.create_sample_consensus(num_issues=0)
        consensus['issues'] = []
        for agent_data in consensus['agents'].values():
            agent_data['issues'] = []

        consensus_path = self.state_dir / "brain_consensus.json"
        with open(consensus_path, 'w') as f:
            json.dump(consensus, f, indent=2)

        engine = LearningEngine(state_dir=str(self.state_dir), verbose=False)
        learning_state = engine.update()

        self.assertEqual(learning_state['run_count'], 1)
        self.assertEqual(len(learning_state['issue_history']), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

---

## Test Results

```bash
$ python3 tests/integration/test_learning_engine.py
```

**Output:**
```
test_01_missing_consensus_file ... ok
test_02_malformed_json ... ok
test_03_new_learning_file_creation ... ok
test_04_updating_existing_learning_file ... ok
test_05_issue_recurrence_tracking ... ok
test_06_stable_hashing_correctness ... ok
test_07_agent_performance_scoring ... ok
test_08_learning_weight_normalization ... ok
test_09_trend_calculation ... ok
test_10_cli_invocation ... ok
test_11_file_isolation ... ok
test_12_large_history_performance ... ok
test_13_recommendations_generation ... ok
test_14_malformed_existing_learning_state ... ok
test_15_empty_consensus_issues ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.141s

OK
```

**Status:** ✅ All 15 tests passed

*Continued in Part 8 with documentation...*
