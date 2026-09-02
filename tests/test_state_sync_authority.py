"""Regression tests for the legacy state-sync execution boundary."""

from pathlib import Path


def test_legacy_state_sync_is_not_present():
    assert not Path("autonomous/state_sync.py").exists()


def test_authority_regression_workflow_covers_state_sync():
    workflow = Path(".github/workflows/factory-authority-regression.yml").read_text()
    assert "tests/test_state_sync_authority.py" in workflow
