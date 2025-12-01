# Batch 23 Implementation Transcript - Part 7A: Test Suite (Part 2/3)

## File: tests/integration/test_learning_engine.py (Lines 351-450)

```python
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

        self.assertEqual(root_files_before, root_files_after)
```

*Continued in Part 7B...*
