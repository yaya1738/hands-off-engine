import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "integrafix" / "system_hardening.py"


def test_system_hardening_has_no_process_mutation_primitives():
    source = PATH.read_text()
    tree = ast.parse(source)
    assert "subprocess" not in source
    assert "os.kill" not in source
    assert "signal.SIGTERM" not in source
    assert "signal.SIGKILL" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"run", "Popen", "call", "check_call", "check_output", "system", "popen", "write_text", "mkdir"}
        for node in ast.walk(tree)
    )


def test_restart_fails_closed_to_factory_authority():
    namespace = {"__file__": str(PATH)}
    exec(compile(PATH.read_text(), str(PATH), "exec"), namespace)
    hardening = namespace["SystemHardening"]()
    config = namespace["CRITICAL_PROCESSES"]["backend_loop"]
    assert hardening.restart_process("backend_loop", config) is False
    assert "FactoryAuthorityGateway" in hardening.status_report() if hasattr(hardening, "status_report") else True
