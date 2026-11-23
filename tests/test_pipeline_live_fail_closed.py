from types import SimpleNamespace

from executor import ho_executor_plan
from executor import trading_safeguards
from scripts import run_pipeline


def test_live_executor_blocks_unimplemented_broker_backend(monkeypatch):
    monkeypatch.setattr(
        ho_executor_plan,
        "get_audit_logger",
        lambda component: SimpleNamespace(log_action=lambda **kwargs: None),
    )
    executor = ho_executor_plan.Executor(dryrun=False)
    action = SimpleNamespace(
        market_id="market-1",
        market_name="Regression test market",
        confidence=0.95,
        amount=5.0,
        side="YES",
        reasoning="test only",
    )

    result = executor.execute_actions([action])[0]

    assert result.success is False
    assert result.executed_amount == 0.0
    assert "no order was placed" in result.message


def test_dryrun_executor_remains_simulated_success(monkeypatch):
    monkeypatch.setattr(
        ho_executor_plan,
        "get_audit_logger",
        lambda component: SimpleNamespace(log_action=lambda **kwargs: None),
    )
    executor = ho_executor_plan.Executor(dryrun=True)
    action = SimpleNamespace(
        market_id="market-1",
        market_name="Regression test market",
        confidence=0.95,
        amount=5.0,
        side="YES",
        reasoning="test only",
    )

    result = executor.execute_actions([action])[0]

    assert result.success is True
    assert result.executed_amount == 5.0
    assert result.message.startswith("DRYRUN:")


def test_live_pipeline_stops_when_wallet_verification_fails(monkeypatch):
    monkeypatch.setattr(
        trading_safeguards,
        "TradingSafeguards",
        lambda: SimpleNamespace(
            check_wallet_balance=lambda amount: (False, "No funder address configured")
        ),
    )

    result = run_pipeline.run_pipeline(dryrun=False, verbose=False)

    assert result["success"] is False
    assert "wallet verification failed" in result["error"].lower()
    assert "No funder address" in result["error"]
