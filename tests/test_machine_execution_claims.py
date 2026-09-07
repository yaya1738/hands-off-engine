from integrafix.machine_communication_integration import MachineIntegration


def test_trade_command_never_claims_execution_without_verified_side_effect(monkeypatch):
    integration = object.__new__(MachineIntegration)

    class DeniedAuthority:
        def submit(self, intent):
            return {"executed": False, "verified": False, "reason": "missing_token_id"}

    import ai.factory.live_order_authority as authority_module
    monkeypatch.setattr(authority_module, "LiveOrderAuthority", DeniedAuthority)

    result = integration._cmd_execute_trade({
        "market": "test",
        "direction": "YES",
        "size": 1,
    })

    assert result["success"] is False
    assert result["executed"] is False
    assert result["verified"] is False


def test_trade_command_reports_failure_on_authority_error(monkeypatch):
    integration = object.__new__(MachineIntegration)

    class BrokenAuthority:
        def submit(self, intent):
            raise RuntimeError("authority unavailable")

    import ai.factory.live_order_authority as authority_module
    monkeypatch.setattr(authority_module, "LiveOrderAuthority", BrokenAuthority)

    result = integration._cmd_execute_trade({"market": "test", "direction": "YES", "size": 1})

    assert result["success"] is False
    assert result["executed"] is False
    assert result["verified"] is False
    assert result["reason"] == "governed_execution_error"
