"""Locked, atomic updates for the shared private finance hub."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


@contextmanager
def _hub_lock(path: Path) -> Iterator[None]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with open(lock_path, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_hub(path: str | Path) -> dict:
    """Read a consistent snapshot while excluding concurrent hub writers."""
    target = Path(path)
    with _hub_lock(target):
        if not target.exists():
            return {"accounts": {}}
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Finance hub root must be a JSON object")
        return data


def update_account(
    path: str | Path,
    account_name: str,
    updates: dict[str, Any],
    *,
    remove_keys: tuple[str, ...] = (),
    top_level_updates: dict[str, Any] | None = None,
) -> dict:
    """Merge one account's changes into the latest snapshot under one lock."""
    target = Path(path)
    with _hub_lock(target):
        if target.exists():
            hub = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(hub, dict):
                raise ValueError("Finance hub root must be a JSON object")
        else:
            hub = {}
        accounts = hub.setdefault("accounts", {})
        if not isinstance(accounts, dict):
            raise ValueError("Finance hub accounts must be a JSON object")
        account = accounts.setdefault(account_name, {})
        if not isinstance(account, dict):
            raise ValueError(f"Finance hub account {account_name!r} must be a JSON object")
        for key in remove_keys:
            account.pop(key, None)
        account.update(updates)
        if top_level_updates:
            hub.update(top_level_updates)

        fd, temp_name = tempfile.mkstemp(
            prefix=target.name + ".",
            suffix=".tmp",
            dir=str(target.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(hub, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
            dir_fd = os.open(str(target.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except Exception:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
            raise
        return hub
