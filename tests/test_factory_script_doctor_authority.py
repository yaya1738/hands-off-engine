import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source():
    return (ROOT / "tools" / "factory_script_doctor.py").read_text()


def test_legacy_script_doctor_has_no_process_execution():
    tree = ast.parse(_source())
    assert not any(
        isinstance(node, ast.Import) and any(alias.name == "subprocess" for alias in node.names)
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"run", "Popen", "call", "check_call", "check_output"}
        for node in ast.walk(tree)
    )


def test_legacy_script_doctor_fails_closed():
    namespace = {"__file__": str(ROOT / "tools" / "factory_script_doctor.py")}
    exec(compile(_source(), "factory_script_doctor.py", "exec"), namespace)
    code, output, error = namespace["run_script"]("anything.py")
    assert code != 0
    assert output == ""
    assert "FactoryAuthorityGateway" in error
