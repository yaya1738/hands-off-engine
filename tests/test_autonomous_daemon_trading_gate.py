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
