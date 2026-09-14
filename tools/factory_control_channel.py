#!/usr/bin/env python3
"""Durable, bounded control/state channel for the live Factory node.

The channel deliberately contains no credentials and performs no execution by
itself. It gives an external agent one compact, stable contract for submitting
idempotent commands and reading the latest observed runtime state.

Files under ``state/`` are runtime-local and are never treated as source code:
``factory_control_state.json`` is the published snapshot and
``factory_control_commands.jsonl`` is the append-only command inbox.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


SCHEMA_VERSION = 1
DEFAULT_STATE = {
    "schema_version": SCHEMA_VERSION,
    "node_id": "unknown",
    "status": "unknown",
    "operating_state": "unknown",
    "objective": None,
    "last_action": None,
    "last_result": None,
    "pending_commands": 0,
    "problem": None,
    "next_action": None,
    "observed_at": None,
    "fresh_until": None,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(name, path)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


def command_idempotency_key(command: Dict[str, Any]) -> str:
    """Return a stable key for a command when callers omit one."""
    explicit = str(command.get("idempotency_key", "")).strip()
    if explicit:
        return explicit
    canonical = json.dumps(
        {k: command[k] for k in sorted(command) if k not in {"id", "created_at"}},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def publish_state(repo_root: Path, **updates: Any) -> Dict[str, Any]:
    """Publish one bounded state snapshot and return it."""
    path = repo_root / "state" / "factory_control_state.json"
    current = dict(DEFAULT_STATE)
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                current.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass
    current.update({k: v for k, v in updates.items() if v is not None})
    current["schema_version"] = SCHEMA_VERSION
    current["observed_at"] = _now()
    _atomic_write(path, current)
    return current


def load_state(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / "state" / "factory_control_state.json"
    if not path.exists():
        return dict(DEFAULT_STATE)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_STATE)
    return {**DEFAULT_STATE, **value} if isinstance(value, dict) else dict(DEFAULT_STATE)


def append_command(repo_root: Path, objective: str, *, source: str = "external", idempotency_key: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Append a durable command; duplicate idempotency keys are ignored."""
    objective = str(objective).strip()
    if not objective:
        raise ValueError("objective must not be empty")
    command = {
        "schema_version": SCHEMA_VERSION,
        "id": str(uuid.uuid4()),
        "objective": objective,
        "source": source,
        "created_at": _now(),
        "idempotency_key": idempotency_key,
        "metadata": metadata or {},
    }
    command["idempotency_key"] = command_idempotency_key(command)
    path = repo_root / "state" / "factory_control_commands.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for existing in _read_jsonl(path):
        if existing.get("idempotency_key") == command["idempotency_key"]:
            return existing
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(command, sort_keys=True) + "\n")
    return command


def _read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return ()
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def pending_commands(repo_root: Path, claimed_ids: Optional[set[str]] = None) -> list[Dict[str, Any]]:
    claimed_ids = claimed_ids or set()
    return [c for c in _read_jsonl(repo_root / "state" / "factory_control_commands.jsonl") if c.get("id") not in claimed_ids]


def compact_snapshot(repo_root: Path) -> Dict[str, Any]:
    """Return only the stable fields intended for external consumers."""
    state = load_state(repo_root)
    return {k: state.get(k) for k in DEFAULT_STATE}


if __name__ == "__main__":
    root = Path(os.environ.get("FACTORY_REPO_ROOT", Path(__file__).resolve().parents[1]))
    print(json.dumps(compact_snapshot(root), sort_keys=True))
