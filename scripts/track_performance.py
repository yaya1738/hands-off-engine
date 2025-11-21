#!/usr/bin/env python3
"""
Performance Tracker for Hands-Off Engine

Logs pipeline execution metrics over time to track:
- Number of orders generated
- Position sizes
- Safety check rejection rates
- Edge and confidence distributions
- System health trends
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


class PerformanceTracker:
    """Track and log pipeline performance metrics"""

    def __init__(self, metrics_file='state/performance_metrics.jsonl'):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

    def collect_metrics(self):
        """Collect current metrics from execution plan and alpha signals"""
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'execution_plan': {},
            'alpha_signals': {},
            'health': {}
        }

        # Execution plan metrics
        plan_file = Path('executor/execution_plan.json')
        if plan_file.exists():
            with open(plan_file) as f:
                plan = json.load(f)

            metrics['execution_plan'] = {
                'total_orders': plan.get('total_orders', 0),
                'total_size_usd': plan.get('total_size_usd', 0),
                'dryrun': plan.get('dryrun', True),
                'avg_order_size': (
                    plan.get('total_size_usd', 0) / plan.get('total_orders', 1)
                    if plan.get('total_orders', 0) > 0 else 0
                ),
                'plan_age_minutes': self._get_age_minutes(plan.get('timestamp'))
            }

            # Extract order details
            orders = plan.get('orders', [])
            if orders:
                confidences = [o.get('confidence', 0) for o in orders]
                metrics['execution_plan'].update({
                    'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
                    'min_confidence': min(confidences) if confidences else 0,
                    'max_confidence': max(confidences) if confidences else 0
                })

        # Alpha signals metrics
        model_file = Path('state/polymarket-model.json')
        if model_file.exists():
            with open(model_file) as f:
                model = json.load(f)

            markets = model.get('markets', [])
            edges = [m.get('model_edge', 0) for m in markets]
            confidences = [m.get('model_confidence', 0) for m in markets]

            metrics['alpha_signals'] = {
                'total_analyzed': model.get('total_markets_analyzed', 0),
                'total_selected': model.get('markets_selected', 0),
                'selection_rate': (
                    model.get('markets_selected', 0) / model.get('total_markets_analyzed', 1)
                    if model.get('total_markets_analyzed', 0) > 0 else 0
                ),
                'avg_edge': sum(edges) / len(edges) if edges else 0,
                'max_edge': max(edges) if edges else 0,
                'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'signals_age_minutes': self._get_age_minutes(model.get('generated_at'))
            }

        # Health metrics
        metrics['health'] = {
            'plan_exists': plan_file.exists(),
            'signals_exist': model_file.exists(),
            'plan_fresh': metrics['execution_plan'].get('plan_age_minutes', 999) < 120,
            'signals_fresh': metrics['alpha_signals'].get('signals_age_minutes', 999) < 120
        }

        return metrics

    def _get_age_minutes(self, timestamp_str):
        """Calculate age in minutes from ISO timestamp"""
        if not timestamp_str:
            return 999999

        try:
            ts_clean = timestamp_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(ts_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_mins = (datetime.now(timezone.utc) - dt).total_seconds() / 60
            return age_mins
        except:
            return 999999

    def log_metrics(self, metrics):
        """Append metrics to JSONL file"""
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')

    def get_recent_metrics(self, hours=24):
        """Get metrics from last N hours"""
        if not self.metrics_file.exists():
            return []

        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        recent = []

        with open(self.metrics_file) as f:
            for line in f:
                try:
                    metric = json.loads(line)
                    ts = datetime.fromisoformat(metric['timestamp'])
                    if ts.timestamp() >= cutoff:
                        recent.append(metric)
                except:
                    continue

        return recent

    def print_summary(self, hours=24):
        """Print summary of recent metrics"""
        metrics = self.get_recent_metrics(hours)

        if not metrics:
            print(f"No metrics in last {hours} hours")
            return

        print(f"\n📊 Performance Summary (last {hours} hours)")
        print("=" * 60)
        print(f"Total runs: {len(metrics)}")

        # Execution plan stats
        total_orders = sum(m['execution_plan'].get('total_orders', 0) for m in metrics)
        total_size = sum(m['execution_plan'].get('total_size_usd', 0) for m in metrics)

        print(f"\n🎯 Execution:")
        print(f"  Total orders planned: {total_orders}")
        print(f"  Total size: ${total_size:.2f}")
        print(f"  Avg orders per run: {total_orders / len(metrics):.1f}")

        # Alpha signal stats
        avg_edge = sum(m['alpha_signals'].get('avg_edge', 0) for m in metrics) / len(metrics)
        avg_selection = sum(m['alpha_signals'].get('selection_rate', 0) for m in metrics) / len(metrics)

        print(f"\n📈 Alpha Signals:")
        print(f"  Avg edge: {avg_edge * 100:.1f}%")
        print(f"  Avg selection rate: {avg_selection * 100:.1f}%")

        # Health stats
        health_rate = sum(
            1 for m in metrics
            if m['health'].get('plan_fresh') and m['health'].get('signals_fresh')
        ) / len(metrics)

        print(f"\n💚 Health:")
        print(f"  Healthy runs: {health_rate * 100:.0f}%")


def main():
    tracker = PerformanceTracker()

    # Collect and log metrics
    metrics = tracker.collect_metrics()
    tracker.log_metrics(metrics)

    print("✓ Metrics logged")
    print(f"  Orders: {metrics['execution_plan'].get('total_orders', 0)}")
    print(f"  Size: ${metrics['execution_plan'].get('total_size_usd', 0):.2f}")
    print(f"  Signals: {metrics['alpha_signals'].get('total_selected', 0)} selected")

    # Print summary if requested
    if '--summary' in sys.argv:
        hours = 24
        if '--hours' in sys.argv:
            idx = sys.argv.index('--hours')
            if idx + 1 < len(sys.argv):
                hours = int(sys.argv[idx + 1])
        tracker.print_summary(hours)


if __name__ == '__main__':
    main()
