"""
Automatic Kernel Update Applier v1.0

Automatically extracts and applies kernel updates from CPU session outputs.
Addresses the critical gap: KERNEL UPDATES GENERATED BUT NOT AUTO-APPLIED.

Features:
- Parses CPU session threads to extract update suggestions
- Uses pattern matching and heuristics to identify:
  - Decisions (strategic choices with rationale)
  - Failed paths (lessons learned from mistakes)
  - Questions (unresolved issues)
  - Summary updates (compressed knowledge)
- Validates updates before application
- Maintains audit trail of all updates
- Supports dry-run mode for safety

API:
    applier = KernelUpdateApplier()
    updates = applier.extract_updates_from_session(conversation_id)
    result = applier.apply_updates(updates)

CLI:
    python -m ai_nexus.kernel_update_applier extract --session-id <id>
    python -m ai_nexus.kernel_update_applier apply --session-id <id>
    python -m ai_nexus.kernel_update_applier auto --session-id <id>
"""

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.spark_plug_types import (
    CpuMessage,
    KernelUpdate,
    create_kernel_update_decision,
    create_kernel_update_failed_path
)
from ai_nexus.memory_kernels import (
    load_kernel,
    append_kernel_update,
    list_kernels
)


class UpdateType(Enum):
    """Types of kernel updates"""
    DECISION = "decision"
    FAILED_PATH = "failed_path"
    QUESTION = "question"
    SUMMARY = "summary"


class UpdateConfidence(Enum):
    """Confidence level of extracted update"""
    HIGH = "high"       # Clear, explicit suggestion
    MEDIUM = "medium"   # Likely suggestion, needs validation
    LOW = "low"         # Possible suggestion, manual review recommended


@dataclass
class ExtractedUpdate:
    """A kernel update extracted from CPU session"""
    update_type: UpdateType
    content: Dict[str, Any]
    confidence: UpdateConfidence
    source_message_id: str
    source_agent: str
    target_kernels: List[str]
    raw_text: str
    extraction_method: str  # "pattern", "heuristic", "explicit"

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['update_type'] = self.update_type.value
        data['confidence'] = self.confidence.value
        return data


@dataclass
class ApplicationResult:
    """Result of applying updates to kernels"""
    success: bool
    updates_applied: int
    updates_skipped: int
    updates_failed: int
    details: List[Dict[str, Any]]
    errors: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


class KernelUpdateApplier:
    """
    Automatic kernel update extraction and application.

    Parses CPU session outputs to identify and apply kernel updates:
    - Decisions: "We should...", "The approach is...", "DECISION:"
    - Failed paths: "This didn't work...", "Mistake was...", "LESSON:"
    - Questions: "Open question:", "Need to investigate:", "QUESTION:"
    - Summary updates: "Key takeaway:", "Summary:", "In conclusion:"
    """

    # Pattern matchers for different update types
    DECISION_PATTERNS = [
        r"(?:DECISION|RECOMMENDATION|STRATEGY)[:]\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"(?:We should|The approach is|I recommend|Best practice is)[:]*\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"(?:Going forward|From now on|The plan is)[:]*\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"\*\*Decision\*\*[:]*\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
    ]

    FAILED_PATH_PATTERNS = [
        r"(?:LESSON|MISTAKE|FAILURE|LEARNING)[:]\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"(?:This didn't work|We tried but|The mistake was|Failed because)[:]*\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"(?:Don't|Avoid|Never)(?:\s+\w+){1,5}\s+because\s+(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"\*\*Lesson\*\*[:]*\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
    ]

    QUESTION_PATTERNS = [
        r"(?:QUESTION|OPEN QUESTION|TO INVESTIGATE|TODO)[:]\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"(?:We still need to|Open question:|Unresolved:|Need to figure out)[:]*\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"\?(?:\s*)(.+?\?)(?:\n|\Z)",
        r"\*\*Question\*\*[:]*\s*(.+?)(?:\n\n|\n[A-Z]|\Z)",
    ]

    SUMMARY_PATTERNS = [
        r"(?:SUMMARY|KEY TAKEAWAY|CONCLUSION|TL;DR)[:]\s*(.+?)(?:\n\n|\Z)",
        r"(?:In summary|To summarize|Key point is|Bottom line)[:]*\s*(.+?)(?:\n\n|\Z)",
        r"\*\*Summary\*\*[:]*\s*(.+?)(?:\n\n|\Z)",
    ]

    # Explicit update markers (highest confidence)
    EXPLICIT_UPDATE_MARKERS = [
        "KERNEL_UPDATE:",
        "UPDATE_DECISION:",
        "UPDATE_LESSON:",
        "UPDATE_QUESTION:",
        "APPLY_TO_KERNEL:"
    ]

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.intercom_dir = self.repo_root / "ai" / "intercom"
        self.update_log = self.repo_root / "state" / "kernel_update_log.jsonl"

        # Cache for loaded sessions
        self._session_cache: Dict[str, List[CpuMessage]] = {}

    # =========================================================================
    # Core Extraction Methods
    # =========================================================================

    def extract_updates_from_session(
        self,
        conversation_id: str,
        target_kernels: Optional[List[str]] = None
    ) -> List[ExtractedUpdate]:
        """
        Extract all kernel updates from a CPU session.

        Args:
            conversation_id: ID of the CPU session
            target_kernels: Optional list of target kernels (if not specified,
                           uses bound kernels from CPU instance)

        Returns:
            List of extracted updates
        """
        # Load session messages
        messages = self._load_session_messages(conversation_id)
        if not messages:
            print(f"No messages found for session: {conversation_id}")
            return []

        # Get target kernels
        if target_kernels is None:
            target_kernels = self._get_session_bound_kernels(conversation_id)

        if not target_kernels:
            # Default to all enabled kernels
            target_kernels = list_kernels()

        # Extract updates from each message
        all_updates = []

        for message in messages:
            # Skip system messages
            if message.from_ == "system":
                continue

            updates = self._extract_from_message(message, target_kernels)
            all_updates.extend(updates)

        # Deduplicate similar updates
        deduped_updates = self._deduplicate_updates(all_updates)

        return deduped_updates

    def _extract_from_message(
        self,
        message: CpuMessage,
        target_kernels: List[str]
    ) -> List[ExtractedUpdate]:
        """Extract updates from a single message"""
        updates = []
        content = message.content

        # Check for explicit update markers first (highest priority)
        explicit_updates = self._extract_explicit_updates(message, target_kernels)
        updates.extend(explicit_updates)

        # Extract decisions
        decisions = self._extract_decisions(message, target_kernels)
        updates.extend(decisions)

        # Extract failed paths/lessons
        lessons = self._extract_failed_paths(message, target_kernels)
        updates.extend(lessons)

        # Extract questions
        questions = self._extract_questions(message, target_kernels)
        updates.extend(questions)

        # Extract summary updates
        summaries = self._extract_summaries(message, target_kernels)
        updates.extend(summaries)

        return updates

    def _extract_explicit_updates(
        self,
        message: CpuMessage,
        target_kernels: List[str]
    ) -> List[ExtractedUpdate]:
        """Extract explicitly marked updates (KERNEL_UPDATE:, etc.)"""
        updates = []
        content = message.content

        # Look for KERNEL_UPDATE: JSON blocks
        kernel_update_pattern = r"KERNEL_UPDATE:\s*```(?:json)?\s*(\{[\s\S]*?\})\s*```"
        matches = re.findall(kernel_update_pattern, content, re.IGNORECASE)

        for match in matches:
            try:
                update_data = json.loads(match)

                update_type_str = update_data.get("type", "decision")
                update_type = UpdateType(update_type_str) if update_type_str in [t.value for t in UpdateType] else UpdateType.DECISION

                target = update_data.get("kernel", update_data.get("kernels", target_kernels))
                if isinstance(target, str):
                    target = [target]

                updates.append(ExtractedUpdate(
                    update_type=update_type,
                    content=update_data.get("content", update_data),
                    confidence=UpdateConfidence.HIGH,
                    source_message_id=message.msg_id,
                    source_agent=message.from_,
                    target_kernels=target,
                    raw_text=match,
                    extraction_method="explicit"
                ))
            except json.JSONDecodeError:
                pass

        return updates

    def _extract_decisions(
        self,
        message: CpuMessage,
        target_kernels: List[str]
    ) -> List[ExtractedUpdate]:
        """Extract decision-type updates"""
        updates = []
        content = message.content

        for pattern in self.DECISION_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)

            for match in matches:
                # Clean up the match
                decision_text = self._clean_extracted_text(match)

                if len(decision_text) < 20:  # Too short to be meaningful
                    continue

                # Try to extract rationale
                rationale = self._extract_rationale(content, match)

                # Determine confidence
                confidence = UpdateConfidence.HIGH if any(
                    marker in content.upper()
                    for marker in ["DECISION:", "RECOMMENDATION:", "**DECISION**"]
                ) else UpdateConfidence.MEDIUM

                updates.append(ExtractedUpdate(
                    update_type=UpdateType.DECISION,
                    content={
                        "decision": decision_text,
                        "rationale": rationale or "Extracted from CPU session discussion"
                    },
                    confidence=confidence,
                    source_message_id=message.msg_id,
                    source_agent=message.from_,
                    target_kernels=target_kernels,
                    raw_text=match,
                    extraction_method="pattern"
                ))

        return updates

    def _extract_failed_paths(
        self,
        message: CpuMessage,
        target_kernels: List[str]
    ) -> List[ExtractedUpdate]:
        """Extract failed path/lesson updates"""
        updates = []
        content = message.content

        for pattern in self.FAILED_PATH_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)

            for match in matches:
                lesson_text = self._clean_extracted_text(match)

                if len(lesson_text) < 15:
                    continue

                # Try to parse attempt/failure/lesson structure
                attempt, failure, lesson = self._parse_failed_path(lesson_text)

                confidence = UpdateConfidence.HIGH if any(
                    marker in content.upper()
                    for marker in ["LESSON:", "MISTAKE:", "**LESSON**"]
                ) else UpdateConfidence.MEDIUM

                updates.append(ExtractedUpdate(
                    update_type=UpdateType.FAILED_PATH,
                    content={
                        "attempt": attempt or "Previous approach",
                        "failure": failure or "Did not achieve expected results",
                        "lesson": lesson or lesson_text
                    },
                    confidence=confidence,
                    source_message_id=message.msg_id,
                    source_agent=message.from_,
                    target_kernels=target_kernels,
                    raw_text=match,
                    extraction_method="pattern"
                ))

        return updates

    def _extract_questions(
        self,
        message: CpuMessage,
        target_kernels: List[str]
    ) -> List[ExtractedUpdate]:
        """Extract question/open-issue updates"""
        updates = []
        content = message.content

        for pattern in self.QUESTION_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)

            for match in matches:
                question_text = self._clean_extracted_text(match)

                if len(question_text) < 10:
                    continue

                # Ensure it looks like a question
                if not question_text.endswith("?"):
                    question_text += "?"

                confidence = UpdateConfidence.HIGH if any(
                    marker in content.upper()
                    for marker in ["QUESTION:", "OPEN QUESTION:", "**QUESTION**"]
                ) else UpdateConfidence.LOW

                updates.append(ExtractedUpdate(
                    update_type=UpdateType.QUESTION,
                    content={
                        "question": question_text
                    },
                    confidence=confidence,
                    source_message_id=message.msg_id,
                    source_agent=message.from_,
                    target_kernels=target_kernels,
                    raw_text=match,
                    extraction_method="pattern"
                ))

        return updates

    def _extract_summaries(
        self,
        message: CpuMessage,
        target_kernels: List[str]
    ) -> List[ExtractedUpdate]:
        """Extract summary updates"""
        updates = []
        content = message.content

        for pattern in self.SUMMARY_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)

            for match in matches:
                summary_text = self._clean_extracted_text(match)

                if len(summary_text) < 30:
                    continue

                confidence = UpdateConfidence.MEDIUM

                updates.append(ExtractedUpdate(
                    update_type=UpdateType.SUMMARY,
                    content={
                        "summary": summary_text
                    },
                    confidence=confidence,
                    source_message_id=message.msg_id,
                    source_agent=message.from_,
                    target_kernels=target_kernels,
                    raw_text=match,
                    extraction_method="pattern"
                ))

        return updates

    # =========================================================================
    # Update Application
    # =========================================================================

    def apply_updates(
        self,
        updates: List[ExtractedUpdate],
        dry_run: bool = False,
        min_confidence: UpdateConfidence = UpdateConfidence.MEDIUM
    ) -> ApplicationResult:
        """
        Apply extracted updates to kernels.

        Args:
            updates: List of extracted updates to apply
            dry_run: If True, validate but don't actually apply
            min_confidence: Minimum confidence level to apply

        Returns:
            ApplicationResult with details of what was applied
        """
        result = ApplicationResult(
            success=True,
            updates_applied=0,
            updates_skipped=0,
            updates_failed=0,
            details=[],
            errors=[]
        )

        confidence_order = {
            UpdateConfidence.HIGH: 0,
            UpdateConfidence.MEDIUM: 1,
            UpdateConfidence.LOW: 2
        }
        min_conf_val = confidence_order[min_confidence]

        for update in updates:
            # Check confidence threshold
            if confidence_order[update.confidence] > min_conf_val:
                result.updates_skipped += 1
                result.details.append({
                    "action": "skipped",
                    "reason": f"Confidence too low: {update.confidence.value}",
                    "update": update.to_dict()
                })
                continue

            # Validate target kernels exist
            valid_kernels = []
            for kernel_id in update.target_kernels:
                if load_kernel(kernel_id) is not None:
                    valid_kernels.append(kernel_id)
                else:
                    result.details.append({
                        "action": "skipped_kernel",
                        "reason": f"Kernel not found: {kernel_id}",
                        "update_type": update.update_type.value
                    })

            if not valid_kernels:
                result.updates_skipped += 1
                continue

            # Create KernelUpdate object
            kernel_update = self._create_kernel_update(update)

            if dry_run:
                result.details.append({
                    "action": "would_apply",
                    "kernels": valid_kernels,
                    "update": update.to_dict()
                })
                result.updates_applied += 1
                continue

            # Apply to each valid kernel
            for kernel_id in valid_kernels:
                try:
                    append_kernel_update(kernel_id, kernel_update)
                    result.details.append({
                        "action": "applied",
                        "kernel": kernel_id,
                        "update_type": update.update_type.value,
                        "confidence": update.confidence.value
                    })
                    result.updates_applied += 1

                    # Log the application
                    self._log_update_application(kernel_id, update, kernel_update)

                except Exception as e:
                    result.errors.append(f"Failed to apply to {kernel_id}: {str(e)}")
                    result.updates_failed += 1
                    result.success = False

        return result

    def auto_apply_from_session(
        self,
        conversation_id: str,
        dry_run: bool = False,
        min_confidence: UpdateConfidence = UpdateConfidence.MEDIUM
    ) -> ApplicationResult:
        """
        Extract and apply updates from a session in one step.

        This is the main entry point for automatic kernel update application.
        """
        print(f"🔍 Extracting updates from session: {conversation_id}")

        updates = self.extract_updates_from_session(conversation_id)

        if not updates:
            print("   No updates found in session")
            return ApplicationResult(
                success=True,
                updates_applied=0,
                updates_skipped=0,
                updates_failed=0,
                details=[{"message": "No updates found"}],
                errors=[]
            )

        print(f"   Found {len(updates)} potential updates")

        if dry_run:
            print("   [DRY RUN] - No changes will be made")

        result = self.apply_updates(updates, dry_run=dry_run, min_confidence=min_confidence)

        print(f"\n📊 Results:")
        print(f"   Applied: {result.updates_applied}")
        print(f"   Skipped: {result.updates_skipped}")
        print(f"   Failed:  {result.updates_failed}")

        if result.errors:
            print(f"\n⚠️ Errors:")
            for error in result.errors:
                print(f"   - {error}")

        return result

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _load_session_messages(self, conversation_id: str) -> List[CpuMessage]:
        """Load messages from a CPU session"""
        if conversation_id in self._session_cache:
            return self._session_cache[conversation_id]

        thread_file = self.intercom_dir / conversation_id / "thread.jsonl"

        if not thread_file.exists():
            return []

        messages = []
        try:
            with open(thread_file) as f:
                for line in f:
                    if line.strip():
                        messages.append(CpuMessage.from_jsonl_line(line))
        except Exception as e:
            print(f"Error loading session: {e}")
            return []

        self._session_cache[conversation_id] = messages
        return messages

    def _get_session_bound_kernels(self, conversation_id: str) -> List[str]:
        """Get bound kernels from CPU instance"""
        cpu_file = self.intercom_dir / conversation_id / "cpu_instance.json"

        if cpu_file.exists():
            try:
                with open(cpu_file) as f:
                    cpu_data = json.load(f)
                return cpu_data.get("bound_kernels", [])
            except:
                pass

        return []

    def _clean_extracted_text(self, text: str) -> str:
        """Clean up extracted text"""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Truncate if too long
        if len(text) > 500:
            text = text[:500] + "..."

        return text.strip()

    def _extract_rationale(self, full_content: str, decision_text: str) -> Optional[str]:
        """Try to extract rationale for a decision"""
        # Look for "because", "since", "reason" near the decision
        patterns = [
            r"because\s+(.+?)(?:\n|\.|$)",
            r"since\s+(.+?)(?:\n|\.|$)",
            r"(?:reason|rationale)[:]*\s*(.+?)(?:\n|\.|$)"
        ]

        # Search in the area around the decision
        decision_pos = full_content.find(decision_text[:50])
        if decision_pos >= 0:
            search_area = full_content[max(0, decision_pos - 200):decision_pos + len(decision_text) + 200]

            for pattern in patterns:
                match = re.search(pattern, search_area, re.IGNORECASE)
                if match:
                    return self._clean_extracted_text(match.group(1))

        return None

    def _parse_failed_path(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Try to parse a failed path into attempt/failure/lesson"""
        # Look for structured format
        patterns = [
            (r"tried\s+(.+?)\s+but\s+(.+)", "attempt_failure"),
            (r"(.+?)\s+didn't work\s+because\s+(.+)", "attempt_failure"),
            (r"lesson[:]*\s*(.+)", "lesson_only")
        ]

        for pattern, ptype in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if ptype == "attempt_failure":
                    return (match.group(1), match.group(2), text)
                elif ptype == "lesson_only":
                    return (None, None, match.group(1))

        return (None, None, text)

    def _deduplicate_updates(self, updates: List[ExtractedUpdate]) -> List[ExtractedUpdate]:
        """Remove duplicate or very similar updates"""
        if not updates:
            return []

        seen_hashes = set()
        deduped = []

        for update in updates:
            # Create a simple hash based on type and content
            content_str = json.dumps(update.content, sort_keys=True)
            hash_key = f"{update.update_type.value}:{content_str[:100]}"

            if hash_key not in seen_hashes:
                seen_hashes.add(hash_key)
                deduped.append(update)

        return deduped

    def _create_kernel_update(self, extracted: ExtractedUpdate) -> KernelUpdate:
        """Convert ExtractedUpdate to KernelUpdate"""
        if extracted.update_type == UpdateType.DECISION:
            return create_kernel_update_decision(
                decision=extracted.content.get("decision", ""),
                rationale=extracted.content.get("rationale", ""),
                source=f"auto_extracted:{extracted.source_message_id}",
                agent=extracted.source_agent
            )

        elif extracted.update_type == UpdateType.FAILED_PATH:
            return create_kernel_update_failed_path(
                attempt=extracted.content.get("attempt", ""),
                failure=extracted.content.get("failure", ""),
                lesson=extracted.content.get("lesson", ""),
                source=f"auto_extracted:{extracted.source_message_id}",
                agent=extracted.source_agent
            )

        elif extracted.update_type == UpdateType.QUESTION:
            return KernelUpdate(
                update_type="question",
                content={"question": extracted.content.get("question", "")},
                source=f"auto_extracted:{extracted.source_message_id}",
                agent=extracted.source_agent
            )

        elif extracted.update_type == UpdateType.SUMMARY:
            return KernelUpdate(
                update_type="summary_edit",
                content={"summary": extracted.content.get("summary", "")},
                source=f"auto_extracted:{extracted.source_message_id}",
                agent=extracted.source_agent
            )

        else:
            raise ValueError(f"Unknown update type: {extracted.update_type}")

    def _log_update_application(
        self,
        kernel_id: str,
        extracted: ExtractedUpdate,
        applied: KernelUpdate
    ):
        """Log update application for audit trail"""
        try:
            self.update_log.parent.mkdir(parents=True, exist_ok=True)

            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "kernel_id": kernel_id,
                "update_type": extracted.update_type.value,
                "confidence": extracted.confidence.value,
                "source_agent": extracted.source_agent,
                "source_message_id": extracted.source_message_id,
                "extraction_method": extracted.extraction_method,
                "content_preview": str(extracted.content)[:200]
            }

            with open(self.update_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except:
            pass  # Best effort logging


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automatic Kernel Update Applier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract updates from a session (dry run)
  python -m ai_nexus.kernel_update_applier extract --session-id autokernel_risk_model_v2_20251127

  # Apply updates from a session
  python -m ai_nexus.kernel_update_applier apply --session-id autokernel_risk_model_v2_20251127

  # Auto-extract and apply in one step
  python -m ai_nexus.kernel_update_applier auto --session-id autokernel_risk_model_v2_20251127

  # List available sessions
  python -m ai_nexus.kernel_update_applier list-sessions
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract updates from session")
    extract_parser.add_argument("--session-id", required=True, help="CPU session ID")
    extract_parser.add_argument("--kernels", help="Comma-separated target kernel IDs")
    extract_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply previously extracted updates")
    apply_parser.add_argument("--session-id", required=True, help="CPU session ID")
    apply_parser.add_argument("--dry-run", action="store_true", help="Validate without applying")
    apply_parser.add_argument("--min-confidence", choices=["high", "medium", "low"], default="medium")
    apply_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Auto command
    auto_parser = subparsers.add_parser("auto", help="Extract and apply in one step")
    auto_parser.add_argument("--session-id", required=True, help="CPU session ID")
    auto_parser.add_argument("--dry-run", action="store_true", help="Validate without applying")
    auto_parser.add_argument("--min-confidence", choices=["high", "medium", "low"], default="medium")
    auto_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # List sessions command
    list_parser = subparsers.add_parser("list-sessions", help="List available CPU sessions")
    list_parser.add_argument("--recent", type=int, default=10, help="Show N most recent sessions")

    args = parser.parse_args()

    applier = KernelUpdateApplier()

    if args.command == "extract":
        target_kernels = None
        if args.kernels:
            target_kernels = [k.strip() for k in args.kernels.split(",")]

        updates = applier.extract_updates_from_session(args.session_id, target_kernels)

        if args.json:
            print(json.dumps([u.to_dict() for u in updates], indent=2))
        else:
            print(f"\n🔍 Extracted {len(updates)} potential updates from session: {args.session_id}")
            print("="*60)

            for i, update in enumerate(updates, 1):
                confidence_emoji = {
                    UpdateConfidence.HIGH: "🟢",
                    UpdateConfidence.MEDIUM: "🟡",
                    UpdateConfidence.LOW: "🔴"
                }
                emoji = confidence_emoji.get(update.confidence, "❓")

                print(f"\n{i}. {emoji} [{update.update_type.value.upper()}] "
                      f"(confidence: {update.confidence.value})")
                print(f"   Agent: {update.source_agent}")
                print(f"   Targets: {', '.join(update.target_kernels)}")

                # Print content preview
                content_str = json.dumps(update.content)
                if len(content_str) > 100:
                    content_str = content_str[:100] + "..."
                print(f"   Content: {content_str}")

            print("\n" + "="*60)

    elif args.command == "apply":
        min_confidence = UpdateConfidence[args.min_confidence.upper()]

        updates = applier.extract_updates_from_session(args.session_id)
        result = applier.apply_updates(updates, dry_run=args.dry_run, min_confidence=min_confidence)

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            mode = "[DRY RUN]" if args.dry_run else ""
            print(f"\n📊 Application Result {mode}")
            print("="*60)
            print(f"   ✅ Applied: {result.updates_applied}")
            print(f"   ⏭️  Skipped: {result.updates_skipped}")
            print(f"   ❌ Failed:  {result.updates_failed}")

            if result.errors:
                print(f"\n⚠️ Errors:")
                for error in result.errors:
                    print(f"   - {error}")

    elif args.command == "auto":
        min_confidence = UpdateConfidence[args.min_confidence.upper()]

        result = applier.auto_apply_from_session(
            args.session_id,
            dry_run=args.dry_run,
            min_confidence=min_confidence
        )

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))

    elif args.command == "list-sessions":
        intercom_dir = REPO_ROOT / "ai" / "intercom"

        if not intercom_dir.exists():
            print("No sessions found (intercom directory does not exist)")
            return

        sessions = []
        for session_dir in intercom_dir.iterdir():
            if session_dir.is_dir():
                thread_file = session_dir / "thread.jsonl"
                if thread_file.exists():
                    mtime = thread_file.stat().st_mtime
                    sessions.append((session_dir.name, mtime))

        sessions.sort(key=lambda x: x[1], reverse=True)
        sessions = sessions[:args.recent]

        if not sessions:
            print("No sessions found")
            return

        print(f"\n📋 Recent CPU Sessions (last {args.recent}):")
        print("="*60)

        for session_id, mtime in sessions:
            dt = datetime.fromtimestamp(mtime)
            print(f"   {session_id}")
            print(f"      Last modified: {dt.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
