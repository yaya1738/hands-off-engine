"""Contract test for operating the system with the consumer ChatGPT UI unavailable.

This intentionally treats consumer-session providers as unavailable and verifies
that the system's external ingress can still create durable work without them.
"""

from pathlib import Path


def test_external_ingress_has_no_consumer_session_dependency(tmp_path, monkeypatch):
    import telegram.human_loop as human_loop_module

    class FakeQueue:
        def __init__(self, root):
            self.root = Path(root)

        def add_task(self, **kwargs):
            self.task = kwargs
            return "ui-outage-task"

    import scripts.autonomous_task_queue as queue_module
    monkeypatch.setattr(queue_module, "AutonomousTaskQueue", FakeQueue)

    response = human_loop_module.HumanLoop(tmp_path).receive(
        "Continue autonomously without the ChatGPT consumer UI.",
        chat_id="authorized-chat",
        username="authorized-user",
    )

    assert "ui-outage-task" in response
    assert "ChatGPT" not in response


def test_autonomous_supervisor_import_surface_contains_no_consumer_provider():
    import ast

    source = Path("tools/autonomy_liveness_supervisor.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.casefold() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.casefold())

    assert not any("chatgpt" in name or "claude" in name for name in imports)


def test_telegram_listener_routes_authenticated_non_command_messages_to_human_loop():
    source = Path("telegram/telegram_bot_listener.py").read_text(encoding="utf-8")
    assert "self.human_loop.receive" in source
    assert "TELEGRAM_CHAT_ID" in source
    assert "if str(chat_id) != str(ALLOWED_CHAT_ID)" in source
