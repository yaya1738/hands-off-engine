"""
Spark Plug Auto-Kernel v0.2

Automatically refresh memory kernels from recent history using CPU (Part 1).

Wire: History (Part 3) → CPU (Part 1) → Kernels (Part 2)

API:
    refresh_kernel_from_history(kernel_id, max_events=50) -> None

CLI:
    python -m ai_nexus.spark_plug_autokernel refresh --kernel-id risk_model_v2

Safety:
    - design_only mode (no trading access)
    - No imports from trading/risk/decider/executor
    - Offline tests with mock CPU

See: docs/SPARK_PLUG_ARCHITECTURE_v0.2.md (v0.2: Auto-Kernel Refresh)
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.spark_plug_types import (
    HistoryEvent,
    KernelUpdate,
    create_history_event
)
from ai_nexus.history_logger import load_history_events, count_history_events
from ai_nexus.spark_plug_history import load_kernel_history_events, get_history_stats
from ai_nexus.history_to_kernels import (
    build_kernel_update_prompt,
    filter_events_by_kernel
)
from ai_nexus.memory_kernels import load_kernel, append_kernel_update
from ai_nexus.tri_agent_session_runner import TriAgentSession


# =============================================================================
# Core API
# =============================================================================

def refresh_kernel_from_history(
    kernel_id: str,
    max_events: int = 50,
    cpu_profile: str = "design_only",
    conversation_id: Optional[str] = None,
    session_goal: Optional[str] = None,
    agents: Optional[List[str]] = None,
    rounds: int = 2,
    dry_run: bool = False
) -> Dict:
    """
    Refresh a memory kernel from recent history using CPU

    Flow:
        1. Load recent history events relevant to kernel_id
        2. Build kernel update prompt using history_to_kernels
        3. Run tri-agent CPU session with prompt + bound kernel
        4. Parse CPU output for kernel updates (future: auto-extract)
        5. Apply updates to kernel (future: auto-apply)

    Args:
        kernel_id: ID of kernel to refresh
        max_events: Maximum number of history events to include (default: 50)
        cpu_profile: CPU safety profile (default: "design_only")
        conversation_id: Optional conversation ID (auto-generated if None)
        session_goal: Optional session goal (auto-generated if None)
        agents: List of agent IDs to use (default: ["chatgpt", "claude_cli"])
        rounds: Number of discussion rounds (default: 2)
        dry_run: If True, only generate prompt but don't run CPU (default: False)

    Returns:
        Dict with status and metadata:
        {
            "status": "success" | "no_history" | "kernel_not_found" | "error",
            "kernel_id": str,
            "events_found": int,
            "conversation_id": str,
            "cpu_run": bool,
            "message": str
        }

    Raises:
        ValueError: If kernel_id is empty or invalid

    Example:
        result = refresh_kernel_from_history(
            kernel_id="risk_model_v2",
            max_events=50
        )
    """
    if not kernel_id:
        raise ValueError("kernel_id cannot be empty")

    # Verify kernel exists
    kernel = load_kernel(kernel_id)
    if kernel is None:
        return {
            "status": "kernel_not_found",
            "kernel_id": kernel_id,
            "events_found": 0,
            "conversation_id": None,
            "cpu_run": False,
            "message": f"Kernel '{kernel_id}' not found. Create it first."
        }

    # Load history events relevant to this kernel
    all_events = load_history_events(limit=max_events * 2)  # Load more, then filter
    relevant_events = filter_events_by_kernel(all_events, kernel_id)

    # Also include events without kernel_id that might be relevant
    # (e.g., general observations that could apply to any kernel)
    general_events = [e for e in all_events if not e.context.get("kernel_id")]
    relevant_events.extend(general_events[:max_events // 4])  # Add up to 25% general events

    # Limit to max_events
    relevant_events = relevant_events[:max_events]

    if not relevant_events:
        return {
            "status": "no_history",
            "kernel_id": kernel_id,
            "events_found": 0,
            "conversation_id": None,
            "cpu_run": False,
            "message": f"No relevant history events found for kernel '{kernel_id}'"
        }

    print(f"📚 Found {len(relevant_events)} relevant history events for kernel '{kernel_id}'")

    # Generate kernel update prompt
    prompt = build_kernel_update_prompt(
        kernel_id=kernel_id,
        max_events=max_events,
        include_kernel_state=True
    )

    # Generate conversation_id if not provided
    if conversation_id is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        conversation_id = f"autokernel_{kernel_id}_{timestamp}"

    # Generate session_goal if not provided
    if session_goal is None:
        session_goal = (
            f"Review recent history and update kernel '{kernel_id}' "
            f"with improved, compressed knowledge"
        )

    # Use default agents if not provided
    if agents is None:
        agents = ["chatgpt", "claude_cli"]

    if dry_run:
        print("\n" + "="*70)
        print("DRY RUN MODE - Generated prompt:")
        print("="*70)
        print(prompt)
        print("="*70)
        print(f"\nWould run CPU session:")
        print(f"  conversation_id: {conversation_id}")
        print(f"  session_goal: {session_goal}")
        print(f"  agents: {agents}")
        print(f"  rounds: {rounds}")
        print(f"  bound_kernels: [{kernel_id}]")
        print(f"  cpu_profile: {cpu_profile}")
        return {
            "status": "dry_run",
            "kernel_id": kernel_id,
            "events_found": len(relevant_events),
            "conversation_id": conversation_id,
            "cpu_run": False,
            "message": "Dry run complete - prompt generated but CPU not executed"
        }

    # Run CPU session
    print(f"\n🚀 Starting CPU session: {conversation_id}")
    print(f"   Goal: {session_goal}")
    print(f"   Agents: {', '.join(agents)}")
    print(f"   Rounds: {rounds}")
    print(f"   Bound kernel: {kernel_id}")
    print()

    try:
        session = TriAgentSession(
            conversation_id=conversation_id,
            session_goal=session_goal,
            bound_kernels=[kernel_id],
            max_rounds=rounds,
            max_cost_usd=1.0,
            continuous=False,
            kernel_update_mode="none"  # We'll handle updates manually
        )

        # Add initial system message with the update prompt
        from ai_nexus.spark_plug_types import create_cpu_message
        initial_msg = create_cpu_message(
            msg_id="msg-0000",
            from_="system",
            role="system",
            content=prompt
        )
        session.append_message(initial_msg)

        # Run the session
        session.run_session(agents=agents, rounds=rounds)

        print(f"\n✅ CPU session complete")
        print(f"   Thread: {session.thread_file}")
        print(f"   CPU Instance: {session.cpu_instance_file}")

        # TODO v0.3: Auto-extract kernel updates from CPU output
        # For now, users need to manually review the thread and apply updates
        print(f"\n📋 Next steps:")
        print(f"   1. Review the CPU discussion in: {session.thread_file}")
        print(f"   2. Manually extract kernel updates")
        print(f"   3. Apply updates using: memory_kernels.append_kernel_update()")
        print()
        print(f"   Future v0.3: Auto-extraction and application of kernel updates")

        return {
            "status": "success",
            "kernel_id": kernel_id,
            "events_found": len(relevant_events),
            "conversation_id": conversation_id,
            "cpu_run": True,
            "message": f"CPU session complete. Review thread at: {session.thread_file}"
        }

    except Exception as e:
        return {
            "status": "error",
            "kernel_id": kernel_id,
            "events_found": len(relevant_events),
            "conversation_id": conversation_id,
            "cpu_run": False,
            "message": f"Error running CPU session: {str(e)}"
        }


def run_autokernel_refresh(
    kernel_id: str,
    mode: str = "cpu",
    dry_run: bool = False,
    max_history_items: int | None = None,
) -> dict:
    """
    Run a full auto-kernel refresh cycle for a single kernel (v0.4)

    This is the v0.4 entry point for AI-Runner integration. It wraps the existing
    refresh_kernel_from_history() function and returns a structured result dict
    suitable for batch processing and auditing.

    Args:
        kernel_id: Kernel identifier (e.g., "risk_model_v2")
        mode: Refresh mode - "cpu" (tri-agent CPU) or "analysis" (future)
        dry_run: If True, don't persist updates to kernel file
        max_history_items: Optional cap on history events to process (default: 50)

    Returns:
        Structured dict with comprehensive refresh results:
        {
            "status": "success" | "error" | "no_history" | "kernel_not_found",
            "kernel_id": "<kernel-id>",
            "mode": "cpu" | "analysis" | "...",
            "history": {
                "sources": ["user_events.jsonl", ...],
                "items_seen": int,
                "items_used": int,
                "time_range": {
                    "start": "2025-11-01T00:00:00Z",
                    "end":   "2025-11-26T10:32:00Z"
                }
            },
            "updates": {
                "applied": [...],
                "skipped": [...],
                "backup_file": None,  # v0.4: no auto-apply yet
                "kernel_file": "..."
            },
            "cpu": {
                "intercom_thread": "...",   # path to thread.jsonl
                "conversation_id": "..."     # CPU run id
            },
            "error": {  # only present if status == "error"
                "type": "...",
                "message": "...",
                "stage": "load_history" | "cpu" | "apply_updates" | "io",
                "traceback": "..."
            }
        }

    Example:
        result = run_autokernel_refresh(
            kernel_id="risk_model_v2",
            mode="cpu",
            dry_run=False
        )
        if result["status"] == "success":
            print(f"CPU thread: {result['cpu']['intercom_thread']}")
    """
    import traceback

    # Set defaults
    if max_history_items is None:
        max_history_items = 50

    # Initialize result structure
    result = {
        "status": "unknown",
        "kernel_id": kernel_id,
        "mode": mode,
        "history": {
            "sources": [],
            "items_seen": 0,
            "items_used": 0,
            "time_range": {
                "start": None,
                "end": None
            }
        },
        "updates": {
            "applied": [],
            "skipped": [],
            "backup_file": None,
            "kernel_file": None
        },
        "cpu": {
            "intercom_thread": None,
            "conversation_id": None
        }
    }

    try:
        # Stage 1: Load kernel
        from ai_nexus.memory_kernels import load_kernel
        kernel = load_kernel(kernel_id)

        if kernel is None:
            result["status"] = "kernel_not_found"
            return result

        # Store kernel file path
        kernel_file = REPO_ROOT / "ai" / "memory" / "kernels" / f"{kernel_id}.json"
        result["updates"]["kernel_file"] = str(kernel_file)

        # Stage 2: Load history using unified loader
        try:
            # Use new unified loader (prefers events.jsonl, falls back to user_events.jsonl)
            relevant_events = load_kernel_history_events(
                kernel_id=kernel_id,
                max_events=max_history_items,
                min_importance=None  # No importance filter for v0.4
            )

            if not relevant_events:
                result["status"] = "no_history"
                return result

            # Get history stats to determine which format was used
            stats = get_history_stats(kernel_id)

            # Populate history metadata
            result["history"]["items_seen"] = stats["total_events"]
            result["history"]["items_used"] = len(relevant_events)

            # Set sources based on which format was actually used
            if stats["using_format"] == "new":
                result["history"]["sources"] = ["events.jsonl"]
            elif stats["using_format"] == "legacy":
                result["history"]["sources"] = ["user_events.jsonl"]
            else:
                result["history"]["sources"] = []

            # Calculate time range
            if relevant_events:
                # Events are newest-first (dict format), so reverse for time range
                result["history"]["time_range"]["start"] = relevant_events[-1].get("ts", "")
                result["history"]["time_range"]["end"] = relevant_events[0].get("ts", "")

        except Exception as e:
            result["status"] = "error"
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "stage": "load_history",
                "traceback": traceback.format_exc()
            }
            return result

        # Stage 3: Run CPU (if mode == "cpu")
        if mode != "cpu":
            result["status"] = "error"
            result["error"] = {
                "type": "NotImplementedError",
                "message": f"Mode '{mode}' not yet implemented. Only 'cpu' is supported in v0.4.",
                "stage": "cpu",
                "traceback": ""
            }
            return result

        try:
            # Use existing v0.2 function to run CPU
            cpu_result = refresh_kernel_from_history(
                kernel_id=kernel_id,
                max_events=max_history_items,
                dry_run=dry_run  # Pass through dry_run flag
            )

            # Extract CPU info from v0.2 result
            result["cpu"]["conversation_id"] = cpu_result.get("conversation_id")

            # Build intercom thread path
            if cpu_result.get("conversation_id"):
                conv_id = cpu_result["conversation_id"]
                thread_path = REPO_ROOT / "ai" / "intercom" / conv_id / "thread.jsonl"
                if thread_path.exists():
                    result["cpu"]["intercom_thread"] = str(thread_path)

            # Check v0.2 result status
            if cpu_result["status"] in ["error", "kernel_not_found", "no_history"]:
                result["status"] = cpu_result["status"]
                if cpu_result["status"] == "error":
                    result["error"] = {
                        "type": "CPUError",
                        "message": cpu_result.get("message", "Unknown CPU error"),
                        "stage": "cpu",
                        "traceback": ""
                    }
                return result

        except Exception as e:
            result["status"] = "error"
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "stage": "cpu",
                "traceback": traceback.format_exc()
            }
            return result

        # Stage 4: Apply updates (v0.4: minimal implementation)
        # NOTE: Full auto-apply will come in v0.3. For v0.4, we just document
        # the CPU output as a suggestion without mutating the kernel file.
        try:
            # v0.4: Create a descriptive update entry pointing to CPU artifacts
            update_entry = {
                "type": "cpu_suggestion",
                "conversation_id": result["cpu"]["conversation_id"],
                "thread": result["cpu"]["intercom_thread"],
                "summary": f"CPU session completed. Review thread for potential kernel updates.",
                "auto_applied": False,
                "reason": "v0.4 does not auto-apply updates. Manual review required.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            result["updates"]["applied"].append(update_entry)

            # In dry_run mode, add note
            if dry_run:
                result["updates"]["skipped"].append({
                    "type": "dry_run",
                    "message": "Dry run mode - no kernel mutations performed"
                })

        except Exception as e:
            result["status"] = "error"
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "stage": "apply_updates",
                "traceback": traceback.format_exc()
            }
            return result

        # Success!
        result["status"] = "success"
        return result

    except Exception as e:
        # Catch-all for unexpected errors
        result["status"] = "error"
        result["error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "stage": "unknown",
            "traceback": traceback.format_exc()
        }
        return result


def list_refreshable_kernels() -> List[str]:
    """
    List kernels that have recent history events

    Returns:
        List of kernel IDs that have at least one history event
    """
    from ai_nexus.memory_kernels import list_kernels

    all_kernels = list_kernels()
    all_events = load_history_events(limit=1000)

    # Find kernels mentioned in history
    kernels_with_history = set()
    for event in all_events:
        if "kernel_id" in event.context:
            kid = event.context["kernel_id"]
            if kid in all_kernels:
                kernels_with_history.add(kid)

    return sorted(list(kernels_with_history))


def get_kernel_history_stats(kernel_id: str) -> Dict:
    """
    Get statistics about history events for a kernel

    Args:
        kernel_id: Kernel ID

    Returns:
        Dict with stats:
        {
            "kernel_id": str,
            "total_events": int,
            "event_types": Dict[str, int],
            "oldest_event": str,  # ISO 8601 timestamp
            "newest_event": str   # ISO 8601 timestamp
        }
    """
    all_events = load_history_events(limit=10000)
    kernel_events = filter_events_by_kernel(all_events, kernel_id)

    if not kernel_events:
        return {
            "kernel_id": kernel_id,
            "total_events": 0,
            "event_types": {},
            "oldest_event": None,
            "newest_event": None
        }

    # Count by type
    event_types = {}
    for event in kernel_events:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

    # Oldest and newest (kernel_events is newest-first from filter)
    newest = kernel_events[0]
    oldest = kernel_events[-1]

    return {
        "kernel_id": kernel_id,
        "total_events": len(kernel_events),
        "event_types": event_types,
        "oldest_event": oldest.timestamp,
        "newest_event": newest.timestamp
    }


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Spark Plug Auto-Kernel: Refresh kernels from history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Refresh a kernel from recent history
  python -m ai_nexus.spark_plug_autokernel refresh \\
      --kernel-id risk_model_v2 \\
      --max-events 50

  # Dry run (generate prompt but don't run CPU)
  python -m ai_nexus.spark_plug_autokernel refresh \\
      --kernel-id risk_model_v2 \\
      --dry-run

  # List kernels with history
  python -m ai_nexus.spark_plug_autokernel list

  # Show history stats for a kernel
  python -m ai_nexus.spark_plug_autokernel stats --kernel-id risk_model_v2
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Refresh command
    parser_refresh = subparsers.add_parser(
        "refresh",
        help="Refresh a kernel from recent history"
    )
    parser_refresh.add_argument(
        "--kernel-id",
        required=True,
        help="Kernel ID to refresh"
    )
    parser_refresh.add_argument(
        "--max-events",
        type=int,
        default=50,
        help="Maximum number of history events to include (default: 50)"
    )
    parser_refresh.add_argument(
        "--conversation-id",
        help="Optional conversation ID (auto-generated if not provided)"
    )
    parser_refresh.add_argument(
        "--session-goal",
        help="Optional session goal (auto-generated if not provided)"
    )
    parser_refresh.add_argument(
        "--agents",
        help="Comma-separated list of agents (default: chatgpt,claude_cli)"
    )
    parser_refresh.add_argument(
        "--rounds",
        type=int,
        default=2,
        help="Number of discussion rounds (default: 2)"
    )
    parser_refresh.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate prompt but don't run CPU"
    )

    # List command
    parser_list = subparsers.add_parser(
        "list",
        help="List kernels with recent history"
    )

    # Stats command
    parser_stats = subparsers.add_parser(
        "stats",
        help="Show history statistics for a kernel"
    )
    parser_stats.add_argument(
        "--kernel-id",
        required=True,
        help="Kernel ID"
    )

    args = parser.parse_args()

    # Execute command
    if args.command == "refresh":
        # Use new v0.4 run_autokernel_refresh() function
        result = run_autokernel_refresh(
            kernel_id=args.kernel_id,
            mode="cpu",
            dry_run=args.dry_run,
            max_history_items=args.max_events
        )

        # Print summary
        print(f"\n{'='*70}")
        print(f"Spark Plug Auto-Kernel Refresh v0.4")
        print(f"{'='*70}")
        print(f"Status: {result['status']}")
        print(f"Kernel: {result['kernel_id']}")
        print(f"Mode: {result['mode']}")

        if result['status'] == 'success':
            print(f"\nHistory:")
            print(f"  Items seen: {result['history']['items_seen']}")
            print(f"  Items used: {result['history']['items_used']}")
            if result['history']['time_range']['start']:
                print(f"  Time range: {result['history']['time_range']['start']} to {result['history']['time_range']['end']}")

            print(f"\nCPU:")
            print(f"  Conversation ID: {result['cpu']['conversation_id']}")
            if result['cpu']['intercom_thread']:
                print(f"  Thread: {result['cpu']['intercom_thread']}")

            print(f"\nUpdates:")
            print(f"  Applied: {len(result['updates']['applied'])} update(s)")
            print(f"  Skipped: {len(result['updates']['skipped'])} update(s)")

        elif result['status'] == 'no_history':
            print(f"\nNo relevant history events found for kernel '{result['kernel_id']}'")

        elif result['status'] == 'kernel_not_found':
            print(f"\nKernel '{result['kernel_id']}' not found")

        elif result['status'] == 'error':
            print(f"\nError occurred:")
            print(f"  Type: {result['error']['type']}")
            print(f"  Stage: {result['error']['stage']}")
            print(f"  Message: {result['error']['message']}")
            if result['error']['traceback']:
                print(f"\nTraceback:")
                print(result['error']['traceback'])

        print(f"{'='*70}\n")

        # Exit with appropriate code
        if result['status'] in ['success', 'no_history', 'kernel_not_found']:
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.command == "list":
        kernels = list_refreshable_kernels()

        if not kernels:
            print("No kernels found with history events.")
            print("\nTo create history events:")
            print("  python -m ai_nexus.history_demo log ...")
        else:
            print(f"Kernels with recent history ({len(kernels)}):")
            print("=" * 50)
            for kid in kernels:
                stats = get_kernel_history_stats(kid)
                print(f"\n  {kid}")
                print(f"    Events: {stats['total_events']}")
                print(f"    Types: {stats['event_types']}")
                print(f"    Latest: {stats['newest_event']}")

    elif args.command == "stats":
        stats = get_kernel_history_stats(args.kernel_id)

        if stats['total_events'] == 0:
            print(f"No history events found for kernel '{args.kernel_id}'")
        else:
            print(f"History statistics for '{args.kernel_id}':")
            print("=" * 50)
            print(f"Total events: {stats['total_events']}")
            print(f"\nEvent types:")
            for event_type, count in stats['event_types'].items():
                print(f"  {event_type}: {count}")
            print(f"\nOldest event: {stats['oldest_event']}")
            print(f"Newest event: {stats['newest_event']}")


if __name__ == "__main__":
    main()
