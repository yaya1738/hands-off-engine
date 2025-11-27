"""
Spark Plug Auto-Kernel v0.3

Automatically refresh memory kernels from recent history using CPU (Part 1).

Wire: History (Part 3) → CPU (Part 1) → Kernels (Part 2)

v0.3 adds Auto-Extract & Apply:
    - Parse CPU thread output for kernel updates (decisions, failed_paths, questions)
    - Auto-apply extracted updates via memory_kernels.append_kernel_update()
    - Closes the loop: history → CPU → kernel → **updated kernel**

API:
    refresh_kernel_from_history(kernel_id, max_events=50) -> None
    extract_kernel_updates_from_thread(thread_path, kernel_id) -> List[KernelUpdate]

CLI:
    python -m ai_nexus.spark_plug_autokernel refresh --kernel-id risk_model_v2
    python -m ai_nexus.spark_plug_autokernel refresh --kernel-id risk_model_v2 --auto-apply

Safety:
    - design_only mode (no trading access)
    - No imports from trading/risk/decider/executor
    - Offline tests with mock CPU

See: docs/SPARK_PLUG_ARCHITECTURE_v0.2.md (v0.2: Auto-Kernel Refresh)
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.spark_plug_types import (
    HistoryEvent,
    KernelUpdate,
    CpuMessage,
    create_history_event,
    create_kernel_update_decision,
    create_kernel_update_failed_path
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
# v0.3: Kernel Update Extraction from CPU Thread Output
# =============================================================================

def load_thread_messages(thread_path: Path) -> List[CpuMessage]:
    """
    Load all messages from a CPU thread JSONL file

    Args:
        thread_path: Path to thread.jsonl file

    Returns:
        List of CpuMessage objects ordered by timestamp
    """
    if not thread_path.exists():
        return []

    messages = []
    with open(thread_path) as f:
        for line in f:
            if line.strip():
                try:
                    messages.append(CpuMessage.from_jsonl_line(line))
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    print(f"[v0.3] Warning: Skipping malformed message: {e}")
                    continue
    return messages


def extract_decisions_from_content(content: str, source: str, agent: str) -> List[KernelUpdate]:
    """
    Extract decision-type kernel updates from LLM response content

    Uses pattern matching to find structured decision statements:
    - "DECISION:" or "Decision:" blocks
    - "We decided to..." or "I recommend..." statements
    - Numbered recommendations

    Args:
        content: LLM response content
        source: CPU session ID (e.g., "cpu_risk_20251126_01")
        agent: Agent that produced the content (e.g., "chatgpt")

    Returns:
        List of KernelUpdate objects of type "decision"
    """
    updates = []

    # Pattern 1: Explicit DECISION: blocks
    decision_pattern = r"(?:DECISION|Decision|RECOMMEND|Recommend)[:\s]+([^\n]+(?:\n(?![A-Z]{2,}:)[^\n]+)*)"
    for match in re.finditer(decision_pattern, content):
        decision_text = match.group(1).strip()
        if len(decision_text) > 10:  # Minimum meaningful decision
            updates.append(create_kernel_update_decision(
                decision=decision_text[:500],  # Cap at 500 chars
                rationale="Extracted from CPU discussion",
                source=source,
                agent=agent
            ))

    # Pattern 2: "We should/recommend/decide to..." statements
    action_pattern = r"(?:We should|I recommend|We decide to|Let's|We will)\s+([^.!?]+[.!?])"
    for match in re.finditer(action_pattern, content, re.IGNORECASE):
        statement = match.group(1).strip()
        if len(statement) > 15 and len(statement) < 300:  # Reasonable length
            # Avoid duplicates
            if not any(statement[:50] in u.content.get("decision", "")[:50] for u in updates):
                updates.append(create_kernel_update_decision(
                    decision=statement,
                    rationale="Extracted from CPU discussion",
                    source=source,
                    agent=agent
                ))

    return updates


def extract_failed_paths_from_content(content: str, source: str, agent: str) -> List[KernelUpdate]:
    """
    Extract failed_path-type kernel updates from LLM response content

    Looks for patterns indicating failed attempts or lessons learned:
    - "This didn't work because..."
    - "We tried X but..."
    - "LESSON:" or "FAILED:" blocks

    Args:
        content: LLM response content
        source: CPU session ID
        agent: Agent that produced the content

    Returns:
        List of KernelUpdate objects of type "failed_path"
    """
    updates = []

    # Pattern 1: Explicit FAILED or LESSON blocks
    failed_pattern = r"(?:FAILED|LESSON|Failed|Lesson)[:\s]+([^\n]+(?:\n(?![A-Z]{2,}:)[^\n]+)*)"
    for match in re.finditer(failed_pattern, content):
        text = match.group(1).strip()
        if len(text) > 10:
            updates.append(create_kernel_update_failed_path(
                attempt="See discussion",
                failure=text[:300],
                lesson="Extracted from CPU discussion",
                source=source,
                agent=agent
            ))

    # Pattern 2: "didn't work" / "failed because" / "problem was" statements
    problem_pattern = r"(?:didn't work|failed because|problem was|issue was|that approach)\s+([^.!?]+[.!?])"
    for match in re.finditer(problem_pattern, content, re.IGNORECASE):
        failure_text = match.group(1).strip()
        if len(failure_text) > 15 and len(failure_text) < 300:
            updates.append(create_kernel_update_failed_path(
                attempt="Approach discussed in CPU session",
                failure=failure_text,
                lesson="Documented for future reference",
                source=source,
                agent=agent
            ))

    return updates


def extract_questions_from_content(content: str, source: str, agent: str) -> List[KernelUpdate]:
    """
    Extract question-type kernel updates from LLM response content

    Looks for open questions that should be tracked:
    - "QUESTION:" or "Open question:" blocks
    - Sentences ending with ?

    Args:
        content: LLM response content
        source: CPU session ID
        agent: Agent that produced the content

    Returns:
        List of KernelUpdate objects of type "question"
    """
    updates = []

    # Pattern 1: Explicit QUESTION blocks
    question_block_pattern = r"(?:QUESTION|Question|OPEN QUESTION|Open question)[:\s]+([^\n]+)"
    for match in re.finditer(question_block_pattern, content):
        question = match.group(1).strip()
        if len(question) > 10:
            updates.append(KernelUpdate(
                update_type="question",
                content={"question": question[:200]},
                source=source,
                agent=agent
            ))

    # Pattern 2: Important questions (ending with ?)
    question_pattern = r"(?:Should we|Do we|How should|What is|What are|Is there|Are there|Could we|Would it)\s+[^?]+\?"
    for match in re.finditer(question_pattern, content, re.IGNORECASE):
        question = match.group(0).strip()
        if len(question) > 15 and len(question) < 200:
            # Avoid duplicates
            if not any(question[:30] in u.content.get("question", "")[:30] for u in updates):
                updates.append(KernelUpdate(
                    update_type="question",
                    content={"question": question},
                    source=source,
                    agent=agent
                ))

    return updates


def extract_kernel_updates_from_thread(
    thread_path: Path,
    kernel_id: str,
    conversation_id: Optional[str] = None
) -> List[KernelUpdate]:
    """
    Extract kernel updates from a CPU thread output (v0.3)

    Parses the thread.jsonl file from a CPU session and extracts:
    - Decisions (update_type="decision")
    - Failed paths (update_type="failed_path")
    - Open questions (update_type="question")

    Args:
        thread_path: Path to the thread.jsonl file
        kernel_id: Target kernel ID for context
        conversation_id: Optional conversation ID for source attribution

    Returns:
        List of KernelUpdate objects ready to be applied via append_kernel_update()

    Example:
        updates = extract_kernel_updates_from_thread(
            thread_path=Path("ai/intercom/autokernel_risk_model_v2_20251126/thread.jsonl"),
            kernel_id="risk_model_v2"
        )
        for update in updates:
            append_kernel_update("risk_model_v2", update)
    """
    if not thread_path.exists():
        print(f"[v0.3] Thread file not found: {thread_path}")
        return []

    messages = load_thread_messages(thread_path)
    if not messages:
        print(f"[v0.3] No messages found in thread: {thread_path}")
        return []

    # Determine source ID
    source = conversation_id or f"cpu_{thread_path.parent.name}"

    all_updates = []

    # Process each assistant message (skip system messages)
    for msg in messages:
        if msg.role != "assistant":
            continue

        agent = msg.from_ or "unknown"
        content = msg.content or ""

        # Extract different types of updates
        decisions = extract_decisions_from_content(content, source, agent)
        failed_paths = extract_failed_paths_from_content(content, source, agent)
        questions = extract_questions_from_content(content, source, agent)

        all_updates.extend(decisions)
        all_updates.extend(failed_paths)
        all_updates.extend(questions)

    # Deduplicate updates (same type + similar content)
    unique_updates = []
    seen_content = set()
    for update in all_updates:
        # Create a fingerprint for deduplication
        if update.update_type == "decision":
            fingerprint = f"decision:{update.content.get('decision', '')[:50]}"
        elif update.update_type == "failed_path":
            fingerprint = f"failed:{update.content.get('failure', '')[:50]}"
        elif update.update_type == "question":
            fingerprint = f"question:{update.content.get('question', '')[:50]}"
        else:
            fingerprint = f"{update.update_type}:{str(update.content)[:50]}"

        if fingerprint not in seen_content:
            seen_content.add(fingerprint)
            unique_updates.append(update)

    print(f"[v0.3] Extracted {len(unique_updates)} kernel updates from thread ({len(all_updates)} before dedup)")
    return unique_updates


def apply_kernel_updates(
    kernel_id: str,
    updates: List[KernelUpdate],
    dry_run: bool = False
) -> Dict:
    """
    Apply a list of kernel updates to a kernel (v0.3)

    Args:
        kernel_id: Target kernel ID
        updates: List of KernelUpdate objects to apply
        dry_run: If True, don't actually apply updates

    Returns:
        Dict with application results:
        {
            "applied": int,
            "skipped": int,
            "errors": int,
            "details": List[Dict]
        }
    """
    result = {
        "applied": 0,
        "skipped": 0,
        "errors": 0,
        "details": []
    }

    if not updates:
        return result

    # Verify kernel exists
    kernel = load_kernel(kernel_id)
    if kernel is None:
        result["errors"] = len(updates)
        result["details"].append({
            "status": "error",
            "message": f"Kernel '{kernel_id}' not found"
        })
        return result

    for update in updates:
        try:
            if dry_run:
                result["skipped"] += 1
                result["details"].append({
                    "status": "skipped",
                    "type": update.update_type,
                    "content": str(update.content)[:100],
                    "reason": "dry_run mode"
                })
            else:
                append_kernel_update(kernel_id, update)
                result["applied"] += 1
                result["details"].append({
                    "status": "applied",
                    "type": update.update_type,
                    "content": str(update.content)[:100]
                })
        except Exception as e:
            result["errors"] += 1
            result["details"].append({
                "status": "error",
                "type": update.update_type,
                "content": str(update.content)[:100],
                "error": str(e)
            })

    return result


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
    dry_run: bool = False,
    auto_apply: bool = False
) -> Dict:
    """
    Refresh a memory kernel from recent history using CPU

    Flow:
        1. Load recent history events relevant to kernel_id
        2. Build kernel update prompt using history_to_kernels
        3. Run tri-agent CPU session with prompt + bound kernel
        4. (v0.3) Parse CPU output for kernel updates (decisions, failed_paths, questions)
        5. (v0.3) Apply updates to kernel if auto_apply=True

    Args:
        kernel_id: ID of kernel to refresh
        max_events: Maximum number of history events to include (default: 50)
        cpu_profile: CPU safety profile (default: "design_only")
        conversation_id: Optional conversation ID (auto-generated if None)
        session_goal: Optional session goal (auto-generated if None)
        agents: List of agent IDs to use (default: ["chatgpt", "claude_cli"])
        rounds: Number of discussion rounds (default: 2)
        dry_run: If True, only generate prompt but don't run CPU (default: False)
        auto_apply: If True, auto-extract and apply kernel updates (v0.3 feature)

    Returns:
        Dict with status and metadata:
        {
            "status": "success" | "no_history" | "kernel_not_found" | "error",
            "kernel_id": str,
            "events_found": int,
            "conversation_id": str,
            "cpu_run": bool,
            "message": str,
            "extracted_updates": int,  # v0.3
            "applied_updates": int     # v0.3
        }

    Raises:
        ValueError: If kernel_id is empty or invalid

    Example:
        result = refresh_kernel_from_history(
            kernel_id="risk_model_v2",
            max_events=50,
            auto_apply=True  # v0.3: auto-extract and apply updates
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

        # v0.3: Auto-extract kernel updates from CPU output
        extracted_updates = 0
        applied_updates = 0

        if auto_apply:
            print(f"\n🔍 [v0.3] Extracting kernel updates from CPU thread...")
            updates = extract_kernel_updates_from_thread(
                thread_path=session.thread_file,
                kernel_id=kernel_id,
                conversation_id=conversation_id
            )
            extracted_updates = len(updates)

            if updates:
                print(f"   Found {len(updates)} potential updates")
                apply_result = apply_kernel_updates(kernel_id, updates, dry_run=False)
                applied_updates = apply_result["applied"]
                print(f"   Applied: {apply_result['applied']}, Skipped: {apply_result['skipped']}, Errors: {apply_result['errors']}")
            else:
                print(f"   No updates extracted from thread")
        else:
            print(f"\n📋 Next steps:")
            print(f"   1. Review the CPU discussion in: {session.thread_file}")
            print(f"   2. Manually extract kernel updates, or re-run with --auto-apply")
            print(f"   3. Apply updates using: memory_kernels.append_kernel_update()")
            print()
            print(f"   v0.3 feature: Use --auto-apply flag to auto-extract and apply updates")

        return {
            "status": "success",
            "kernel_id": kernel_id,
            "events_found": len(relevant_events),
            "conversation_id": conversation_id,
            "cpu_run": True,
            "message": f"CPU session complete. Review thread at: {session.thread_file}",
            "extracted_updates": extracted_updates,
            "applied_updates": applied_updates
        }

    except Exception as e:
        return {
            "status": "error",
            "kernel_id": kernel_id,
            "events_found": len(relevant_events),
            "conversation_id": conversation_id,
            "cpu_run": False,
            "message": f"Error running CPU session: {str(e)}",
            "extracted_updates": 0,
            "applied_updates": 0
        }


def run_autokernel_refresh(
    kernel_id: str,
    mode: str = "cpu",
    dry_run: bool = False,
    max_history_items: int | None = None,
    auto_apply: bool = True,
) -> dict:
    """
    Run a full auto-kernel refresh cycle for a single kernel (v0.4 + v0.3 auto-apply)

    This is the v0.4 entry point for AI-Runner integration. It wraps the existing
    refresh_kernel_from_history() function and returns a structured result dict
    suitable for batch processing and auditing.

    v0.3 adds auto_apply: Extract and apply kernel updates from CPU output.

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
            # Use existing v0.2 function to run CPU with v0.3 auto_apply
            cpu_result = refresh_kernel_from_history(
                kernel_id=kernel_id,
                max_events=max_history_items,
                dry_run=dry_run,  # Pass through dry_run flag
                auto_apply=auto_apply  # v0.3: auto-extract and apply updates
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

        # Stage 4: Apply updates (v0.3: now with auto-extract/apply)
        try:
            # v0.3: Include auto-extracted update count in result
            extracted_updates = cpu_result.get("extracted_updates", 0)
            applied_updates = cpu_result.get("applied_updates", 0)

            # Create descriptive update entry
            update_entry = {
                "type": "cpu_suggestion" if not auto_apply else "auto_applied",
                "conversation_id": result["cpu"]["conversation_id"],
                "thread": result["cpu"]["intercom_thread"],
                "extracted_updates": extracted_updates,
                "applied_updates": applied_updates,
                "summary": f"CPU session completed. {'Auto-applied ' + str(applied_updates) + ' updates.' if auto_apply and applied_updates > 0 else 'Review thread for potential kernel updates.'}",
                "auto_applied": auto_apply and applied_updates > 0,
                "reason": "v0.3 auto-extract/apply enabled" if auto_apply else "Manual review required",
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

  # Refresh with auto-extract and apply updates (v0.3 feature)
  python -m ai_nexus.spark_plug_autokernel refresh \\
      --kernel-id risk_model_v2 \\
      --auto-apply

  # Dry run (generate prompt but don't run CPU)
  python -m ai_nexus.spark_plug_autokernel refresh \\
      --kernel-id risk_model_v2 \\
      --dry-run

  # Extract updates from an existing thread file (v0.3)
  python -m ai_nexus.spark_plug_autokernel extract \\
      --thread-path ai/intercom/autokernel_risk_model_v2_20251126/thread.jsonl \\
      --kernel-id risk_model_v2 \\
      --apply

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
    parser_refresh.add_argument(
        "--auto-apply",
        action="store_true",
        help="[v0.3] Auto-extract and apply kernel updates from CPU output"
    )

    # Extract command (v0.3)
    parser_extract = subparsers.add_parser(
        "extract",
        help="[v0.3] Extract kernel updates from an existing thread file"
    )
    parser_extract.add_argument(
        "--thread-path",
        required=True,
        help="Path to thread.jsonl file"
    )
    parser_extract.add_argument(
        "--kernel-id",
        required=True,
        help="Target kernel ID"
    )
    parser_extract.add_argument(
        "--apply",
        action="store_true",
        help="Apply extracted updates to the kernel"
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
        # Use new v0.4 run_autokernel_refresh() function with v0.3 auto_apply
        result = run_autokernel_refresh(
            kernel_id=args.kernel_id,
            mode="cpu",
            dry_run=args.dry_run,
            max_history_items=args.max_events,
            auto_apply=args.auto_apply  # v0.3: auto-extract and apply updates
        )

        # Print summary
        print(f"\n{'='*70}")
        print(f"Spark Plug Auto-Kernel Refresh v0.3")
        print(f"{'='*70}")
        print(f"Status: {result['status']}")
        print(f"Kernel: {result['kernel_id']}")
        print(f"Mode: {result['mode']}")
        print(f"Auto-apply: {args.auto_apply}")

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
            # v0.3: Show extracted and applied update counts
            if result['updates']['applied']:
                for upd in result['updates']['applied']:
                    if 'extracted_updates' in upd:
                        print(f"  Extracted from thread: {upd['extracted_updates']}")
                        print(f"  Applied to kernel: {upd['applied_updates']}")

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

    elif args.command == "extract":
        # v0.3: Extract updates from an existing thread file
        thread_path = Path(args.thread_path)
        if not thread_path.exists():
            print(f"Error: Thread file not found: {thread_path}")
            sys.exit(1)

        print(f"\n{'='*70}")
        print(f"Spark Plug v0.3 - Extract Kernel Updates from Thread")
        print(f"{'='*70}")
        print(f"Thread: {thread_path}")
        print(f"Kernel: {args.kernel_id}")
        print(f"Apply: {args.apply}")
        print()

        # Extract updates
        updates = extract_kernel_updates_from_thread(
            thread_path=thread_path,
            kernel_id=args.kernel_id
        )

        if not updates:
            print("No kernel updates found in thread.")
            sys.exit(0)

        print(f"\nExtracted {len(updates)} updates:")
        for i, upd in enumerate(updates, 1):
            print(f"  [{i}] {upd.update_type}: {str(upd.content)[:60]}...")

        # Apply if requested
        if args.apply:
            print(f"\nApplying updates to kernel '{args.kernel_id}'...")
            apply_result = apply_kernel_updates(args.kernel_id, updates)
            print(f"  Applied: {apply_result['applied']}")
            print(f"  Skipped: {apply_result['skipped']}")
            print(f"  Errors: {apply_result['errors']}")
        else:
            print(f"\nTo apply these updates, re-run with --apply flag")

        print(f"{'='*70}\n")
        sys.exit(0)

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
