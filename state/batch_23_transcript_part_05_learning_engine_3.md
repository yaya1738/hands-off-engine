# Batch 23 Implementation Transcript - Part 5: Learning Engine (Part 3/3)

## File: ai/ho_learning_engine.py (Lines 551-end)

```python
    def generate_recommendations(
        self,
        learning_state: Dict[str, Any]
    ) -> None:
        """Generate actionable recommendations based on learning state."""
        self.log("Generating recommendations")

        recommendations = []

        # Check for recurring critical issues
        critical_issues = [
            issue for issue in learning_state['issue_history']
            if issue['occurrences'] >= 3 and issue['severity'] == 'high'
        ]

        if critical_issues:
            recommendations.append(
                f"Critical issue recurring {len(critical_issues)} time(s): address immediately"
            )

        # Check for low-performing agents
        agent_perf = learning_state['agent_performance']
        low_performers = [
            name for name, perf in agent_perf.items()
            if perf['accuracy'] < 0.6 and perf['runs'] >= 3
        ]

        if low_performers:
            for agent in low_performers:
                recommendations.append(
                    f"{agent} shows lower agreement stability — reduce weight"
                )

        # Check error rate trend
        trends = learning_state['trend_metrics']
        if trends['error_rate_mean'] > 0.15:
            recommendations.append(
                "High error rate detected — review agent configurations"
            )

        # Check consensus trend
        if trends['consensus_trend'] == 'down':
            recommendations.append(
                "Consensus quality declining — investigate agent disagreements"
            )

        if not recommendations:
            recommendations.append("System operating within normal parameters")

        learning_state['recommendations'] = recommendations

        for i, rec in enumerate(recommendations, 1):
            self.log(f"  {i}. {rec}")

    def update(self) -> Dict[str, Any]:
        """Main update cycle: process consensus and update learning state."""
        self.log("=" * 60)
        self.log("Starting learning engine update cycle")
        self.log("=" * 60)

        # Load inputs
        consensus = self.load_consensus()
        learning_state = self.load_learning_state()

        # Initialize if needed
        if learning_state is None:
            learning_state = self.initialize_learning_state()

        # Increment run count
        learning_state['run_count'] += 1
        learning_state['generated_at'] = datetime.utcnow().isoformat() + "Z"

        self.log(f"Processing run #{learning_state['run_count']}")

        # Update learning state
        self.update_issue_history(learning_state, consensus)
        self.update_agent_performance(learning_state, consensus)
        self.calculate_learning_weights(learning_state)
        self.calculate_trend_metrics(learning_state, consensus)
        self.generate_recommendations(learning_state)

        # Save updated state
        self.save_learning_state(learning_state)

        self.log("=" * 60)
        self.log("Learning engine update complete")
        self.log("=" * 60)

        return learning_state

    def save_learning_state(self, learning_state: Dict[str, Any]) -> None:
        """Save learning state to disk."""
        self.log(f"Saving learning state to {self.learning_path}")

        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

        with open(self.learning_path, 'w') as f:
            json.dump(learning_state, f, indent=2)

        self.log(f"Saved learning state (run {learning_state['run_count']})")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Hands-Off Learning Engine (Batch 23)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ai/ho_learning_engine.py
  python3 ai/ho_learning_engine.py --verbose
  python3 ai/ho_learning_engine.py --state-dir /custom/path
        """
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--state-dir',
        default='state',
        help='Directory containing state files (default: state)'
    )

    args = parser.parse_args()

    try:
        engine = LearningEngine(
            state_dir=args.state_dir,
            verbose=args.verbose
        )

        learning_state = engine.update()

        # Print summary
        print("\n" + "=" * 60)
        print("LEARNING ENGINE SUMMARY")
        print("=" * 60)
        print(f"Run count: {learning_state['run_count']}")
        print(f"Total issues tracked: {len(learning_state['issue_history'])}")
        print(f"Active agents: {len(learning_state['agent_performance'])}")
        print()
        print("Learning weights:")
        for agent, weight in learning_state['learning_weights'].items():
            print(f"  {agent}: {weight:.2f}")
        print()
        print("Recommendations:")
        for i, rec in enumerate(learning_state['recommendations'], 1):
            print(f"  {i}. {rec}")
        print("=" * 60)

        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

**Status:** ✅ Learning engine implementation complete (850+ lines)

*Continued in Part 6 with test suite...*
