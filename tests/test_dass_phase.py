import json

from tools import autonomous_phase_supervisor as phase_supervisor
from tools.factory_forensics.dass_phase import select_phase


def _measurement(achieved: bool) -> dict:
    return {
        "dass_coverage_percent": 100.0 if achieved else 99.9,
        "target_percent": 100,
        "dass_pure": achieved,
        "operational_unclassified_files": [] if achieved else ["tools/missing.py"],
        "quarantined_import_hits": [],
    }


def test_select_phase_requires_full_pure_measurement():
    assert select_phase(_measurement(True)) == "post_dass"

    impure = {**_measurement(True), "dass_pure": False}
    assert select_phase(impure) == "pre_dass"

    quarantined = {**_measurement(True), "quarantined_import_hits": ["x"]}
    assert select_phase(quarantined) == "pre_dass"

    assert select_phase(_measurement(False)) == "pre_dass"


def test_persist_phase_records_transition(tmp_path, monkeypatch):
    monkeypatch.setattr(phase_supervisor, "ROOT", tmp_path)
    state = phase_supervisor.persist_phase(
        "post_dass", _measurement(True), {"phase": "pre_dass"}
    )
    assert state["transition"] is True
    assert state["dass_achieved"] is True
    saved = json.loads((tmp_path / "state" / "dass_phase.json").read_text())
    assert saved["phase"] == "post_dass"
    assert saved["previous_phase"] == "pre_dass"


def test_main_uses_pre_dass_objective_when_measurement_is_not_achieved(monkeypatch, tmp_path):
    seen = {}

    monkeypatch.setattr(phase_supervisor, "ROOT", tmp_path)
    monkeypatch.setattr(phase_supervisor, "measure", lambda: _measurement(False))

    def fake_run_once(repo_root):
        seen["repo_root"] = repo_root
        seen["objective"] = phase_supervisor.supervisor.MISSION_OBJECTIVE
        return {"execution_succeeded": True, "converged": False}

    monkeypatch.setattr(phase_supervisor.supervisor, "run_once", fake_run_once)

    assert phase_supervisor.main() == 0
    assert seen["repo_root"] == tmp_path
    assert seen["objective"] == phase_supervisor.PRE_DASS_OBJECTIVE
    persisted = json.loads((tmp_path / "state" / "autonomy_liveness.json").read_text())
    assert persisted["dass_phase"]["phase"] == "pre_dass"
    assert persisted["dass_phase"]["dass_achieved"] is False


def test_main_uses_post_dass_objective_only_for_verified_achievement(monkeypatch, tmp_path):
    seen = {}

    monkeypatch.setattr(phase_supervisor, "ROOT", tmp_path)
    monkeypatch.setattr(phase_supervisor, "measure", lambda: _measurement(True))

    def fake_run_once(repo_root):
        seen["objective"] = phase_supervisor.supervisor.MISSION_OBJECTIVE
        return {"execution_succeeded": False, "converged": True}

    monkeypatch.setattr(phase_supervisor.supervisor, "run_once", fake_run_once)

    assert phase_supervisor.main() == 0
    assert seen["objective"] == phase_supervisor.POST_DASS_OBJECTIVE
    persisted = json.loads((tmp_path / "state" / "autonomy_liveness.json").read_text())
    assert persisted["dass_phase"]["phase"] == "post_dass"
    assert persisted["dass_phase"]["dass_achieved"] is True


def test_failed_cycle_does_not_fake_success_or_advance_phase(monkeypatch, tmp_path):
    monkeypatch.setattr(phase_supervisor, "ROOT", tmp_path)
    monkeypatch.setattr(phase_supervisor, "measure", lambda: _measurement(False))
    monkeypatch.setattr(
        phase_supervisor.supervisor,
        "run_once",
        lambda repo_root: {"execution_succeeded": False, "converged": False},
    )

    assert phase_supervisor.main() == 1
    persisted = json.loads((tmp_path / "state" / "autonomy_liveness.json").read_text())
    assert persisted["dass_phase"]["phase"] == "pre_dass"
    assert persisted["dass_phase"]["dass_achieved"] is False
