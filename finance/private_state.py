"""Private finance storage paths shared by repository finance modules."""

from __future__ import annotations

import os
from pathlib import Path


def private_root() -> Path:
    configured = os.environ.get("HANDS_OFF_PRIVATE_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".config" / "hands-off-engine"


def private_finance_hub_path() -> Path:
    root = private_root().resolve()
    directory = root / "finance"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        root.chmod(0o700)
        directory.chmod(0o700)
    except OSError:
        pass
    return directory / "private_finance_hub.json"
