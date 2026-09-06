import pytest

from integrafix.trading_pipeline import EdgeSignal, TradingPipeline


def _signal():
    return EdgeSignal(
        id="sig-test",
        market_id="market-test",
        market_question="test market",
        side="YES",
        edge=0.1,
        fair_price=0.6,
        market_price=0.5,
        confidence=0.9,
        source="test",
        reasoning="test",
        detected_at="2026-01-01T00:00:00+00:00",
    )


def test_legacy_live_execution_is_fail_closed(monkeypatch):
    pipeline = TradingPipeline()

    def unexpected_live_call(*args, **kwargs):
        pytest.fail("legacy trading pipeline must not reach a real CLOB executor")

    monkeypatch.setattr(pipeline, "_execute_real_trade", unexpected_live_call)

    trade = pipeline.execute_signal(_signal(), size=1, dry_run=False)

    assert trade.status.value == "cancelled"
    assert trade.error == "legacy direct trading execution is disabled"
    assert trade.order_id is None


def test_dry_run_remains_available():
    pipeline = TradingPipeline()
    trade = pipeline.execute_signal(_signal(), size=1, dry_run=True)

    assert trade.status.value == "executed"
    assert trade.order_id.startswith("DRY_")
