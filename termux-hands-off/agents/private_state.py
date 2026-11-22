"""Resolve private Termux finance files outside the public repository."""

from __future__ import annotations

import os
from pathlib import Path


def private_root() -> Path:
    configured = os.environ.get("HANDS_OFF_PRIVATE_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".config" / "hands-off-engine"


def _relative(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("private-state path must be relative and cannot traverse directories")
    return path


def _secure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def private_path(relative: str | Path, *, create_parent: bool = False) -> Path:
    """Prefer migrated legacy runtime data, then migrated repo data.

    Missing files resolve to the legacy-runtime location. No public-repository
    or plaintext legacy fallback is permitted.
    """
    rel = _relative(relative)
    root = private_root()
    candidates = (
        root / "legacy_runtime" / rel,
        root / "termux-hands-off" / rel,
    )
    target = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    if create_parent:
        _secure_directory(target.parent)
    return target


def private_directory(relative: str | Path, *, create: bool = False) -> Path:
    rel = _relative(relative)
    root = private_root()
    candidates = (
        root / "legacy_runtime" / rel,
        root / "termux-hands-off" / rel,
    )
    target = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    if create:
        _secure_directory(target)
    return target
