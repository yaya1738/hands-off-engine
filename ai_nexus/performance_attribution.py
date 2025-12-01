"""
Performance Attribution System v1.0

Links decisions to their outcomes to understand what's actually working.
Addresses the gap: NO DECISION-TO-OUTCOME ATTRIBUTION.

Features:
- Tracks decisions with their outcomes
- Correlates kernel decisions with performance changes
- Identifies high-impact and low-impact decisions
- Generates decision effectiveness reports
- Supports learning from both successes and failures

Flow:
    1. Record decision when made (with expected outcome)
    2. Monitor performance after decision
    3. Attribute performance changes to decisions
    4. Update decision confidence based on outcomes
    5. Feed learnings back to kernels

API:
    attribution = PerformanceAttribution()
    attribution.record_decision(decision, expected_outcome)
    attribution.attribute_outcomes()
    report = attribution.generate_effectiveness_report()

CLI:
    python -m ai_nexus.performance_attribution record --decision "..." --expected "..."
    python -m ai_nexus.performance_attribution attribute
    python -m ai_nexus.performance_attribution report
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


class OutcomeType(Enum):
    """Types of decision outcomes"""
    POSITIVE = "positive"         # Better than expected
    NEUTRAL = "neutral"           # As expected
    NEGATIVE = "negative"         # Worse than expected
    UNKNOWN = "unknown"           # Cannot determine


class DecisionCategory(Enum):
    """Categories of decisions"""
    RISK = "risk"
    ALPHA = "alpha"
    STRATEGY = "strategy"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


@dataclass
class TrackedDecision:
    """A decision being tracked for attribution"""
    decision_id: str
    decision_text: str
    category: DecisionCategory
    kernel_id: str
    made_at: str
    expected_outcome: str
    metrics_at_decision: Dict[str, float]
    outcome: Optional[OutcomeType] = None
    outcome_measured_at: Optional[str] = None
    actual_outcome: Optional[str] = None
    metrics_after: Optional[Dict[str, float]] = None
    impact_score: Optional[float] = None
    attribution_confidence: float = 0.0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['category'] = self.category.value
        if self.outcome:
            data['outcome'] = self.outcome.value
        return data


@dataclass
class AttributionReport:
    """Decision attribution report"""
    timestamp: str
    period_days: int
    decisions_tracked: int
    decisions_attributed: int
    high_impact_decisions: List[Dict[str, Any]]
    low_impact_decisions: List[Dict[str, Any]]
    category_effectiveness: Dict[str, float]
    kernel_effectiveness: Dict[str, float]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class PerformanceAttribution:
    """
    Links decisions to their performance outcomes.

    Tracks:
    - When decisions are made
    - What metrics looked like at decision time
    - How metrics changed after decision
    - Whether the decision achieved its expected outcome
    """

    # Attribution windows
    SHORT_TERM_DAYS = 3      # Quick impact assessment
    MEDIUM_TERM_DAYS = 7     # Standard attribution window
    LONG_TERM_DAYS = 30      # Long-term impact

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.decisions_file = self.state_dir / "tracked_decisions.jsonl"
        self.metrics_file = self.state_dir / "performance_metrics.jsonl"

    # =========================================================================
    # Decision Recording
    # =========================================================================

    def record_decision(
        self,
        decision_text: str,
        expected_outcome: str,
        kernel_id: str,
        category: Optional[DecisionCategory] = None
    ) -> TrackedDecision:
        """
        Record a decision for attribution tracking.

        Args:
            decision_text: The decision that was made
            expected_outcome: What outcome is expected
            kernel_id: Which kernel this decision came from
            category: Decision category (auto-detected if not provided)
        """
        # Auto-detect category if not provided
        if category is None:
            category = self._detect_category(decision_text, kernel_id)

        # Get current metrics
        current_metrics = self._get_current_metrics()

        # Create tracked decision
        decision = TrackedDecision(
            decision_id=f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(decision_text) % 10000:04d}",
            decision_text=decision_text,
            category=category,
            kernel_id=kernel_id,
            made_at=datetime.now(timezone.utc).isoformat(),
            expected_outcome=expected_outcome,
            metrics_at_decision=current_metrics
        )

        # Save decision
        self._save_decision(decision)

        return decision

    def _detect_category(self, decision_text: str, kernel_id: str) -> DecisionCategory:
        """Auto-detect decision category"""
        text_lower = decision_text.lower()

        if kernel_id == "risk_model_v2" or any(word in text_lower for word in ["risk", "kelly", "sizing", "position"]):
            return DecisionCategory.RISK
        elif kernel_id == "alpha_polymarket_core" or any(word in text_lower for word in ["alpha", "edge", "signal", "market"]):
            return DecisionCategory.ALPHA
        elif kernel_id == "system_health" or any(word in text_lower for word in ["system", "health", "infra", "monitor"]):
            return DecisionCategory.INFRASTRUCTURE
        elif any(word in text_lower for word in ["strategy", "approach", "philosophy"]):
            return DecisionCategory.STRATEGY
        else:
            return DecisionCategory.OTHER

    def _get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics"""
        metrics = {}

        if not self.metrics_file.exists():
            return metrics

        # Get most recent metrics entry
        try:
            with open(self.metrics_file) as f:
                lines = f.readlines()
                if lines:
                    latest = json.loads(lines[-1])

                    # Extract key metrics
                    exec_plan = latest.get("execution_plan", {})
                    alpha = latest.get("alpha_signals", {})

                    metrics = {
                        "total_orders": exec_plan.get("total_orders", 0),
                        "total_size_usd": exec_plan.get("total_size_usd", 0),
                        "avg_confidence": exec_plan.get("avg_confidence", 0),
                        "avg_edge": alpha.get("avg_edge", 0),
                        "selection_rate": alpha.get("selection_rate", 0)
                    }
        except:
            pass

        return metrics

    def _save_decision(self, decision: TrackedDecision):
        """Save tracked decision"""
        try:
            self.decisions_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.decisions_file, 'a') as f:
                f.write(json.dumps(decision.to_dict()) + '\n')
        except:
            pass

    # =========================================================================
    # Attribution Analysis
    # =========================================================================

    def attribute_outcomes(
        self,
        attribution_window_days: int = MEDIUM_TERM_DAYS
    ) -> List[TrackedDecision]:
        """
        Attribute performance outcomes to tracked decisions.

        Analyzes decisions made within the attribution window
        and correlates with performance changes.
        """
        decisions = self._load_decisions_needing_attribution(attribution_window_days)

        if not decisions:
            return []

        attributed = []

        for decision in decisions:
            # Skip if already attributed
            if decision.outcome is not None:
                continue

            # Get metrics after decision
            metrics_after = self._get_metrics_after(decision.made_at, attribution_window_days)

            if not metrics_after:
                continue

            # Calculate impact
            impact, outcome = self._calculate_impact(
                decision.metrics_at_decision,
                metrics_after,
                decision.expected_outcome
            )

            # Update decision
            decision.outcome = outcome
            decision.outcome_measured_at = datetime.now(timezone.utc).isoformat()
            decision.metrics_after = metrics_after
            decision.impact_score = impact
            decision.attribution_confidence = self._calculate_attribution_confidence(decision)

            attributed.append(decision)

            # Update stored decision
            self._update_decision(decision)

        return attributed

    def _load_decisions_needing_attribution(
        self,
        window_days: int
    ) -> List[TrackedDecision]:
        """Load decisions that need attribution"""
        if not self.decisions_file.exists():
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        decisions = []

        try:
            with open(self.decisions_file) as f:
                for line in f:
                    try:
                        data = json.loads(line)

                        # Parse datetime
                        made_at = datetime.fromisoformat(data['made_at'].replace("Z", "+00:00"))

                        # Only include decisions within window that haven't been attributed
                        if made_at >= cutoff and data.get('outcome') is None:
                            # Convert back to TrackedDecision
                            data['category'] = DecisionCategory(data['category'])
                            if data.get('outcome'):
                                data['outcome'] = OutcomeType(data['outcome'])
                            decisions.append(TrackedDecision(**data))
                    except:
                        continue
        except:
            pass

        return decisions

    def _get_metrics_after(self, decision_time: str, window_days: int) -> Dict[str, float]:
        """Get average metrics after a decision"""
        if not self.metrics_file.exists():
            return {}

        try:
            decision_dt = datetime.fromisoformat(decision_time.replace("Z", "+00:00"))
            end_dt = decision_dt + timedelta(days=window_days)

            metrics_values = defaultdict(list)

            with open(self.metrics_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        ts = entry.get("timestamp", "")
                        if ts:
                            entry_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if decision_dt < entry_dt <= end_dt:
                                exec_plan = entry.get("execution_plan", {})
                                alpha = entry.get("alpha_signals", {})

                                for key, val in [
                                    ("total_orders", exec_plan.get("total_orders")),
                                    ("total_size_usd", exec_plan.get("total_size_usd")),
                                    ("avg_confidence", exec_plan.get("avg_confidence")),
                                    ("avg_edge", alpha.get("avg_edge")),
                                    ("selection_rate", alpha.get("selection_rate"))
                                ]:
                                    if val is not None:
                                        metrics_values[key].append(val)
                    except:
                        continue

            # Calculate averages
            return {
                key: sum(vals) / len(vals)
                for key, vals in metrics_values.items()
                if vals
            }
        except:
            return {}

    def _calculate_impact(
        self,
        metrics_before: Dict[str, float],
        metrics_after: Dict[str, float],
        expected_outcome: str
    ) -> Tuple[float, OutcomeType]:
        """
        Calculate the impact of a decision.

        Returns (impact_score, outcome_type)
        """
        if not metrics_before or not metrics_after:
            return 0.0, OutcomeType.UNKNOWN

        # Calculate changes for each metric
        changes = {}
        for key in metrics_before:
            if key in metrics_after:
                before = metrics_before[key]
                after = metrics_after[key]
                if before != 0:
                    changes[key] = (after - before) / abs(before)
                else:
                    changes[key] = 0

        if not changes:
            return 0.0, OutcomeType.UNKNOWN

        # Overall impact is weighted average of changes
        # Higher weight for edge and confidence as primary indicators
        weights = {
            "avg_edge": 0.3,
            "avg_confidence": 0.2,
            "selection_rate": 0.2,
            "total_orders": 0.15,
            "total_size_usd": 0.15
        }

        total_weight = 0
        weighted_change = 0

        for key, change in changes.items():
            weight = weights.get(key, 0.1)
            weighted_change += change * weight
            total_weight += weight

        impact_score = weighted_change / total_weight if total_weight > 0 else 0

        # Determine outcome based on impact
        if impact_score > 0.1:
            outcome = OutcomeType.POSITIVE
        elif impact_score < -0.1:
            outcome = OutcomeType.NEGATIVE
        else:
            outcome = OutcomeType.NEUTRAL

        return impact_score, outcome

    def _calculate_attribution_confidence(self, decision: TrackedDecision) -> float:
        """
        Calculate confidence in the attribution.

        Higher confidence when:
        - More data points available
        - Larger metric changes
        - Clear correlation with decision timing
        """
        confidence = 0.5  # Base confidence

        # More metrics = higher confidence
        if decision.metrics_at_decision and len(decision.metrics_at_decision) >= 4:
            confidence += 0.1
        if decision.metrics_after and len(decision.metrics_after) >= 4:
            confidence += 0.1

        # Larger impact = higher confidence (clearer signal)
        if decision.impact_score is not None:
            if abs(decision.impact_score) > 0.2:
                confidence += 0.2
            elif abs(decision.impact_score) > 0.1:
                confidence += 0.1

        return min(1.0, confidence)

    def _update_decision(self, decision: TrackedDecision):
        """Update a decision in the file"""
        if not self.decisions_file.exists():
            return

        # Read all decisions
        decisions = []
        try:
            with open(self.decisions_file) as f:
                for line in f:
                    try:
                        decisions.append(json.loads(line))
                    except:
                        continue
        except:
            return

        # Update the matching decision
        for i, dec in enumerate(decisions):
            if dec.get("decision_id") == decision.decision_id:
                decisions[i] = decision.to_dict()
                break

        # Rewrite file
        try:
            with open(self.decisions_file, 'w') as f:
                for dec in decisions:
                    f.write(json.dumps(dec) + '\n')
        except:
            pass

    # =========================================================================
    # Reporting
    # =========================================================================

    def generate_effectiveness_report(
        self,
        days: int = 30
    ) -> AttributionReport:
        """Generate decision effectiveness report"""
        decisions = self._load_all_decisions(days)

        if not decisions:
            return AttributionReport(
                timestamp=datetime.now(timezone.utc).isoformat(),
                period_days=days,
                decisions_tracked=0,
                decisions_attributed=0,
                high_impact_decisions=[],
                low_impact_decisions=[],
                category_effectiveness={},
                kernel_effectiveness={},
                recommendations=["No decisions tracked yet. Start recording decisions."]
            )

        attributed = [d for d in decisions if d.outcome is not None]

        # High impact decisions (positive)
        high_impact = sorted(
            [d for d in attributed if d.impact_score and d.impact_score > 0],
            key=lambda x: x.impact_score,
            reverse=True
        )[:5]

        # Low impact decisions (negative)
        low_impact = sorted(
            [d for d in attributed if d.impact_score and d.impact_score < 0],
            key=lambda x: x.impact_score
        )[:5]

        # Category effectiveness
        category_outcomes = defaultdict(list)
        for d in attributed:
            if d.impact_score is not None:
                category_outcomes[d.category.value].append(d.impact_score)

        category_effectiveness = {
            cat: sum(scores) / len(scores) if scores else 0
            for cat, scores in category_outcomes.items()
        }

        # Kernel effectiveness
        kernel_outcomes = defaultdict(list)
        for d in attributed:
            if d.impact_score is not None:
                kernel_outcomes[d.kernel_id].append(d.impact_score)

        kernel_effectiveness = {
            kernel: sum(scores) / len(scores) if scores else 0
            for kernel, scores in kernel_outcomes.items()
        }

        # Recommendations
        recommendations = []

        if high_impact:
            recommendations.append(
                f"Continue approaches from high-impact decisions "
                f"(best: {high_impact[0].decision_text[:50]}...)"
            )

        if low_impact:
            recommendations.append(
                f"Review and reconsider low-impact decisions "
                f"(worst: {low_impact[0].decision_text[:50]}...)"
            )

        # Category-specific recommendations
        for cat, effectiveness in sorted(category_effectiveness.items(), key=lambda x: x[1]):
            if effectiveness < -0.1:
                recommendations.append(f"Review {cat} decisions - showing negative impact")

        return AttributionReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            period_days=days,
            decisions_tracked=len(decisions),
            decisions_attributed=len(attributed),
            high_impact_decisions=[d.to_dict() for d in high_impact],
            low_impact_decisions=[d.to_dict() for d in low_impact],
            category_effectiveness=category_effectiveness,
            kernel_effectiveness=kernel_effectiveness,
            recommendations=recommendations[:5]
        )

    def _load_all_decisions(self, days: int) -> List[TrackedDecision]:
        """Load all decisions within period"""
        if not self.decisions_file.exists():
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        decisions = []

        try:
            with open(self.decisions_file) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        made_at = datetime.fromisoformat(data['made_at'].replace("Z", "+00:00"))

                        if made_at >= cutoff:
                            data['category'] = DecisionCategory(data['category'])
                            if data.get('outcome'):
                                data['outcome'] = OutcomeType(data['outcome'])
                            decisions.append(TrackedDecision(**data))
                    except:
                        continue
        except:
            pass

        return decisions

    # =========================================================================
    # Auto-Recording from Kernels
    # =========================================================================

    def auto_record_from_kernels(self) -> int:
        """
        Automatically record new decisions from kernels.

        Scans kernels for decisions not yet being tracked.
        """
        recorded = 0

        for kernel_id in list_kernels():
            kernel = load_kernel(kernel_id)
            if kernel is None:
                continue

            # Check recent decisions
            for decision in kernel.key_decisions[-5:]:
                decision_dict = decision.to_dict() if hasattr(decision, 'to_dict') else vars(decision)
                decision_text = decision_dict.get('decision', '')

                # Skip if already tracked (simple check)
                if self._is_decision_tracked(decision_text):
                    continue

                # Record it
                try:
                    self.record_decision(
                        decision_text=decision_text,
                        expected_outcome=decision_dict.get('rationale', 'Improve performance'),
                        kernel_id=kernel_id
                    )
                    recorded += 1
                except:
                    pass

        return recorded

    def _is_decision_tracked(self, decision_text: str) -> bool:
        """Check if a decision is already being tracked"""
        if not self.decisions_file.exists():
            return False

        try:
            with open(self.decisions_file) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get('decision_text', '') == decision_text:
                            return True
                    except:
                        continue
        except:
            pass

        return False


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Performance Attribution System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record a decision
  python -m ai_nexus.performance_attribution record \\
      --decision "Use Kelly fraction 0.15" \\
      --expected "Reduce drawdown risk" \\
      --kernel risk_model_v2

  # Attribute outcomes to decisions
  python -m ai_nexus.performance_attribution attribute

  # Generate effectiveness report
  python -m ai_nexus.performance_attribution report

  # Auto-record from kernels
  python -m ai_nexus.performance_attribution auto-record
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Record command
    record_parser = subparsers.add_parser("record", help="Record a decision")
    record_parser.add_argument("--decision", required=True, help="Decision text")
    record_parser.add_argument("--expected", required=True, help="Expected outcome")
    record_parser.add_argument("--kernel", required=True, help="Source kernel ID")
    record_parser.add_argument("--category", choices=["risk", "alpha", "strategy", "infrastructure", "other"])

    # Attribute command
    attr_parser = subparsers.add_parser("attribute", help="Attribute outcomes to decisions")
    attr_parser.add_argument("--window", type=int, default=7, help="Attribution window in days")
    attr_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate effectiveness report")
    report_parser.add_argument("--days", type=int, default=30, help="Days to analyze")
    report_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Auto-record command
    auto_parser = subparsers.add_parser("auto-record", help="Auto-record from kernels")

    args = parser.parse_args()

    attribution = PerformanceAttribution()

    if args.command == "record":
        category = None
        if args.category:
            category = DecisionCategory(args.category)

        decision = attribution.record_decision(
            decision_text=args.decision,
            expected_outcome=args.expected,
            kernel_id=args.kernel,
            category=category
        )

        print(f"✅ Decision recorded:")
        print(f"   ID: {decision.decision_id}")
        print(f"   Category: {decision.category.value}")
        print(f"   Kernel: {decision.kernel_id}")

    elif args.command == "attribute":
        attributed = attribution.attribute_outcomes(args.window)

        if args.json:
            print(json.dumps([d.to_dict() for d in attributed], indent=2))
        else:
            print(f"\n📊 Attribution Results ({len(attributed)} decisions)")
            print("="*60)

            for d in attributed:
                outcome_emoji = {
                    OutcomeType.POSITIVE: "✅",
                    OutcomeType.NEUTRAL: "➡️",
                    OutcomeType.NEGATIVE: "❌",
                    OutcomeType.UNKNOWN: "❓"
                }.get(d.outcome, "?")

                print(f"\n{outcome_emoji} {d.decision_text[:50]}...")
                print(f"   Outcome: {d.outcome.value if d.outcome else 'unknown'}")
                print(f"   Impact: {d.impact_score:.2f}" if d.impact_score else "   Impact: N/A")
                print(f"   Confidence: {d.attribution_confidence:.0%}")

    elif args.command == "report":
        report = attribution.generate_effectiveness_report(args.days)

        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"\n📊 DECISION EFFECTIVENESS REPORT")
            print("="*60)
            print(f"   Period: Last {report.period_days} days")
            print(f"   Decisions Tracked: {report.decisions_tracked}")
            print(f"   Decisions Attributed: {report.decisions_attributed}")

            if report.high_impact_decisions:
                print(f"\n   ✅ High Impact Decisions:")
                for d in report.high_impact_decisions[:3]:
                    print(f"      • {d['decision_text'][:40]}... (impact: {d['impact_score']:.2f})")

            if report.low_impact_decisions:
                print(f"\n   ❌ Low Impact Decisions:")
                for d in report.low_impact_decisions[:3]:
                    print(f"      • {d['decision_text'][:40]}... (impact: {d['impact_score']:.2f})")

            if report.category_effectiveness:
                print(f"\n   📊 Category Effectiveness:")
                for cat, eff in sorted(report.category_effectiveness.items(), key=lambda x: -x[1]):
                    emoji = "✅" if eff > 0 else "❌" if eff < 0 else "➡️"
                    print(f"      {emoji} {cat}: {eff:+.2f}")

            if report.recommendations:
                print(f"\n   💡 Recommendations:")
                for rec in report.recommendations:
                    print(f"      - {rec}")

    elif args.command == "auto-record":
        recorded = attribution.auto_record_from_kernels()
        print(f"✅ Auto-recorded {recorded} decisions from kernels")


if __name__ == "__main__":
    main()
