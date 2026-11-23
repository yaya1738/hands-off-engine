import importlib
from types import SimpleNamespace


def test_auto_identity_does_not_trust_root_host_or_agent_presence(monkeypatch, tmp_path):
    monkeypatch.delenv("HANDS_OFF_OWNER_SSH_KEY_FINGERPRINTS", raising=False)
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(tmp_path))
    monkeypatch.setenv("SSH_AUTH_SOCK", "/tmp/fake-agent.sock")

    import security.auto_identity as auto_identity
    importlib.reload(auto_identity)

    monkeypatch.setattr(auto_identity, "get_ssh_key_comment", lambda: None)
    monkeypatch.setattr(auto_identity, "get_ssh_client_ip", lambda: None)
    monkeypatch.setattr(auto_identity, "log_identity_check", lambda result: None)
    monkeypatch.setattr(auto_identity.os, "getuid", lambda: 0)
    monkeypatch.setattr(auto_identity.os, "uname", lambda: SimpleNamespace(nodename="handsoff-test"))

    result = auto_identity.is_yair()

    assert result["is_master"] is False
    assert result["confidence"] == 0.0
    assert result["identity"] == "Unknown"


def test_identity_gate_requires_configured_fingerprint_and_optional_device(monkeypatch, tmp_path):
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(tmp_path))
    monkeypatch.delenv("HANDS_OFF_OWNER_SSH_KEY_FINGERPRINTS", raising=False)
    monkeypatch.delenv("HANDS_OFF_OWNER_DEVICE_IDS", raising=False)

    import security.identity_gate as identity_gate
    importlib.reload(identity_gate)

    assert identity_gate.is_master(device_id="device-A") is False

    monkeypatch.setenv("HANDS_OFF_OWNER_SSH_KEY_FINGERPRINTS", "SHA256:test-fingerprint")
    monkeypatch.setenv("HANDS_OFF_OWNER_DEVICE_IDS", "device-A")
    importlib.reload(identity_gate)

    assert identity_gate.is_master(ssh_key_comment="SHA256:test-fingerprint", device_id="device-A") is True
    assert identity_gate.is_master(ssh_key_comment="SHA256:test-fingerprint", device_id="device-B") is False
    assert identity_gate.is_master(device_id="device-A") is False


def test_absolute_identity_denies_when_private_profile_is_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(tmp_path))
    monkeypatch.delenv("HANDS_OFF_IDENTITY_PROFILE", raising=False)

    import security.absolute_identity as absolute_identity
    importlib.reload(absolute_identity)

    verifier = absolute_identity.AbsoluteIdentity()
    result = verifier.full_verification()

    assert result["verified"] is False
    assert result["confidence"] == 0.0
    assert result["verdict"] == "UNVERIFIED"
