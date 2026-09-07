import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.casefold() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.casefold())
    return modules


def test_autonomous_supervisor_has_no_consumer_provider_import():
    modules = _import_modules(REPO_ROOT / "tools" / "autonomy_liveness_supervisor.py")
    assert not any("chatgpt" in module or "claude" in module for module in modules)


def test_legacy_claude_processor_is_not_a_model_consumer():
    source = (REPO_ROOT / "scripts" / "claude_task_processor.sh").read_text(encoding="utf-8").casefold()
    assert "exec /usr/bin/python3" in source
    assert "autonomy_liveness_supervisor.py" in source
    assert "claude --" not in source


def test_external_control_surface_exists():
    listener = (REPO_ROOT / "telegram" / "telegram_bot_listener.py").read_text(encoding="utf-8")
    assert "HumanLoop" in listener
    assert "getUpdates" in listener
    assert "ALLOWED_CHAT_ID" in listener


def test_ai_nexus_runner_does_not_eagerly_import_chatgpt():
    modules = _import_modules(REPO_ROOT / "ai_nexus" / "runner.py")
    assert "ai_nexus.provider_chatgpt" not in modules
