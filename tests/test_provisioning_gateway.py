from infra.provisioning_gateway import request_provision


def test_provisioning_gateway_is_audit_only(tmp_path, monkeypatch):
    audit_file = tmp_path / "provisioning_events.jsonl"
    monkeypatch.setattr("infra.provisioning_gateway.AUDIT_FILE", audit_file)

    event = request_provision(
        "test",
        "create_droplet",
        cost_usd=10,
        capital_context={"capital_available_usd": 0},
    )

    assert event["decision"] == "AUDIT_ONLY"
    assert event["approval_status"] == "AUDIT_ONLY"
    assert event["execution_enabled"] is False
    assert event["executor"] is None
    assert audit_file.exists()
    assert audit_file.read_text(encoding="utf-8").strip()
