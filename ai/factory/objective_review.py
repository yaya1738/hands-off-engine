#!/usr/bin/env python3
"""Authenticated, append-only Factory objective review and planning handoff.

Review acceptance means eligible for planning only. This module never creates
task assignments, dispatches workers, invokes executors, or grants execution.
The Telegram actor is revalidated against the operator allowlist even though
the ingress is expected to have authenticated the request already.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai.factory.authority_gateway import FactoryAuthorityGateway


class ObjectiveReviewError(ValueError):
    """Raised when an objective review is invalid or unauthorized."""


class FactoryObjectiveReview:
    """Append-only review ledger with idempotent, planning-only handoff."""

    def __init__(self, repo_root: Path | str | None = None, gateway=None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
        self.state_dir = self.repo_root / "state"
        self.events_path = self.state_dir / "factory_objective_reviews.jsonl"
        self.planning_path = self.state_dir / "factory_planning_queue.jsonl"
        self.lock_path = self.state_dir / "factory_objective_review.lock"
        self.gateway = gateway or FactoryAuthorityGateway(self.repo_root)

    @staticmethod
    def _authorize(*, authenticated: bool, authenticated_actor_id: Any, channel: str) -> str:
        if authenticated is not True:
            raise ObjectiveReviewError("authenticated operator identity required")
        if channel != "telegram":
            raise ObjectiveReviewError("unsupported review channel")
        actor_id = str(authenticated_actor_id) if authenticated_actor_id is not None else ""
        allowed = {
            item.strip()
            for item in os.getenv("TELEGRAM_ADMIN_USER_IDS", "").split(",")
            if item.strip()
        }
        if not allowed or actor_id not in allowed:
            raise ObjectiveReviewError("operator is not in TELEGRAM_ADMIN_USER_IDS")
        return actor_id

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict]:
        records = []
        if not path.exists():
            return records
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    records.append(item)
        return records

    @staticmethod
    def _append(path: Path, record: dict) -> None:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def review(
        self,
        goal_id: str,
        decision: str,
        *,
        authenticated: bool = False,
        authenticated_actor_id: Any = None,
        channel: str = "telegram",
        correlation_id: str | None = None,
    ) -> dict:
        """Accept for planning or reject; never grant execution authority."""
        actor_id = self._authorize(
            authenticated=authenticated,
            authenticated_actor_id=authenticated_actor_id,
            channel=channel,
        )
        if not isinstance(goal_id, str) or len(goal_id) != 64 or any(
            char not in "0123456789abcdef" for char in goal_id.lower()
        ):
            raise ObjectiveReviewError("goal_id must be a 64-character hexadecimal ID")
        if decision not in {"accept_for_planning", "reject"}:
            raise ObjectiveReviewError("decision must be accept_for_planning or reject")
        if correlation_id is not None and (
            not isinstance(correlation_id, str) or not correlation_id.strip() or len(correlation_id) > 200
        ):
            raise ObjectiveReviewError("correlation_id must be 1..200 characters")

        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                goal = self.gateway.get_goal(goal_id)
                if goal is None:
                    raise ObjectiveReviewError("objective not found")
                if goal.get("execution_enabled") is not False:
                    raise ObjectiveReviewError("objective execution state is not fail-closed")

                events = self._read_jsonl(self.events_path)
                prior = next((event for event in events if event.get("goal_id") == goal_id), None)
                if prior:
                    if prior.get("decision") != decision:
                        raise ObjectiveReviewError("objective already has a conflicting terminal review")
                    if prior.get("actor_id") != actor_id:
                        raise ObjectiveReviewError("replay actor does not match original reviewer")
                    if decision == "accept_for_planning":
                        self._ensure_planning_handoff(goal, prior)
                    return {
                        "status": "idempotent_replay",
                        "goal_id": goal_id,
                        "review_event_id": prior["event_id"],
                        "planning_only": decision == "accept_for_planning",
                        "execution_enabled": False,
                    }

                event_id = hashlib.sha256(
                    f"{goal_id}\n{decision}\n{actor_id}".encode("utf-8")
                ).hexdigest()
                event = {
                    "event_id": event_id,
                    "goal_id": goal_id,
                    "decision": decision,
                    "actor_id": actor_id,
                    "channel": channel,
                    "correlation_id": correlation_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "execution_enabled": False,
                }
                self._append(self.events_path, event)
                if decision == "accept_for_planning":
                    self._ensure_planning_handoff(goal, event)
                return {
                    "status": "accepted_for_planning" if decision == "accept_for_planning" else "rejected",
                    "goal_id": goal_id,
                    "review_event_id": event_id,
                    "planning_only": decision == "accept_for_planning",
                    "execution_enabled": False,
                }
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _ensure_planning_handoff(self, goal: dict, event: dict) -> None:
        """Idempotently append a planning-only record; never dispatch it."""
        existing = self._read_jsonl(self.planning_path)
        if any(item.get("goal_id") == goal["goal_id"] for item in existing):
            return
        self._append(self.planning_path, {
            "goal_id": goal["goal_id"],
            "objective": goal["objective"],
            "priority": goal["priority"],
            "source": goal["source"],
            "review_event_id": event["event_id"],
            "status": "queued_for_planning",
            "dispatch_enabled": False,
            "execution_enabled": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })


__all__ = ["FactoryObjectiveReview", "ObjectiveReviewError"]
