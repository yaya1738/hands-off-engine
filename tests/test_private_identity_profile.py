"""Identity verification must not depend on public source-code personal facts."""

import importlib.util
import json
import os
from pathlib import Path


IDENTITY_PATH = Path("security/absolute_identity.py")


def load_identity(tmp_path, monkeypatch):
    private_dir = tmp_path / "private"
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(private_dir))
    spec = importlib.util.spec_from_file_location("private_identity_test", IDENTITY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, private_dir


def test_missing_private_profile_fails_closed_and_logs_privately(tmp_path, monkeypatch):
    module, private_dir = load_identity(tmp_path, monkeypatch)

    verifier = module.AbsoluteIdentity()
    result = verifier.full_verification()

    assert result["verified"] is False
    assert result["confidence"] == 0.0
    assert result["verdict"] == "UNVERIFIED"
    assert result["signals"] == ["PROFILE:missing_or_invalid"]
    assert (private_dir / "security" / "verification_audit.jsonl").exists()


def test_malformed_private_profile_fails_closed(tmp_path, monkeypatch):
    module, private_dir = load_identity(tmp_path, monkeypatch)
    (private_dir / "security").mkdir(parents=True)
    (private_dir / "security" / "yair_identity_profile.json").write_text("{not-json", encoding="utf-8")

    verifier = module.AbsoluteIdentity()
    assert verifier.profile == {}
    assert verifier.full_verification()["verified"] is False


def test_human_challenge_layer_has_no_embedded_answer_fallback(tmp_path, monkeypatch):
    module, _ = load_identity(tmp_path, monkeypatch)
    verifier = module.AbsoluteIdentity()

    assert verifier.verify_human_identity({"untrusted_input": "anything"}) == 0.0
    assert "HUMAN:private_challenge_not_configured" in verifier.signals


def test_identity_paths_default_to_private_config_directory(tmp_path, monkeypatch):
    module, private_dir = load_identity(tmp_path, monkeypatch)

    assert module.PROFILE_PATH == private_dir / "yair_identity_profile.json"
    assert module.VERIFICATION_LOG == private_dir / "verification_audit.jsonl"


def test_audit_log_is_created_with_owner_only_permissions(tmp_path, monkeypatch):
    if os.name != "posix":
        return
    module, private_dir = load_identity(tmp_path, monkeypatch)
    result = module.AbsoluteIdentity().full_verification()

    log = private_dir / "verification_audit.jsonl"
    assert result["verified"] is False
    assert log.stat().st_mode & 0o777 == 0o600
    assert private_dir.stat().st_mode & 0o777 == 0o700
    record = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert record["verdict"] == "UNVERIFIED"
