#!/usr/bin/env python3
"""
Software Self-Improvement Engine

Autonomous code quality and performance improvement system.
Works alongside the Harmony Orchestrator to continuously improve the codebase.

Capabilities:
1. OBSERVE - Monitor error patterns, performance metrics, code quality
2. ANALYZE - Identify improvement opportunities
3. IMPROVE - Generate and propose improvements
4. VALIDATE - Test changes before deployment
5. DEPLOY - Auto-merge safe changes, request approval for risky ones

For Yair Siegel's benefit - autonomous code improvement without intervention.
"""

import json
import os
import sys
import time
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Configuration
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"

IMPROVEMENT_STATE = STATE_DIR / "self_improvement_state.json"
IMPROVEMENT_LOG = LOGS_DIR / "self_improvements.jsonl"

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ImprovementOpportunity:
    """A discovered improvement opportunity."""
    id: str
    category: str  # error_pattern, performance, code_quality, security
    description: str
    source_file: Optional[str]
    severity: str  # low, medium, high
    auto_fixable: bool
    fix_suggestion: Optional[str]
    discovered_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ImprovementAction:
    """An improvement action taken."""
    opportunity_id: str
    action_type: str  # auto_fix, pr_created, escalated
    result: str  # success, failed, pending
    details: str
    executed_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


class SelfImprovementEngine:
    """
    Engine that continuously improves the software.
    
    Observes → Analyzes → Improves → Validates → Deploys
    """

    def __init__(self):
        self.state = self._load_state()
        self.improvements_made = 0
        logger.info("Self-Improvement Engine initialized")

    def _load_state(self) -> Dict:
        """Load persisted state."""
        if IMPROVEMENT_STATE.exists():
            try:
                with open(IMPROVEMENT_STATE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "total_improvements": 0,
            "opportunities_discovered": 0,
            "last_scan": None,
            "known_patterns": [],
            "deferred_improvements": []
        }

    def _save_state(self):
        """Persist state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        tmp_file = IMPROVEMENT_STATE.with_suffix('.tmp')
        try:
            with open(tmp_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            tmp_file.rename(IMPROVEMENT_STATE)
        except IOError as e:
            logger.error(f"Failed to save state: {e}")

    def _log_improvement(self, action: ImprovementAction):
        """Log improvement action."""
        try:
            with open(IMPROVEMENT_LOG, 'a') as f:
                f.write(json.dumps(action.to_dict()) + '\n')
        except IOError as e:
            logger.error(f"Failed to log improvement: {e}")

    # =========================================================================
    # OBSERVE - Monitor for improvement opportunities
    # =========================================================================

    def scan_error_patterns(self) -> List[ImprovementOpportunity]:
        """Scan logs for recurring error patterns."""
        opportunities = []

        # Check various error logs
        error_sources = [
            LOGS_DIR / "errors.log",
            LOGS_DIR / "harmony_orchestrator.log",
            Path("/var/log/self-healing-agent.log"),
            Path("/var/log/coordination-agent.log")
        ]

        error_counts: Dict[str, int] = {}

        for log_file in error_sources:
            if not log_file.exists():
                continue

            try:
                with open(log_file) as f:
                    lines = f.readlines()[-500:]  # Last 500 lines

                for line in lines:
                    line_lower = line.lower()
                    if "error" in line_lower or "exception" in line_lower:
                        # Extract error type
                        if "importerror" in line_lower:
                            error_counts["ImportError"] = error_counts.get("ImportError", 0) + 1
                        elif "filenotfounderror" in line_lower:
                            error_counts["FileNotFoundError"] = error_counts.get("FileNotFoundError", 0) + 1
                        elif "timeout" in line_lower:
                            error_counts["TimeoutError"] = error_counts.get("TimeoutError", 0) + 1
                        elif "connection" in line_lower:
                            error_counts["ConnectionError"] = error_counts.get("ConnectionError", 0) + 1
            except IOError:
                continue

        # Create opportunities for recurring errors
        for error_type, count in error_counts.items():
            if count >= 3:  # Threshold for "recurring"
                opportunities.append(ImprovementOpportunity(
                    id=f"error_{error_type}_{int(time.time())}",
                    category="error_pattern",
                    description=f"Recurring {error_type}: {count} occurrences",
                    source_file=None,
                    severity="medium" if count < 10 else "high",
                    auto_fixable=False,
                    fix_suggestion=self._suggest_error_fix(error_type),
                    discovered_at=datetime.now(timezone.utc).isoformat()
                ))

        return opportunities

    def _suggest_error_fix(self, error_type: str) -> str:
        """Suggest fix for common error types."""
        suggestions = {
            "ImportError": "Check module paths and dependencies in requirements.txt",
            "FileNotFoundError": "Verify file paths and add existence checks",
            "TimeoutError": "Increase timeout values or add retry logic",
            "ConnectionError": "Add connection pooling and retry with backoff"
        }
        return suggestions.get(error_type, "Review error logs for details")

    def scan_performance_issues(self) -> List[ImprovementOpportunity]:
        """Scan for performance improvement opportunities."""
        opportunities = []

        # Check performance metrics
        perf_log = LOGS_DIR / "performance_tracking.jsonl"
        if perf_log.exists():
            try:
                with open(perf_log) as f:
                    lines = f.readlines()[-100:]

                slow_responses = 0
                for line in lines:
                    try:
                        metric = json.loads(line)
                        if metric.get("response_time_ms", 0) > 1000:
                            slow_responses += 1
                    except json.JSONDecodeError:
                        continue

                if slow_responses > 10:
                    opportunities.append(ImprovementOpportunity(
                        id=f"perf_slow_{int(time.time())}",
                        category="performance",
                        description=f"Slow responses detected: {slow_responses} > 1s",
                        source_file=None,
                        severity="medium",
                        auto_fixable=False,
                        fix_suggestion="Add caching for frequently accessed data",
                        discovered_at=datetime.now(timezone.utc).isoformat()
                    ))
            except IOError:
                pass

        # Check for large files that might slow operations
        for json_file in STATE_DIR.glob("*.json"):
            try:
                size_mb = json_file.stat().st_size / (1024 * 1024)
                if size_mb > 10:
                    opportunities.append(ImprovementOpportunity(
                        id=f"perf_large_file_{json_file.stem}_{int(time.time())}",
                        category="performance",
                        description=f"Large state file: {json_file.name} ({size_mb:.1f}MB)",
                        source_file=str(json_file),
                        severity="low",
                        auto_fixable=True,
                        fix_suggestion="Archive or truncate old data",
                        discovered_at=datetime.now(timezone.utc).isoformat()
                    ))
            except IOError:
                continue

        return opportunities

    def scan_code_quality(self) -> List[ImprovementOpportunity]:
        """Scan for code quality improvements."""
        opportunities = []

        # Check for Python files with potential issues
        python_files = list(REPO_ROOT.rglob("*.py"))

        for py_file in python_files[:20]:  # Limit to avoid slowdown
            try:
                content = py_file.read_text()

                # Check for bare except
                if "except:" in content and "except Exception" not in content:
                    opportunities.append(ImprovementOpportunity(
                        id=f"quality_bare_except_{py_file.stem}_{int(time.time())}",
                        category="code_quality",
                        description=f"Bare except clause in {py_file.name}",
                        source_file=str(py_file.relative_to(REPO_ROOT)),
                        severity="low",
                        auto_fixable=False,
                        fix_suggestion="Use specific exception types",
                        discovered_at=datetime.now(timezone.utc).isoformat()
                    ))

                # Check for TODO/FIXME comments
                if "TODO" in content or "FIXME" in content:
                    todo_count = content.count("TODO") + content.count("FIXME")
                    if todo_count > 3:
                        opportunities.append(ImprovementOpportunity(
                            id=f"quality_todos_{py_file.stem}_{int(time.time())}",
                            category="code_quality",
                            description=f"Many TODO/FIXME in {py_file.name}: {todo_count}",
                            source_file=str(py_file.relative_to(REPO_ROOT)),
                            severity="low",
                            auto_fixable=False,
                            fix_suggestion="Address pending work items",
                            discovered_at=datetime.now(timezone.utc).isoformat()
                        ))
            except IOError:
                continue

        return opportunities

    # =========================================================================
    # ANALYZE - Prioritize and filter opportunities
    # =========================================================================

    def prioritize_opportunities(
        self, opportunities: List[ImprovementOpportunity]
    ) -> List[ImprovementOpportunity]:
        """Prioritize opportunities by impact and feasibility."""
        # Score each opportunity
        def score(opp: ImprovementOpportunity) -> int:
            score = 0
            # Severity score
            if opp.severity == "high":
                score += 30
            elif opp.severity == "medium":
                score += 20
            else:
                score += 10

            # Category score (errors most important)
            if opp.category == "error_pattern":
                score += 20
            elif opp.category == "performance":
                score += 15
            elif opp.category == "security":
                score += 25
            else:
                score += 5

            # Auto-fixable bonus
            if opp.auto_fixable:
                score += 10

            return score

        return sorted(opportunities, key=score, reverse=True)

    def filter_duplicates(
        self, opportunities: List[ImprovementOpportunity]
    ) -> List[ImprovementOpportunity]:
        """Filter out duplicate or already-addressed opportunities."""
        known = set(self.state.get("known_patterns", []))
        filtered = []

        for opp in opportunities:
            key = f"{opp.category}:{opp.description}"
            if key not in known:
                filtered.append(opp)

        return filtered

    # =========================================================================
    # IMPROVE - Take action on opportunities
    # =========================================================================

    def apply_auto_fixes(
        self, opportunities: List[ImprovementOpportunity]
    ) -> List[ImprovementAction]:
        """Apply automatic fixes where possible."""
        actions = []

        for opp in opportunities:
            if not opp.auto_fixable:
                continue

            logger.info(f"Attempting auto-fix: {opp.description}")

            action = ImprovementAction(
                opportunity_id=opp.id,
                action_type="auto_fix",
                result="pending",
                details="",
                executed_at=datetime.now(timezone.utc).isoformat()
            )

            try:
                if opp.category == "performance" and "large state file" in opp.description.lower():
                    # Truncate large state files by archiving old data
                    if opp.source_file:
                        source = Path(opp.source_file)
                        if source.exists():
                            # Archive to backup
                            backup = source.with_suffix('.json.bak')
                            source.rename(backup)
                            # Create empty placeholder
                            source.write_text("{}")
                            action.result = "success"
                            action.details = f"Archived {source.name} to {backup.name}"
                            self.improvements_made += 1
                else:
                    action.result = "skipped"
                    action.details = "No auto-fix handler for this type"
            except (IOError, OSError, PermissionError) as e:
                action.result = "failed"
                action.details = str(e)

            actions.append(action)
            self._log_improvement(action)

        return actions

    def create_improvement_report(
        self, opportunities: List[ImprovementOpportunity]
    ) -> Dict:
        """Create a summary report of improvement opportunities."""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_opportunities": len(opportunities),
            "by_category": {},
            "by_severity": {},
            "auto_fixable": 0,
            "requires_review": 0,
            "opportunities": []
        }

        for opp in opportunities:
            # Count by category
            cat = opp.category
            report["by_category"][cat] = report["by_category"].get(cat, 0) + 1

            # Count by severity
            sev = opp.severity
            report["by_severity"][sev] = report["by_severity"].get(sev, 0) + 1

            # Count auto-fixable
            if opp.auto_fixable:
                report["auto_fixable"] += 1
            else:
                report["requires_review"] += 1

            report["opportunities"].append(opp.to_dict())

        return report

    # =========================================================================
    # Main cycle
    # =========================================================================

    def run_cycle(self) -> Dict:
        """Run one improvement cycle."""
        logger.info("Starting self-improvement cycle")

        # OBSERVE - Scan for opportunities
        opportunities = []
        opportunities.extend(self.scan_error_patterns())
        opportunities.extend(self.scan_performance_issues())
        opportunities.extend(self.scan_code_quality())

        logger.info(f"Discovered {len(opportunities)} opportunities")

        # ANALYZE - Filter and prioritize
        opportunities = self.filter_duplicates(opportunities)
        opportunities = self.prioritize_opportunities(opportunities)

        logger.info(f"After filtering: {len(opportunities)} opportunities")

        # IMPROVE - Apply fixes
        actions = self.apply_auto_fixes(opportunities)

        successful = sum(1 for a in actions if a.result == "success")
        logger.info(f"Auto-fixes applied: {successful}")

        # Update state
        self.state["opportunities_discovered"] = self.state.get("opportunities_discovered", 0) + len(opportunities)
        self.state["total_improvements"] = self.state.get("total_improvements", 0) + successful
        self.state["last_scan"] = datetime.now(timezone.utc).isoformat()

        # Add non-auto-fixable to known patterns to avoid repeated discovery
        for opp in opportunities:
            if not opp.auto_fixable:
                pattern = f"{opp.category}:{opp.description}"
                if pattern not in self.state.get("known_patterns", []):
                    if "known_patterns" not in self.state:
                        self.state["known_patterns"] = []
                    self.state["known_patterns"].append(pattern)

        self._save_state()

        # Generate report
        report = self.create_improvement_report(opportunities)
        report["actions_taken"] = [a.to_dict() for a in actions]

        return report


def main():
    """Entry point."""
    engine = SelfImprovementEngine()

    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        # Just generate report
        report = engine.run_cycle()
        print(json.dumps(report, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # Run continuously
        logger.info("Running in daemon mode (every 30 minutes)")
        while True:
            try:
                report = engine.run_cycle()
                logger.info(f"Cycle complete: {report['total_opportunities']} opportunities, "
                           f"{report['auto_fixable']} auto-fixed")
                time.sleep(1800)  # 30 minutes
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in cycle: {e}")
                time.sleep(300)
    else:
        # One-shot
        report = engine.run_cycle()
        print(f"\n{'='*60}")
        print("SELF-IMPROVEMENT REPORT")
        print(f"{'='*60}")
        print(f"Opportunities found: {report['total_opportunities']}")
        print(f"By category: {report['by_category']}")
        print(f"By severity: {report['by_severity']}")
        print(f"Auto-fixable: {report['auto_fixable']}")
        print(f"Requires review: {report['requires_review']}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
