import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "termux-hands-off" / "agent" / "orchestrator.py"


def test_orchestrator_has_no_process_or_shell_execution():
    source = PATH.read_text()
    tree = ast.parse(source)
    assert "subprocess" not in source
    assert "shell=True" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"run", "Popen", "call", "check_call", "check_output", "system", "popen", "write_text", "mkdir"}
        for node in ast.walk(tree)
    )


def test_orchestrator_run_fails_closed():
    namespace = {"__file__": str(PATH)}
    exec(compile(PATH.read_text(), str(PATH), "exec"), namespace)
    message = namespace["run"](["rm", "-rf", "/"])
    assert "FactoryAuthorityGateway" in message
    assert namespace["build_master"]()["disabled"] is True
