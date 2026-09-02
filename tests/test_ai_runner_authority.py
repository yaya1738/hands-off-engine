import importlib
import logging
import sys
import types
from pathlib import Path


def test_ai_runner_legacy_execution_is_blocked(monkeypatch):
    # The legacy module imports requests only for its LLM client. Stub that
    # optional dependency because this regression exercises the execution
    # boundary and must run in the minimal authority CI environment.
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace())
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
