#!/usr/bin/env python3
"""
Daily Backup Runner

Creates daily backups of critical state files.
Should be run daily via cron.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.backup import BackupSystem


def main():
    backup = BackupSystem()
    
    print(f"Creating daily backup...")
    print(f"Backup directory: {backup.backup_dir}")
    
    # Create backup
    success = backup.create_daily_backup()
    
    if success:
        print("✓ Backup created successfully")
    else:
        print("⚠ Backup completed with some failures")
        sys.exit(1)
    
    # Cleanup old backups
    print(f"\nCleaning up backups older than {backup.retention_days} days...")
    removed = backup.cleanup_old_backups()
    print(f"✓ Removed {removed} old backup(s)")


if __name__ == "__main__":
    main()
