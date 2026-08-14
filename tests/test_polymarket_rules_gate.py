from datetime import datetime, timedelta, timezone

from ai.finance.polymarket_rules_gate import PolymarketRulesGate


def snapshot(observed_at):
    return {
        "market_id": "example-market",
        "observed_at": observed_at,
        "source": "authoritative-current-rules",
        "fees_enabled": True,
        "fee_schedule": {"version": "current"},
        "order_type": "limit",
        "orderbook_depth": {"bid": 1000, "ask": 1000},
        "market_constraints": {"active": True},
    }


def test_gate_denies_when_global_live_trading_is_disabled():
    now = datetime.now(timezone.utc)
    decision = PolymarketRulesGate().check(
        snapshot(now.isoformat()),
        live_trading_enabled=False,
        now=now,
    )
    assert decision.allowed is False
    assert decision.reason == "live_trading_globally_disabled"


def test_gate_denies_stale_rules():
    now = datetime.now(timezone.utc)
    stale = now - timedelta(minutes=6)
    decision = PolymarketRulesGate(freshness_seconds=300).check(
        snapshot(stale.isoformat()),
        live_trading_enabled=True,
        now=now,
    )
    assert decision.allowed is False
    assert decision.reason == "rules_snapshot_stale"


def test_gate_denies_incomplete_rules():
    now = datetime.now(timezone.utc)
    decision = PolymarketRulesGate().check(
        {"market_id": "example-market", "observed_at": now.isoformat()},
        live_trading_enabled=True,
        now=now,
    )
    assert decision.allowed is False
    assert decision.reason.startswith("rules_snapshot_missing:")


def test_gate_accepts_fresh_complete_rules_only_when_unbanned():
    now = datetime.now(timezone.utc)
    decision = PolymarketRulesGate().check(
        snapshot(now.isoformat()),
        live_trading_enabled=True,
        now=now,
    )
    assert decision.allowed is True
    assert decision.reason == "current_rules_valid"
