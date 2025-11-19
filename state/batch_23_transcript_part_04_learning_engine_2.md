# Batch 23 Implementation Transcript - Part 4: Learning Engine (Part 2/2)

## File: ai/ho_learning_engine.py (Lines 251-550)

```python
    def calculate_agent_accuracy(
        self,
        agent_name: str,
        agent_data: Dict[str, Any],
        consensus: Dict[str, Any]
    ) -> float:
        """
        Calculate accuracy score for an agent.

        Accuracy is based on:
        1. Agreement with consensus severity
        2. Overlap of recommendations with consensus

        Args:
            agent_name: Name of the agent
            agent_data: Agent-specific data from consensus
            consensus: Overall consensus data

        Returns:
            Accuracy score between 0.0 and 1.0
        """
        agent_issues = agent_data.get('issues', [])
        consensus_issues = consensus.get('issues', [])

        if not consensus_issues:
            return 1.0  # No issues to compare

        # Compare severity alignment
        severity_matches = 0
        total_comparisons = 0

        for cons_issue in consensus_issues:
            cons_severity = cons_issue.get('severity', 'unknown')
            cons_msg = cons_issue.get('message', '')

            for agent_issue in agent_issues:
                agent_msg = agent_issue.get('message', '')
                if self._message_similarity(cons_msg, agent_msg) > 0.7:
                    agent_severity = agent_issue.get('severity', 'unknown')
                    if agent_severity == cons_severity:
                        severity_matches += 1
                    total_comparisons += 1
                    break

        if total_comparisons == 0:
            accuracy = 0.5
        else:
            accuracy = severity_matches / total_comparisons

        return accuracy

    def _message_similarity(self, msg1: str, msg2: str) -> float:
        """Calculate simple similarity between two messages."""
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def update_agent_performance(
        self,
        learning_state: Dict[str, Any],
        consensus: Dict[str, Any]
    ) -> None:
        """Update agent performance metrics."""
        self.log("Updating agent performance")

        agents = consensus.get('agents', {})

        for agent_name, agent_data in agents.items():
            if agent_name not in learning_state['agent_performance']:
                learning_state['agent_performance'][agent_name] = {
                    "accuracy": 0.0,
                    "runs": 0,
                    "total_accuracy": 0.0
                }

            perf = learning_state['agent_performance'][agent_name]

            # Calculate accuracy for this run
            accuracy = self.calculate_agent_accuracy(
                agent_name, agent_data, consensus
            )

            # Update rolling metrics
            perf['runs'] += 1
            perf['total_accuracy'] += accuracy
            perf['accuracy'] = perf['total_accuracy'] / perf['runs']

            self.log(f"  {agent_name}: accuracy={perf['accuracy']:.3f}, runs={perf['runs']}")

    def calculate_learning_weights(
        self,
        learning_state: Dict[str, Any]
    ) -> None:
        """Calculate learning weights for each agent based on performance."""
        self.log("Calculating learning weights")

        agent_perf = learning_state['agent_performance']

        if not agent_perf:
            self.log("  No agent performance data available")
            return

        # Calculate weights based on accuracy
        weights = {}
        total_accuracy = sum(
            perf['accuracy'] for perf in agent_perf.values()
        )

        if total_accuracy > 0:
            for agent_name, perf in agent_perf.items():
                weight = perf['accuracy'] / total_accuracy
                weights[agent_name] = round(weight, 2)
        else:
            # Equal weights if no accuracy data
            equal_weight = 1.0 / len(agent_perf)
            for agent_name in agent_perf.keys():
                weights[agent_name] = round(equal_weight, 2)

        # Normalize to ensure sum = 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            for agent_name in weights:
                weights[agent_name] = round(weights[agent_name] / total_weight, 2)

        learning_state['learning_weights'] = weights

        self.log(f"  Weights: {weights}")

    def calculate_trend_metrics(
        self,
        learning_state: Dict[str, Any],
        consensus: Dict[str, Any]
    ) -> None:
        """Calculate trend metrics over time."""
        self.log("Calculating trend metrics")

        issues = consensus.get('issues', [])
        total_issues = len(issues)

        # Calculate error rate
        high_severity_count = sum(
            1 for issue in issues
            if issue.get('severity') == 'high'
        )
        error_rate = high_severity_count / total_issues if total_issues > 0 else 0.0

        # Calculate consensus score
        consensus_scores = [
            issue.get('confidence', 0.0) for issue in issues
        ]
        consensus_mean = (
            sum(consensus_scores) / len(consensus_scores)
            if consensus_scores else 0.0
        )

        # Update trend metrics
        trends = learning_state['trend_metrics']

        # Simple running average
        run_count = learning_state['run_count']
        if run_count > 0:
            alpha = 1.0 / (run_count + 1)
            trends['error_rate_mean'] = (
                (1 - alpha) * trends['error_rate_mean'] + alpha * error_rate
            )
            trends['consensus_mean'] = (
                (1 - alpha) * trends['consensus_mean'] + alpha * consensus_mean
            )
        else:
            trends['error_rate_mean'] = error_rate
            trends['consensus_mean'] = consensus_mean

        # Determine trend direction
        if run_count > 0:
            if consensus_mean > trends['consensus_mean'] * 1.05:
                trends['consensus_trend'] = "up"
            elif consensus_mean < trends['consensus_mean'] * 0.95:
                trends['consensus_trend'] = "down"
            else:
                trends['consensus_trend'] = "flat"
        else:
            trends['consensus_trend'] = "flat"

        trends['error_rate_std'] = round(error_rate * 0.1, 2)
```

*Continued in Part 5...*
