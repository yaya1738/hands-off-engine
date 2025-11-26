"""
Spark Plug History Logging v0.1

Captures important system actions as structured events that feed Spark Plug kernels.
Append-only JSONL storage with best-effort logging (failures never crash callers).
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class HistoryEvent:
    """Structured event representing a significant system action."""

    event_id: str
    ts: datetime
    kind: str              # "risk_decision", "decider_outcome", "system_health", "ai_coordination", etc.
    source: str            # "risk_model_v2", "ho_decider", "infra_healthcheck", "ai_runner.sparkplug", etc.
    kernel_ids: list[str]  # kernels this should feed
    summary: str           # 1-2 line human summary
    details: dict[str, Any]
    importance: int        # 1-10
    tags: list[str]


# Default storage path
HISTORY_LOG_PATH = Path(__file__).parent.parent / "ai" / "history" / "events.jsonl"


def default_kernel_ids_for_event(kind: str, source: str) -> list[str]:
    """
    Derive default kernel IDs based on event kind and source.

    This routing logic determines which Spark Plug kernels should be updated
    when new events arrive.
    """
    # Explicit routing rules
    if kind == "risk_decision":
        return ["risk_model_v2", "trading_philosophy"]
    elif kind == "decider_outcome":
        return ["risk_model_v2", "alpha_polymarket_core", "trading_philosophy"]
    elif kind == "system_health":
        return ["system_health"]
    elif kind == "ai_coordination":
        return ["ai_coordination", "system_health"]
    else:
        # Fallback: everything feeds trading_philosophy
        return ["trading_philosophy"]


def log_history_event(event: HistoryEvent) -> None:
    """
    Append a history event to the JSONL log file.

    Best-effort only: failures are logged to console but never raise exceptions.
    Auto-generates event_id and ts if not provided.
    """
    try:
        # Fill in defaults
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        if not event.ts:
            event.ts = datetime.now(timezone.utc)

        # Validate required fields
        if not event.kernel_ids:
            print(f"[history_log] WARNING: Event {event.event_id} has empty kernel_ids, skipping")
            return
        if not event.kind:
            print(f"[history_log] WARNING: Event {event.event_id} has empty kind, skipping")
            return
        if not event.source:
            print(f"[history_log] WARNING: Event {event.event_id} has empty source, skipping")
            return
        if not event.summary:
            print(f"[history_log] WARNING: Event {event.event_id} has empty summary, skipping")
            return

        # Ensure directory exists
        HISTORY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and make ts JSON-serializable
        event_dict = asdict(event)
        event_dict["ts"] = event.ts.isoformat()

        # Append to JSONL file
        with open(HISTORY_LOG_PATH, "a") as f:
            f.write(json.dumps(event_dict) + "\n")

    except Exception as e:
        # Never crash callers - just log the error
        print(f"[history_log] ERROR: Failed to log event: {e}")


def log_kernel_history_event(
    *,
    kernel_ids: list[str] | None,
    kind: str,
    source: str,
    summary: str,
    details: dict | None = None,
    importance: int = 5,
    tags: list[str] | None = None,
    ts: datetime | None = None,
) -> None:
    """
    Convenience function to log a kernel history event.

    If kernel_ids is None/empty, automatically derives appropriate kernels
    based on the event kind and source.

    Args:
        kernel_ids: Target kernels (auto-derived if None/empty)
        kind: Event type (e.g., "risk_decision", "decider_outcome")
        source: Event source (e.g., "risk_model_v2", "ho_decider")
        summary: 1-2 line human-readable summary
        details: Additional structured data (default: empty dict)
        importance: 1-10 importance score (default: 5)
        tags: List of tags for filtering (default: empty list)
        ts: Event timestamp (default: now UTC)
    """
    try:
        # Auto-derive kernel_ids if not provided
        if not kernel_ids:
            kernel_ids = default_kernel_ids_for_event(kind, source)

        # Build event
        event = HistoryEvent(
            event_id="",  # Will be auto-generated
            ts=ts or datetime.now(timezone.utc),
            kind=kind,
            source=source,
            kernel_ids=kernel_ids,
            summary=summary,
            details=details or {},
            importance=importance,
            tags=tags or [],
        )

        # Delegate to main logging function
        log_history_event(event)

    except Exception as e:
        # Never crash callers
        print(f"[history_log] ERROR: Failed to log kernel history event: {e}")
