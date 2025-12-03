"""
History-to-Kernels Connector v0.1 (Part 3: User Expansion)

Converts recent history events into kernel update prompts.

This is the bridge between:
    - ai/history/user_events.jsonl (raw events)
    - ai/memory/kernels/*.json (compressed memory)

Flow:
    1. Load recent history events
    2. Build context-aware summary
    3. Generate prompt for CPU to update kernel
    4. CPU processes prompt → creates KernelUpdate → updates kernel

API:
    - build_history_summary(max_events, event_type, kernel_id) -> str
    - build_kernel_update_prompt(kernel_id, max_events) -> str

Safety:
    - File-based, no network calls
    - No imports of trading/risk/decider/executor modules
    - Read-only (doesn't modify kernels directly)

See: docs/SPARK_PLUG_PART3_USER_CONNECTOR_v0.1.md
"""

from typing import List, Optional
from pathlib import Path

from ai_nexus.spark_plug_types import HistoryEvent
from ai_nexus.history_logger import load_history_events
from ai_nexus.spark_plug_history import load_kernel_history_events
from ai_nexus.memory_kernels import load_kernel

# Paths
REPO_ROOT = Path(__file__).parent.parent


# =============================================================================
# Core API
# =============================================================================

def build_history_summary(
    max_events: int = 20,
    event_type: Optional[str] = None,
    kernel_id: Optional[str] = None
) -> str:
    """
    Build a natural language summary of recent history events

    Args:
        max_events: Maximum number of events to include
        event_type: Filter by event type (optional)
        kernel_id: Filter by kernel_id in context (optional)

    Returns:
        Multi-line string summarizing recent history

    Example output:
        Recent History (Last 20 Events)
        ================================

        [2025-11-26T10:30:00Z] user_message from user:froggy
        "What's the current Kelly fraction for risk model v2?"
        Context: kernel_id=risk_model_v2

        [2025-11-26T10:31:00Z] system_decision from cpu_risk_20251125_01
        "Updated Kelly fraction to 0.15 based on recent drawdown analysis"
        Context: kernel_id=risk_model_v2, decision_id=dec_001
    """
    # Load events using new unified loader if kernel_id specified
    if kernel_id:
        # Use new unified loader (prefers events.jsonl, falls back to user_events.jsonl)
        events = load_kernel_history_events(
            kernel_id=kernel_id,
            max_events=max_events,
            min_importance=None  # No importance filter for now
        )
    else:
        # Use old loader for backward compatibility when no kernel_id specified
        events = load_history_events(limit=max_events, event_type=event_type)
        # Convert old HistoryEvent objects to dict format
        events = [
            {
                "event_id": e.event_id,
                "ts": e.timestamp,
                "kind": e.event_type,
                "source": e.source,
                "summary": e.content,
                "details": e.context,
                "importance": None,
                "tags": []
            }
            for e in events
        ]

    if not events:
        return "No recent history events found."

    # Build summary
    lines = []
    lines.append(f"Recent History (Last {len(events)} Events)")
    lines.append("=" * 50)
    lines.append("")

    for event in events:
        # Handle both dict and HistoryEvent object
        timestamp = event.get("ts", event.get("timestamp", ""))
        event_type = event.get("kind", event.get("event_type", ""))
        source = event.get("source", "")
        content = event.get("summary", event.get("content", ""))
        details = event.get("details", event.get("context", {}))

        lines.append(f"[{timestamp}] {event_type} from {source}")
        lines.append(f'"{content}"')

        # Add details/context if present
        if details:
            ctx_str = ", ".join(f"{k}={v}" for k, v in details.items())
            lines.append(f"Context: {ctx_str}")

        lines.append("")

    return "\n".join(lines)


def build_kernel_update_prompt(
    kernel_id: str,
    max_events: int = 20,
    include_kernel_state: bool = True
) -> str:
    """
    Build a prompt for CPU to update a kernel based on recent history

    This prompt is designed to be fed into a CPU (Part 1) which will then
    generate KernelUpdate objects to update the kernel.

    Args:
        kernel_id: ID of the kernel to update
        max_events: Maximum number of history events to include
        include_kernel_state: Whether to include current kernel state in prompt

    Returns:
        Complete prompt string for CPU

    Example usage:
        prompt = build_kernel_update_prompt("risk_model_v2", max_events=20)
        # Feed prompt to CPU
        # CPU generates KernelUpdate
        # KernelUpdate applied to kernel via append_kernel_update()
    """
    prompt_lines = []

    # Header
    prompt_lines.append("=" * 70)
    prompt_lines.append("KERNEL UPDATE TASK")
    prompt_lines.append("=" * 70)
    prompt_lines.append("")
    prompt_lines.append(f"Target Kernel: {kernel_id}")
    prompt_lines.append("")

    # Current kernel state (optional)
    if include_kernel_state:
        kernel = load_kernel(kernel_id)
        if kernel:
            prompt_lines.append("--- Current Kernel State ---")
            prompt_lines.append("")
            prompt_lines.append(f"Topic: {kernel.topic}")
            prompt_lines.append(f"Last Updated: {kernel.last_updated}")
            prompt_lines.append("")
            prompt_lines.append("Summary:")
            prompt_lines.append(kernel.summary if kernel.summary else "(empty)")
            prompt_lines.append("")
            prompt_lines.append(f"Key Decisions: {len(kernel.key_decisions)}")
            if kernel.key_decisions:
                prompt_lines.append("  Recent decisions:")
                for decision in kernel.key_decisions[-3:]:  # Last 3
                    prompt_lines.append(f"    - {decision.decision} ({decision.date})")
            prompt_lines.append("")
            prompt_lines.append(f"Failed Paths: {len(kernel.failed_paths)}")
            prompt_lines.append(f"Open Questions: {len(kernel.open_questions)}")
            if kernel.open_questions:
                prompt_lines.append("  Questions:")
                for q in kernel.open_questions[:3]:  # First 3
                    prompt_lines.append(f"    - {q}")
            prompt_lines.append("")
        else:
            prompt_lines.append(f"⚠ Warning: Kernel '{kernel_id}' not found.")
            prompt_lines.append(f"You may need to create it first.")
            prompt_lines.append("")

    # Recent history
    prompt_lines.append("--- Recent History ---")
    prompt_lines.append("")
    history_summary = build_history_summary(
        max_events=max_events,
        kernel_id=kernel_id
    )
    prompt_lines.append(history_summary)
    prompt_lines.append("")

    # Task instructions
    prompt_lines.append("--- Task ---")
    prompt_lines.append("")
    prompt_lines.append("Review the recent history events above and determine if any kernel updates are needed.")
    prompt_lines.append("")
    prompt_lines.append("Consider:")
    prompt_lines.append("  1. Are there new decisions that should be captured?")
    prompt_lines.append("  2. Are there failed attempts that should be documented?")
    prompt_lines.append("  3. Are there new questions that should be tracked?")
    prompt_lines.append("  4. Does the summary need updating to reflect recent context?")
    prompt_lines.append("")
    prompt_lines.append("Output:")
    prompt_lines.append("  - List any KernelUpdates that should be applied")
    prompt_lines.append("  - For each update, specify:")
    prompt_lines.append("    - update_type (decision, failed_path, question, summary_edit)")
    prompt_lines.append("    - content (decision, rationale, etc.)")
    prompt_lines.append("    - source (e.g., cpu_risk_01, user:froggy)")
    prompt_lines.append("")
    prompt_lines.append("=" * 70)

    return "\n".join(prompt_lines)


def filter_events_by_kernel(
    events: List[HistoryEvent],
    kernel_id: str
) -> List[HistoryEvent]:
    """
    Filter history events relevant to a specific kernel

    Args:
        events: List of HistoryEvent objects
        kernel_id: Kernel ID to filter by

    Returns:
        Filtered list of events
    """
    return [e for e in events if e.context.get("kernel_id") == kernel_id]


def suggest_kernel_topics(max_events: int = 100) -> List[str]:
    """
    Suggest potential kernel topics based on recent history

    Analyzes recent events and identifies topics that might benefit from
    having a dedicated memory kernel.

    Args:
        max_events: Number of recent events to analyze

    Returns:
        List of suggested kernel topic strings

    Example:
        ["risk_management", "alpha_strategy", "infrastructure_decisions"]
    """
    events = load_history_events(limit=max_events)

    if not events:
        return []

    # Extract kernel_ids mentioned in context
    mentioned_kernels = set()
    for event in events:
        if "kernel_id" in event.context:
            mentioned_kernels.add(event.context["kernel_id"])

    # Look for common topics in content (simple keyword analysis)
    topic_keywords = {
        "risk": ["risk", "drawdown", "kelly", "position size", "exposure"],
        "alpha": ["alpha", "signal", "strategy", "edge", "prediction"],
        "infrastructure": ["infra", "system", "architecture", "deployment", "monitoring"],
        "coordination": ["coordination", "planning", "decision", "priority", "workflow"]
    }

    topic_counts = {topic: 0 for topic in topic_keywords}
    for event in events:
        content_lower = event.content.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                topic_counts[topic] += 1

    # Suggest topics mentioned frequently
    suggestions = mentioned_kernels
    for topic, count in topic_counts.items():
        if count >= 3:  # Threshold: mentioned in at least 3 events
            suggestions.add(topic)

    return sorted(list(suggestions))


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="History-to-Kernels Connector: Generate kernel update prompts from history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show history summary
  python -m ai_nexus.history_to_kernels summary --max-events 20

  # Generate kernel update prompt
  python -m ai_nexus.history_to_kernels prompt --kernel-id risk_model_v2 --max-events 20

  # Suggest kernel topics
  python -m ai_nexus.history_to_kernels suggest --max-events 50
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Summary command
    parser_summary = subparsers.add_parser(
        "summary",
        help="Show history summary"
    )
    parser_summary.add_argument(
        "--max-events",
        type=int,
        default=20,
        help="Maximum number of events to include"
    )
    parser_summary.add_argument(
        "--type",
        help="Filter by event type"
    )
    parser_summary.add_argument(
        "--kernel-id",
        help="Filter by kernel ID"
    )

    # Prompt command
    parser_prompt = subparsers.add_parser(
        "prompt",
        help="Generate kernel update prompt"
    )
    parser_prompt.add_argument(
        "--kernel-id",
        required=True,
        help="Kernel ID to generate prompt for"
    )
    parser_prompt.add_argument(
        "--max-events",
        type=int,
        default=20,
        help="Maximum number of events to include"
    )
    parser_prompt.add_argument(
        "--no-kernel-state",
        action="store_true",
        help="Exclude current kernel state from prompt"
    )

    # Suggest command
    parser_suggest = subparsers.add_parser(
        "suggest",
        help="Suggest kernel topics based on history"
    )
    parser_suggest.add_argument(
        "--max-events",
        type=int,
        default=100,
        help="Number of events to analyze"
    )

    args = parser.parse_args()

    # Execute command
    if args.command == "summary":
        summary = build_history_summary(
            max_events=args.max_events,
            event_type=args.type if hasattr(args, 'type') else None,
            kernel_id=args.kernel_id if hasattr(args, 'kernel_id') else None
        )
        print(summary)

    elif args.command == "prompt":
        prompt = build_kernel_update_prompt(
            kernel_id=args.kernel_id,
            max_events=args.max_events,
            include_kernel_state=not args.no_kernel_state
        )
        print(prompt)

    elif args.command == "suggest":
        print("Analyzing recent history for kernel topic suggestions...")
        print()
        topics = suggest_kernel_topics(max_events=args.max_events)

        if topics:
            print(f"Suggested Kernel Topics (based on last {args.max_events} events):")
            print("=" * 50)
            for topic in topics:
                print(f"  - {topic}")
        else:
            print("No topic suggestions found.")
            print("(Need more history events with kernel context or topic keywords)")
        print()
