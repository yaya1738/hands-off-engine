import importlib
import logging
from pathlib import Path


def test_ai_runner_legacy_execution_is_blocked(monkeypatch):
    # ai_runner historically initializes a root-owned log path at import time.
    # Neutralize that setup so the authority regression can run as an ordinary
    # GitHub Actions user without changing production behavior.
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(logging, "FileHandler", lambda *args, **kwargs: logging.NullHandler())

    module = importlib.import_module("ai.ai_runner")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess execution must not be reached")

    monkeypatch.setattr(module.subprocess, "run", fail_if_called)

    result = module.execute_command("echo should-never-run")

    assert result["status"] == "blocked"
    assert result["authority"] == "FactoryAuthorityGateway"
    assert result["returncode"] == -1
