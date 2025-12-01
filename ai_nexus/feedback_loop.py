"""
Feedback Loop Closure System v1.0

Automatically generates kernel updates from performance metrics.
Addresses the critical gap: PERFORMANCE METRICS NOT FEEDING BACK TO KERNELS.

This module implements the missing link between:
    Decisions → Actions → Outcomes → Lessons → Kernel Updates

Features:
- Analyzes performance trends to extract lessons
- Detects successful and failed strategies
- Generates kernel updates based on outcomes
- Correlates decisions with their results
- Supports continuous learning loop

Flow:
    1. Load performance metrics history
    2. Identify significant trends (improvements/degradations)
    3. Correlate with recent decisions in kernels
    4. Generate lessons learned (failed_paths for degradations, decisions for improvements)
    5. Apply updates to relevant kernels

API:
    loop = FeedbackLoopClosure()
    insights = loop.analyze_performance()
    updates = loop.generate_kernel_updates()
    result = loop.close_loop()

CLI:
    python -m ai_nexus.feedback_loop analyze
    python -m ai_nexus.feedback_loop generate
    python -m ai_nexus.feedback_loop close --dry-run
"""

import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.memory_kernels import load_kernel, append_kernel_update, list_kernels
from ai_nexus.spark_plug_types import KernelUpdate


class TrendDirection(Enum):
    """Direction of a metric trend"""
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class InsightType(Enum):
    """Type of performance insight"""
    SUCCESS_PATTERN = "success_pattern"      # Something is working well
    FAILURE_PATTERN = "failure_pattern"      # Something is not working
    CORRELATION = "correlation"              # Relationship between metrics
    ANOMALY = "anomaly"                      # Unusual behavior
    THRESHOLD_BREACH = "threshold_breach"    # Crossed important threshold


@dataclass
class MetricTrend:
    """Trend analysis for a single metric"""
    metric_name: str
    direction: TrendDirection
    change_pct: float
    current_value: float
    previous_value: float
    period_days: int
    significance: float  # 0-1 how significant the change is
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['direction'] = self.direction.value
        return data


@dataclass
class PerformanceInsight:
    """An insight derived from performance analysis"""
    insight_id: str
    insight_type: InsightType
    description: str
    metrics_involved: List[str]
    suggested_action: str
    confidence: float  # 0-1
    target_kernels: List[str]
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['insight_type'] = self.insight_type.value
        return data


@dataclass
class FeedbackLoopResult:
    """Result of feedback loop closure"""
    timestamp: str
    trends_analyzed: int
    insights_generated: int
    updates_created: int
    updates_applied: int
    kernels_updated: List[str]
    details: List[Dict[str, Any]]

    def to_dict(self) -> Dict:
        return asdict(self)


class FeedbackLoopClosure:
    """
    Closes the feedback loop between performance metrics and kernel learning.

    Monitors:
    - Alpha signal quality (edge, confidence)
    - Execution metrics (orders, sizes)
    - System health scores
    - Decision outcomes

    Updates:
    - risk_model_v2: Risk-related learnings
    - alpha_polymarket_core: Alpha generation learnings
    - trading_philosophy: Strategic learnings
    - system_health: Infrastructure learnings
    """

    # Metric-to-kernel mapping
    METRIC_KERNEL_MAP = {
        "edge": ["alpha_polymarket_core", "trading_philosophy"],
        "confidence": ["alpha_polymarket_core", "risk_model_v2"],
        "orders": ["risk_model_v2", "trading_philosophy"],
        "size_usd": ["risk_model_v2"],
        "selection_rate": ["alpha_polymarket_core"],
        "health_score": ["system_health"],
    }

    # Significance thresholds
    IMPROVEMENT_THRESHOLD = 0.15   # 15% improvement is significant
    DEGRADATION_THRESHOLD = -0.15  # 15% degradation is significant
    MIN_DATA_POINTS = 5            # Minimum data points for trend analysis

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.metrics_file = self.state_dir / "performance_metrics.jsonl"
        self.health_file = self.state_dir / "health_history.jsonl"
        self.feedback_log = self.state_dir / "feedback_loop_log.jsonl"

        # Insight counter
        self._insight_counter = 0

    # =========================================================================
    # Core Analysis Methods
    # =========================================================================

    def analyze_performance(
        self,
        days: int = 7,
        comparison_days: int = 7
    ) -> Tuple[List[MetricTrend], List[PerformanceInsight]]:
        """
        Analyze performance metrics for trends and insights.

        Args:
            days: Number of days to analyze for recent period
            comparison_days: Number of previous days to compare against

        Returns:
            Tuple of (trends, insights)
        """
        # Load metrics
        recent_metrics = self._load_metrics_for_period(days)
        previous_metrics = self._load_metrics_for_period(
            comparison_days,
            offset_days=days
        )

        if not recent_metrics:
            return [], []

        # Analyze trends
        trends = self._analyze_trends(recent_metrics, previous_metrics)

        # Generate insights from trends
        insights = self._generate_insights(trends, recent_metrics)

        return trends, insights

    def _analyze_trends(
        self,
        recent: List[Dict],
        previous: List[Dict]
    ) -> List[MetricTrend]:
        """Analyze metric trends between two periods"""
        trends = []

        # Metrics to analyze
        metric_paths = [
            ("execution_plan.avg_confidence", "confidence"),
            ("alpha_signals.avg_edge", "edge"),
            ("alpha_signals.selection_rate", "selection_rate"),
            ("execution_plan.total_orders", "orders"),
            ("execution_plan.total_size_usd", "size_usd"),
        ]

        for metric_path, metric_name in metric_paths:
            recent_values = self._extract_values(recent, metric_path)
            previous_values = self._extract_values(previous, metric_path)

            trend = self._compute_trend(metric_name, recent_values, previous_values)
            if trend:
                trends.append(trend)

        return trends

    def _compute_trend(
        self,
        metric_name: str,
        recent_values: List[float],
        previous_values: List[float]
    ) -> Optional[MetricTrend]:
        """Compute trend for a single metric"""
        if len(recent_values) < self.MIN_DATA_POINTS:
            return MetricTrend(
                metric_name=metric_name,
                direction=TrendDirection.INSUFFICIENT_DATA,
                change_pct=0,
                current_value=recent_values[-1] if recent_values else 0,
                previous_value=previous_values[-1] if previous_values else 0,
                period_days=len(recent_values),
                significance=0,
                context={"reason": "Insufficient data points"}
            )

        recent_avg = sum(recent_values) / len(recent_values)

        if previous_values:
            previous_avg = sum(previous_values) / len(previous_values)
        else:
            previous_avg = recent_avg

        if previous_avg == 0:
            change_pct = 0
        else:
            change_pct = (recent_avg - previous_avg) / abs(previous_avg)

        # Determine direction
        if change_pct >= self.IMPROVEMENT_THRESHOLD:
            direction = TrendDirection.IMPROVING
        elif change_pct <= self.DEGRADATION_THRESHOLD:
            direction = TrendDirection.DEGRADING
        else:
            direction = TrendDirection.STABLE

        # Compute significance (higher change = more significant)
        significance = min(1.0, abs(change_pct) / 0.5)  # Cap at 50% change

        return MetricTrend(
            metric_name=metric_name,
            direction=direction,
            change_pct=change_pct,
            current_value=recent_avg,
            previous_value=previous_avg,
            period_days=len(recent_values),
            significance=significance,
            context={
                "recent_samples": len(recent_values),
                "previous_samples": len(previous_values)
            }
        )

    def _generate_insights(
        self,
        trends: List[MetricTrend],
        recent_metrics: List[Dict]
    ) -> List[PerformanceInsight]:
        """Generate performance insights from trends"""
        insights = []

        for trend in trends:
            if trend.direction == TrendDirection.INSUFFICIENT_DATA:
                continue

            target_kernels = self.METRIC_KERNEL_MAP.get(trend.metric_name, ["trading_philosophy"])

            if trend.direction == TrendDirection.IMPROVING:
                insight = self._create_success_insight(trend, target_kernels)
                insights.append(insight)

            elif trend.direction == TrendDirection.DEGRADING:
                insight = self._create_failure_insight(trend, target_kernels)
                insights.append(insight)

        # Look for correlations between improving and degrading metrics
        improving = [t for t in trends if t.direction == TrendDirection.IMPROVING]
        degrading = [t for t in trends if t.direction == TrendDirection.DEGRADING]

        if improving and degrading:
            correlation_insight = self._create_correlation_insight(improving, degrading)
            if correlation_insight:
                insights.append(correlation_insight)

        return insights

    def _create_success_insight(
        self,
        trend: MetricTrend,
        target_kernels: List[str]
    ) -> PerformanceInsight:
        """Create insight for improving metric"""
        self._insight_counter += 1

        return PerformanceInsight(
            insight_id=f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._insight_counter}",
            insight_type=InsightType.SUCCESS_PATTERN,
            description=f"{trend.metric_name} improved by {trend.change_pct:.0%} "
                       f"({trend.previous_value:.3f} → {trend.current_value:.3f})",
            metrics_involved=[trend.metric_name],
            suggested_action=f"Continue current approach for {trend.metric_name}. "
                           f"Document what's working.",
            confidence=trend.significance,
            target_kernels=target_kernels,
            evidence={
                "trend": trend.to_dict(),
                "period_analyzed": f"{trend.period_days} days"
            }
        )

    def _create_failure_insight(
        self,
        trend: MetricTrend,
        target_kernels: List[str]
    ) -> PerformanceInsight:
        """Create insight for degrading metric"""
        self._insight_counter += 1

        return PerformanceInsight(
            insight_id=f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._insight_counter}",
            insight_type=InsightType.FAILURE_PATTERN,
            description=f"{trend.metric_name} degraded by {abs(trend.change_pct):.0%} "
                       f"({trend.previous_value:.3f} → {trend.current_value:.3f})",
            metrics_involved=[trend.metric_name],
            suggested_action=f"Investigate degradation in {trend.metric_name}. "
                           f"Review recent changes and decisions.",
            confidence=trend.significance,
            target_kernels=target_kernels,
            evidence={
                "trend": trend.to_dict(),
                "period_analyzed": f"{trend.period_days} days"
            }
        )

    def _create_correlation_insight(
        self,
        improving: List[MetricTrend],
        degrading: List[MetricTrend]
    ) -> Optional[PerformanceInsight]:
        """Create insight about metric correlations"""
        if not improving or not degrading:
            return None

        self._insight_counter += 1

        improving_names = [t.metric_name for t in improving]
        degrading_names = [t.metric_name for t in degrading]

        # Collect all target kernels
        all_kernels = set()
        for t in improving + degrading:
            kernels = self.METRIC_KERNEL_MAP.get(t.metric_name, [])
            all_kernels.update(kernels)

        return PerformanceInsight(
            insight_id=f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._insight_counter}",
            insight_type=InsightType.CORRELATION,
            description=f"Mixed performance: {', '.join(improving_names)} improving "
                       f"while {', '.join(degrading_names)} degrading",
            metrics_involved=improving_names + degrading_names,
            suggested_action="Investigate potential tradeoffs between improving "
                           "and degrading metrics. May need to rebalance priorities.",
            confidence=0.7,
            target_kernels=list(all_kernels) or ["trading_philosophy"],
            evidence={
                "improving": [t.to_dict() for t in improving],
                "degrading": [t.to_dict() for t in degrading]
            }
        )

    # =========================================================================
    # Kernel Update Generation
    # =========================================================================

    def generate_kernel_updates(
        self,
        insights: Optional[List[PerformanceInsight]] = None
    ) -> List[Tuple[str, KernelUpdate]]:
        """
        Generate kernel updates from performance insights.

        Returns list of (kernel_id, update) tuples.
        """
        if insights is None:
            _, insights = self.analyze_performance()

        updates = []

        for insight in insights:
            kernel_updates = self._insight_to_updates(insight)
            updates.extend(kernel_updates)

        return updates

    def _insight_to_updates(
        self,
        insight: PerformanceInsight
    ) -> List[Tuple[str, KernelUpdate]]:
        """Convert a performance insight to kernel updates"""
        updates = []

        for kernel_id in insight.target_kernels:
            # Verify kernel exists
            if load_kernel(kernel_id) is None:
                continue

            if insight.insight_type == InsightType.SUCCESS_PATTERN:
                # Add as a decision (what's working)
                update = KernelUpdate(
                    update_type="decision",
                    content={
                        "decision": f"Performance data shows: {insight.description}",
                        "rationale": f"Automated feedback loop analysis. {insight.suggested_action}",
                        "status": "approved"
                    },
                    source="feedback_loop_auto",
                    agent="feedback_loop"
                )
                updates.append((kernel_id, update))

            elif insight.insight_type == InsightType.FAILURE_PATTERN:
                # Add as a failed path (lesson learned)
                update = KernelUpdate(
                    update_type="failed_path",
                    content={
                        "attempt": "Recent operational approach",
                        "failure": insight.description,
                        "lesson": insight.suggested_action
                    },
                    source="feedback_loop_auto",
                    agent="feedback_loop"
                )
                updates.append((kernel_id, update))

            elif insight.insight_type == InsightType.CORRELATION:
                # Add as an open question
                update = KernelUpdate(
                    update_type="question",
                    content={
                        "question": f"Performance correlation detected: {insight.description}. "
                                   f"How should we address potential tradeoffs?"
                    },
                    source="feedback_loop_auto",
                    agent="feedback_loop"
                )
                updates.append((kernel_id, update))

            elif insight.insight_type in [InsightType.ANOMALY, InsightType.THRESHOLD_BREACH]:
                # Add as an open question requiring investigation
                update = KernelUpdate(
                    update_type="question",
                    content={
                        "question": f"Anomaly detected: {insight.description}. "
                                   f"Needs investigation."
                    },
                    source="feedback_loop_auto",
                    agent="feedback_loop"
                )
                updates.append((kernel_id, update))

        return updates

    # =========================================================================
    # Loop Closure
    # =========================================================================

    def close_loop(
        self,
        dry_run: bool = False,
        min_confidence: float = 0.5
    ) -> FeedbackLoopResult:
        """
        Close the feedback loop: analyze → generate → apply.

        This is the main entry point for automatic feedback loop closure.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        print("🔄 Closing feedback loop...")
        print("="*60)

        # Analyze performance
        print("\n📊 Analyzing performance trends...")
        trends, insights = self.analyze_performance()

        print(f"   Trends analyzed: {len(trends)}")
        print(f"   Insights generated: {len(insights)}")

        for trend in trends:
            emoji = {
                TrendDirection.IMPROVING: "📈",
                TrendDirection.DEGRADING: "📉",
                TrendDirection.STABLE: "➡️",
                TrendDirection.INSUFFICIENT_DATA: "❓"
            }.get(trend.direction, "?")
            print(f"   {emoji} {trend.metric_name}: {trend.change_pct:+.0%}")

        # Filter by confidence
        filtered_insights = [i for i in insights if i.confidence >= min_confidence]
        print(f"\n   Insights above {min_confidence:.0%} confidence: {len(filtered_insights)}")

        if not filtered_insights:
            print("\n✅ No significant insights requiring kernel updates")
            return FeedbackLoopResult(
                timestamp=timestamp,
                trends_analyzed=len(trends),
                insights_generated=len(insights),
                updates_created=0,
                updates_applied=0,
                kernels_updated=[],
                details=[]
            )

        # Generate updates
        print("\n📝 Generating kernel updates...")
        updates = self.generate_kernel_updates(filtered_insights)
        print(f"   Updates created: {len(updates)}")

        if dry_run:
            print("\n[DRY RUN] - No changes will be applied")
            return FeedbackLoopResult(
                timestamp=timestamp,
                trends_analyzed=len(trends),
                insights_generated=len(insights),
                updates_created=len(updates),
                updates_applied=0,
                kernels_updated=[],
                details=[{"dry_run": True, "would_apply": len(updates)}]
            )

        # Apply updates
        print("\n⚡ Applying updates to kernels...")
        applied_count = 0
        kernels_updated = set()
        details = []

        for kernel_id, update in updates:
            try:
                append_kernel_update(kernel_id, update)
                applied_count += 1
                kernels_updated.add(kernel_id)
                details.append({
                    "action": "applied",
                    "kernel": kernel_id,
                    "type": update.update_type
                })
                print(f"   ✓ Applied {update.update_type} to {kernel_id}")
            except Exception as e:
                details.append({
                    "action": "failed",
                    "kernel": kernel_id,
                    "error": str(e)
                })
                print(f"   ✗ Failed to apply to {kernel_id}: {e}")

        # Log the feedback loop execution
        self._log_feedback_loop(timestamp, trends, insights, updates, applied_count)

        result = FeedbackLoopResult(
            timestamp=timestamp,
            trends_analyzed=len(trends),
            insights_generated=len(insights),
            updates_created=len(updates),
            updates_applied=applied_count,
            kernels_updated=list(kernels_updated),
            details=details
        )

        print(f"\n✅ Feedback loop closed")
        print(f"   Kernels updated: {', '.join(kernels_updated) if kernels_updated else 'none'}")
        print("="*60)

        return result

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _load_metrics_for_period(
        self,
        days: int,
        offset_days: int = 0
    ) -> List[Dict]:
        """Load performance metrics for a time period"""
        if not self.metrics_file.exists():
            return []

        now = datetime.now(timezone.utc)
        end_date = now - timedelta(days=offset_days)
        start_date = end_date - timedelta(days=days)

        metrics = []

        try:
            with open(self.metrics_file) as f:
                for line in f:
                    try:
                        metric = json.loads(line)
                        ts = metric.get("timestamp", "")
                        if ts:
                            metric_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if start_date <= metric_dt <= end_date:
                                metrics.append(metric)
                    except:
                        continue
        except:
            pass

        return metrics

    def _extract_values(self, metrics: List[Dict], path: str) -> List[float]:
        """Extract values from metrics by path"""
        values = []

        for metric in metrics:
            value = metric
            for key in path.split("."):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break

            if value is not None:
                try:
                    values.append(float(value))
                except:
                    pass

        return values

    def _log_feedback_loop(
        self,
        timestamp: str,
        trends: List[MetricTrend],
        insights: List[PerformanceInsight],
        updates: List[Tuple[str, KernelUpdate]],
        applied_count: int
    ):
        """Log feedback loop execution"""
        try:
            self.feedback_log.parent.mkdir(parents=True, exist_ok=True)

            log_entry = {
                "timestamp": timestamp,
                "trends_count": len(trends),
                "insights_count": len(insights),
                "updates_count": len(updates),
                "applied_count": applied_count,
                "trends_summary": [
                    {"metric": t.metric_name, "direction": t.direction.value, "change": t.change_pct}
                    for t in trends
                ],
                "insights_summary": [
                    {"type": i.insight_type.value, "confidence": i.confidence}
                    for i in insights
                ]
            }

            with open(self.feedback_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except:
            pass


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Feedback Loop Closure System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze performance trends
  python -m ai_nexus.feedback_loop analyze

  # Generate kernel updates (dry run)
  python -m ai_nexus.feedback_loop generate --dry-run

  # Close the feedback loop (analyze + generate + apply)
  python -m ai_nexus.feedback_loop close

  # Close loop with custom parameters
  python -m ai_nexus.feedback_loop close --days 14 --min-confidence 0.7
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze performance trends")
    analyze_parser.add_argument("--days", type=int, default=7, help="Days to analyze")
    analyze_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate kernel updates")
    generate_parser.add_argument("--days", type=int, default=7, help="Days to analyze")
    generate_parser.add_argument("--dry-run", action="store_true", help="Don't apply updates")
    generate_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Close command
    close_parser = subparsers.add_parser("close", help="Close the feedback loop")
    close_parser.add_argument("--days", type=int, default=7, help="Days to analyze")
    close_parser.add_argument("--dry-run", action="store_true", help="Don't apply updates")
    close_parser.add_argument("--min-confidence", type=float, default=0.5, help="Minimum confidence")
    close_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    loop = FeedbackLoopClosure()

    if args.command == "analyze":
        trends, insights = loop.analyze_performance(days=args.days)

        if args.json:
            print(json.dumps({
                "trends": [t.to_dict() for t in trends],
                "insights": [i.to_dict() for i in insights]
            }, indent=2))
        else:
            print(f"\n📊 Performance Analysis (last {args.days} days)")
            print("="*60)

            print("\n📈 Trends:")
            for trend in trends:
                emoji = {
                    TrendDirection.IMPROVING: "✅",
                    TrendDirection.DEGRADING: "❌",
                    TrendDirection.STABLE: "➡️",
                    TrendDirection.INSUFFICIENT_DATA: "❓"
                }.get(trend.direction, "?")
                print(f"   {emoji} {trend.metric_name}: {trend.change_pct:+.0%} "
                      f"(significance: {trend.significance:.0%})")

            if insights:
                print(f"\n💡 Insights ({len(insights)}):")
                for insight in insights:
                    type_emoji = {
                        InsightType.SUCCESS_PATTERN: "🎯",
                        InsightType.FAILURE_PATTERN: "⚠️",
                        InsightType.CORRELATION: "🔗",
                        InsightType.ANOMALY: "🔍"
                    }.get(insight.insight_type, "?")
                    print(f"\n   {type_emoji} [{insight.insight_type.value}]")
                    print(f"      {insight.description}")
                    print(f"      Targets: {', '.join(insight.target_kernels)}")
                    print(f"      Confidence: {insight.confidence:.0%}")

    elif args.command == "generate":
        trends, insights = loop.analyze_performance(days=args.days)
        updates = loop.generate_kernel_updates(insights)

        if args.json:
            print(json.dumps([
                {"kernel": k, "type": u.update_type, "content": u.content}
                for k, u in updates
            ], indent=2))
        else:
            print(f"\n📝 Generated Kernel Updates ({len(updates)})")
            print("="*60)

            for kernel_id, update in updates:
                print(f"\n   [{update.update_type}] → {kernel_id}")
                print(f"      Content: {json.dumps(update.content)[:100]}...")

            if args.dry_run:
                print("\n[DRY RUN] - Updates not applied")

    elif args.command == "close":
        result = loop.close_loop(
            dry_run=args.dry_run,
            min_confidence=args.min_confidence
        )

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
