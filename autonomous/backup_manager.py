#!/usr/bin/env python3
"""
Autonomous Backup Manager
==========================

Creates and maintains backups across multiple locations for redundancy.

Backups:
- Code → GitHub, GitLab, S3
- Data → Local, S3, Database
- State → Multiple encrypted copies
- Configs → Versioned and replicated

Never lose anything. Full redundancy.

Master: Yair Siegel
"""

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
BACKUP_DIR = PROJECT_ROOT / "backups"


class BackupManager:
    """Manages all system backups."""

    def __init__(self):
        self.state_file = STATE_DIR / "backup_manager.json"
        self.state = self._load_state()

        BACKUP_DIR.mkdir(exist_ok=True)

        # Backup locations
        self.locations = {
            "local": {
                "path": BACKUP_DIR,
                "enabled": True,
                "priority": 1
            },
            "github": {
                "remote": "origin",
                "branch": "local-sync",
                "enabled": True,
                "priority": 2
            },
            "gitlab": {
                "remote": "gitlab",
                "branch": "main",
                "enabled": False,  # Need to set up
                "priority": 3
            },
            "s3": {
                "bucket": "hands-off-engine-backups",
                "enabled": False,  # Need AWS creds
                "priority": 4
            }
        }

    def _load_state(self) -> Dict:
        """Load backup manager state."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backups_created": 0,
            "last_backup": None,
            "backup_locations": [],
            "total_size": 0
        }

    def _save_state(self):
        """Save backup manager state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def backup_code_to_github(self) -> bool:
        """Backup code to GitHub."""
        try:
            # Check if there are changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                print("⚠️  Uncommitted changes found. Commit first.")
                return False

            # Push to GitHub
            subprocess.run(
                ["git", "push", "origin", "local-sync"],
                cwd=PROJECT_ROOT,
                check=True
            )

            print("✅ Code backed up to GitHub")
            return True

        except Exception as e:
            print(f"❌ GitHub backup failed: {e}")
            return False

    def backup_state_files(self) -> bool:
        """Backup all state files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = BACKUP_DIR / f"state_backup_{timestamp}"
            backup_path.mkdir(exist_ok=True)

            # Copy all state files
            if STATE_DIR.exists():
                shutil.copytree(
                    STATE_DIR,
                    backup_path / "state",
                    dirs_exist_ok=True
                )

            # Copy config files
            config_dir = PROJECT_ROOT / "config"
            if config_dir.exists():
                shutil.copytree(
                    config_dir,
                    backup_path / "config",
                    dirs_exist_ok=True
                )

            # Copy finance data
            finance_dir = PROJECT_ROOT / "finance"
            if finance_dir.exists():
                shutil.copytree(
                    finance_dir,
                    backup_path / "finance",
                    dirs_exist_ok=True
                )

            print(f"✅ State backed up to: {backup_path}")

            self.state["backups_created"] += 1
            self.state["last_backup"] = datetime.now(timezone.utc).isoformat()
            self._save_state()

            return True

        except Exception as e:
            print(f"❌ State backup failed: {e}")
            return False

    def backup_critical_data(self) -> Dict[str, bool]:
        """Backup all critical data."""
        results = {
            "code": False,
            "state": False,
        }

        print("🔄 Starting full backup...")

        # Backup code
        results["code"] = self.backup_code_to_github()

        # Backup state
        results["state"] = self.backup_state_files()

        # Clean old backups (keep last 10)
        self.cleanup_old_backups(keep=10)

        return results

    def cleanup_old_backups(self, keep: int = 10):
        """Clean up old local backups, keeping only the most recent."""
        try:
            backups = sorted(
                BACKUP_DIR.glob("state_backup_*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            for old_backup in backups[keep:]:
                shutil.rmtree(old_backup)
                print(f"🗑️  Removed old backup: {old_backup.name}")

        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

    def setup_gitlab_mirror(self):
        """Set up GitLab as a mirror for redundancy."""
        print("📋 To set up GitLab mirror:")
        print("1. Create repo on GitLab")
        print("2. Run: git remote add gitlab <gitlab-url>")
        print("3. Run: git push gitlab main")
        print("4. Enable automatic mirroring")

    def setup_s3_backup(self):
        """Set up S3 backup."""
        print("📋 To set up S3 backup:")
        print("1. Create S3 bucket")
        print("2. Set AWS credentials in .env")
        print("3. Run: aws s3 sync state/ s3://bucket/state/")

    def verify_backups(self) -> Dict[str, bool]:
        """Verify all backup locations are accessible."""
        status = {}

        # Check local backups
        status["local"] = BACKUP_DIR.exists() and len(list(BACKUP_DIR.glob("*"))) > 0

        # Check GitHub
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                check=True
            )
            status["github"] = bool(result.stdout.strip())
        except:
            status["github"] = False

        # Check GitLab
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "gitlab"],
                cwd=PROJECT_ROOT,
                capture_output=True
            )
            status["gitlab"] = bool(result.stdout.strip())
        except:
            status["gitlab"] = False

        # Check S3
        status["s3"] = bool(os.environ.get("AWS_ACCESS_KEY_ID"))

        return status

    def display_status(self):
        """Display backup status."""
        print("=" * 80)
        print("💾 BACKUP MANAGER")
        print("=" * 80)
        print()

        print("📊 STATISTICS:")
        print("-" * 80)
        print(f"  Total Backups Created: {self.state['backups_created']}")
        print(f"  Last Backup: {self.state.get('last_backup', 'Never')}")
        print()

        print("📍 BACKUP LOCATIONS:")
        print("-" * 80)

        status = self.verify_backups()
        for location, enabled in status.items():
            icon = "✅" if enabled else "❌"
            priority = self.locations.get(location, {}).get("priority", "?")
            print(f"  {icon} {location.upper()} (Priority {priority})")

        print()

        # Show local backup count
        if BACKUP_DIR.exists():
            backup_count = len(list(BACKUP_DIR.glob("state_backup_*")))
            print(f"📦 Local Backups: {backup_count}")
            print()

        print("=" * 80)


def main():
    """Run backup manager."""
    print("Initializing Backup Manager...")
    print()

    manager = BackupManager()
    manager.display_status()

    print("🚀 Running full backup...")
    print()

    results = manager.backup_critical_data()

    print()
    print("📊 BACKUP RESULTS:")
    print("-" * 80)
    for component, success in results.items():
        icon = "✅" if success else "❌"
        print(f"  {icon} {component.upper()}: {'Success' if success else 'Failed'}")

    print()
    print("💡 To enable more backup locations:")
    print("-" * 80)
    print("  • GitLab mirror: manager.setup_gitlab_mirror()")
    print("  • S3 backup: manager.setup_s3_backup()")
    print()


if __name__ == "__main__":
    main()
