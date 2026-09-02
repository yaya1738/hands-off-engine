import ast
from pathlib import Path

TARGET = Path("autonomous/self_healer.py")


def test_legacy_self_healer_has_no_execution_authority():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert "import subprocess" not in source
    assert "from subprocess" not in source
    assert "os.system" not in source
    assert "shell=True" not in source
    assert "shutil.copy2" not in source
    assert "pkill" not in source
    assert "systemctl start" not in source
    assert "subprocess." not in source

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"Popen", "run", "call", "check_call", "check_output"}


def test_legacy_self_healer_routes_mutations_to_factory_authority():
    source = TARGET.read_text(encoding="utf-8")
    assert "FactoryAuthorityGateway" in source
    assert "gateway.submit_development_request" in source
    assert "governed_request" in source
    assert "governed_repair_required" in source


def test_legacy_self_healer_does_not_repair_state_files():
    source = TARGET.read_text(encoding="utf-8")
    assert "filepath.write_text" not in source
    assert "filepath.rename" not in source
    assert "os.remove" not in source
    assert "unlink(" not in source
