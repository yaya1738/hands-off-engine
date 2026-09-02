import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "termux-hands-off" / "autopilot" / "control_server.py"


def load_module():
    spec = importlib.util.spec_from_file_location("legacy_control_server", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_control_server_has_no_remote_execution_authority():
    module = load_module()
    assert module.HOST == "127.0.0.1"
    source = MODULE_PATH.read_text()
    assert "legacy_remote_execution_disabled" in source
    assert "subprocess" not in source
    assert "shell=True" not in source
