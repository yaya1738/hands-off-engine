import json

from tools.autonomous_phase_supervisor import persist_phase
from tools.factory_forensics.dass_phase import select_phase


def test_select_phase_requires_full_pure_measurement():
    base = {
        "dass_coverage_percent": 100.0,
        "target_percent": 100,
        "dass_pure": True,
        "operational_unclassified_files": [],
        "quarantined_import_hits": [],
    }
    assert select_phase(base) == "post_dass"

    impure = {**base, "quarantined_import_hits": ["x"]}
    assert select_phase(impure) == "pre_dass"

    incomplete = {**base, "dass_coverage_percent": 99.9}
    assert select_phase(incomplete) == "pre_dass"


def test_persist_phase_records_transition(tmp_path, monkeypatch):
    import tools.autonomous_phase_supervisor as phase

    monkeypatch.setattr(phase, "ROOT", tmp_path)
    report = {"dass_coverage_percent": 100.0, "target_percent": 100, "dass_pure": True}
    state = persist_phase("post_dass", report, {"phase": "pre_dass"})
    assert state["transition"] is True
    assert state["dass_achieved"] is True
    saved = json.loads((tmp_path / "state" / "dass_phase.json").read_text())
    assert saved["phase"] == "post_dass"
    assert saved["previous_phase"] == "pre_dass"
