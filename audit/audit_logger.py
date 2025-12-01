#!/usr/bin/env python3
"""
Core audit logging functionality
Immutable event logging with JSON storage
"""
import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AuditEvent:
    """Immutable audit event record"""
    event_id: str
    session_id: str
    timestamp: str
    component: str
    action: str
    metadata: Dict[str, Any]
    cost: Optional[float] = None
    revenue: Optional[float] = None
    outcome: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class AuditLogger:
    """
    Centralized audit logger for all AI operations

    Features:
    - Immutable event log (append-only)
    - Session-based tracking
    - Component-based filtering
    - Cost and revenue tracking
    - Error tracking
    """

    def __init__(self, log_dir: str = "audit/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = str(uuid.uuid4())

    def log_event(
        self,
        component: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
        cost: Optional[float] = None,
        revenue: Optional[float] = None,
        outcome: Optional[str] = None,
        error: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AuditEvent:
        """
        Log an audit event

        Args:
            component: Component name (e.g., "ai.claude", "ai.chatgpt", "trading.polymarket")
            action: Action being performed (e.g., "plan_generation", "trade_execution")
            metadata: Additional context data
            cost: Cost incurred (in USD)
            revenue: Revenue generated (in USD)
            outcome: Outcome description
            error: Error message if failed
            session_id: Optional session ID (defaults to logger's session)

        Returns:
            AuditEvent object
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id or self.session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            component=component,
            action=action,
            metadata=metadata or {},
            cost=cost,
            revenue=revenue,
            outcome=outcome,
            error=error
        )

        # Write to component-specific log file
        log_file = self.log_dir / f"{component.replace('.', '_')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

        # Also write to session log
        session_log = self.log_dir / f"session_{event.session_id}.jsonl"
        with open(session_log, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

        return event

    def get_events(
        self,
        component: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditEvent]:
        """
        Query audit events with filters

        Args:
            component: Filter by component
            session_id: Filter by session
            start_time: Filter by start timestamp
            end_time: Filter by end timestamp

        Returns:
            List of matching AuditEvent objects
        """
        events = []

        # Determine which files to read
        if component:
            log_files = [self.log_dir / f"{component.replace('.', '_')}.jsonl"]
        elif session_id:
            log_files = [self.log_dir / f"session_{session_id}.jsonl"]
        else:
            log_files = list(self.log_dir.glob("*.jsonl"))

        for log_file in log_files:
            if not log_file.exists():
                continue

            with open(log_file, "r") as f:
                for line in f:
                    event_data = json.loads(line.strip())

                    # Apply filters
                    if session_id and event_data["session_id"] != session_id:
                        continue

                    event_time = datetime.fromisoformat(event_data["timestamp"])
                    if start_time and event_time < start_time:
                        continue
                    if end_time and event_time > end_time:
                        continue

                    events.append(AuditEvent(**event_data))

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        return events

    def get_session_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for a session

        Args:
            session_id: Session to summarize (defaults to current session)

        Returns:
            Dictionary with summary statistics
        """
        sid = session_id or self.session_id
        events = self.get_events(session_id=sid)

        total_cost = sum(e.cost or 0 for e in events)
        total_revenue = sum(e.revenue or 0 for e in events)
        net_profit = total_revenue - total_cost

        component_stats = {}
        for event in events:
            if event.component not in component_stats:
                component_stats[event.component] = {
                    "event_count": 0,
                    "cost": 0.0,
                    "revenue": 0.0,
                    "errors": 0
                }

            stats = component_stats[event.component]
            stats["event_count"] += 1
            stats["cost"] += event.cost or 0
            stats["revenue"] += event.revenue or 0
            if event.error:
                stats["errors"] += 1

        return {
            "session_id": sid,
            "total_events": len(events),
            "total_cost": total_cost,
            "total_revenue": total_revenue,
            "net_profit": net_profit,
            "roi": (net_profit / total_cost * 100) if total_cost > 0 else 0,
            "component_stats": component_stats,
            "start_time": events[0].timestamp if events else None,
            "end_time": events[-1].timestamp if events else None
        }
