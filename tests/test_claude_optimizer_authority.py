import ast
from pathlib import Path

TARGET = Path("autonomous/claude_optimizer.py")


def test_legacy_claude_optimizer_has_no_mutation_execution():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert "shell=True" not in source
    assert "subprocess.Popen" not in source
    assert "os.system" not in source
    assert "write_text(" not in source
    assert "open(instructions_file, 'w')" not in source
    assert "open(instructions_file, \"w\")" not in source

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                assert node.func.attr not in {"Popen", "run", "call", "check_call", "check_output"}


def test_legacy_claude_optimizer_fails_closed():
    source = TARGET.read_text(encoding="utf-8")
    assert "FactoryAuthorityGateway" in source
    assert "Legacy ClaudeOptimizer execution is disabled" in source
    assert "Legacy ClaudeOptimizer file mutation is disabled" in source
