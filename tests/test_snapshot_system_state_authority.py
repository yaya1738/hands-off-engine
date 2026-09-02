import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "snapshot_system_state.py"


def _source():
    return PATH.read_text()


def test_snapshot_has_no_process_network_or_persistence_execution():
    tree = ast.parse(_source())
    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    assert "subprocess" not in imports
    assert "requests" not in imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"run", "Popen", "system", "popen", "remove", "unlink", "write_text", "mkdir"}


def test_snapshot_contains_no_embedded_bot_credential_and_is_nonpersistent():
    source = _source()
    assert "api.telegram.org/bot" not in source
    assert ".env.polymarket" not in source
    namespace = {"__file__": str(PATH)}
    exec(compile(source, str(PATH), "exec"), namespace)
    snapshot = namespace["generate_snapshot"]()
    assert snapshot["disabled"] is True
    assert snapshot["authority"] == "FactoryAuthorityGateway"
