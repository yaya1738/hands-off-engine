#!/usr/bin/env python3
"""
Automatic backup and recovery manager.

Features:
- Continuous backups of state files
- Point-in-time recovery
- Cloud backup integration (S3, B2, rsync)
- Backup verification and testing
- Retention policies
- Disaster recovery procedures
"""

import os
import sys
import json
import time
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup"""
    backup_id: str
    timestamp: str
    files: List[str]
    total_size_bytes: int
    checksum: str
    backup_type: str  # "full", "incremental", "snapshot"
    location: str
    verified: bool = False


class BackupManager:
    """Manages backups and recovery"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.state_dir = Path(self.config["state_dir"])
        self.backup_dir = Path(self.config["backup_dir"])
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.backup_dir / "backup_metadata.jsonl"

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration"""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("config_load_failed", error=str(e))

        return {
            "state_dir": "/home/user/hands-off-engine/state",
            "backup_dir": "/home/user/hands-off-engine/backups",
            "backup_patterns": [
                "/home/user/hands-off-engine/state/*.json",
                "/home/user/hands-off-engine/termux-hands-off/state/*.json",
                "/home/user/hands-off-engine/executor/*.json",
                "/home/user/hands-off-engine/decider/*.json",
                "/home/user/hands-off-engine/alpha/*.json",
            ],
            "retention": {
                "hourly": {"count": 24, "keep_every": 3600},  # 24 hourly backups
                "daily": {"count": 30, "keep_every": 86400},   # 30 daily backups
                "weekly": {"count": 12, "keep_every": 604800}, # 12 weekly backups
                "monthly": {"count": 12, "keep_every": 2592000}, # 12 monthly backups
            },
            "cloud_backup": {
                "enabled": False,
                "provider": "s3",  # "s3", "b2", "rsync"
                "destination": "s3://my-bucket/hands-off-backups/",
                "encryption": True,
                "compress": True,
            },
            "verification": {
                "enabled": True,
                "verify_on_create": True,
                "random_restore_test": True,
                "test_frequency_hours": 24,
            },
            "max_backup_size_mb": 1000,
        }

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error("checksum_calculation_error", file=str(file_path), error=str(e))
            return ""

    def _get_files_to_backup(self) -> List[Path]:
        """Get list of files to backup"""
        files = []

        for pattern in self.config["backup_patterns"]:
            try:
                # Use glob to expand patterns
                pattern_path = Path(pattern)
                parent = pattern_path.parent
                glob_pattern = pattern_path.name

                for file_path in parent.glob(glob_pattern):
                    if file_path.is_file():
                        # Skip existing backups
                        if ".bak." not in str(file_path):
                            files.append(file_path)

            except Exception as e:
                logger.debug("pattern_expansion_error", pattern=pattern, error=str(e))

        return files

    def create_backup(self, backup_type: str = "snapshot") -> Optional[BackupMetadata]:
        """
        Create a new backup.

        Args:
            backup_type: "full", "incremental", or "snapshot"

        Returns:
            BackupMetadata object or None on failure
        """
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp = datetime.now().isoformat()

        logger.info(
            "backup_starting",
            backup_id=backup_id,
            backup_type=backup_type
        )

        # Get files to backup
        source_files = self._get_files_to_backup()

        if not source_files:
            logger.warning("no_files_to_backup")
            return None

        # Create backup directory for this backup
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        backed_up_files = []
        total_size = 0
        checksum_data = []

        # Copy files
        for source_file in source_files:
            try:
                # Calculate relative path
                rel_path = source_file.relative_to("/home/user/hands-off-engine")
                dest_file = backup_path / rel_path

                # Create parent directories
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(source_file, dest_file)

                # Track metadata
                size = dest_file.stat().st_size
                checksum = self._calculate_checksum(dest_file)

                backed_up_files.append(str(rel_path))
                total_size += size
                checksum_data.append(f"{rel_path}:{checksum}")

                logger.debug(
                    "file_backed_up",
                    file=str(rel_path),
                    size_bytes=size
                )

            except Exception as e:
                logger.error(
                    "file_backup_error",
                    file=str(source_file),
                    error=str(e),
                    error_type=type(e).__name__
                )

        if not backed_up_files:
            logger.error("backup_failed_no_files_copied")
            return None

        # Calculate overall checksum
        overall_checksum = hashlib.sha256(
            "\n".join(sorted(checksum_data)).encode()
        ).hexdigest()

        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=timestamp,
            files=backed_up_files,
            total_size_bytes=total_size,
            checksum=overall_checksum,
            backup_type=backup_type,
            location=str(backup_path),
            verified=False
        )

        # Save metadata to backup directory
        metadata_file = backup_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(asdict(metadata), f, indent=2)

        # Append to global metadata log
        with open(self.metadata_file, 'a') as f:
            f.write(json.dumps(asdict(metadata)) + "\n")

        logger.info(
            "backup_created",
            backup_id=backup_id,
            files_count=len(backed_up_files),
            total_size_mb=f"{total_size / (1024**2):.2f}",
            checksum=overall_checksum[:16]
        )

        # Verify if configured
        if self.config["verification"]["verify_on_create"]:
            metadata.verified = self.verify_backup(backup_id)

        # Upload to cloud if configured
        if self.config["cloud_backup"]["enabled"]:
            self._upload_to_cloud(backup_path)

        return metadata

    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity.

        Args:
            backup_id: ID of backup to verify

        Returns:
            True if backup is valid
        """
        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            logger.error("backup_not_found", backup_id=backup_id)
            return False

        # Load metadata
        metadata_file = backup_path / "metadata.json"

        if not metadata_file.exists():
            logger.error("metadata_not_found", backup_id=backup_id)
            return False

        try:
            with open(metadata_file) as f:
                metadata = json.load(f)

            # Recalculate checksums
            checksum_data = []

            for rel_path in metadata["files"]:
                file_path = backup_path / rel_path

                if not file_path.exists():
                    logger.error("backup_file_missing", file=rel_path)
                    return False

                checksum = self._calculate_checksum(file_path)
                checksum_data.append(f"{rel_path}:{checksum}")

            # Calculate overall checksum
            overall_checksum = hashlib.sha256(
                "\n".join(sorted(checksum_data)).encode()
            ).hexdigest()

            if overall_checksum != metadata["checksum"]:
                logger.error(
                    "backup_checksum_mismatch",
                    backup_id=backup_id,
                    expected=metadata["checksum"][:16],
                    actual=overall_checksum[:16]
                )
                return False

            logger.info(
                "backup_verified",
                backup_id=backup_id,
                files_count=len(metadata["files"])
            )

            return True

        except Exception as e:
            logger.error(
                "backup_verification_error",
                backup_id=backup_id,
                error=str(e),
                error_type=type(e).__name__
            )
            return False

    def restore_backup(
        self,
        backup_id: str,
        destination: Optional[str] = None,
        dry_run: bool = False
    ) -> bool:
        """
        Restore from backup.

        Args:
            backup_id: ID of backup to restore
            destination: Destination directory (defaults to original locations)
            dry_run: If True, don't actually restore, just log what would happen

        Returns:
            True if restore successful
        """
        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            logger.error("backup_not_found", backup_id=backup_id)
            return False

        # Load metadata
        metadata_file = backup_path / "metadata.json"

        if not metadata_file.exists():
            logger.error("metadata_not_found", backup_id=backup_id)
            return False

        try:
            with open(metadata_file) as f:
                metadata = json.load(f)

            logger.info(
                "restore_starting",
                backup_id=backup_id,
                files_count=len(metadata["files"]),
                dry_run=dry_run
            )

            # Verify backup first
            if not self.verify_backup(backup_id):
                logger.error("backup_verification_failed_refusing_restore", backup_id=backup_id)
                return False

            restored_count = 0

            for rel_path in metadata["files"]:
                source_file = backup_path / rel_path

                if destination:
                    dest_file = Path(destination) / rel_path
                else:
                    dest_file = Path("/home/user/hands-off-engine") / rel_path

                if dry_run:
                    logger.info("would_restore", source=str(source_file), dest=str(dest_file))
                    restored_count += 1
                else:
                    try:
                        # Create parent directories
                        dest_file.parent.mkdir(parents=True, exist_ok=True)

                        # Backup existing file if it exists
                        if dest_file.exists():
                            backup_name = f"{dest_file}.before_restore.{int(time.time())}"
                            shutil.copy2(dest_file, backup_name)
                            logger.info("existing_file_backed_up", file=str(dest_file), backup=backup_name)

                        # Restore file
                        shutil.copy2(source_file, dest_file)
                        restored_count += 1

                        logger.debug("file_restored", file=str(rel_path))

                    except Exception as e:
                        logger.error(
                            "file_restore_error",
                            file=str(rel_path),
                            error=str(e),
                            error_type=type(e).__name__
                        )

            success = restored_count == len(metadata["files"])

            logger.info(
                "restore_complete" if success else "restore_partial",
                backup_id=backup_id,
                restored=restored_count,
                total=len(metadata["files"]),
                dry_run=dry_run
            )

            return success

        except Exception as e:
            logger.error(
                "restore_error",
                backup_id=backup_id,
                error=str(e),
                error_type=type(e).__name__
            )
            return False

    def list_backups(self, limit: Optional[int] = None) -> List[BackupMetadata]:
        """
        List available backups.

        Args:
            limit: Maximum number of backups to return (most recent first)

        Returns:
            List of BackupMetadata objects
        """
        backups = []

        if not self.metadata_file.exists():
            return backups

        try:
            with open(self.metadata_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        backups.append(BackupMetadata(**data))

            # Sort by timestamp (most recent first)
            backups.sort(key=lambda b: b.timestamp, reverse=True)

            if limit:
                backups = backups[:limit]

            return backups

        except Exception as e:
            logger.error("list_backups_error", error=str(e))
            return []

    def cleanup_old_backups(self) -> int:
        """
        Clean up old backups according to retention policy.

        Returns:
            Number of backups deleted
        """
        retention = self.config["retention"]
        backups = self.list_backups()

        if not backups:
            return 0

        # Group backups by retention period
        now = datetime.now()
        keep_backups = set()

        for period_name, period_config in retention.items():
            count = period_config["count"]
            interval = period_config["keep_every"]

            kept = 0
            last_kept_time = None

            for backup in backups:
                backup_time = datetime.fromisoformat(backup.timestamp)
                age = (now - backup_time).total_seconds()

                # Check if this backup falls in this retention period
                if last_kept_time is None or (backup_time - last_kept_time).total_seconds() >= interval:
                    keep_backups.add(backup.backup_id)
                    last_kept_time = backup_time
                    kept += 1

                    if kept >= count:
                        break

        # Delete backups not in keep list
        deleted_count = 0

        for backup in backups:
            if backup.backup_id not in keep_backups:
                try:
                    backup_path = Path(backup.location)

                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                        deleted_count += 1

                        logger.info(
                            "backup_deleted",
                            backup_id=backup.backup_id,
                            age_days=(now - datetime.fromisoformat(backup.timestamp)).days
                        )

                except Exception as e:
                    logger.error(
                        "backup_deletion_error",
                        backup_id=backup.backup_id,
                        error=str(e)
                    )

        logger.info(
            "backup_cleanup_complete",
            deleted=deleted_count,
            kept=len(keep_backups),
            total=len(backups)
        )

        return deleted_count

    def _upload_to_cloud(self, backup_path: Path) -> bool:
        """Upload backup to cloud storage"""
        cloud_config = self.config["cloud_backup"]

        if not cloud_config["enabled"]:
            return False

        provider = cloud_config["provider"]
        destination = cloud_config["destination"]

        try:
            logger.info("cloud_upload_starting", provider=provider, path=str(backup_path))

            if provider == "s3":
                # Use AWS CLI
                cmd = [
                    "aws", "s3", "sync",
                    str(backup_path),
                    destination,
                    "--quiet"
                ]

                if cloud_config.get("encryption"):
                    cmd.extend(["--sse", "AES256"])

            elif provider == "b2":
                # Use B2 CLI
                cmd = [
                    "b2", "sync",
                    str(backup_path),
                    destination
                ]

            elif provider == "rsync":
                # Use rsync
                cmd = [
                    "rsync", "-az",
                    "--delete",
                    str(backup_path) + "/",
                    destination
                ]

            else:
                logger.error("unknown_cloud_provider", provider=provider)
                return False

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            if result.returncode == 0:
                logger.info("cloud_upload_complete", provider=provider)
                return True
            else:
                logger.error(
                    "cloud_upload_failed",
                    provider=provider,
                    returncode=result.returncode,
                    stderr=result.stderr[:200]
                )
                return False

        except Exception as e:
            logger.error(
                "cloud_upload_error",
                provider=provider,
                error=str(e),
                error_type=type(e).__name__
            )
            return False

    def get_backup_status(self) -> dict:
        """Get backup system status"""
        backups = self.list_backups()

        if not backups:
            return {
                "total_backups": 0,
                "latest_backup": None,
                "total_size_mb": 0,
                "status": "no_backups"
            }

        latest = backups[0]
        total_size = sum(b.total_size_bytes for b in backups)

        # Check age of latest backup
        latest_age = (datetime.now() - datetime.fromisoformat(latest.timestamp)).total_seconds()

        if latest_age > 7200:  # 2 hours
            status = "stale"
        elif latest_age > 3600:  # 1 hour
            status = "warning"
        else:
            status = "healthy"

        return {
            "total_backups": len(backups),
            "latest_backup": {
                "backup_id": latest.backup_id,
                "timestamp": latest.timestamp,
                "age_minutes": int(latest_age / 60),
                "files_count": len(latest.files),
                "size_mb": f"{latest.total_size_bytes / (1024**2):.2f}",
                "verified": latest.verified
            },
            "total_size_mb": f"{total_size / (1024**2):.2f}",
            "status": status,
            "cloud_enabled": self.config["cloud_backup"]["enabled"]
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Backup manager")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--create", action="store_true", help="Create new backup")
    parser.add_argument("--list", action="store_true", help="List backups")
    parser.add_argument("--verify", help="Verify specific backup")
    parser.add_argument("--restore", help="Restore specific backup")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (for restore)")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old backups")
    parser.add_argument("--status", action="store_true", help="Show backup status")

    args = parser.parse_args()

    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ]
    )

    manager = BackupManager(config_path=args.config)

    if args.create:
        metadata = manager.create_backup()
        if metadata:
            print(json.dumps(asdict(metadata), indent=2))
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.list:
        backups = manager.list_backups()
        for backup in backups:
            print(f"{backup.backup_id} - {backup.timestamp} - {len(backup.files)} files - {backup.total_size_bytes / (1024**2):.2f} MB")
        sys.exit(0)

    elif args.verify:
        success = manager.verify_backup(args.verify)
        sys.exit(0 if success else 1)

    elif args.restore:
        success = manager.restore_backup(args.restore, dry_run=args.dry_run)
        sys.exit(0 if success else 1)

    elif args.cleanup:
        deleted = manager.cleanup_old_backups()
        print(f"Deleted {deleted} old backups")
        sys.exit(0)

    elif args.status:
        status = manager.get_backup_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
