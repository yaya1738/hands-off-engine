import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validation_runner_has_no_process_execution():
    path = ROOT / "ai/factory/validation_runner.py"
    source = path.read_text()
    tree = ast.parse(source)
    assert "import subprocess" not in source
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"run", "Popen", "call", "check_call", "check_output", "system", "popen"} for node in ast.walk(tree))


def test_validation_runner_fails_closed():
    path = ROOT / "ai/factory/validation_runner.py"
    namespace = {"__file__": str(path)}
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    result = namespace["FactoryValidationRunner"]().run_test_check()
    assert result["success"] is False
    assert "FactoryAuthorityGateway" in result["error"]
