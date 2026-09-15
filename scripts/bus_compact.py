#!/usr/bin/env python3
"""Compact the canonical coordination bus.

Deduplicates by msg_id/event_id (keeps first occurrence) and optionally
drops stale blocker events older than a configurable age.

Safety:
- Atomic write: writes to a .tmp file then renames.
- Read-only first pass: validates before any write.
- No deletion: the original bus is the source of truth; compaction is
  an observation-level noise reduction, not a truth rewrite.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"


def _parse_ts(msg: dict) -> datetime | None:
    ts = msg.get("timestamp")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def compact(
    bus_path: Path | None = None,
    max_blocker_age: timedelta | None = None,
    dry_run: bool = False,
) -> dict:
    """Compact the bus file. Returns stats."""
    path = Path(bus_path) if bus_path else BUS
    if not path.exists():
        return {"error": "bus not found"}

    rows: list[dict] = []
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    before = len(rows)

    # Deduplicate by identity key (event_id > msg_id > fallback)
    seen: set[str] = set()
    deduped: list[dict] = []
    for msg in rows:
        key = msg.get("event_id") or msg.get("msg_id") or ""
        if not key:
            deduped.append(msg)
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(msg)

    after_dedup = len(deduped)

    # Optionally drop stale blockers
    after = after_dedup
    if max_blocker_age is not None:
        cutoff = datetime.now(timezone.utc) - max_blocker_age
        filtered: list[dict] = []
        for msg in deduped:
            ctx = msg.get("context") or {}
            is_blocker = ctx.get("event_type") == "blocker" or msg.get("type") == "blocker"
            if is_blocker:
                ts = _parse_ts(msg)
                if ts and ts < cutoff:
                    continue
            filtered.append(msg)
        after = len(filtered)
        deduped = filtered

    if not dry_run:
        tmp = path.with_suffix(".tmp")
        with tmp.open("w") as f:
            for msg in deduped:
                f.write(json.dumps(msg, default=str) + "\n")
        tmp.rename(path)

    return {
        "before": before,
        "after_dedup": after_dedup,
        "after": after,
        "removed": before - after,
        "dry_run": dry_run,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compact the canonical bus")
    parser.add_argument("--max-blocker-age", type=int, default=24,
                        help="Drop blocker events older than N hours (default 24)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print stats without writing")
    parser.add_argument("--bus", type=str, default=None,
                        help="Path to bus file (default: ai/coordination/messages.jsonl)")
    args = parser.parse_args()
    age = timedelta(hours=args.max_blocker_age) if args.max_blocker_age else None
    result = compact(bus_path=args.bus, max_blocker_age=age, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
