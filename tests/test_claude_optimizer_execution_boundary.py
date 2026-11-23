from autonomous.claude_optimizer import ClaudeOptimizer
import autonomous.claude_optimizer as optimizer_module


def test_claude_optimizer_cannot_execute_after_advisory_validation(monkeypatch):
    optimizer = ClaudeOptimizer.__new__(ClaudeOptimizer)
    monkeypatch.setattr(
        optimizer,
        "validate_action",
        lambda action_type, target, **kwargs: (True, "advisory layers passed"),
    )

    def forbidden_run(*args, **kwargs):
        raise AssertionError("ClaudeOptimizer must not reach shell execution")

    monkeypatch.setattr(optimizer_module.subprocess, "run", forbidden_run)

    allowed, reason = optimizer.safe_execute("echo should-not-run")

    assert allowed is False
    assert "governed authority" in reason.lower()
