import ast
from pathlib import Path

SOURCE = Path("scripts/autonomous_daemon.py").read_text()
TREE = ast.parse(SOURCE)


def test_daemon_has_no_subprocess_import_or_execution():
    assert "import subprocess" not in SOURCE
    assert "subprocess.run" not in SOURCE
    assert "subprocess.Popen" not in SOURCE


def test_legacy_subprocess_hook_fails_closed():
    namespace = {"__name__": "autonomous_daemon_test", "__file__": str(Path("scripts/autonomous_daemon.py").resolve())}
    exec(compile(SOURCE, "scripts/autonomous_daemon.py", "exec"), namespace)
    ok, message = namespace["run_subprocess"](["rm", "-rf", "/"])
    assert ok is False
    assert "FactoryAuthority" in message
