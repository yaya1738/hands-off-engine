import ast
from pathlib import Path


TARGET = Path("infrastructure/selfheal.py")


def test_legacy_selfheal_has_no_shell_execution_or_direct_mutation():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert "subprocess" not in source
    assert "os.system" not in source
    assert "shutil.copy2" not in source
    assert "os.remove" not in source
    assert "shell=True" not in source

    # Guard specifically against subprocess execution calls.  Do not reject
    # unrelated APIs that legitimately expose a method named `run`.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                assert node.func.attr not in {"Popen", "run", "call", "check_call", "check_output"}


def test_selfheal_mutations_are_explicitly_governed():
    source = TARGET.read_text(encoding="utf-8")
    assert '"FactoryAuthorityGateway"' in source
    assert '"mutation_mode": "fail_closed"' in source
    assert "selfheal_mutation_blocked" in source
