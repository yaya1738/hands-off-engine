import ast
from pathlib import Path

SOURCE = Path("autonomous/full_activation.py").read_text()
TREE = ast.parse(SOURCE)


def test_legacy_full_activation_has_no_process_or_remote_execution():
    forbidden = ("subprocess", "doctl", "rsync", "curl")
    imports = {alias.name for node in ast.walk(TREE) if isinstance(node, ast.Import) for alias in node.names}
    calls = {
        node.func.attr
        for node in ast.walk(TREE)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "subprocess" not in imports
    assert not {"system", "popen"} & calls
    assert not any(token in SOURCE for token in forbidden if token != "subprocess")


def test_legacy_operations_fail_closed():
    namespace = {
        "__name__": "full_activation_test",
        "__file__": str(Path("autonomous/full_activation.py").resolve()),
    }
    exec(compile(SOURCE, "autonomous/full_activation.py", "exec"), namespace)
    activation = namespace["FullActivation"]()
    assert activation.full_activation()["disabled"] is True
    assert activation.activate_node_coordination()["disabled"] is True
    assert activation.get_status()["ready_for_capital"] is False
