"""
Cross-Session Learning Persistence Layer v1.0

Ensures learning persists and accumulates across CPU sessions.
Addresses the gap: KERNELS NOT FULLY SHARED BETWEEN SESSIONS.

Features:
- Automatic kernel context injection into new sessions
- Cross-session decision synthesis
- Learning continuity tracking
- Session outcome correlation
- Institutional memory management

Flow:
    1. Before session: Load relevant kernel context
    2. During session: Track learning events
    3. After session: Extract and persist learnings
    4. Between sessions: Synthesize accumulated knowledge

API:
    persistence = CrossSessionLearning()
    context = persistence.prepare_session_context(session_id, kernels)
    persistence.record_session_outcome(session_id, outcome)
    synthesis = persistence.synthesize_learnings()

CLI:
    python -m ai_nexus.cross_session_learning prepare --session-id <id>
    python -m ai_nexus.cross_session_learning record --session-id <id>
    python -m ai_nexus.cross_session_learning synthesize
"""

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.memory_kernels import load_kernel, list_kernels, append_kernel_update
from ai_nexus.spark_plug_types import KernelUpdate, CpuInstance


class SessionOutcome(Enum):
    """Outcome classification for CPU sessions"""
    SUCCESSFUL = "successful"          # Goals achieved, good learnings
    PARTIAL = "partial"                # Some goals achieved
    UNSUCCESSFUL = "unsuccessful"      # Goals not achieved
    INCONCLUSIVE = "inconclusive"      # Cannot determine outcome
    ERROR = "error"                    # Session ended with error


@dataclass
class SessionLearning:
    """Learning extracted from a single session"""
    session_id: str
    timestamp: str
    kernels_used: List[str]
    decisions_made: int
    lessons_learned: int
    questions_raised: int
    outcome: SessionOutcome
    key_insights: List[str]
    context_quality: float  # How well was context prepared (0-1)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['outcome'] = self.outcome.value
        return data


@dataclass
class SessionContext:
    """Prepared context for a new session"""
    session_id: str
    prepared_at: str
    kernels_loaded: List[str]
    kernel_summaries: Dict[str, str]
    recent_decisions: List[Dict[str, Any]]
    recent_lessons: List[Dict[str, Any]]
    open_questions: List[str]
    prior_session_insights: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_context_prompt(self) -> str:
        """Generate a context prompt for the session"""
        parts = []

        parts.append("## SESSION CONTEXT (Cross-Session Learning)")
        parts.append("")

        # Kernel summaries
        if self.kernel_summaries:
            parts.append("### Relevant Knowledge Kernels:")
            for kernel_id, summary in self.kernel_summaries.items():
                parts.append(f"**{kernel_id}**: {summary}")
            parts.append("")

        # Recent decisions
        if self.recent_decisions:
            parts.append("### Recent Decisions (last 7 days):")
            for decision in self.recent_decisions[:5]:
                parts.append(f"- {decision.get('decision', 'N/A')} "
                           f"(Source: {decision.get('source', 'unknown')})")
            parts.append("")

        # Recent lessons
        if self.recent_lessons:
            parts.append("### Recent Lessons Learned:")
            for lesson in self.recent_lessons[:5]:
                parts.append(f"- {lesson.get('lesson', 'N/A')}")
            parts.append("")

        # Open questions
        if self.open_questions:
            parts.append("### Open Questions to Consider:")
            for question in self.open_questions[:5]:
                parts.append(f"- {question}")
            parts.append("")

        # Prior session insights
        if self.prior_session_insights:
            parts.append("### Insights from Prior Sessions:")
            for insight in self.prior_session_insights[:3]:
                parts.append(f"- {insight}")
            parts.append("")

        return "\n".join(parts)


@dataclass
class LearningSynthesis:
    """Synthesized learnings across multiple sessions"""
    timestamp: str
    sessions_analyzed: int
    period_days: int
    key_patterns: List[str]
    recurring_decisions: List[Dict[str, Any]]
    unresolved_questions: List[str]
    success_factors: List[str]
    failure_factors: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class CrossSessionLearning:
    """
    Manages learning continuity across CPU sessions.

    Responsibilities:
    - Prepare rich context for new sessions
    - Track session outcomes and learnings
    - Synthesize knowledge across sessions
    - Identify patterns in successful/failed sessions
    """

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.intercom_dir = self.repo_root / "ai" / "intercom"
        self.kernels_dir = self.repo_root / "ai" / "memory" / "kernels"

        # Session learning storage
        self.session_log = self.state_dir / "session_learnings.jsonl"
        self.synthesis_file = self.state_dir / "learning_synthesis.json"

        # Context history
        self.context_log = self.state_dir / "session_contexts.jsonl"

    # =========================================================================
    # Session Preparation
    # =========================================================================

    def prepare_session_context(
        self,
        session_id: str,
        kernel_ids: Optional[List[str]] = None,
        include_recent_days: int = 7
    ) -> SessionContext:
        """
        Prepare comprehensive context for a new session.

        Loads:
        - Kernel summaries and key decisions
        - Recent lessons from all relevant kernels
        - Open questions requiring attention
        - Insights from prior similar sessions
        """
        if kernel_ids is None:
            kernel_ids = list_kernels()

        # Load kernel summaries
        kernel_summaries = {}
        recent_decisions = []
        recent_lessons = []
        open_questions = []

        for kernel_id in kernel_ids:
            kernel = load_kernel(kernel_id)
            if kernel is None:
                continue

            kernel_summaries[kernel_id] = kernel.summary

            # Collect recent decisions
            for decision in kernel.key_decisions[-5:]:
                decision_dict = decision.to_dict() if hasattr(decision, 'to_dict') else vars(decision)
                decision_dict['kernel'] = kernel_id
                recent_decisions.append(decision_dict)

            # Collect recent lessons
            for failed_path in kernel.failed_paths[-3:]:
                lesson_dict = failed_path.to_dict() if hasattr(failed_path, 'to_dict') else vars(failed_path)
                lesson_dict['kernel'] = kernel_id
                recent_lessons.append(lesson_dict)

            # Collect open questions
            open_questions.extend(kernel.open_questions)

        # Load prior session insights
        prior_insights = self._get_prior_session_insights(include_recent_days)

        context = SessionContext(
            session_id=session_id,
            prepared_at=datetime.now(timezone.utc).isoformat(),
            kernels_loaded=kernel_ids,
            kernel_summaries=kernel_summaries,
            recent_decisions=recent_decisions,
            recent_lessons=recent_lessons,
            open_questions=open_questions[:10],  # Limit to top 10
            prior_session_insights=prior_insights
        )

        # Log context preparation
        self._log_context(context)

        return context

    def _get_prior_session_insights(self, days: int) -> List[str]:
        """Get insights from recent sessions"""
        insights = []

        if not self.session_log.exists():
            return insights

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        try:
            with open(self.session_log) as f:
                for line in f:
                    try:
                        learning = json.loads(line)
                        ts = learning.get("timestamp", "")
                        if ts:
                            learning_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if learning_dt >= cutoff:
                                insights.extend(learning.get("key_insights", []))
                    except:
                        continue
        except:
            pass

        # Deduplicate and limit
        seen = set()
        unique_insights = []
        for insight in insights:
            if insight not in seen:
                seen.add(insight)
                unique_insights.append(insight)

        return unique_insights[:10]

    def _log_context(self, context: SessionContext):
        """Log context preparation for audit"""
        try:
            self.context_log.parent.mkdir(parents=True, exist_ok=True)

            with open(self.context_log, 'a') as f:
                f.write(json.dumps(context.to_dict()) + '\n')
        except:
            pass

    # =========================================================================
    # Session Recording
    # =========================================================================

    def record_session_outcome(
        self,
        session_id: str,
        outcome: SessionOutcome,
        key_insights: Optional[List[str]] = None
    ) -> SessionLearning:
        """
        Record the outcome and learnings from a completed session.

        Extracts learning metrics from the session thread and CPU instance.
        """
        # Load session data
        cpu_instance = self._load_cpu_instance(session_id)
        thread_messages = self._load_session_thread(session_id)

        # Count learning events
        decisions_made = 0
        lessons_learned = 0
        questions_raised = 0

        if key_insights is None:
            key_insights = []

        # Analyze messages for learning content
        for message in thread_messages:
            content = message.get("content", "").upper()

            if any(marker in content for marker in ["DECISION:", "RECOMMENDATION:", "WE SHOULD"]):
                decisions_made += 1
            if any(marker in content for marker in ["LESSON:", "LEARNED:", "MISTAKE WAS"]):
                lessons_learned += 1
            if any(marker in content for marker in ["QUESTION:", "OPEN QUESTION", "?"]):
                questions_raised += 1

        # Determine context quality
        context_quality = self._assess_context_quality(session_id)

        # Get kernels used
        kernels_used = []
        if cpu_instance:
            kernels_used = cpu_instance.get("bound_kernels", [])

        learning = SessionLearning(
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            kernels_used=kernels_used,
            decisions_made=decisions_made,
            lessons_learned=lessons_learned,
            questions_raised=questions_raised,
            outcome=outcome,
            key_insights=key_insights,
            context_quality=context_quality
        )

        # Log the learning
        self._log_session_learning(learning)

        return learning

    def _load_cpu_instance(self, session_id: str) -> Optional[Dict]:
        """Load CPU instance for a session"""
        cpu_file = self.intercom_dir / session_id / "cpu_instance.json"

        if cpu_file.exists():
            try:
                with open(cpu_file) as f:
                    return json.load(f)
            except:
                pass

        return None

    def _load_session_thread(self, session_id: str) -> List[Dict]:
        """Load messages from a session thread"""
        thread_file = self.intercom_dir / session_id / "thread.jsonl"
        messages = []

        if thread_file.exists():
            try:
                with open(thread_file) as f:
                    for line in f:
                        if line.strip():
                            messages.append(json.loads(line))
            except:
                pass

        return messages

    def _assess_context_quality(self, session_id: str) -> float:
        """Assess how well context was prepared for this session"""
        # Check if context was prepared
        quality = 0.5  # Default mid-quality

        if not self.context_log.exists():
            return quality

        try:
            with open(self.context_log) as f:
                for line in f:
                    try:
                        context = json.loads(line)
                        if context.get("session_id") == session_id:
                            # Context was prepared
                            quality = 0.7

                            # Bonus for having kernels
                            if context.get("kernels_loaded"):
                                quality += 0.1

                            # Bonus for recent decisions
                            if context.get("recent_decisions"):
                                quality += 0.1

                            # Bonus for prior insights
                            if context.get("prior_session_insights"):
                                quality += 0.1

                            break
                    except:
                        continue
        except:
            pass

        return min(1.0, quality)

    def _log_session_learning(self, learning: SessionLearning):
        """Log session learning"""
        try:
            self.session_log.parent.mkdir(parents=True, exist_ok=True)

            with open(self.session_log, 'a') as f:
                f.write(json.dumps(learning.to_dict()) + '\n')
        except:
            pass

    # =========================================================================
    # Learning Synthesis
    # =========================================================================

    def synthesize_learnings(
        self,
        days: int = 30,
        min_sessions: int = 3
    ) -> LearningSynthesis:
        """
        Synthesize learnings across multiple sessions.

        Identifies:
        - Patterns in successful sessions
        - Common failure modes
        - Recurring decisions
        - Unresolved questions
        """
        # Load recent session learnings
        learnings = self._load_recent_learnings(days)

        if len(learnings) < min_sessions:
            return LearningSynthesis(
                timestamp=datetime.now(timezone.utc).isoformat(),
                sessions_analyzed=len(learnings),
                period_days=days,
                key_patterns=["Insufficient sessions for synthesis"],
                recurring_decisions=[],
                unresolved_questions=[],
                success_factors=[],
                failure_factors=[],
                recommendations=["Run more CPU sessions to enable synthesis"]
            )

        # Analyze patterns
        key_patterns = []
        recurring_decisions = []
        unresolved_questions = set()
        success_factors = []
        failure_factors = []

        # Separate by outcome
        successful = [l for l in learnings if l.get("outcome") == "successful"]
        unsuccessful = [l for l in learnings if l.get("outcome") == "unsuccessful"]

        # Success patterns
        if successful:
            avg_decisions = sum(l.get("decisions_made", 0) for l in successful) / len(successful)
            avg_context_quality = sum(l.get("context_quality", 0) for l in successful) / len(successful)

            success_factors.append(f"Avg decisions per successful session: {avg_decisions:.1f}")
            success_factors.append(f"Avg context quality in successful sessions: {avg_context_quality:.0%}")

            # Collect insights from successful sessions
            for l in successful:
                key_patterns.extend(l.get("key_insights", []))

        # Failure patterns
        if unsuccessful:
            avg_decisions = sum(l.get("decisions_made", 0) for l in unsuccessful) / len(unsuccessful)
            avg_context_quality = sum(l.get("context_quality", 0) for l in unsuccessful) / len(unsuccessful)

            failure_factors.append(f"Avg decisions per unsuccessful session: {avg_decisions:.1f}")
            failure_factors.append(f"Avg context quality in unsuccessful sessions: {avg_context_quality:.0%}")

        # Analyze kernel usage patterns
        kernel_success_rate = {}
        for l in learnings:
            outcome = l.get("outcome", "inconclusive")
            is_success = outcome == "successful"
            for kernel in l.get("kernels_used", []):
                if kernel not in kernel_success_rate:
                    kernel_success_rate[kernel] = {"success": 0, "total": 0}
                kernel_success_rate[kernel]["total"] += 1
                if is_success:
                    kernel_success_rate[kernel]["success"] += 1

        for kernel, stats in kernel_success_rate.items():
            if stats["total"] >= 2:
                rate = stats["success"] / stats["total"]
                if rate >= 0.7:
                    success_factors.append(f"Kernel '{kernel}' associated with high success rate ({rate:.0%})")
                elif rate <= 0.3:
                    failure_factors.append(f"Kernel '{kernel}' associated with low success rate ({rate:.0%})")

        # Generate recommendations
        recommendations = []

        if avg_context_quality < 0.7 if successful else True:
            recommendations.append("Improve session context preparation to increase success rate")

        if not successful and unsuccessful:
            recommendations.append("Analyze unsuccessful sessions for common failure modes")

        if len(unresolved_questions) > 5:
            recommendations.append(f"Address accumulated open questions ({len(unresolved_questions)} pending)")

        # Deduplicate patterns
        key_patterns = list(set(key_patterns))[:10]

        synthesis = LearningSynthesis(
            timestamp=datetime.now(timezone.utc).isoformat(),
            sessions_analyzed=len(learnings),
            period_days=days,
            key_patterns=key_patterns,
            recurring_decisions=recurring_decisions[:10],
            unresolved_questions=list(unresolved_questions)[:10],
            success_factors=success_factors[:5],
            failure_factors=failure_factors[:5],
            recommendations=recommendations[:5]
        )

        # Save synthesis
        self._save_synthesis(synthesis)

        return synthesis

    def _load_recent_learnings(self, days: int) -> List[Dict]:
        """Load session learnings from recent period"""
        if not self.session_log.exists():
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        learnings = []

        try:
            with open(self.session_log) as f:
                for line in f:
                    try:
                        learning = json.loads(line)
                        ts = learning.get("timestamp", "")
                        if ts:
                            learning_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if learning_dt >= cutoff:
                                learnings.append(learning)
                    except:
                        continue
        except:
            pass

        return learnings

    def _save_synthesis(self, synthesis: LearningSynthesis):
        """Save synthesis to file"""
        try:
            self.synthesis_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.synthesis_file, 'w') as f:
                json.dump(synthesis.to_dict(), f, indent=2)
        except:
            pass

    # =========================================================================
    # Integration Methods
    # =========================================================================

    def inject_context_into_session(
        self,
        session_id: str,
        kernel_ids: List[str]
    ) -> str:
        """
        Prepare and return context prompt for injection into session.

        This is the main entry point for pre-session context preparation.
        """
        context = self.prepare_session_context(session_id, kernel_ids)
        return context.to_context_prompt()

    def auto_record_session(self, session_id: str) -> SessionLearning:
        """
        Automatically record session outcome based on analysis.

        Infers outcome from session content and metrics.
        """
        thread = self._load_session_thread(session_id)
        cpu = self._load_cpu_instance(session_id)

        # Infer outcome based on content analysis
        outcome = SessionOutcome.INCONCLUSIVE

        if not thread:
            outcome = SessionOutcome.ERROR
        else:
            # Look for success/failure indicators
            all_content = " ".join(m.get("content", "") for m in thread).lower()

            success_indicators = ["completed", "success", "achieved", "resolved", "done"]
            failure_indicators = ["failed", "error", "unable", "blocked", "stuck"]

            success_count = sum(1 for ind in success_indicators if ind in all_content)
            failure_count = sum(1 for ind in failure_indicators if ind in all_content)

            if success_count > failure_count and success_count > 0:
                outcome = SessionOutcome.SUCCESSFUL
            elif failure_count > success_count and failure_count > 0:
                outcome = SessionOutcome.UNSUCCESSFUL
            elif success_count > 0 and failure_count > 0:
                outcome = SessionOutcome.PARTIAL
            else:
                outcome = SessionOutcome.INCONCLUSIVE

        # Extract key insights
        key_insights = self._extract_session_insights(thread)

        return self.record_session_outcome(session_id, outcome, key_insights)

    def _extract_session_insights(self, thread: List[Dict]) -> List[str]:
        """Extract key insights from session thread"""
        insights = []

        for message in thread:
            content = message.get("content", "")

            # Look for explicitly marked insights
            import re
            patterns = [
                r"(?:KEY INSIGHT|IMPORTANT|TAKEAWAY)[:]\s*(.+?)(?:\n|$)",
                r"(?:In conclusion|To summarize)[:]*\s*(.+?)(?:\n|$)"
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match) > 20:  # Meaningful length
                        insights.append(match.strip()[:200])

        return insights[:5]


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cross-Session Learning Persistence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prepare context for a new session
  python -m ai_nexus.cross_session_learning prepare --session-id new_session

  # Record session outcome
  python -m ai_nexus.cross_session_learning record --session-id session_123 --outcome successful

  # Auto-record session (infer outcome)
  python -m ai_nexus.cross_session_learning auto-record --session-id session_123

  # Synthesize learnings across sessions
  python -m ai_nexus.cross_session_learning synthesize
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Prepare command
    prepare_parser = subparsers.add_parser("prepare", help="Prepare session context")
    prepare_parser.add_argument("--session-id", required=True, help="Session ID")
    prepare_parser.add_argument("--kernels", help="Comma-separated kernel IDs")
    prepare_parser.add_argument("--output", choices=["prompt", "json"], default="prompt")

    # Record command
    record_parser = subparsers.add_parser("record", help="Record session outcome")
    record_parser.add_argument("--session-id", required=True, help="Session ID")
    record_parser.add_argument("--outcome", required=True,
                              choices=["successful", "partial", "unsuccessful", "inconclusive", "error"])
    record_parser.add_argument("--insights", help="Comma-separated key insights")

    # Auto-record command
    auto_parser = subparsers.add_parser("auto-record", help="Auto-record session")
    auto_parser.add_argument("--session-id", required=True, help="Session ID")

    # Synthesize command
    synth_parser = subparsers.add_parser("synthesize", help="Synthesize learnings")
    synth_parser.add_argument("--days", type=int, default=30, help="Days to analyze")
    synth_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    persistence = CrossSessionLearning()

    if args.command == "prepare":
        kernel_ids = None
        if args.kernels:
            kernel_ids = [k.strip() for k in args.kernels.split(",")]

        context = persistence.prepare_session_context(args.session_id, kernel_ids)

        if args.output == "json":
            print(json.dumps(context.to_dict(), indent=2))
        else:
            print(context.to_context_prompt())

    elif args.command == "record":
        outcome = SessionOutcome(args.outcome)
        insights = []
        if args.insights:
            insights = [i.strip() for i in args.insights.split(",")]

        learning = persistence.record_session_outcome(args.session_id, outcome, insights)

        print(f"✅ Recorded session outcome:")
        print(f"   Session: {learning.session_id}")
        print(f"   Outcome: {learning.outcome.value}")
        print(f"   Decisions: {learning.decisions_made}")
        print(f"   Lessons: {learning.lessons_learned}")
        print(f"   Context Quality: {learning.context_quality:.0%}")

    elif args.command == "auto-record":
        learning = persistence.auto_record_session(args.session_id)

        print(f"✅ Auto-recorded session:")
        print(f"   Session: {learning.session_id}")
        print(f"   Inferred Outcome: {learning.outcome.value}")
        print(f"   Key Insights: {len(learning.key_insights)}")

    elif args.command == "synthesize":
        synthesis = persistence.synthesize_learnings(days=args.days)

        if args.json:
            print(json.dumps(synthesis.to_dict(), indent=2))
        else:
            print(f"\n🧠 Learning Synthesis (last {args.days} days)")
            print("="*60)
            print(f"   Sessions Analyzed: {synthesis.sessions_analyzed}")

            if synthesis.key_patterns:
                print(f"\n   Key Patterns:")
                for pattern in synthesis.key_patterns[:5]:
                    print(f"      • {pattern}")

            if synthesis.success_factors:
                print(f"\n   Success Factors:")
                for factor in synthesis.success_factors:
                    print(f"      ✅ {factor}")

            if synthesis.failure_factors:
                print(f"\n   Failure Factors:")
                for factor in synthesis.failure_factors:
                    print(f"      ❌ {factor}")

            if synthesis.recommendations:
                print(f"\n   Recommendations:")
                for rec in synthesis.recommendations:
                    print(f"      💡 {rec}")


if __name__ == "__main__":
    main()
