#!/usr/bin/env python3
"""Build a bounded read-only observability snapshot for the Control Room.

The canonical coordination bus remains the source of truth. Task lifecycle
state is only a durable projection, so operators and agents can inspect both
views without introducing another transport or mutating execution state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lifecycle_dashboard import current_state


def _read_bus(path: Path, limit: int) -> List[dict]:
    if not path.exists() or limit <= 0:
        return []
    rows: List[dict] = []
    with path.open("rb") as handle:
        handle.seek(0, 2)
        position = handle.tell()
        carry = b""
        while position > 0 and len(rows) < limit:
            size = min(8192, position)
            position -= size
            handle.seek(position)
            chunk = handle.read(size)
            data = chunk + carry
            parts = data.split(b"\n")
            carry = parts.pop(0)
            for line in reversed(parts):
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    rows.append(value)
                    if len(rows) >= limit:
                        break
    if carry and len(rows) < limit:
        try:
            value = json.loads(carry)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict):
            rows.append(value)
    rows.reverse()
    return rows


def _read_lifecycle(path: Path, limit: int) -> Dict[str, dict]:
    if not path.exists() or limit <= 0:
        return {}
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    items = [(str(k), v) for k, v in value.items() if isinstance(v, dict)]
    items.sort(key=lambda item: (str(item[1].get("updated_at", "")), item[0]), reverse=True)
    return {
        task_id: {**entry, "current_state": current_state(entry)}
        for task_id, entry in items[:limit]
    }


def build_snapshot(repo_root: Optional[Path] = None, bus_limit: int = 120, lifecycle_limit: int = 100) -> Dict[str, Any]:
    """Return bounded bus + lifecycle state without executing or mutating work."""
    root = Path(repo_root) if repo_root else ROOT
    bus = root / "ai" / "coordination" / "messages.jsonl"
    lifecycle = root / "state" / "task_lifecycle.json"
    events = _read_bus(bus, bus_limit)
    tasks = _read_lifecycle(lifecycle, lifecycle_limit)
    return {
        "source_of_truth": "ai/coordination/messages.jsonl",
        "bus": {
            "available": bus.exists(),
            "event_count": len(events),
            "events": events,
        },
        "lifecycle": {
            "available": lifecycle.exists(),
            "task_count": len(tasks),
            "tasks": tasks,
        },
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Print bounded Control Room observability state")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--bus-limit", type=int, default=120)
    parser.add_argument("--lifecycle-limit", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(build_snapshot(args.repo_root, args.bus_limit, args.lifecycle_limit), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
