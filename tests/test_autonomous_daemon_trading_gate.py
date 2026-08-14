from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

_original_mkdir = Path.mkdir


def _mkdir_without_system_log_side_effect(self, *args, **kwargs):
    if str(self) == "/var/log/hands-off":
        return None
    return _original_mkdir(self, *args, **kwargs)


Path.mkdir = _mkdir_without_system_log_side_effect
try:
    from scripts import autonomous_daemon
finally:
    Path.mkdir = _original_mkdir


def test_trading_pipeline_is_hard_blocked(monkeypatch):
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("live trading subprocess must not be launched")

    monkeypatch.setattr(autonomous_daemon, "run_subprocess", forbidden)
    monkeypatch.setattr(autonomous_daemon, "LIVE_TRADING_ENABLED", False)

    assert autonomous_daemon.task_trading_pipeline() is False
    assert called is False


def test_trading_pipeline_requires_fresh_current_rules_before_subprocess(monkeypatch):
    called = False
    now = datetime.now(timezone.utc)
    stale_snapshot = {
        "market_id": "example-market",
        "observed_at": (now - timedelta(minutes=6)).isoformat(),
        "source": "test",
        "fees_enabled": True,
        "fee_schedule": {"version": "current"},
        "order_type": "market",
        "orderbook_depth": {"ask": 1000},
        "market_constraints": {"active": True},
    }

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("trading subprocess must not launch before rules gate")

    monkeypatch.setattr(autonomous_daemon, "run_subprocess", forbidden)
    monkeypatch.setattr(autonomous_daemon, "LIVE_TRADING_ENABLED", True)
    monkeypatch.setenv("POLYMARKET_RULES_SNAPSHOT_JSON", json.dumps(stale_snapshot))

    assert autonomous_daemon.task_trading_pipeline() is False
    assert called is False
