from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_autonomous_supervisor_has_no_consumer_session_dependency():
    source = (REPO_ROOT / "tools" / "autonomy_liveness_supervisor.py").read_text(encoding="utf-8").casefold()
    forbidden = ("chatgpt", "claude", "consumer session", "continue prompt")
    assert not any(term in source for term in forbidden)


def test_legacy_claude_processor_is_not_a_model_consumer():
    source = (REPO_ROOT / "scripts" / "claude_task_processor.sh").read_text(encoding="utf-8").casefold()
    assert "exec /usr/bin/python3" in source
    assert "autonomy_liveness_supervisor.py" in source
    assert "claude" in source  # filename/compatibility documentation is allowed
    assert "claude --" not in source
    assert "chatgpt" in source
    assert "consumer session" in source


def test_external_control_surface_exists():
    listener = (REPO_ROOT / "telegram" / "telegram_bot_listener.py").read_text(encoding="utf-8")
    assert "HumanLoop" in listener
    assert "getUpdates" in listener
    assert "ALLOWED_CHAT_ID" in listener
