"""Non-destructive migration tests for private finance and identity state."""

import json
import os
from pathlib import Path

from scripts.migrate_private_state import migrate


def test_migration_copies_private_records_without_modifying_sources(tmp_path):
    source = tmp_path / "repo"
    destination = tmp_path / "private"
    record = source / "finance" / "dollar_access.json"
    record.parent.mkdir(parents=True)
    original = b'{"status":"private"}'
    record.write_bytes(original)

    result = migrate(source, destination)

    copied = destination / "finance" / "dollar_access.json"
    assert copied.read_bytes() == original
    assert record.read_bytes() == original
    assert result["files"][0]["status"] == "copied"
    assert result["manifest_status"] == "written"
    assert (destination / "migration_manifest.json").exists()


def test_migration_is_idempotent_and_does_not_overwrite(tmp_path):
    source = tmp_path / "repo"
    destination = tmp_path / "private"
    record = source / "security" / "yair_identity_profile.json"
    record.parent.mkdir(parents=True)
    record.write_text('{"version":1}', encoding="utf-8")

    first = migrate(source, destination)
    second = migrate(source, destination)

    assert first["files"][0]["status"] == "copied"
    assert second["files"][0]["status"] == "already_preserved"
    assert second["manifest_status"] == "updated"
    assert json.loads((destination / "migration_manifest.json").read_text())["files"]


def test_migration_reports_conflict_without_overwriting_private_copy(tmp_path):
    source = tmp_path / "repo"
    destination = tmp_path / "private"
    record = source / "termux-hands-off" / "agents" / "external_accounts.json"
    record.parent.mkdir(parents=True)
    record.write_text('{"balance":"old"}', encoding="utf-8")
    target = destination / "termux-hands-off" / "agents" / "external_accounts.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"balance":"newer-private-copy"}', encoding="utf-8")

    result = migrate(source, destination)

    assert result["files"][0]["status"] == "conflict_existing_destination"
    assert target.read_text(encoding="utf-8") == '{"balance":"newer-private-copy"}'


def test_private_destination_permissions_are_restricted_on_posix(tmp_path):
    if os.name != "posix":
        return
    source = tmp_path / "repo"
    destination = tmp_path / "private"
    record = source / "finance" / "yair_finance_hub.json"
    record.parent.mkdir(parents=True)
    record.write_text('{"summary":null}', encoding="utf-8")

    migrate(source, destination)

    assert destination.stat().st_mode & 0o777 == 0o700
    assert (destination / "finance" / "yair_finance_hub.json").stat().st_mode & 0o777 == 0o600
    assert (destination / "migration_manifest.json").stat().st_mode & 0o777 == 0o600


def test_migration_does_not_create_or_copy_missing_files(tmp_path):
    source = tmp_path / "empty-repo"
    destination = tmp_path / "private"

    result = migrate(source, destination)

    assert result["files"] == []
    assert result["manifest_status"] == "written"



def test_migration_also_preserves_legacy_hands_off_runtime_paths(tmp_path):
    source = tmp_path / "repo"
    legacy = tmp_path / "hands-off"
    destination = tmp_path / "private"
    record = legacy / "agents" / "external_accounts.json"
    record.parent.mkdir(parents=True)
    record.write_text('{"account":"private"}', encoding="utf-8")

    result = migrate(source, destination, legacy)

    copied = destination / "legacy_runtime" / "agents" / "external_accounts.json"
    assert copied.read_text(encoding="utf-8") == '{"account":"private"}'
    assert result["files"][0]["source"].startswith("legacy_runtime:")
    assert result["files"][0]["status"] == "copied"
