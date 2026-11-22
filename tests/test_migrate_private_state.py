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



def test_private_finance_hub_is_migrated_out_of_repo_state_tree(tmp_path):
    source = tmp_path / "repo"
    destination = tmp_path / "private"
    old_hub = source / "state" / "private_finance_hub.json"
    old_hub.parent.mkdir(parents=True)
    old_hub.write_text('{"accounts":{},"status":"private"}', encoding="utf-8")

    result = migrate(source, destination)

    new_hub = destination / "finance" / "private_finance_hub.json"
    assert new_hub.read_text(encoding="utf-8") == old_hub.read_text(encoding="utf-8")
    assert old_hub.exists()
    assert result["files"][0]["destination"] == "finance/private_finance_hub.json"



def test_migration_preserves_recursive_finance_snapshots_and_security_archive(tmp_path):
    source = tmp_path / "repo"
    destination = tmp_path / "private"
    snapshot = source / "termux-hands-off" / "data" / "finances" / "snapshots" / "snapshot.json"
    state_env = source / "termux-hands-off" / "state" / "alerts.env"
    archive = source / "termux-hands-off" / "security_snapshot.tar"
    for path in (snapshot, state_env, archive):
        path.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text('{"net_worth":null}', encoding="utf-8")
    state_env.write_text("ALERTS_ENABLED=false\n", encoding="utf-8")
    archive.write_bytes(b"private-archive-placeholder")

    result = migrate(source, destination)

    assert (destination / "termux-hands-off" / "data" / "finances" / "snapshots" / "snapshot.json").exists()
    assert (destination / "termux-hands-off" / "state" / "alerts.env").exists()
    assert (destination / "backups" / "security_snapshot.tar").read_bytes() == archive.read_bytes()
    assert len(result["files"]) == 3


def test_legacy_runtime_recursive_finance_history_is_preserved(tmp_path):
    source = tmp_path / "repo"
    legacy = tmp_path / "hands-off"
    destination = tmp_path / "private"
    snapshot = legacy / "data" / "finances" / "snapshots" / "old.json"
    log = legacy / "logs" / "finance_balances.log"
    snapshot.parent.mkdir(parents=True)
    log.parent.mkdir(parents=True)
    snapshot.write_text('{"status":"historical"}', encoding="utf-8")
    log.write_text('{"usd_total":null}\n', encoding="utf-8")

    migrate(source, destination, legacy)

    assert (destination / "legacy_runtime" / "data" / "finances" / "snapshots" / "old.json").exists()
    assert (destination / "legacy_runtime" / "logs" / "finance_balances.log").exists()



def test_migration_preserves_local_polymarket_env_only_under_private_secrets(tmp_path):
    source = tmp_path / "repo"
    destination = tmp_path / "private"
    env_file = source / ".env.polymarket"
    env_file.write_text("POLYMARKET_PRIVATE_KEY=placeholder\n", encoding="utf-8")

    result = migrate(source, destination)

    private_copy = destination / "secrets" / ".env.polymarket"
    assert private_copy.read_text(encoding="utf-8") == env_file.read_text(encoding="utf-8")
    assert private_copy.stat().st_mode & 0o777 == 0o600
    assert result["files"][0]["destination"] == "secrets/.env.polymarket"


def test_migration_preserves_autopilot_admin_environment(tmp_path):
    source = tmp_path / "repo"
    destination = tmp_path / "private"
    admin_env = source / "termux-hands-off" / "autopilot" / "admin.env"
    admin_env.parent.mkdir(parents=True)
    admin_env.write_text("ADMIN_TOKEN=placeholder\n", encoding="utf-8")

    migrate(source, destination)

    private_copy = destination / "termux-hands-off" / "autopilot" / "admin.env"
    assert private_copy.read_text(encoding="utf-8") == admin_env.read_text(encoding="utf-8")



def test_migration_preserves_tracked_vault_and_local_secret_vault(tmp_path):
    source = tmp_path / "repo"
    secrets_root = tmp_path / "config"
    secrets = secrets_root / "hands-off"
    destination = tmp_path / "private"
    tracked_vault = source / "termux-hands-off" / "agent" / "vault.json"
    local_vault = secrets / "vault.json"
    tracked_vault.parent.mkdir(parents=True)
    secrets.mkdir(parents=True)
    tracked_vault.write_text('{"OKX_API_KEY":"tracked"}', encoding="utf-8")
    local_vault.write_text('{"OKX_API_KEY":"local"}', encoding="utf-8")

    result = migrate(source, destination, secrets_root=secrets_root)

    assert (destination / "secrets" / "termux-agent-vault.json").read_text(encoding="utf-8") == tracked_vault.read_text(encoding="utf-8")
    assert (destination / "secrets" / "vault.json").read_text(encoding="utf-8") == local_vault.read_text(encoding="utf-8")
    assert tracked_vault.exists() and local_vault.exists()
    assert len(result["files"]) == 2



def test_migration_preserves_keys_vault_and_rotated_backups(tmp_path):
    source = tmp_path / "repo"
    secrets_root = tmp_path / "config"
    destination = tmp_path / "private"
    current = secrets_root / "keys.vault"
    backup = secrets_root / "keys.vault.bak.123"
    secrets_root.mkdir(parents=True)
    current.write_text("KEY=private", encoding="utf-8")
    backup.write_text("KEY=historical", encoding="utf-8")

    migrate(source, destination, secrets_root=secrets_root)

    assert (destination / "secrets" / "keys.vault").read_text(encoding="utf-8") == "KEY=private"
    assert (destination / "secrets" / "keys.vault.bak.123").read_text(encoding="utf-8") == "KEY=historical"



def test_migration_preserves_legacy_cron_logs(tmp_path):
    source = tmp_path / "repo"
    cron_logs = tmp_path / ".cron-logs"
    destination = tmp_path / "private"
    log = cron_logs / "finance.log"
    cron_logs.mkdir(parents=True)
    log.write_text("historical finance log\n", encoding="utf-8")

    migrate(source, destination, cron_logs_root=cron_logs)

    preserved = destination / "logs" / "cron" / "finance.log"
    assert preserved.read_text(encoding="utf-8") == log.read_text(encoding="utf-8")
