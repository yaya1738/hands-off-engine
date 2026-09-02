"""Regression coverage for removal of known legacy privileged execution surfaces."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_state_sync_is_removed():
    assert not (ROOT / "autonomous" / "state_sync.py").exists()
