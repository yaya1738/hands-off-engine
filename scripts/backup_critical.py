#!/usr/bin/env python3
"""Backup critical system files to prevent data loss."""

import shutil
import json
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path("/root/hands-off-engine")
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

CRITICAL_FILES = [
    ".env",
    ".env.polymarket",
    "state/unified_system_state.json",
    "state/brain_state.json",
    "state/script_registry.json",
    "state/self_preservation.json",
    "state/threat_analysis.json",
    "state/system_topology.json",
]

def backup():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_subdir = BACKUP_DIR / timestamp
    backup_subdir.mkdir(exist_ok=True)
    
    backed_up = []
    for filepath in CRITICAL_FILES:
        src = BASE_DIR / filepath
        if src.exists():
            dst = backup_subdir / filepath.replace("/", "_")
            shutil.copy2(src, dst)
            backed_up.append(filepath)
    
    # Write manifest
    manifest = {
        "timestamp": timestamp,
        "files": backed_up,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    with open(backup_subdir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Backed up {len(backed_up)} files to {backup_subdir}")
    
    # Clean old backups (keep last 7)
    all_backups = sorted(BACKUP_DIR.glob("2*"), reverse=True)
    for old_backup in all_backups[7:]:
        shutil.rmtree(old_backup)
        print(f"Cleaned old backup: {old_backup.name}")

if __name__ == "__main__":
    backup()
