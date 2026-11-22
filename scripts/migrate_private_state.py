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
    ".env.polymarket",
    "finance/dollar_access.json",
    "finance/yair_finance_hub.json",
    "termux-hands-off/agents/external_accounts.json",
    "termux-hands-off/agents/cards.json",
    "termux-hands-off/agents/emergency_info.json",
    "termux-hands-off/agents/finance_rules.json",
    "termux-hands-off/agent/vault.json",
    "termux-hands-off/agent/vault.json.bak",
    "termux-hands-off/security_snapshot.tar",
    "security/yair_identity_profile.json",
    "security/yair_human_identity.json",
    "security/verification_audit.jsonl",
    "security/identity_checks.jsonl",
    "state/private_finance_hub.json",
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

LEGACY_RUNTIME_PATHS = (
    "agents/external_accounts.json",
    "agents/cards.json",
    "agents/emergency_info.json",
    "agent/vault.json",
    "agent/vault.json.bak",
    "agents/finance_rules.json",
    "agents/perf_inputs.json",
    "logs/finance_balances.log",
    "logs/finance_credit.log",
    "logs/finance_pnl.log",
    "logs/finance_events.log",
    "logs/finance_errors.log",
    "logs/finance_alerts.log",
    "logs/guardrail_actions.log",
    "logs/rotate_today.json",
    "logs/finance_daily.csv",
    "logs/cards_status.json",
    "logs/cards_minpay.json",
    "logs/polymarket_positions.jsonl",
    "logs/polymarket_positions.csv",
    "logs/polymarket_pull.log",
    "logs/performance_daily.csv",
    "logs/pnl_ledger.json",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def private_root() -> Path:
    configured = os.environ.get("HANDS_OFF_PRIVATE_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".config" / "hands-off-engine"


def collect_sources(source_root: Path, legacy_runtime_root: Path | None = None, secrets_root: Path | None = None) -> list[tuple[Path, Path, str]]:
    candidates: dict[Path, tuple[Path, str]] = {}
    for relative in FIXED_RELATIVE_PATHS:
        source = source_root / relative
        if source.is_file():
            if relative == "state/private_finance_hub.json":
                destination_relative = Path("finance/private_finance_hub.json")
            elif relative == ".env.polymarket":
                destination_relative = Path("secrets/.env.polymarket")
            elif relative == "termux-hands-off/agent/vault.json":
                destination_relative = Path("secrets/termux-agent-vault.json")
            elif relative == "termux-hands-off/agent/vault.json.bak":
                destination_relative = Path("secrets/termux-agent-vault.json.bak")
            elif relative == "termux-hands-off/security_snapshot.tar":
                destination_relative = Path("backups/security_snapshot.tar")
            else:
                destination_relative = Path(relative)
            candidates[source] = (destination_relative, "repo")

    for state_dir in (source_root / "state", source_root / "termux-hands-off" / "state"):
        if state_dir.is_dir():
            for pattern in STATE_PATTERNS:
                for source in state_dir.glob(pattern):
                    if source.is_file():
                        relative = source.relative_to(source_root)
                        candidates[source] = (relative, "repo")

    # Preserve the complete historical finance snapshot tree, private logs,
    # and Termux runtime state (including env files and backup archives).
    for directory in (
        source_root / "termux-hands-off" / "state",
        source_root / "termux-hands-off" / "logs",
        source_root / "termux-hands-off" / "data" / "finances",
        source_root / "termux-hands-off" / "autopilot",
    ):
        if directory.is_dir():
            for source in directory.rglob("*"):
                if source.is_file():
                    relative = source.relative_to(source_root)
                    candidates[source] = (relative, "repo")

    if secrets_root is not None:
        secrets_root = secrets_root.expanduser().resolve()
        for relative_text in ("vault.json", "tg.env", "ifttt.env", "auto_sources.env"):
            source = secrets_root / relative_text
            if source.is_file():
                candidates[source] = (Path("secrets") / relative_text, "secrets_root")

    if legacy_runtime_root is not None:
        legacy_runtime_root = legacy_runtime_root.expanduser().resolve()
        if legacy_runtime_root.is_dir():
            for relative_text in LEGACY_RUNTIME_PATHS:
                source = legacy_runtime_root / relative_text
                if source.is_file():
                    candidates[source] = (Path("legacy_runtime") / relative_text, "legacy_runtime")
            for directory_text in ("state", "logs", "data/finances", "security", "finance", "autopilot"):
                directory = legacy_runtime_root / directory_text
                if directory.is_dir():
                    for source in directory.rglob("*"):
                        if source.is_file():
                            relative = Path("legacy_runtime") / source.relative_to(legacy_runtime_root)
                            candidates[source] = (relative, "legacy_runtime")
            env_file = legacy_runtime_root / ".env.polymarket"
            if env_file.is_file():
                candidates[env_file] = (Path("legacy_runtime/secrets/.env.polymarket"), "legacy_runtime")
            archive = legacy_runtime_root / "security_snapshot.tar"
            if archive.is_file():
                candidates[archive] = (Path("backups/security_snapshot-legacy.tar"), "legacy_runtime")

    return [(source, relative, label) for source, (relative, label) in sorted(
        candidates.items(), key=lambda item: str(item[1][0])
    )]

def copy_without_overwrite(source: Path, destination: Path) -> tuple[str, str, int]:
    data = source.read_bytes()
    digest = sha256_bytes(data)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        destination.parent.chmod(0o700)
    except OSError:
        pass

    try:
        fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        existing_digest = sha256_bytes(destination.read_bytes())
        if existing_digest == digest:
            return "already_preserved", digest, len(data)
        return "conflict_existing_destination", digest, len(data)

    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        destination.chmod(0o600)
    except Exception:
        try:
            destination.unlink()
        except OSError:
            pass
        raise
    return "copied", digest, len(data)


def migrate(source_root: Path, destination_root: Path, legacy_runtime_root: Path | None = None, secrets_root: Path | None = None) -> dict:
    source_root = source_root.expanduser().resolve()
    destination_root = destination_root.expanduser().resolve()
    destination_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        destination_root.chmod(0o700)
    except OSError:
        pass

    results = []
    for source, relative, source_label in collect_sources(source_root, legacy_runtime_root, secrets_root):
        destination = destination_root / relative
        status, digest, size = copy_without_overwrite(source, destination)
        results.append({
            "source": f"{source_label}:{source}",
            "destination": str(relative),
            "sha256": digest,
            "bytes": size,
            "status": status,
        })

    manifest = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source_root),
        "legacy_runtime_root": str(legacy_runtime_root.expanduser().resolve()) if legacy_runtime_root else None,
        "secrets_root": str(secrets_root.expanduser().resolve()) if secrets_root else None,
        "files": results,
    }
    manifest_path = destination_root / "migration_manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        merged = list(old.get("files", []))
        known = {(item.get("source"), item.get("sha256")) for item in merged}
        for item in results:
            identity = (item["source"], item["sha256"])
            if identity not in known:
                merged.append(item)
                known.add(identity)
        manifest["files"] = merged
        manifest_status = "updated"
    else:
        manifest_status = "written"

    encoded = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=".manifest-", dir=destination_root)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.chmod(0o600)
        os.replace(temp_path, manifest_path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
    manifest_path.chmod(0o600)
    return {**manifest, "files": results, "manifest_status": manifest_status}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--legacy-runtime-root", type=Path, default=Path.home() / "hands-off")
    parser.add_argument("--secrets-root", type=Path, default=Path.home() / ".config" / "hands-off")
    parser.add_argument("--destination", type=Path, default=private_root())
    args = parser.parse_args()

    result = migrate(args.source_root, args.destination, args.legacy_runtime_root, args.secrets_root)
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
