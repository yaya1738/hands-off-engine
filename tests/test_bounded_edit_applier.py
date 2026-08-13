from pathlib import Path

import pytest

from ai.factory.bounded_edit_applier import BoundedEditApplier


def test_applies_only_authorized_single_replacement(tmp_path: Path):
    target = tmp_path / "target.txt"
    target.write_text("before\n")

    result = BoundedEditApplier(str(tmp_path)).apply(
        {"path": "target.txt", "operation": "replace_text", "old": "before", "new": "after"},
        ["target.txt"],
    )

    assert result["status"] == "applied"
    assert target.read_text() == "after\n"


def test_rejects_unauthorized_path(tmp_path: Path):
    (tmp_path / "target.txt").write_text("before")
    with pytest.raises(PermissionError):
        BoundedEditApplier(str(tmp_path)).apply(
            {"path": "other.txt", "operation": "replace_text", "old": "before", "new": "after"},
            ["target.txt"],
        )


def test_rejects_ambiguous_replacement(tmp_path: Path):
    target = tmp_path / "target.txt"
    target.write_text("before before")
    with pytest.raises(ValueError, match="exactly one"):
        BoundedEditApplier(str(tmp_path)).apply(
            {"path": "target.txt", "operation": "replace_text", "old": "before", "new": "after"},
            ["target.txt"],
        )
