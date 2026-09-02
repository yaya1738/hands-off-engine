#!/usr/bin/env python3
"""
Legacy Backup Manager compatibility facade.

Backup creation, repository pushes, deletion/cleanup, and state persistence are
privileged operations owned by FactoryAuthorityGateway. This module retains
read-only status compatibility and fails closed for mutation entrypoints.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
BACKUP_DIR = PROJECT_ROOT / "backups"


_AUTHORITY = "FactoryAuthorityGateway"


class BackupManager:
    """Read-only compatibility facade for the legacy backup manager."""

    def __init__(self):
        self.state_file = STATE_DIR / "backup_manager.json"
        self.state = self._load_state()
        self.locations = {
            "local": {"path": BACKUP_DIR, "enabled": True, "priority": 1},
            "github": {"remote": "origin", "branch": "local-sync", "enabled": True, "priority": 2},
            "gitlab": {"remote": "gitlab", "branch": "main", "enabled": False, "priority": 3},
            "s3": {"bucket": "hands-off-engine-backups", "enabled": False, "priority": 4},
        }

    def _load_state(self) -> Dict:
        """Read existing backup metadata without creating or modifying files."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backups_created": 0,
            "last_backup": None,
            "backup_locations": [],
            "total_size": 0,
        }

    def _disabled(self, operation: str) -> bool:
        print(
            f"[FACTORY-AUTHORITY] legacy backup operation '{operation}' is disabled; "
            f"submit through {_AUTHORITY}."
        )
        return False

    def _save_state(self):
        """Legacy persistence is intentionally disabled."""
        return self._disabled("save_state")

    def backup_code_to_github(self) -> bool:
        return self._disabled("backup_code_to_github")

    def backup_state_files(self) -> bool:
        return self._disabled("backup_state_files")

    def backup_critical_data(self) -> Dict[str, bool]:
        self._disabled("backup_critical_data")
        return {"code": False, "state": False}

    def cleanup_old_backups(self, keep: int = 10):
        self._disabled("cleanup_old_backups")
        return []

    def setup_gitlab_mirror(self):
        return self._disabled("setup_gitlab_mirror")

    def setup_s3_backup(self):
        return self._disabled("setup_s3_backup")

    def verify_backups(self) -> Dict[str, bool]:
        """Return read-only local status; remote verification needs authority."""
        local_ok = BACKUP_DIR.exists() and any(BACKUP_DIR.iterdir())
        return {
            "local": local_ok,
            "github": False,
            "gitlab": False,
            "s3": False,
            "authority_required": True,
        }

    def display_status(self):
        """Display non-authoritative backup metadata."""
        print("=" * 80)
        print("💾 BACKUP MANAGER (READ-ONLY)")
        print("=" * 80)
        print(f"  Total Backups Created: {self.state.get('backups_created', 0)}")
        print(f"  Last Backup: {self.state.get('last_backup', 'Never')}")
        print(f"  Authority: {_AUTHORITY}")
        print("=" * 80)


def main():
    """Show status only; never perform a backup from the legacy entrypoint."""
    manager = BackupManager()
    manager.display_status()
    manager.backup_critical_data()


if __name__ == "__main__":
    main()
