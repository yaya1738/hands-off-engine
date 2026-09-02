import ast
from pathlib import Path

SOURCE = Path("autonomous/full_activation.py").read_text()
TREE = ast.parse(SOURCE)


def _executable_nodes():
    nodes = list(TREE.body)
    if nodes and isinstance(nodes[0], ast.Expr) and isinstance(nodes[0].value, ast.Constant) and isinstance(nodes[0].value.value, str):
        nodes = nodes[1:]
    return nodes


def test_legacy_full_activation_has_no_process_or_remote_execution():
    executable = "\n".join(ast.unparse(node) for node in _executable_nodes())
    imports = {alias.name for node in ast.walk(TREE) if isinstance(node, ast.Import) for alias in node.names}
    calls = {
        node.func.attr
        for node in ast.walk(TREE)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "subprocess" not in imports
    assert not {"system", "popen"} & calls
    assert not any(token in executable for token in ("doctl", "rsync", "curl"))


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
