import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.factory_execution_adapter import execute_factory_command


def test_factory_live_requires_approval():
    result = execute_factory_command(
        {"id": "fx-1", "mode": "LIVE", "objective": "inspect runtime"},
        execution_gate=True,
    )
    assert result["status"] == "approval_required"


def test_factory_live_requires_explicit_executor_gate():
    result = execute_factory_command(
        {"id": "fx-2", "mode": "LIVE", "approval_status": "approved", "objective": "inspect runtime"},
        execution_gate=False,
    )
    assert result["status"] == "awaiting_executor_gate"


def test_factory_dryrun_never_requires_execution_gate():
    result = execute_factory_command(
        {"id": "fx-3", "mode": "DRYRUN", "objective": "inspect runtime"},
        execution_gate=False,
    )
    assert result["status"] == "dryrun_only"


def test_factory_missing_objective_fails_closed():
    result = execute_factory_command(
        {"id": "fx-4", "mode": "LIVE", "approval_status": "approved"},
        execution_gate=True,
    )
    assert result["status"] == "rejected"
