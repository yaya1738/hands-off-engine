#!/usr/bin/env python3
"""Bus Cleanup — archives old messages to keep messages.jsonl manageable.

The bus grows fast from continuation events. This archives messages
older than 2 hours to messages_archive/YYYY-MM-DD.jsonl while keeping
task_assignments and task_results.
"""
import json
import gzip
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent.parent
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
ARCHIVE_DIR = ROOT / "ai" / "coordination" / "archive"
KEEP_TYPES = {"task_assignment", "task_result", "status_update", "handoff_summary", "handoff_agreement", "coordination", "topology_reconciliation"}
MAX_AGE_HOURS = 2


def run():
    if not BUS.exists():
        print("No bus file")
        return
    
    lines = BUS.read_text().splitlines()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=MAX_AGE_HOURS)
    
    keep = []
    archive = []
    
    for line in lines:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
            msg_type = msg.get("type", "")
            ts_str = msg.get("timestamp", "")
            
            # Always keep important types
            if msg_type in KEEP_TYPES:
                keep.append(line)
                continue
            
            # Parse timestamp and check age
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts < cutoff:
                    archive.append(line)
                else:
                    keep.append(line)
            except Exception:
                keep.append(line)  # Can't parse, keep it
        except json.JSONDecodeError:
            keep.append(line)  # Can't parse, keep it
    
    if not archive:
        print(f"No messages to archive ({len(keep)} kept)")
        return
    
    # Archive
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_file = ARCHIVE_DIR / f"messages_{now.strftime('%Y%m%d_%H%M')}.jsonl.gz"
    with gzip.open(archive_file, "wt") as f:
        for line in archive:
            f.write(line + "\n")
    
    # Rewrite bus with only kept messages
    with open(BUS, "w") as f:
        for line in keep:
            f.write(line + "\n")
    
    print(f"Archived {len(archive)} messages to {archive_file.name}")
    print(f"Bus: {len(lines)} → {len(keep)} messages")


if __name__ == "__main__":
    run()
