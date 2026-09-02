import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "task_dispatch.py"


def test_task_dispatch_has_no_process_or_shell_execution():
    source = PATH.read_text()
    tree = ast.parse(source)
    assert "subprocess" not in source
    assert "shell=True" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"run", "Popen", "call", "check_call", "check_output", "system", "popen"}
        for node in ast.walk(tree)
    )


def test_task_dispatch_fails_closed_for_remote_execution():
    namespace = {"__file__": str(PATH)}
    exec(compile(PATH.read_text(), str(PATH), "exec"), namespace)
    result = namespace["dispatch_to_node"](namespace["COMPUTE_NODES"][0], "health_check")
    assert result["success"] is False
    assert "FactoryAuthorityGateway" in result["error"]
