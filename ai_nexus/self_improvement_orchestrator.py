"""
Self-Improvement Orchestrator v1.0

Master coordinator for all self-monitoring and self-improvement systems.
This is the brain that ties everything together for autonomous system improvement.

Coordinates:
- Self-Monitoring Hub (health aggregation)
- Anomaly Detection Engine (pattern detection)
- Kernel Update Applier (learning extraction)
- Feedback Loop Closure (metrics → learning)
- Cross-Session Learning (persistence)
- Performance Attribution (decision → outcome linking)

Flow:
    1. Monitor system health continuously
    2. Detect anomalies and degradation
    3. Analyze performance trends
    4. Extract learnings from sessions
    5. Apply improvements to kernels
    6. Track improvement effectiveness

API:
    orchestrator = SelfImprovementOrchestrator()
    status = orchestrator.run_improvement_cycle()
    report = orchestrator.generate_improvement_report()

CLI:
    python -m ai_nexus.self_improvement_orchestrator run
    python -m ai_nexus.self_improvement_orchestrator status
    python -m ai_nexus.self_improvement_orchestrator report
    python -m ai_nexus.self_improvement_orchestrator daemon --interval 3600
"""

import json
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import all subsystems
from ai_nexus.self_monitoring_hub import SelfMonitoringHub, HealthStatus
from ai_nexus.anomaly_detection import AnomalyDetector, AnomalySeverity
from ai_nexus.kernel_update_applier import KernelUpdateApplier, UpdateConfidence
from ai_nexus.feedback_loop import FeedbackLoopClosure
from ai_nexus.cross_session_learning import CrossSessionLearning, SessionOutcome


class ImprovementPhase(Enum):
    """Phases of the improvement cycle"""
    MONITORING = "monitoring"
    ANOMALY_DETECTION = "anomaly_detection"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    LEARNING_EXTRACTION = "learning_extraction"
    UPDATE_APPLICATION = "update_application"
    SYNTHESIS = "synthesis"
    IDLE = "idle"


@dataclass
class ImprovementCycleResult:
    """Result of a single improvement cycle"""
    cycle_id: str
    timestamp: str
    duration_seconds: float
    phases_completed: List[str]
    health_score: float
    anomalies_detected: int
    insights_generated: int
    updates_applied: int
    kernels_updated: List[str]
    recommendations: List[str]
    errors: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SystemImprovementReport:
    """Comprehensive system improvement report"""
    timestamp: str
    period_days: int
    cycles_completed: int
    total_anomalies: int
    total_updates_applied: int
    health_trend: str  # improving, stable, degrading
    key_improvements: List[str]
    persistent_issues: List[str]
    learning_summary: Dict[str, Any]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class SelfImprovementOrchestrator:
    """
    Master coordinator for autonomous system improvement.

    Responsibilities:
    - Schedule and run improvement cycles
    - Coordinate all subsystems
    - Track improvement effectiveness
    - Generate comprehensive reports
    - Manage autonomous operation
    """

    # Default configuration
    DEFAULT_CYCLE_INTERVAL = 3600  # 1 hour
    MIN_CYCLE_INTERVAL = 300       # 5 minutes minimum
    MAX_CYCLE_DURATION = 600       # 10 minutes max per cycle

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.state_dir = self.repo_root / "state"

        # Initialize subsystems
        self.monitoring_hub = SelfMonitoringHub()
        self.anomaly_detector = AnomalyDetector()
        self.update_applier = KernelUpdateApplier()
        self.feedback_loop = FeedbackLoopClosure()
        self.cross_session = CrossSessionLearning()

        # State tracking
        self.current_phase = ImprovementPhase.IDLE
        self.cycle_log = self.state_dir / "improvement_cycles.jsonl"
        self.config_file = self.state_dir / "orchestrator_config.json"

        # Cycle counter
        self._cycle_counter = self._load_cycle_counter()

    # =========================================================================
    # Core Improvement Cycle
    # =========================================================================

    def run_improvement_cycle(
        self,
        dry_run: bool = False,
        phases: Optional[List[str]] = None
    ) -> ImprovementCycleResult:
        """
        Run a complete self-improvement cycle.

        Phases (in order):
        1. Monitoring - Check system health
        2. Anomaly Detection - Identify unusual patterns
        3. Performance Analysis - Analyze metrics trends
        4. Learning Extraction - Extract from sessions
        5. Update Application - Apply improvements
        6. Synthesis - Consolidate learnings

        Args:
            dry_run: If True, analyze but don't apply changes
            phases: Optional list of phases to run (default: all)

        Returns:
            ImprovementCycleResult with cycle details
        """
        self._cycle_counter += 1
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._cycle_counter}"
        start_time = time.time()

        print(f"\n{'='*70}")
        print(f"🔄 SELF-IMPROVEMENT CYCLE: {cycle_id}")
        print(f"{'='*70}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        # Initialize result tracking
        phases_completed = []
        health_score = 0.0
        anomalies_detected = 0
        insights_generated = 0
        updates_applied = 0
        kernels_updated = []
        recommendations = []
        errors = []

        # Define all phases
        all_phases = [
            ImprovementPhase.MONITORING,
            ImprovementPhase.ANOMALY_DETECTION,
            ImprovementPhase.PERFORMANCE_ANALYSIS,
            ImprovementPhase.LEARNING_EXTRACTION,
            ImprovementPhase.UPDATE_APPLICATION,
            ImprovementPhase.SYNTHESIS
        ]

        # Filter phases if specified
        if phases:
            all_phases = [p for p in all_phases if p.value in phases]

        for phase in all_phases:
            self.current_phase = phase
            phase_start = time.time()

            try:
                print(f"▶ Phase: {phase.value.upper()}")

                if phase == ImprovementPhase.MONITORING:
                    result = self._run_monitoring_phase()
                    health_score = result.get("health_score", 0)
                    recommendations.extend(result.get("recommendations", []))

                elif phase == ImprovementPhase.ANOMALY_DETECTION:
                    result = self._run_anomaly_detection_phase()
                    anomalies_detected = result.get("anomalies_count", 0)
                    recommendations.extend(result.get("recommendations", []))

                elif phase == ImprovementPhase.PERFORMANCE_ANALYSIS:
                    result = self._run_performance_analysis_phase()
                    insights_generated += result.get("insights_count", 0)

                elif phase == ImprovementPhase.LEARNING_EXTRACTION:
                    result = self._run_learning_extraction_phase()
                    insights_generated += result.get("insights_count", 0)

                elif phase == ImprovementPhase.UPDATE_APPLICATION:
                    if not dry_run:
                        result = self._run_update_application_phase()
                        updates_applied = result.get("updates_applied", 0)
                        kernels_updated = result.get("kernels_updated", [])
                    else:
                        print("   [DRY RUN] Skipping update application")
                        result = {"skipped": True}

                elif phase == ImprovementPhase.SYNTHESIS:
                    result = self._run_synthesis_phase()
                    recommendations.extend(result.get("recommendations", []))

                phases_completed.append(phase.value)
                phase_duration = time.time() - phase_start
                print(f"   ✓ Completed in {phase_duration:.1f}s\n")

            except Exception as e:
                errors.append(f"{phase.value}: {str(e)}")
                print(f"   ✗ Error: {e}\n")

            # Check timeout
            if time.time() - start_time > self.MAX_CYCLE_DURATION:
                print("⚠️ Cycle timeout reached, stopping")
                break

        # Finalize
        self.current_phase = ImprovementPhase.IDLE
        duration = time.time() - start_time

        # Deduplicate recommendations
        recommendations = list(set(recommendations))[:10]

        result = ImprovementCycleResult(
            cycle_id=cycle_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=duration,
            phases_completed=phases_completed,
            health_score=health_score,
            anomalies_detected=anomalies_detected,
            insights_generated=insights_generated,
            updates_applied=updates_applied,
            kernels_updated=kernels_updated,
            recommendations=recommendations,
            errors=errors
        )

        # Log cycle
        self._log_cycle(result)
        self._save_cycle_counter()

        # Print summary
        print(f"{'='*70}")
        print(f"✅ CYCLE COMPLETE: {cycle_id}")
        print(f"{'='*70}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Health Score: {health_score:.0%}")
        print(f"   Anomalies Detected: {anomalies_detected}")
        print(f"   Insights Generated: {insights_generated}")
        print(f"   Updates Applied: {updates_applied}")
        print(f"   Kernels Updated: {', '.join(kernels_updated) if kernels_updated else 'none'}")

        if errors:
            print(f"\n   ⚠️ Errors: {len(errors)}")
            for error in errors[:3]:
                print(f"      - {error}")

        if recommendations[:3]:
            print(f"\n   💡 Top Recommendations:")
            for rec in recommendations[:3]:
                print(f"      - {rec}")

        print(f"{'='*70}\n")

        return result

    # =========================================================================
    # Phase Implementations
    # =========================================================================

    def _run_monitoring_phase(self) -> Dict[str, Any]:
        """Run the monitoring phase"""
        print("   Checking system health...")

        report = self.monitoring_hub.get_system_health()

        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.CRITICAL: "🔴",
            HealthStatus.UNKNOWN: "❓"
        }

        print(f"   Status: {status_emoji.get(report.overall_status, '?')} {report.overall_status.value}")
        print(f"   Score: {report.overall_score:.0%}")
        print(f"   Components: {len(report.components)}")

        return {
            "health_score": report.overall_score,
            "status": report.overall_status.value,
            "components": len(report.components),
            "recommendations": report.recommendations[:5]
        }

    def _run_anomaly_detection_phase(self) -> Dict[str, Any]:
        """Run the anomaly detection phase"""
        print("   Detecting anomalies...")

        # Train baselines if needed
        if not self.anomaly_detector.baselines:
            print("   Training baselines (first run)...")
            self.anomaly_detector.train_baselines(hours=168)

        anomalies = self.anomaly_detector.detect_all()

        severity_counts = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.WARNING: 0,
            AnomalySeverity.INFO: 0
        }

        for anomaly in anomalies:
            severity_counts[anomaly.severity] = severity_counts.get(anomaly.severity, 0) + 1

        print(f"   Anomalies: {len(anomalies)} "
              f"(🔴 {severity_counts[AnomalySeverity.CRITICAL]} / "
              f"🟠 {severity_counts[AnomalySeverity.WARNING]} / "
              f"🔵 {severity_counts[AnomalySeverity.INFO]})")

        recommendations = []
        if severity_counts[AnomalySeverity.CRITICAL] > 0:
            recommendations.append(f"URGENT: {severity_counts[AnomalySeverity.CRITICAL]} critical anomalies detected")

        return {
            "anomalies_count": len(anomalies),
            "severity_breakdown": {k.value: v for k, v in severity_counts.items()},
            "recommendations": recommendations
        }

    def _run_performance_analysis_phase(self) -> Dict[str, Any]:
        """Run the performance analysis phase"""
        print("   Analyzing performance trends...")

        trends, insights = self.feedback_loop.analyze_performance(days=7)

        print(f"   Trends analyzed: {len(trends)}")
        print(f"   Insights generated: {len(insights)}")

        return {
            "trends_count": len(trends),
            "insights_count": len(insights)
        }

    def _run_learning_extraction_phase(self) -> Dict[str, Any]:
        """Run the learning extraction phase"""
        print("   Extracting learnings from sessions...")

        # Find recent sessions
        intercom_dir = self.repo_root / "ai" / "intercom"
        recent_sessions = []

        if intercom_dir.exists():
            cutoff_time = time.time() - 86400 * 7  # Last 7 days

            for session_dir in intercom_dir.iterdir():
                if session_dir.is_dir():
                    thread_file = session_dir / "thread.jsonl"
                    if thread_file.exists():
                        if thread_file.stat().st_mtime > cutoff_time:
                            recent_sessions.append(session_dir.name)

        print(f"   Recent sessions found: {len(recent_sessions)}")

        # Extract updates from sessions
        total_updates = 0
        for session_id in recent_sessions[:5]:  # Limit to 5 most recent
            try:
                updates = self.update_applier.extract_updates_from_session(session_id)
                total_updates += len(updates)
            except:
                pass

        print(f"   Potential updates extracted: {total_updates}")

        return {
            "sessions_analyzed": len(recent_sessions),
            "insights_count": total_updates
        }

    def _run_update_application_phase(self) -> Dict[str, Any]:
        """Run the update application phase"""
        print("   Applying updates to kernels...")

        # Close feedback loop
        result = self.feedback_loop.close_loop(dry_run=False, min_confidence=0.5)

        print(f"   Updates applied: {result.updates_applied}")
        print(f"   Kernels updated: {', '.join(result.kernels_updated) if result.kernels_updated else 'none'}")

        return {
            "updates_applied": result.updates_applied,
            "kernels_updated": result.kernels_updated
        }

    def _run_synthesis_phase(self) -> Dict[str, Any]:
        """Run the synthesis phase"""
        print("   Synthesizing cross-session learnings...")

        synthesis = self.cross_session.synthesize_learnings(days=30)

        print(f"   Sessions analyzed: {synthesis.sessions_analyzed}")
        print(f"   Key patterns: {len(synthesis.key_patterns)}")

        return {
            "sessions_synthesized": synthesis.sessions_analyzed,
            "patterns_found": len(synthesis.key_patterns),
            "recommendations": synthesis.recommendations
        }

    # =========================================================================
    # Daemon Mode
    # =========================================================================

    def run_daemon(
        self,
        interval_seconds: int = DEFAULT_CYCLE_INTERVAL,
        max_cycles: Optional[int] = None
    ):
        """
        Run the orchestrator as a daemon (continuous improvement).

        Args:
            interval_seconds: Seconds between cycles
            max_cycles: Maximum cycles to run (None = infinite)
        """
        interval_seconds = max(interval_seconds, self.MIN_CYCLE_INTERVAL)
        cycles_run = 0

        print(f"\n🤖 SELF-IMPROVEMENT DAEMON STARTED")
        print(f"   Interval: {interval_seconds}s ({interval_seconds/60:.0f} minutes)")
        print(f"   Max Cycles: {max_cycles or 'infinite'}")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while max_cycles is None or cycles_run < max_cycles:
                # Run improvement cycle
                try:
                    self.run_improvement_cycle()
                    cycles_run += 1
                except Exception as e:
                    print(f"⚠️ Cycle error: {e}")

                # Check if we should continue
                if max_cycles is not None and cycles_run >= max_cycles:
                    break

                # Wait for next cycle
                print(f"💤 Sleeping for {interval_seconds}s until next cycle...")
                print(f"   Next cycle at: {(datetime.now() + timedelta(seconds=interval_seconds)).strftime('%H:%M:%S')}\n")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print(f"\n\n⏹️ Daemon stopped by user")
            print(f"   Cycles completed: {cycles_run}")

    # =========================================================================
    # Reporting
    # =========================================================================

    def generate_improvement_report(self, days: int = 7) -> SystemImprovementReport:
        """Generate comprehensive improvement report"""
        print(f"\n📊 Generating improvement report for last {days} days...")

        # Load cycle history
        cycles = self._load_recent_cycles(days)

        # Calculate metrics
        total_anomalies = sum(c.get("anomalies_detected", 0) for c in cycles)
        total_updates = sum(c.get("updates_applied", 0) for c in cycles)

        # Health trend
        if len(cycles) >= 2:
            recent_health = sum(c.get("health_score", 0) for c in cycles[-3:]) / min(3, len(cycles))
            older_health = sum(c.get("health_score", 0) for c in cycles[:3]) / min(3, len(cycles))

            if recent_health > older_health + 0.05:
                health_trend = "improving"
            elif recent_health < older_health - 0.05:
                health_trend = "degrading"
            else:
                health_trend = "stable"
        else:
            health_trend = "insufficient_data"

        # Key improvements (from successful updates)
        key_improvements = []
        all_kernels = set()
        for c in cycles:
            all_kernels.update(c.get("kernels_updated", []))
        if all_kernels:
            key_improvements.append(f"Updated {len(all_kernels)} kernels: {', '.join(all_kernels)}")

        if total_updates > 0:
            key_improvements.append(f"Applied {total_updates} automatic improvements")

        # Persistent issues
        persistent_issues = []
        if health_trend == "degrading":
            persistent_issues.append("System health is trending downward")

        # Get learning summary
        synthesis = self.cross_session.synthesize_learnings(days=days)
        learning_summary = {
            "sessions_analyzed": synthesis.sessions_analyzed,
            "patterns_found": len(synthesis.key_patterns),
            "success_factors": len(synthesis.success_factors),
            "failure_factors": len(synthesis.failure_factors)
        }

        # Recommendations
        recommendations = []
        if health_trend == "degrading":
            recommendations.append("Investigate causes of health degradation")
        if total_anomalies > 10:
            recommendations.append("High anomaly count - review system stability")
        recommendations.extend(synthesis.recommendations[:3])

        report = SystemImprovementReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            period_days=days,
            cycles_completed=len(cycles),
            total_anomalies=total_anomalies,
            total_updates_applied=total_updates,
            health_trend=health_trend,
            key_improvements=key_improvements,
            persistent_issues=persistent_issues,
            learning_summary=learning_summary,
            recommendations=list(set(recommendations))[:5]
        )

        return report

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "current_phase": self.current_phase.value,
            "cycles_completed": self._cycle_counter,
            "last_cycle": self._get_last_cycle_time(),
            "subsystems": {
                "monitoring_hub": "active",
                "anomaly_detector": "active" if self.anomaly_detector.baselines else "needs_baseline",
                "update_applier": "active",
                "feedback_loop": "active",
                "cross_session": "active"
            }
        }

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _log_cycle(self, result: ImprovementCycleResult):
        """Log cycle result"""
        try:
            self.cycle_log.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cycle_log, 'a') as f:
                f.write(json.dumps(result.to_dict()) + '\n')
        except:
            pass

    def _load_recent_cycles(self, days: int) -> List[Dict]:
        """Load recent cycle results"""
        if not self.cycle_log.exists():
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cycles = []

        try:
            with open(self.cycle_log) as f:
                for line in f:
                    try:
                        cycle = json.loads(line)
                        ts = cycle.get("timestamp", "")
                        if ts:
                            cycle_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if cycle_dt >= cutoff:
                                cycles.append(cycle)
                    except:
                        continue
        except:
            pass

        return cycles

    def _get_last_cycle_time(self) -> Optional[str]:
        """Get timestamp of last cycle"""
        if not self.cycle_log.exists():
            return None

        last_cycle = None
        try:
            with open(self.cycle_log) as f:
                for line in f:
                    try:
                        cycle = json.loads(line)
                        last_cycle = cycle.get("timestamp")
                    except:
                        continue
        except:
            pass

        return last_cycle

    def _load_cycle_counter(self) -> int:
        """Load cycle counter from config"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                return config.get("cycle_counter", 0)
            except:
                pass
        return 0

    def _save_cycle_counter(self):
        """Save cycle counter to config"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            config = {}
            if self.config_file.exists():
                try:
                    with open(self.config_file) as f:
                        config = json.load(f)
                except:
                    pass

            config["cycle_counter"] = self._cycle_counter
            config["last_updated"] = datetime.now(timezone.utc).isoformat()

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Self-Improvement Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single improvement cycle
  python -m ai_nexus.self_improvement_orchestrator run

  # Run dry-run cycle (no changes)
  python -m ai_nexus.self_improvement_orchestrator run --dry-run

  # Check current status
  python -m ai_nexus.self_improvement_orchestrator status

  # Generate improvement report
  python -m ai_nexus.self_improvement_orchestrator report

  # Run as daemon (continuous improvement)
  python -m ai_nexus.self_improvement_orchestrator daemon --interval 3600
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run improvement cycle")
    run_parser.add_argument("--dry-run", action="store_true", help="Don't apply changes")
    run_parser.add_argument("--phases", help="Comma-separated phases to run")
    run_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show current status")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate improvement report")
    report_parser.add_argument("--days", type=int, default=7, help="Days to analyze")
    report_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Daemon command
    daemon_parser = subparsers.add_parser("daemon", help="Run as daemon")
    daemon_parser.add_argument("--interval", type=int, default=3600, help="Seconds between cycles")
    daemon_parser.add_argument("--max-cycles", type=int, help="Maximum cycles to run")

    args = parser.parse_args()

    orchestrator = SelfImprovementOrchestrator()

    if args.command == "run":
        phases = None
        if args.phases:
            phases = [p.strip() for p in args.phases.split(",")]

        result = orchestrator.run_improvement_cycle(dry_run=args.dry_run, phases=phases)

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))

    elif args.command == "status":
        status = orchestrator.get_status()

        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"\n🤖 Self-Improvement Orchestrator Status")
            print("="*50)
            print(f"   Current Phase: {status['current_phase']}")
            print(f"   Cycles Completed: {status['cycles_completed']}")
            print(f"   Last Cycle: {status['last_cycle'] or 'never'}")
            print(f"\n   Subsystems:")
            for name, state in status['subsystems'].items():
                emoji = "✅" if state == "active" else "⚠️"
                print(f"      {emoji} {name}: {state}")

    elif args.command == "report":
        report = orchestrator.generate_improvement_report(days=args.days)

        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            trend_emoji = {
                "improving": "📈",
                "stable": "➡️",
                "degrading": "📉",
                "insufficient_data": "❓"
            }

            print(f"\n📊 SYSTEM IMPROVEMENT REPORT")
            print("="*60)
            print(f"   Period: Last {report.period_days} days")
            print(f"   Cycles Completed: {report.cycles_completed}")
            print(f"   Health Trend: {trend_emoji.get(report.health_trend, '?')} {report.health_trend}")
            print(f"   Total Anomalies: {report.total_anomalies}")
            print(f"   Total Updates Applied: {report.total_updates_applied}")

            if report.key_improvements:
                print(f"\n   ✅ Key Improvements:")
                for imp in report.key_improvements:
                    print(f"      - {imp}")

            if report.persistent_issues:
                print(f"\n   ⚠️ Persistent Issues:")
                for issue in report.persistent_issues:
                    print(f"      - {issue}")

            print(f"\n   📚 Learning Summary:")
            for key, val in report.learning_summary.items():
                print(f"      - {key}: {val}")

            if report.recommendations:
                print(f"\n   💡 Recommendations:")
                for rec in report.recommendations:
                    print(f"      - {rec}")

            print("="*60)

    elif args.command == "daemon":
        orchestrator.run_daemon(
            interval_seconds=args.interval,
            max_cycles=args.max_cycles
        )


if __name__ == "__main__":
    main()
