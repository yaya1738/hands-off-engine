"""Finance hub storage must live outside the public checkout."""

import importlib.util
import os
from pathlib import Path


MODULE_PATH = Path("finance/private_state.py")


def test_finance_hub_resolves_under_private_config_with_restricted_modes(tmp_path, monkeypatch):
    if os.name != "posix":
        return
    private_root = tmp_path / "private"
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(private_root))
    spec = importlib.util.spec_from_file_location("finance_private_state_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    path = module.private_finance_hub_path()

    assert path == private_root / "finance" / "private_finance_hub.json"
    assert str(path).startswith(str(private_root))
    assert private_root.stat().st_mode & 0o777 == 0o700
    assert path.parent.stat().st_mode & 0o777 == 0o700
