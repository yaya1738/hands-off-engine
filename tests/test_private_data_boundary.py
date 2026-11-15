"""Regression tests for the private-data boundary."""

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PATHS = (
    "security/yair_identity_profile.json",
    "security/yair_human_identity.json",
    "security/verification_audit.jsonl",
    "finance/yair_finance_hub.json",
    "state/doctor_meetings.jsonl",
    "termux-hands-off/agents/emergency_info.json",
    "termux-hands-off/agents/external_accounts.json",
    "termux-hands-off/agents/cards.json",
    "termux-hands-off/agent/balances_manual.yaml",
    "termux-hands-off/agent/balances_manual.yaml.bak",
    "termux-hands-off/agent/addresses_eth.yaml",
)


def test_personal_data_files_are_not_in_repository_tree():
    for relative_path in PRIVATE_PATHS:
        assert not (ROOT / relative_path).exists(), relative_path


def test_private_data_paths_are_ignored():
    ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for relative_path in PRIVATE_PATHS:
        assert relative_path in ignore_text, relative_path


def test_identity_verifier_has_no_embedded_human_constants():
    source = (ROOT / "security/absolute_identity.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "HUMAN_CONSTANTS" not in source
    assert "HUMAN_IDENTITY_PATH" not in source
    assert "Disabled: hard-coded personal challenge facts were removed." in source


def test_finance_refresh_fails_safely_without_private_hub():
    source = (ROOT / "finance/refresh_balances.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "if not FINANCE_HUB.exists():" in source
    assert "restore it from a secure local backup" in source

def test_identity_allowlists_are_not_hardcoded():
    for relative_path in ("security/identity_gate.py", "security/auto_identity.py"):
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(source)
        assert "HANDS_OFF_MASTER_DEVICES" in source
        assert "HANDS_OFF_MASTER_SSH_FINGERPRINTS" in source
        assert "HANDS_OFF_TRUSTED_IPS" in source
        assert not __import__("re").search(
            r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}", source, __import__("re").I
        )
        assert not __import__("re").search(
            r"\\b\\d{1,3}(?:\\.\\d{1,3}){3}\\b", source
        )
        assert not __import__("re").search(r"SHA256:[A-Za-z0-9+/=]{20,}", source)


def test_public_bootstrap_has_no_private_user_snapshot():
    import json

    bootstrap = json.loads(
        (ROOT / "ai/memory/kernels/system_bootstrap.json").read_text(encoding="utf-8")
    )
    assert bootstrap["identity"]["server_ip"] == ""
    assert bootstrap["financial_state"]["polymarket_balance"] is None
    assert bootstrap["financial_state"]["positions"] == []
    assert bootstrap["live_services"]["telegram_bot"]["chat_id"] == ""
    assert bootstrap["user_context"]["email"] == ""
    assert bootstrap["user_context"]["situation"].startswith("Private user context")
