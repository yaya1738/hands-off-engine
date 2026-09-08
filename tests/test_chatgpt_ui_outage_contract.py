"""Contract tests proving routine operation does not require the ChatGPT consumer UI."""

import json
import re
from pathlib import Path

from telegram.human_loop import HumanLoop
from tools import autonomy_liveness_supervisor as supervisor


class FakeRuntime:
    class Autonomy:
        @staticmethod
        def discovery_gate(objective, context):
            return {"capability_graph_analysis": {"gaps": []}}

    def __init__(self):
        self.autonomy = self.Autonomy()


class FakeLoop:
    def __init__(self, runtime):
        self.runtime = runtime

    def select_next(self, context):
        return {
            "status": "selected",
            "selected": {
                "objective": "process authenticated external request",
                "strategic_objective_id": "adaptive-human-independence",
                "score": 100,
            },
        }


class FakeGateway:
    def execute_autonomous(self, objective):
        return {
            "decision": {"status": "READY"},
            "execution": {"success": True, "steps_completed": ["execute", "verify"]},
        }


def test_external_request_reaches_autonomous_execution_without_consumer_ui(monkeypatch, tmp_path: Path):
    """Authenticated external work must reach governed execution without a consumer session."""
    loop = HumanLoop(tmp_path)
    response = loop.receive(
        "Execute this request autonomously without the ChatGPT consumer UI.",
        chat_id="42",
        username="authenticated-user",
    )

    assert re.search(r"task [a-f0-9]{8}", response)
    queued = supervisor.AutonomousTaskQueue(tmp_path).get_next_task()
    assert queued is not None
    assert queued["source"] == "telegram_user"
    assert queued["metadata"]["chat_id"] == "42"

    monkeypatch.setattr(supervisor, "FactoryRuntime", FakeRuntime)
    monkeypatch.setattr(supervisor, "FactoryAutonomousObjectiveLoop", FakeLoop)
    monkeypatch.setattr(supervisor, "FactoryAuthorityGateway", lambda runtime=None: FakeGateway())

    result = supervisor.run_once(tmp_path)

    assert result["execution_succeeded"] is True
    assert result["verification_observed"] is True
    assert result["live_system_active"] is True
    assert supervisor.AutonomousTaskQueue(tmp_path).get_next_task() is None
    completed = tmp_path / "state" / "autonomous_tasks_completed.jsonl"
    assert completed.exists()
    record = json.loads(completed.read_text(encoding="utf-8").splitlines()[-1])
    assert record["task"]["metadata"]["chat_id"] == "42"


def test_consumer_provider_is_not_required_by_autonomous_control_plane():
    """The control plane contains no eager ChatGPT/Claude consumer dependency."""
    import ast

    source = Path("tools/autonomy_liveness_supervisor.py").read_text(encoding="utf-8").casefold()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    assert not any("chatgpt" in name or "claude" in name for name in imports)


def test_telegram_listener_routes_authenticated_messages_without_consumer_session():
    source = Path("telegram/telegram_bot_listener.py").read_text(encoding="utf-8")
    assert "self.human_loop.receive" in source
    assert "TELEGRAM_CHAT_ID" in source
    assert "if str(chat_id) != str(ALLOWED_CHAT_ID)" in source
