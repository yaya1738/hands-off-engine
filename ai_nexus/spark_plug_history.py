"""
Spark Plug History Bridge (v0.4+)

Unified history loader that reads from both:
  - ai/history/events.jsonl (new structured format from history_log.py)
  - ai/history/user_events.jsonl (legacy format from history_logger.py)

Prefers new format, falls back gracefully to old format.

API:
    load_kernel_history_events(kernel_id, max_events, min_importance) -> List[dict]

Safety:
    - Read-only (no writes)
    - Graceful fallback (missing files return empty list)
    - Malformed lines are skipped, never crash
    - No imports from trading/risk/decider/executor
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Paths
REPO_ROOT = Path(__file__).parent.parent
NEW_HISTORY_FILE = REPO_ROOT / "ai" / "history" / "events.jsonl"
LEGACY_HISTORY_FILE = REPO_ROOT / "ai" / "history" / "user_events.jsonl"


def normalize_legacy_event(legacy_event: Dict) -> Dict:
    """
    Convert a legacy user_events.jsonl event to the new normalized format

    Legacy format (from spark_plug_types.HistoryEvent):
        {
            "event_id": str,
            "timestamp": str (ISO 8601),
            "event_type": str,
            "source": str,
            "content": str,
            "context": {
                "kernel_id": str (optional),
                ...other fields...
            }
        }

    New normalized format:
        {
            "event_id": str,
            "ts": str,
            "kind": str,
            "source": str,
            "kernel_ids": List[str],
            "summary": str,
            "details": dict,
            "importance": int | None,
            "tags": List[str]
        }
    """
    # Extract kernel_id from context if present
    context = legacy_event.get("context", {})
    kernel_id = context.get("kernel_id")
    kernel_ids = [kernel_id] if kernel_id else []

    return {
        "event_id": legacy_event.get("event_id", ""),
        "ts": legacy_event.get("timestamp", ""),
        "kind": legacy_event.get("event_type"),  # map event_type -> kind
        "source": legacy_event.get("source"),
        "kernel_ids": kernel_ids,
        "summary": legacy_event.get("content", ""),
        "details": context,
        "importance": None,  # Legacy events don't have importance
        "tags": []  # Legacy events don't have tags
    }


def load_from_new_format(
    kernel_id: str,
    max_events: Optional[int] = None,
    min_importance: Optional[int] = None
) -> List[Dict]:
    """
    Load events from new structured format (events.jsonl)

    Returns normalized event dicts
    """
    if not NEW_HISTORY_FILE.exists():
        return []

    events = []

    try:
        with open(NEW_HISTORY_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)

                    # Filter by kernel_id
                    if kernel_id not in event.get("kernel_ids", []):
                        continue

                    # Filter by importance if specified
                    if min_importance is not None:
                        event_importance = event.get("importance")
                        if event_importance is None or event_importance < min_importance:
                            continue

                    events.append(event)

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    # Skip malformed lines
                    print(f"[spark_plug_history] Warning: Skipping malformed event: {e}")
                    continue

    except Exception as e:
        print(f"[spark_plug_history] Warning: Error reading {NEW_HISTORY_FILE}: {e}")
        return []

    # Sort by timestamp descending (newest first)
    events.sort(key=lambda e: e.get("ts", ""), reverse=True)

    # Apply limit
    if max_events is not None:
        events = events[:max_events]

    return events


def load_from_legacy_format(
    kernel_id: str,
    max_events: Optional[int] = None
) -> List[Dict]:
    """
    Load events from legacy format (user_events.jsonl) and normalize

    Returns normalized event dicts
    """
    if not LEGACY_HISTORY_FILE.exists():
        return []

    events = []

    try:
        with open(LEGACY_HISTORY_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    legacy_event = json.loads(line)

                    # Check if this event is relevant to the kernel
                    context = legacy_event.get("context", {})
                    event_kernel_id = context.get("kernel_id")

                    # Only include events with matching kernel_id
                    # (Higher-level code can add general events if needed)
                    if event_kernel_id == kernel_id:
                        normalized = normalize_legacy_event(legacy_event)
                        events.append(normalized)

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    # Skip malformed lines
                    print(f"[spark_plug_history] Warning: Skipping malformed legacy event: {e}")
                    continue

    except Exception as e:
        print(f"[spark_plug_history] Warning: Error reading {LEGACY_HISTORY_FILE}: {e}")
        return []

    # Sort by timestamp descending (newest first)
    events.sort(key=lambda e: e.get("ts", ""), reverse=True)

    # Apply limit
    if max_events is not None:
        events = events[:max_events]

    return events


def load_kernel_history_events(
    kernel_id: str,
    max_events: Optional[int] = None,
    min_importance: Optional[int] = None,
) -> List[Dict]:
    """
    Load history events relevant to a given kernel_id

    Prefers new format (ai/history/events.jsonl) but falls back gracefully
    to legacy format (ai/history/user_events.jsonl) if no new events found.

    Args:
        kernel_id: Kernel identifier (e.g., "risk_model_v2")
        max_events: Maximum number of events to return (default: all)
        min_importance: Minimum importance level (1-10) for filtering (default: no filter)
                       Only applies to new format events (legacy events have no importance)

    Returns:
        List of normalized event dicts with structure:
        {
            "event_id": str,
            "ts": str (ISO 8601 timestamp),
            "kind": str | None,
            "source": str | None,
            "kernel_ids": List[str],
            "summary": str,
            "details": dict,
            "importance": int | None,
            "tags": List[str]
        }

        Ordered by timestamp descending (newest first).
        Returns empty list if no events found or files missing.

    Example:
        # Get last 50 events for risk_model_v2 with importance >= 6
        events = load_kernel_history_events(
            kernel_id="risk_model_v2",
            max_events=50,
            min_importance=6
        )
    """
    # Try new format first
    events = load_from_new_format(
        kernel_id=kernel_id,
        max_events=max_events,
        min_importance=min_importance
    )

    if events:
        return events

    # Fall back to legacy format
    print(f"[spark_plug_history] No events found in new format, falling back to legacy format")
    events = load_from_legacy_format(
        kernel_id=kernel_id,
        max_events=max_events
    )

    return events


def get_history_stats(kernel_id: str) -> Dict:
    """
    Get statistics about available history for a kernel

    Returns:
        {
            "new_format_events": int,
            "legacy_format_events": int,
            "total_events": int,
            "using_format": "new" | "legacy" | "none"
        }
    """
    new_events = load_from_new_format(kernel_id=kernel_id)
    legacy_events = load_from_legacy_format(kernel_id=kernel_id)

    using_format = "none"
    if new_events:
        using_format = "new"
    elif legacy_events:
        using_format = "legacy"

    return {
        "new_format_events": len(new_events),
        "legacy_format_events": len(legacy_events),
        "total_events": len(new_events) + len(legacy_events),
        "using_format": using_format
    }
