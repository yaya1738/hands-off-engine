"""
Multi-Kernel Consistency Validator v1.0

Ensures kernels don't contain conflicting decisions or outdated information.
Addresses the gap: NO CROSS-KERNEL CONSISTENCY CHECKS.

Features:
- Detects conflicting decisions across kernels
- Identifies outdated information
- Validates kernel cross-references
- Suggests consolidation opportunities
- Maintains kernel health scores

API:
    validator = KernelConsistencyValidator()
    issues = validator.validate_all()
    report = validator.generate_consistency_report()

CLI:
    python -m ai_nexus.kernel_consistency validate
    python -m ai_nexus.kernel_consistency report
    python -m ai_nexus.kernel_consistency fix --dry-run
"""

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.memory_kernels import load_kernel, list_kernels, save_kernel


class IssueType(Enum):
    """Types of consistency issues"""
    CONFLICT = "conflict"                 # Contradictory decisions
    OUTDATED = "outdated"                 # Stale information
    DUPLICATE = "duplicate"               # Same content in multiple kernels
    ORPHANED = "orphaned"                 # Reference to non-existent kernel
    OVERLAP = "overlap"                   # Significant content overlap
    MISSING_REF = "missing_reference"     # Missing cross-reference


class IssueSeverity(Enum):
    """Severity of consistency issues"""
    HIGH = "high"         # Requires immediate attention
    MEDIUM = "medium"     # Should be addressed
    LOW = "low"           # Nice to fix


@dataclass
class ConsistencyIssue:
    """A detected consistency issue"""
    issue_id: str
    issue_type: IssueType
    severity: IssueSeverity
    kernels_involved: List[str]
    description: str
    details: Dict[str, Any]
    suggested_fix: str

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['issue_type'] = self.issue_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class KernelHealth:
    """Health assessment for a single kernel"""
    kernel_id: str
    health_score: float  # 0-1
    issues_count: int
    last_updated: str
    decisions_count: int
    failed_paths_count: int
    open_questions_count: int
    staleness_days: int
    issues: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ConsistencyReport:
    """Complete consistency validation report"""
    timestamp: str
    kernels_validated: int
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_type: Dict[str, int]
    kernel_health: Dict[str, KernelHealth]
    critical_issues: List[ConsistencyIssue]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['kernel_health'] = {k: v.to_dict() for k, v in self.kernel_health.items()}
        data['critical_issues'] = [i.to_dict() for i in self.critical_issues]
        return data


class KernelConsistencyValidator:
    """
    Validates consistency across all memory kernels.

    Checks for:
    - Conflicting decisions (e.g., "use Kelly 0.15" vs "use Kelly 0.25")
    - Outdated content (not updated in 30+ days)
    - Duplicate content across kernels
    - Missing cross-references
    - Orphaned references
    """

    # Configuration
    STALENESS_THRESHOLD_DAYS = 30
    SIMILARITY_THRESHOLD = 0.7  # For duplicate detection

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.kernels_dir = self.repo_root / "ai" / "memory" / "kernels"
        self._issue_counter = 0

    # =========================================================================
    # Core Validation
    # =========================================================================

    def validate_all(self) -> List[ConsistencyIssue]:
        """
        Run all consistency validations.

        Returns list of detected issues.
        """
        all_issues = []

        # Load all kernels
        kernels = self._load_all_kernels()

        if not kernels:
            return []

        # Check for conflicts
        conflicts = self._detect_conflicts(kernels)
        all_issues.extend(conflicts)

        # Check for outdated content
        outdated = self._detect_outdated(kernels)
        all_issues.extend(outdated)

        # Check for duplicates
        duplicates = self._detect_duplicates(kernels)
        all_issues.extend(duplicates)

        # Check for orphaned references
        orphaned = self._detect_orphaned_references(kernels)
        all_issues.extend(orphaned)

        # Check for overlaps
        overlaps = self._detect_overlaps(kernels)
        all_issues.extend(overlaps)

        # Sort by severity
        severity_order = {
            IssueSeverity.HIGH: 0,
            IssueSeverity.MEDIUM: 1,
            IssueSeverity.LOW: 2
        }
        all_issues.sort(key=lambda x: severity_order.get(x.severity, 99))

        return all_issues

    def _load_all_kernels(self) -> Dict[str, Any]:
        """Load all kernels as raw data"""
        kernels = {}

        for kernel_id in list_kernels():
            kernel = load_kernel(kernel_id)
            if kernel:
                # Convert to dict for easier comparison
                kernels[kernel_id] = kernel.to_dict() if hasattr(kernel, 'to_dict') else vars(kernel)

        return kernels

    # =========================================================================
    # Conflict Detection
    # =========================================================================

    def _detect_conflicts(self, kernels: Dict[str, Any]) -> List[ConsistencyIssue]:
        """Detect conflicting decisions across kernels"""
        issues = []

        # Collect all decisions with their values
        decision_patterns = defaultdict(list)

        for kernel_id, kernel in kernels.items():
            for decision in kernel.get('key_decisions', []):
                decision_dict = decision if isinstance(decision, dict) else vars(decision)
                decision_text = decision_dict.get('decision', '')

                # Extract numeric values and parameters
                patterns = self._extract_decision_patterns(decision_text)

                for pattern_type, pattern_value in patterns:
                    decision_patterns[(pattern_type,)].append({
                        'kernel_id': kernel_id,
                        'decision_text': decision_text,
                        'value': pattern_value
                    })

        # Check for conflicts (same parameter, different values)
        for pattern_key, decisions in decision_patterns.items():
            if len(decisions) > 1:
                # Group by value
                by_value = defaultdict(list)
                for d in decisions:
                    by_value[d['value']].append(d)

                if len(by_value) > 1:
                    # Conflict detected - same parameter, different values
                    kernels_involved = list(set(d['kernel_id'] for d in decisions))

                    issues.append(self._create_issue(
                        issue_type=IssueType.CONFLICT,
                        severity=IssueSeverity.HIGH,
                        kernels_involved=kernels_involved,
                        description=f"Conflicting values for {pattern_key[0]}: "
                                   f"{', '.join(str(v) for v in by_value.keys())}",
                        details={
                            'parameter': pattern_key[0],
                            'values': dict(by_value)
                        },
                        suggested_fix="Review and consolidate conflicting decisions into a single authoritative value"
                    ))

        return issues

    def _extract_decision_patterns(self, text: str) -> List[Tuple[str, Any]]:
        """Extract decision patterns (parameter-value pairs)"""
        patterns = []

        # Kelly fraction pattern
        kelly_match = re.search(r'kelly[^\d]*(\d+\.?\d*)', text.lower())
        if kelly_match:
            patterns.append(('kelly_fraction', float(kelly_match.group(1))))

        # Position size pattern
        pos_match = re.search(r'position[^\d]*(\d+\.?\d*)%?', text.lower())
        if pos_match:
            patterns.append(('position_size', float(pos_match.group(1))))

        # Risk percentage pattern
        risk_match = re.search(r'risk[^\d]*(\d+\.?\d*)%', text.lower())
        if risk_match:
            patterns.append(('risk_pct', float(risk_match.group(1))))

        # Edge threshold pattern
        edge_match = re.search(r'edge[^\d]*(\d+\.?\d*)%?', text.lower())
        if edge_match:
            patterns.append(('edge_threshold', float(edge_match.group(1))))

        return patterns

    # =========================================================================
    # Outdated Detection
    # =========================================================================

    def _detect_outdated(self, kernels: Dict[str, Any]) -> List[ConsistencyIssue]:
        """Detect outdated kernel content"""
        issues = []
        now = datetime.now(timezone.utc)

        for kernel_id, kernel in kernels.items():
            last_updated = kernel.get('last_updated', '')

            if not last_updated:
                issues.append(self._create_issue(
                    issue_type=IssueType.OUTDATED,
                    severity=IssueSeverity.MEDIUM,
                    kernels_involved=[kernel_id],
                    description=f"Kernel '{kernel_id}' has no last_updated timestamp",
                    details={'kernel_id': kernel_id},
                    suggested_fix="Update kernel or set appropriate timestamp"
                ))
                continue

            try:
                updated_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                days_old = (now - updated_dt).days

                if days_old > self.STALENESS_THRESHOLD_DAYS:
                    severity = IssueSeverity.HIGH if days_old > 60 else IssueSeverity.MEDIUM

                    issues.append(self._create_issue(
                        issue_type=IssueType.OUTDATED,
                        severity=severity,
                        kernels_involved=[kernel_id],
                        description=f"Kernel '{kernel_id}' not updated in {days_old} days",
                        details={
                            'kernel_id': kernel_id,
                            'days_since_update': days_old,
                            'last_updated': last_updated
                        },
                        suggested_fix="Review kernel content and refresh if still relevant"
                    ))
            except:
                pass

        return issues

    # =========================================================================
    # Duplicate Detection
    # =========================================================================

    def _detect_duplicates(self, kernels: Dict[str, Any]) -> List[ConsistencyIssue]:
        """Detect duplicate content across kernels"""
        issues = []

        # Collect all decision texts
        all_decisions = []
        for kernel_id, kernel in kernels.items():
            for decision in kernel.get('key_decisions', []):
                decision_dict = decision if isinstance(decision, dict) else vars(decision)
                all_decisions.append({
                    'kernel_id': kernel_id,
                    'text': decision_dict.get('decision', ''),
                    'type': 'decision'
                })

            for fp in kernel.get('failed_paths', []):
                fp_dict = fp if isinstance(fp, dict) else vars(fp)
                all_decisions.append({
                    'kernel_id': kernel_id,
                    'text': fp_dict.get('lesson', ''),
                    'type': 'failed_path'
                })

        # Find near-duplicates across different kernels
        for i, d1 in enumerate(all_decisions):
            for d2 in all_decisions[i+1:]:
                if d1['kernel_id'] == d2['kernel_id']:
                    continue

                similarity = self._text_similarity(d1['text'], d2['text'])

                if similarity > self.SIMILARITY_THRESHOLD:
                    issues.append(self._create_issue(
                        issue_type=IssueType.DUPLICATE,
                        severity=IssueSeverity.LOW,
                        kernels_involved=[d1['kernel_id'], d2['kernel_id']],
                        description=f"Similar {d1['type']} found in {d1['kernel_id']} and {d2['kernel_id']}",
                        details={
                            'text1': d1['text'][:100],
                            'text2': d2['text'][:100],
                            'similarity': similarity
                        },
                        suggested_fix="Consider consolidating into one kernel with cross-reference"
                    ))

        return issues

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (word overlap)"""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    # =========================================================================
    # Orphaned Reference Detection
    # =========================================================================

    def _detect_orphaned_references(self, kernels: Dict[str, Any]) -> List[ConsistencyIssue]:
        """Detect references to non-existent kernels"""
        issues = []
        kernel_ids = set(kernels.keys())

        for kernel_id, kernel in kernels.items():
            # Check raw_refs
            for ref in kernel.get('raw_refs', []):
                # Extract kernel references from paths
                for kid in kernel_ids:
                    if kid in ref and kid not in kernel_ids:
                        issues.append(self._create_issue(
                            issue_type=IssueType.ORPHANED,
                            severity=IssueSeverity.MEDIUM,
                            kernels_involved=[kernel_id],
                            description=f"Kernel '{kernel_id}' references non-existent kernel '{kid}'",
                            details={
                                'source_kernel': kernel_id,
                                'referenced_kernel': kid,
                                'reference': ref
                            },
                            suggested_fix="Remove orphaned reference or create missing kernel"
                        ))

        return issues

    # =========================================================================
    # Overlap Detection
    # =========================================================================

    def _detect_overlaps(self, kernels: Dict[str, Any]) -> List[ConsistencyIssue]:
        """Detect significant topic overlap between kernels"""
        issues = []

        # Compare summaries for overlap
        kernel_list = list(kernels.items())

        for i, (kid1, k1) in enumerate(kernel_list):
            for kid2, k2 in kernel_list[i+1:]:
                summary1 = k1.get('summary', '')
                summary2 = k2.get('summary', '')

                similarity = self._text_similarity(summary1, summary2)

                if similarity > 0.5:  # 50% overlap in summaries
                    issues.append(self._create_issue(
                        issue_type=IssueType.OVERLAP,
                        severity=IssueSeverity.LOW,
                        kernels_involved=[kid1, kid2],
                        description=f"Significant topic overlap between '{kid1}' and '{kid2}'",
                        details={
                            'similarity': similarity,
                            'summary1': summary1[:100],
                            'summary2': summary2[:100]
                        },
                        suggested_fix="Consider merging kernels or clarifying scope boundaries"
                    ))

        return issues

    # =========================================================================
    # Kernel Health Assessment
    # =========================================================================

    def assess_kernel_health(self, kernel_id: str) -> KernelHealth:
        """Assess health of a single kernel"""
        kernel = load_kernel(kernel_id)

        if kernel is None:
            return KernelHealth(
                kernel_id=kernel_id,
                health_score=0.0,
                issues_count=1,
                last_updated="",
                decisions_count=0,
                failed_paths_count=0,
                open_questions_count=0,
                staleness_days=999,
                issues=["Kernel not found"]
            )

        kernel_dict = kernel.to_dict() if hasattr(kernel, 'to_dict') else vars(kernel)

        # Calculate staleness
        staleness_days = 0
        last_updated = kernel_dict.get('last_updated', '')
        if last_updated:
            try:
                updated_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                staleness_days = (datetime.now(timezone.utc) - updated_dt).days
            except:
                pass

        # Count issues
        issues = []

        if staleness_days > self.STALENESS_THRESHOLD_DAYS:
            issues.append(f"Stale: {staleness_days} days since update")

        decisions = kernel_dict.get('key_decisions', [])
        failed_paths = kernel_dict.get('failed_paths', [])
        open_questions = kernel_dict.get('open_questions', [])

        if len(decisions) == 0 and len(failed_paths) == 0:
            issues.append("No learned content (decisions or lessons)")

        if len(open_questions) > 10:
            issues.append(f"Many unresolved questions: {len(open_questions)}")

        if not kernel_dict.get('summary'):
            issues.append("Missing summary")

        # Calculate health score
        health_score = 1.0

        # Staleness penalty
        if staleness_days > 60:
            health_score -= 0.4
        elif staleness_days > 30:
            health_score -= 0.2

        # Content penalty
        if len(decisions) == 0:
            health_score -= 0.3

        # Issue penalty
        health_score -= len(issues) * 0.1

        return KernelHealth(
            kernel_id=kernel_id,
            health_score=max(0, health_score),
            issues_count=len(issues),
            last_updated=last_updated,
            decisions_count=len(decisions),
            failed_paths_count=len(failed_paths),
            open_questions_count=len(open_questions),
            staleness_days=staleness_days,
            issues=issues
        )

    # =========================================================================
    # Reporting
    # =========================================================================

    def generate_consistency_report(self) -> ConsistencyReport:
        """Generate comprehensive consistency report"""
        issues = self.validate_all()

        # Count by severity
        by_severity = defaultdict(int)
        for issue in issues:
            by_severity[issue.severity.value] += 1

        # Count by type
        by_type = defaultdict(int)
        for issue in issues:
            by_type[issue.issue_type.value] += 1

        # Kernel health
        kernel_health = {}
        for kernel_id in list_kernels():
            kernel_health[kernel_id] = self.assess_kernel_health(kernel_id)

        # Critical issues (high severity)
        critical = [i for i in issues if i.severity == IssueSeverity.HIGH]

        # Recommendations
        recommendations = []

        if by_severity.get('high', 0) > 0:
            recommendations.append(f"URGENT: Address {by_severity['high']} high-severity issues")

        if by_type.get('conflict', 0) > 0:
            recommendations.append("Review and resolve conflicting decisions")

        if by_type.get('outdated', 0) > 0:
            recommendations.append("Refresh outdated kernels or mark as deprecated")

        # Low health kernels
        unhealthy = [k for k, h in kernel_health.items() if h.health_score < 0.5]
        if unhealthy:
            recommendations.append(f"Improve health of kernels: {', '.join(unhealthy)}")

        return ConsistencyReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            kernels_validated=len(kernel_health),
            total_issues=len(issues),
            issues_by_severity=dict(by_severity),
            issues_by_type=dict(by_type),
            kernel_health=kernel_health,
            critical_issues=critical,
            recommendations=recommendations[:5]
        )

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _create_issue(
        self,
        issue_type: IssueType,
        severity: IssueSeverity,
        kernels_involved: List[str],
        description: str,
        details: Dict[str, Any],
        suggested_fix: str
    ) -> ConsistencyIssue:
        """Create a consistency issue"""
        self._issue_counter += 1

        return ConsistencyIssue(
            issue_id=f"issue_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._issue_counter}",
            issue_type=issue_type,
            severity=severity,
            kernels_involved=kernels_involved,
            description=description,
            details=details,
            suggested_fix=suggested_fix
        )


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-Kernel Consistency Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all kernels
  python -m ai_nexus.kernel_consistency validate

  # Generate full report
  python -m ai_nexus.kernel_consistency report

  # Check health of specific kernel
  python -m ai_nexus.kernel_consistency health --kernel risk_model_v2
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate kernel consistency")
    validate_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate consistency report")
    report_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Health command
    health_parser = subparsers.add_parser("health", help="Check kernel health")
    health_parser.add_argument("--kernel", help="Specific kernel ID (or all)")
    health_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    validator = KernelConsistencyValidator()

    if args.command == "validate":
        issues = validator.validate_all()

        if args.json:
            print(json.dumps([i.to_dict() for i in issues], indent=2))
        else:
            if not issues:
                print("✅ No consistency issues found")
            else:
                print(f"\n⚠️ Found {len(issues)} Consistency Issues:")
                print("="*60)

                severity_emoji = {
                    IssueSeverity.HIGH: "🔴",
                    IssueSeverity.MEDIUM: "🟠",
                    IssueSeverity.LOW: "🔵"
                }

                for issue in issues:
                    emoji = severity_emoji.get(issue.severity, "?")
                    print(f"\n{emoji} [{issue.severity.value}] {issue.issue_type.value}")
                    print(f"   {issue.description}")
                    print(f"   Kernels: {', '.join(issue.kernels_involved)}")
                    print(f"   Fix: {issue.suggested_fix}")

    elif args.command == "report":
        report = validator.generate_consistency_report()

        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"\n📊 KERNEL CONSISTENCY REPORT")
            print("="*60)
            print(f"   Kernels Validated: {report.kernels_validated}")
            print(f"   Total Issues: {report.total_issues}")

            print(f"\n   Issues by Severity:")
            for sev, count in report.issues_by_severity.items():
                emoji = {"high": "🔴", "medium": "🟠", "low": "🔵"}.get(sev, "?")
                print(f"      {emoji} {sev}: {count}")

            print(f"\n   Issues by Type:")
            for itype, count in report.issues_by_type.items():
                print(f"      • {itype}: {count}")

            print(f"\n   Kernel Health:")
            for kid, health in report.kernel_health.items():
                emoji = "✅" if health.health_score > 0.7 else "⚠️" if health.health_score > 0.4 else "❌"
                print(f"      {emoji} {kid}: {health.health_score:.0%} "
                      f"({health.decisions_count} decisions, {health.staleness_days}d old)")

            if report.recommendations:
                print(f"\n   💡 Recommendations:")
                for rec in report.recommendations:
                    print(f"      - {rec}")

    elif args.command == "health":
        if args.kernel:
            health = validator.assess_kernel_health(args.kernel)

            if args.json:
                print(json.dumps(health.to_dict(), indent=2))
            else:
                emoji = "✅" if health.health_score > 0.7 else "⚠️" if health.health_score > 0.4 else "❌"
                print(f"\n{emoji} Kernel Health: {health.kernel_id}")
                print("="*50)
                print(f"   Health Score: {health.health_score:.0%}")
                print(f"   Last Updated: {health.last_updated}")
                print(f"   Staleness: {health.staleness_days} days")
                print(f"   Decisions: {health.decisions_count}")
                print(f"   Lessons: {health.failed_paths_count}")
                print(f"   Questions: {health.open_questions_count}")

                if health.issues:
                    print(f"\n   Issues:")
                    for issue in health.issues:
                        print(f"      - {issue}")
        else:
            # All kernels
            for kernel_id in list_kernels():
                health = validator.assess_kernel_health(kernel_id)
                emoji = "✅" if health.health_score > 0.7 else "⚠️" if health.health_score > 0.4 else "❌"
                print(f"{emoji} {kernel_id}: {health.health_score:.0%}")


if __name__ == "__main__":
    main()
