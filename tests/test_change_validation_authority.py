import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_validation_execution_fails_closed():
    path = ROOT / "ai/factory/change_validation.py"
    namespace = {"__file__": str(path)}
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    validator = namespace["FactoryChangeValidation"]()
    result = validator._run(["python", "-c", "print('blocked')"])
    assert result["success"] is False
    assert "FactoryAuthorityGateway" in result["stderr"]


def test_action_router_validation_does_not_execute():
    path = ROOT / "ai/factory/change_validation.py"
    source = path.read_text()
    tree = ast.parse(source)
    assert "subprocess" not in source
    assert "shell=True" not in source
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"run", "Popen", "call", "check_call", "check_output", "system", "popen"} for node in ast.walk(tree))
