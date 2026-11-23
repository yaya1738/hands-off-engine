"""Private-state resolver never falls back to public or plaintext legacy paths."""

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path("termux-hands-off/agents/private_state.py")


def load_private_state(tmp_path, monkeypatch):
    root = tmp_path / "private"
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(root))
    spec = importlib.util.spec_from_file_location("private_state_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


def test_resolver_prefers_migrated_legacy_runtime_file(tmp_path, monkeypatch):
    module, root = load_private_state(tmp_path, monkeypatch)
    legacy = root / "legacy_runtime" / "agents" / "external_accounts.json"
    repo_copy = root / "termux-hands-off" / "agents" / "external_accounts.json"
    legacy.parent.mkdir(parents=True)
    repo_copy.parent.mkdir(parents=True)
    legacy.write_text('{"source":"runtime"}', encoding="utf-8")
    repo_copy.write_text('{"source":"repo"}', encoding="utf-8")

    assert module.private_path("agents/external_accounts.json") == legacy


def test_resolver_uses_migrated_repo_copy_when_legacy_is_absent(tmp_path, monkeypatch):
    module, root = load_private_state(tmp_path, monkeypatch)
    repo_copy = root / "termux-hands-off" / "agents" / "external_accounts.json"
    repo_copy.parent.mkdir(parents=True)
    repo_copy.write_text("{}", encoding="utf-8")

    assert module.private_path("agents/external_accounts.json") == repo_copy


def test_missing_path_resolves_only_under_private_runtime_root(tmp_path, monkeypatch):
    module, root = load_private_state(tmp_path, monkeypatch)

    path = module.private_path("agents/external_accounts.json")

    assert path == root / "legacy_runtime" / "agents" / "external_accounts.json"
    assert "hands-off/agents" not in str(path)


def test_create_parent_restricts_private_directory(tmp_path, monkeypatch):
    module, root = load_private_state(tmp_path, monkeypatch)

    path = module.private_path("logs/finance_balances.log", create_parent=True)

    assert path.parent.exists()
    assert root.stat().st_mode & 0o777 == 0o700
    assert path.parent.stat().st_mode & 0o777 == 0o700


def test_path_traversal_is_rejected(tmp_path, monkeypatch):
    module, _ = load_private_state(tmp_path, monkeypatch)

    with pytest.raises(ValueError):
        module.private_path("../outside.json")
