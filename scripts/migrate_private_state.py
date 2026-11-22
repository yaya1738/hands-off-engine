#!/usr/bin/env python3
"""Copy tracked/local financial and identity records into private local storage.

This is a preservation-only operation: it never deletes or modifies source files,
never overwrites an existing destination, and reports conflicts for manual review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


FIXED_RELATIVE_PATHS = (
    "finance/dollar_access.json",
    "finance/yair_finance_hub.json",
    "termux-hands-off/agents/external_accounts.json",
    "security/yair_identity_profile.json",
    "security/yair_human_identity.json",
    "security/verification_audit.jsonl",
    "state/optimal_trigger_config.json",
    "state/filler_actions.jsonl",
)

STATE_PATTERNS = (
    "finance*.json",
    "pnl*.json",
    "crypto_holdings.json",
    "fiat_accounts.json",
    "pnl_ledger.json",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def private_root() -> Path:
    configured = os.environ.get("HANDS_OFF_PRIVATE_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".config" / "hands-off-engine"


def collect_sources(source_root: Path) -> list[Path]:
    candidates = {source_root / rel for rel in FIXED_RELATIVE_PATHS}
    state_dir = source_root / "termux-hands-off" / "state"
    if state_dir.is_dir():
        for pattern in STATE_PATTERNS:
            candidates.update(state_dir.glob(pattern))
    return sorted(path for path in candidates if path.is_file())


def copy_without_overwrite(source: Path, destination: Path) -> tuple[str, str, int]:
    data = source.read_bytes()
    digest = sha256_bytes(data)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        destination.parent.chmod(0o700)
    except OSError:
        pass

    if destination.exists():
        existing_digest = sha256_bytes(destination.read_bytes())
        if existing_digest == digest:
            return "already_preserved", digest, len(data)
        return "conflict_existing_destination", digest, len(data)

    fd, temp_name = tempfile.mkstemp(prefix=".private-state-", dir=destination.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.chmod(0o600)
        try:
            os.link(temp_path, destination)
            status = "copied"
        except FileExistsError:
            existing_digest = sha256_bytes(destination.read_bytes())
            status = "already_preserved" if existing_digest == digest else "conflict_existing_destination"
        return status, digest, len(data)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def migrate(source_root: Path, destination_root: Path) -> dict:
    source_root = source_root.expanduser().resolve()
    destination_root = destination_root.expanduser().resolve()
    destination_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        destination_root.chmod(0o700)
    except OSError:
        pass

    results = []
    for source in collect_sources(source_root):
        relative = source.relative_to(source_root)
        destination = destination_root / relative
        status, digest, size = copy_without_overwrite(source, destination)
        results.append({
            "source": str(relative),
            "destination": str(relative),
            "sha256": digest,
            "bytes": size,
            "status": status,
        })

    manifest = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source_root),
        "files": results,
    }
    manifest_path = destination_root / "migration_manifest.json"
    encoded = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        old_files = {(item["source"], item["sha256"]) for item in old.get("files", [])}
        new_files = {(item["source"], item["sha256"]) for item in results}
        if not new_files.issubset(old_files):
            return {**manifest, "manifest_status": "conflict_existing_manifest"}
        manifest_status = "already_preserved"
    else:
        fd, temp_name = tempfile.mkstemp(prefix=".manifest-", dir=destination_root)
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            temp_path.chmod(0o600)
            try:
                os.link(temp_path, manifest_path)
                manifest_status = "written"
            except FileExistsError:
                manifest_status = "conflict_existing_manifest"
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    manifest_path.chmod(0o600) if manifest_path.exists() else None
    return {**manifest, "manifest_status": manifest_status}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--destination", type=Path, default=private_root())
    args = parser.parse_args()

    result = migrate(args.source_root, args.destination)
    copied = sum(item["status"] == "copied" for item in result["files"])
    preserved = sum(item["status"] == "already_preserved" for item in result["files"])
    conflicts = sum(item["status"] == "conflict_existing_destination" for item in result["files"])
    print(f"Private-state preservation: copied={copied}, already_preserved={preserved}, conflicts={conflicts}")
    print(f"Manifest: {result['manifest_status']}")
    for item in result["files"]:
        print(f"{item['status']}: {item['source']} ({item['bytes']} bytes)")
    if conflicts or result["manifest_status"] == "conflict_existing_manifest":
        return 2
    print("Source files were not deleted or modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
