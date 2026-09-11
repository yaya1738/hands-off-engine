from pathlib import Path

from tools.factory_forensics import dass_measurement


def test_missing_required_active_paths_are_structural_gaps(tmp_path, monkeypatch):
    monkeypatch.setattr(dass_measurement, "ROOT", tmp_path)
    required = ["present.py", "missing.py"]
    (tmp_path / "present.py").write_text("# present\n", encoding="utf-8")

    missing = dass_measurement.missing_required_paths({"required_active_paths": required})

    assert missing == ["missing.py"]


def test_missing_required_paths_are_empty_when_all_present(tmp_path, monkeypatch):
    monkeypatch.setattr(dass_measurement, "ROOT", tmp_path)
    (tmp_path / "runtime.py").write_text("# runtime\n", encoding="utf-8")

    assert dass_measurement.missing_required_paths({"required_active_paths": ["runtime.py"]}) == []


def test_classification_keeps_operational_files_outside_dass_as_unclassified():
    scope = {
        "active_roots": ["ai/factory/"],
        "non_dass_quarantined_roots": ["backups/"],
    }

    assert dass_measurement.classify("ai/factory/runtime.py", scope) == "dass"
    assert dass_measurement.classify("backups/old.py", scope) == "quarantined"
    assert dass_measurement.classify("scripts/runner.py", scope) == "unclassified"
