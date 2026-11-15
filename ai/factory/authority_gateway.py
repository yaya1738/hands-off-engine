#!/usr/bin/env python3
"""Durable, idempotent Factory objective admission.

This gateway only records objectives for review. It has no dispatch, worker,
approval, or execution method. Queue entries are explicitly non-executable.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ObjectiveQueueIntegrityError(RuntimeError):
    """Raised when the durable objective queue cannot be trusted."""


class FactoryAuthorityGateway:
    """Append-only objective queue; admission never grants execution authority."""

    @staticmethod
    def _open_private(path: Path, mode: str):
        """Open (creating if needed) with owner-only permissions.

        Newly created files and locks are 0600 regardless of umask, so
        objective text and admission metadata are never group/world
        readable. Existing files keep their current mode (safe replacement).
        """
        flags = {
            "a": os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            "a+": os.O_RDWR | os.O_CREAT | os.O_APPEND,
        }.get(mode)
        if flags is None:
            raise ValueError(f"unsupported private-open mode: {mode}")
        descriptor = os.open(path, flags, 0o600)
        return os.fdopen(descriptor, mode, encoding="utf-8")

    def __init__(self, repo_root: Path | str | None = None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
        self.state_dir = self.repo_root / "state"
        self.queue_path = self.state_dir / "factory_objectives.jsonl"
        self.lock_path = self.state_dir / "factory_objectives.lock"

    @staticmethod
    def _validate_text(value: Any, name: str, limit: int) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        value = value.strip()
        if len(value) > limit:
            raise ValueError(f"{name} exceeds {limit} characters")
        return value

    def _iter_queue_records(self):
        """Yield the complete queue, rejecting corruption instead of hiding it."""
        if not self.queue_path.exists():
            return
        with self.queue_path.open("r", encoding="utf-8") as queue:
            for line_number, line in enumerate(queue, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ObjectiveQueueIntegrityError(
                        f"objective queue contains invalid JSON on line {line_number}"
                    ) from exc
                if not isinstance(record, dict):
                    raise ObjectiveQueueIntegrityError(
                        f"objective queue record on line {line_number} must be a JSON object"
                    )
                yield record

    def submit_goal(
        self,
        objective: str,
        *,
        priority: int = 3,
        source: str = "runtime",
        idempotency_key: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Persist one pending-review objective; never schedule or execute it."""
        objective = self._validate_text(objective, "objective", 1000)
        source = self._validate_text(source, "source", 80)
        if isinstance(priority, bool) or not isinstance(priority, int) or not 1 <= priority <= 5:
            raise ValueError("priority must be an integer from 1 to 5")
        key = self._validate_text(idempotency_key, "idempotency_key", 200) if idempotency_key is not None else None
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        try:
            metadata_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise ValueError("metadata must be JSON serializable") from exc
        if len(metadata_json) > 4096:
            raise ValueError("metadata exceeds 4096 characters")

        key = key or hashlib.sha256(f"{source}\n{objective}".encode("utf-8")).hexdigest()
        goal_id = hashlib.sha256(key.encode("utf-8")).hexdigest()
        record = {
            "goal_id": goal_id,
            "idempotency_key": key,
            "objective": objective,
            "priority": priority,
            "source": source,
            "status": "pending_review",
            "approval_required": True,
            "execution_enabled": False,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self._open_private(self.lock_path, "a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                matching_record = None
                conflicting_reuse = False
                for existing in self._iter_queue_records():
                    if existing.get("idempotency_key") == key:
                        if existing.get("objective") != objective:
                            conflicting_reuse = True
                        elif matching_record is None:
                            matching_record = existing
                if conflicting_reuse:
                    raise ValueError("idempotency key already belongs to a different objective")
                if matching_record is not None:
                    return {
                        "status": "idempotent_replay",
                        "goal_id": matching_record.get("goal_id", goal_id),
                        "execution_enabled": False,
                    }
                with self._open_private(self.queue_path, "a") as queue:
                    queue.write(json.dumps(record, sort_keys=True) + "\n")
                    queue.flush()
                    os.fsync(queue.fileno())
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

        return {
            "status": "queued_for_review",
            "goal_id": goal_id,
            "execution_enabled": False,
        }

    def list_goals(self, *, limit: int = 50, status: str | None = None) -> list[dict]:
        """Return a bounded newest-first view of queued objectives (read-only)."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ValueError("limit must be an integer from 1 to 200")
        if status is not None:
            status = self._validate_text(status, "status", 40)
        tail = deque(self._iter_queue_records(), maxlen=2000)
        records = []
        for record in reversed(tail):
            if status is not None and record.get("status") != status:
                continue
            records.append(record)
            if len(records) >= limit:
                break
        return records

    def get_goal(self, goal_id: str) -> dict | None:
        """Find one objective by stable ID without modifying queue state."""
        goal_id = self._validate_text(goal_id, "goal_id", 64)
        if len(goal_id) != 64 or any(ch not in "0123456789abcdef" for ch in goal_id.lower()):
            raise ValueError("goal_id must be a 64-character hexadecimal ID")
        matching_record = None
        for record in self._iter_queue_records():
            if record.get("goal_id") == goal_id and matching_record is None:
                matching_record = record
        return matching_record


__all__ = ["FactoryAuthorityGateway", "ObjectiveQueueIntegrityError"]
