"""
History Logger v0.1 (Part 3: User Expansion)

Append-only logging system for historical events.

API:
    - append_history_event(event) -> None
    - load_history_events(limit=None, event_type=None) -> List[HistoryEvent]
    - count_history_events(event_type=None) -> int

Storage:
    - ai/history/user_events.jsonl (append-only JSONL)

Safety:
    - File-based, no network calls
    - No imports of trading/risk/decider/executor modules
    - Append-only (no deletion or modification of history)

See: docs/SPARK_PLUG_PART3_USER_CONNECTOR_v0.1.md
"""

import json
from pathlib import Path
from typing import List, Optional

from ai_nexus.spark_plug_types import HistoryEvent

# Paths
REPO_ROOT = Path(__file__).parent.parent
HISTORY_FILE = REPO_ROOT / "ai" / "history" / "user_events.jsonl"


# =============================================================================
# Core API
# =============================================================================

def append_history_event(event: HistoryEvent) -> None:
    """
    Append a HistoryEvent to the history log

    Args:
        event: HistoryEvent to append

    Side effects:
        - Creates ai/history/ directory if it doesn't exist
        - Appends event as JSONL line to user_events.jsonl
    """
    # Ensure directory exists
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Append event as JSONL line
    with open(HISTORY_FILE, 'a') as f:
        f.write(event.to_jsonl_line() + '\n')


def load_history_events(
    limit: Optional[int] = None,
    event_type: Optional[str] = None,
    offset: int = 0
) -> List[HistoryEvent]:
    """
    Load history events from the log

    Args:
        limit: Maximum number of events to return (most recent first)
        event_type: Filter by event type (e.g., "user_message", "system_decision")
        offset: Skip first N events (useful for pagination)

    Returns:
        List of HistoryEvent objects, ordered from newest to oldest

    Examples:
        # Get last 20 events
        events = load_history_events(limit=20)

        # Get last 10 user messages
        user_msgs = load_history_events(limit=10, event_type="user_message")

        # Get events 20-40 (for pagination)
        page2 = load_history_events(limit=20, offset=20)
    """
    if not HISTORY_FILE.exists():
        return []

    # Read all lines
    with open(HISTORY_FILE) as f:
        lines = [line.strip() for line in f if line.strip()]

    # Parse into HistoryEvent objects
    events = []
    for line in lines:
        try:
            event = HistoryEvent.from_jsonl_line(line)
            events.append(event)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # Skip malformed lines
            print(f"Warning: Skipping malformed history event: {e}")
            continue

    # Filter by event_type if specified
    if event_type:
        events = [e for e in events if e.event_type == event_type]

    # Reverse to get newest first
    events.reverse()

    # Apply offset and limit
    if offset > 0:
        events = events[offset:]

    if limit is not None:
        events = events[:limit]

    return events


def count_history_events(event_type: Optional[str] = None) -> int:
    """
    Count history events in the log

    Args:
        event_type: Filter by event type (optional)

    Returns:
        Number of events matching the filter
    """
    if not HISTORY_FILE.exists():
        return 0

    count = 0
    with open(HISTORY_FILE) as f:
        for line in f:
            if not line.strip():
                continue

            try:
                if event_type:
                    event_data = json.loads(line)
                    if event_data.get("event_type") == event_type:
                        count += 1
                else:
                    count += 1
            except (json.JSONDecodeError, KeyError):
                continue

    return count


def get_event_types() -> List[str]:
    """
    Get list of all event types present in the history

    Returns:
        List of unique event types
    """
    if not HISTORY_FILE.exists():
        return []

    event_types = set()
    with open(HISTORY_FILE) as f:
        for line in f:
            if not line.strip():
                continue

            try:
                event_data = json.loads(line)
                event_types.add(event_data.get("event_type", "unknown"))
            except json.JSONDecodeError:
                continue

    return sorted(list(event_types))


# =============================================================================
# Utility Functions
# =============================================================================

def clear_history(confirm: bool = False) -> None:
    """
    Clear all history events

    Args:
        confirm: Must be True to actually clear (safety check)

    Raises:
        ValueError: If confirm is False
    """
    if not confirm:
        raise ValueError(
            "Must pass confirm=True to clear history. "
            "This is a destructive operation."
        )

    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()


def get_history_stats() -> dict:
    """
    Get statistics about the history log

    Returns:
        Dict with stats: total_events, event_types, oldest_timestamp, newest_timestamp
    """
    events = load_history_events()

    if not events:
        return {
            "total_events": 0,
            "event_types": {},
            "oldest_timestamp": None,
            "newest_timestamp": None
        }

    # Count by event type
    event_type_counts = {}
    for event in events:
        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1

    # Oldest and newest (events are already newest-first)
    newest = events[0]
    oldest = events[-1]

    return {
        "total_events": len(events),
        "event_types": event_type_counts,
        "oldest_timestamp": oldest.timestamp,
        "newest_timestamp": newest.timestamp
    }


# =============================================================================
# Example Usage (for testing)
# =============================================================================

if __name__ == "__main__":
    from ai_nexus.spark_plug_types import create_history_event

    # Example: Log a user message
    print("Logging example events...")

    event1 = create_history_event(
        event_type="user_message",
        source="user:froggy",
        content="What's the current Kelly fraction for risk model v2?",
        kernel_id="risk_model_v2"
    )
    append_history_event(event1)
    print(f"✓ Logged: {event1.event_id}")

    event2 = create_history_event(
        event_type="system_decision",
        source="cpu_risk_20251125_01",
        content="Updated Kelly fraction to 0.15 based on recent drawdown analysis",
        kernel_id="risk_model_v2",
        decision_id="dec_001"
    )
    append_history_event(event2)
    print(f"✓ Logged: {event2.event_id}")

    # Load and display
    print("\n--- Recent History ---")
    recent = load_history_events(limit=10)
    for event in recent:
        print(f"[{event.timestamp}] {event.event_type}: {event.content[:60]}...")

    # Stats
    print("\n--- History Stats ---")
    stats = get_history_stats()
    print(f"Total events: {stats['total_events']}")
    print(f"Event types: {stats['event_types']}")
    print(f"Oldest: {stats['oldest_timestamp']}")
    print(f"Newest: {stats['newest_timestamp']}")
