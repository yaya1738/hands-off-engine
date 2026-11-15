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
from pathlib import Path
from typing import Any


class FactoryAuthorityGateway:
    """Append-only objective queue; admission never grants execution authority."""

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
        }

        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                if self.queue_path.exists():
                    with self.queue_path.open("r", encoding="utf-8") as queue:
                        for line in queue:
                            if not line.strip():
                                continue
                            try:
                                existing = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if existing.get("idempotency_key") == key:
                                if existing.get("objective") != objective:
                                    raise ValueError("idempotency key already belongs to a different objective")
                                return {
                                    "status": "idempotent_replay",
                                    "goal_id": existing.get("goal_id", goal_id),
                                    "execution_enabled": False,
                                }
                with self.queue_path.open("a", encoding="utf-8") as queue:
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


__all__ = ["FactoryAuthorityGateway"]
