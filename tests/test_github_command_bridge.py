import json
from pathlib import Path

from scripts.github_command_bridge import _parse


def test_parse_requires_allowlisted_action():
    assert _parse("[factory-command]\nidempotency_key=x\nobjective=test\naction=bus_summary")[0]["action"] == "bus_summary"
    assert _parse("[factory-command]\nidempotency_key=x\nobjective=test\naction=execute") is None


def test_read_file_fact_requires_path():
    assert _parse("[factory-command]\nidempotency_key=x\nobjective=test\naction=read_file_fact") is None
    parsed = _parse("[factory-command]\nidempotency_key=x\nobjective=test\naction=read_file_fact\nfile_path=scripts/task_worker.py")
    assert parsed[1]["file_path"] == "scripts/task_worker.py"


def test_command_identity_is_explicit():
    parsed = _parse("[factory-command]\nidempotency_key=sep18-test\nobjective=test\naction=bus_summary")
    assert parsed[0]["idempotency_key"] == "sep18-test"
