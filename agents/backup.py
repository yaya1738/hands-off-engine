"""
Backup System for Hands-Off Engine

Manages backups of critical state files:
- Daily backups to state/backups/YYYY-MM-DD/
- Keeps 7 days of backups
- Verifies backup integrity
- Provides restoration capabilities
"""

import json
import os
import shutil
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit.audit_logger import AuditLogger
from agents.alerts import get_alert_system, AlertLevel


class BackupSystem:
    """Manages backups of critical state files"""
    
    def __init__(
        self,
        state_dir: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        retention_days: int = 7
    ):
        """
        Initialize backup system
        
        Args:
            state_dir: Directory containing state files (defaults to ./state)
            backup_dir: Directory for backups (defaults to ./state/backups)
            retention_days: Number of days to keep backups
        """
        repo_root = Path(__file__).parent.parent
        self.state_dir = state_dir or (repo_root / "state")
        self.backup_dir = backup_dir or (self.state_dir / "backups")
        self.retention_days = retention_days
        
        self.audit_logger = AuditLogger(component="backup")
        self.alerts = get_alert_system()
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to backup (relative to state_dir)
        self.backup_files = [
            "polymarket-model.json",
            "knowledge.json",
            "approval_queue.json",
            "autonomous_task_queue.json",
            "autonomous_tasks_completed.jsonl",
            "self_healing_state.json",
            "optimization_log.json",
            "performance_metrics.jsonl"
        ]
    
    def create_daily_backup(self) -> bool:
        """
        Create daily backup of all state files
        
        Returns:
            True if backup was successful
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_backup_dir = self.backup_dir / today
        
        # Skip if backup already exists for today
        if today_backup_dir.exists():
            self.audit_logger.log(
                event_type="backup_skipped",
                event_data={"reason": "backup_already_exists", "date": today}
            )
            return True
        
        # Create backup directory
        today_backup_dir.mkdir(parents=True, exist_ok=True)
        
        backed_up_files = []
        failed_files = []
        
        # Backup each file
        for filename in self.backup_files:
            source_path = self.state_dir / filename
            
            if not source_path.exists():
                continue
            
            try:
                dest_path = today_backup_dir / filename
                
                # Copy file
                shutil.copy2(source_path, dest_path)
                
                # Verify integrity
                if self._verify_file_integrity(source_path, dest_path):
                    backed_up_files.append(filename)
                else:
                    failed_files.append(filename)
                    dest_path.unlink()  # Remove corrupted backup
                    
            except Exception as e:
                failed_files.append(filename)
                self.audit_logger.log(
                    event_type=AuditLogger.EVENT_ERROR,
                    event_data={
                        "error": "backup_failed",
                        "file": filename,
                        "exception": str(e)
                    }
                )
        
        # Create backup manifest
        manifest = {
            "date": today,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "files": backed_up_files,
            "failed": failed_files,
            "total_files": len(backed_up_files)
        }
        
        manifest_path = today_backup_dir / "_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Log audit event
        self.audit_logger.log(
            event_type="backup_created",
            event_data=manifest
        )
        
        # Send alert if failures
        if failed_files:
            self.alerts.send_alert(
                f"Backup completed with {len(failed_files)} failures",
                level=AlertLevel.WARNING,
                context={"failed_files": failed_files}
            )
        
        return len(failed_files) == 0
    
    def restore_from_backup(self, filename: str, date: Optional[str] = None) -> bool:
        """
        Restore a file from backup
        
        Args:
            filename: Name of file to restore
            date: Date of backup (YYYY-MM-DD format). If None, uses most recent.
            
        Returns:
            True if restoration was successful
        """
        # Find backup
        if date:
            backup_dir = self.backup_dir / date
            if not backup_dir.exists():
                self.audit_logger.log(
                    event_type=AuditLogger.EVENT_ERROR,
                    event_data={"error": "backup_not_found", "date": date}
                )
                return False
        else:
            # Find most recent backup with this file
            backup_dir = self._find_latest_backup_with_file(filename)
            if not backup_dir:
                self.audit_logger.log(
                    event_type=AuditLogger.EVENT_ERROR,
                    event_data={"error": "no_backup_found", "file": filename}
                )
                return False
        
        source_path = backup_dir / filename
        dest_path = self.state_dir / filename
        
        try:
            # Create backup of current file before overwriting
            if dest_path.exists():
                backup_current = dest_path.with_suffix('.bak')
                shutil.copy2(dest_path, backup_current)
            
            # Restore from backup
            shutil.copy2(source_path, dest_path)
            
            # Verify restoration
            if not self._verify_file_integrity(source_path, dest_path):
                # Restore from backup of current if verification fails
                if backup_current.exists():
                    shutil.copy2(backup_current, dest_path)
                raise Exception("Integrity verification failed")
            
            # Log success
            self.audit_logger.log(
                event_type="backup_restored",
                event_data={
                    "file": filename,
                    "backup_date": backup_dir.name
                }
            )
            
            self.alerts.alert_self_healing_action(
                "restore_from_backup",
                filename,
                success=True
            )
            
            return True
            
        except Exception as e:
            self.audit_logger.log(
                event_type=AuditLogger.EVENT_ERROR,
                event_data={
                    "error": "restore_failed",
                    "file": filename,
                    "exception": str(e)
                }
            )
            
            self.alerts.alert_self_healing_action(
                "restore_from_backup",
                filename,
                success=False
            )
            
            return False
    
    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention_days
        
        Returns:
            Number of backups removed
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        removed_count = 0
        
        for backup_dir in self.backup_dir.iterdir():
            if not backup_dir.is_dir():
                continue
            
            try:
                backup_date = datetime.strptime(backup_dir.name, "%Y-%m-%d")
                backup_date = backup_date.replace(tzinfo=timezone.utc)
                
                if backup_date < cutoff_date:
                    shutil.rmtree(backup_dir)
                    removed_count += 1
                    
                    self.audit_logger.log(
                        event_type="backup_removed",
                        event_data={"date": backup_dir.name}
                    )
                    
            except ValueError:
                # Not a valid date directory, skip
                continue
        
        return removed_count
    
    def verify_backup_integrity(self, date: str) -> Dict[str, bool]:
        """
        Verify integrity of all files in a backup
        
        Args:
            date: Backup date (YYYY-MM-DD format)
            
        Returns:
            Dictionary mapping filenames to integrity check results
        """
        backup_dir = self.backup_dir / date
        if not backup_dir.exists():
            return {}
        
        manifest_path = backup_dir / "_manifest.json"
        if not manifest_path.exists():
            return {}
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        results = {}
        for filename in manifest.get("files", []):
            backup_file = backup_dir / filename
            if backup_file.exists():
                results[filename] = self._verify_json_integrity(backup_file)
            else:
                results[filename] = False
        
        return results
    
    def _verify_file_integrity(self, source: Path, dest: Path) -> bool:
        """Verify file was copied correctly"""
        if not dest.exists():
            return False
        
        # Compare file sizes
        if source.stat().st_size != dest.stat().st_size:
            return False
        
        # Compare checksums
        source_hash = self._calculate_checksum(source)
        dest_hash = self._calculate_checksum(dest)
        
        return source_hash == dest_hash
    
    def _verify_json_integrity(self, file_path: Path) -> bool:
        """Verify JSON file is valid"""
        try:
            with open(file_path) as f:
                json.load(f)
            return True
        except:
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _find_latest_backup_with_file(self, filename: str) -> Optional[Path]:
        """Find most recent backup containing the specified file"""
        backup_dirs = sorted(
            [d for d in self.backup_dir.iterdir() if d.is_dir()],
            reverse=True
        )
        
        for backup_dir in backup_dirs:
            if (backup_dir / filename).exists():
                return backup_dir
        
        return None


if __name__ == "__main__":
    # Simple test
    backup = BackupSystem()
    print(f"Backup directory: {backup.backup_dir}")
    
    # Create backup
    success = backup.create_daily_backup()
    print(f"Backup created: {success}")
    
    # Cleanup old backups
    removed = backup.cleanup_old_backups()
    print(f"Old backups removed: {removed}")
