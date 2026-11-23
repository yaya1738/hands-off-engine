"""Regression tests for GitHub command bridge admission contracts."""
from scripts.github_command_bridge import _parse


def _command(action="bus_summary", extra=""):
    return (
        "[factory-command]\n"
        "idempotency_key=test-command-1\n"
        "objective=bounded read-only test objective\n"
        f"action={action}\n"
        f"{extra}"
    )


def test_parse_returns_optional_continuation_to_poll_consumer():
    parsed = _parse(_command(extra="next_action_action=lifecycle_summary\n"))
    assert parsed is not None
    command, params, next_action = parsed
    assert command["action"] == "bus_summary"
    assert params == {}
    assert next_action == {"action": "lifecycle_summary", "params": {}}


def test_factory_execute_is_forced_to_dryrun():
    parsed = _parse(_command(action="factory_execute"))
    assert parsed is not None
    command, params, next_action = parsed
    assert command["action"] == "factory_execute"
    assert params == {
        "mode": "DRYRUN",
        "objective": "bounded read-only test objective",
    }
    assert next_action is None


def test_unknown_continuation_is_rejected():
    assert _parse(_command(extra="next_action_action=live_trade\n")) is None
