from tools.factory_forensics import dass_phase


def _measurement(achieved: bool) -> dict:
    return {
        "dass_coverage_percent": 100.0 if achieved else 99.9,
        "target_percent": 100,
        "dass_pure": achieved,
        "operational_unclassified_files": [] if achieved else ["tools/missing.py"],
        "quarantined_import_hits": [],
        "active_unmapped_files": [],
    }


def test_select_phase_requires_structural_achievement_and_live_runtime(monkeypatch):
    monkeypatch.setattr(dass_phase, "_live_runtime_observed", lambda: True)
    assert dass_phase.select_phase(_measurement(True)) == "post_dass"

    monkeypatch.setattr(dass_phase, "_live_runtime_observed", lambda: False)
    assert dass_phase.select_phase(_measurement(True)) == "pre_dass"


def test_structural_failures_cannot_become_dass_even_with_live_runtime(monkeypatch):
    monkeypatch.setattr(dass_phase, "_live_runtime_observed", lambda: True)
    assert dass_phase.select_phase(_measurement(False)) == "pre_dass"

    impure = {**_measurement(True), "dass_pure": False}
    assert dass_phase.select_phase(impure) == "pre_dass"

    quarantined = {**_measurement(True), "quarantined_import_hits": ["x"]}
    assert dass_phase.select_phase(quarantined) == "pre_dass"

    unmapped = {**_measurement(True), "active_unmapped_files": ["tools/missing.py"]}
    assert dass_phase.select_phase(unmapped) == "pre_dass"


def test_live_runtime_requires_current_healthy_attestation(tmp_path, monkeypatch):
    monkeypatch.setattr(dass_phase, "LIVENESS", tmp_path / "autonomy_liveness.json")
    assert dass_phase._live_runtime_observed() is False

    (tmp_path / "autonomy_liveness.json").write_text(
        '{"live_system_active": true, "operating_state": "live_degraded", '
        '"live_attestation": {"active": true, '
        '"mechanism": "governed_autonomous_supervisor_cycle", '
        '"observed_at": "2099-01-01T00:00:00+00:00", "expires_at": 4102444800}}',
        encoding="utf-8",
    )
    assert dass_phase._live_runtime_observed() is False

    (tmp_path / "autonomy_liveness.json").write_text(
        '{"live_system_active": true, "operating_state": "live_steady_state", '
        '"live_attestation": {"active": true, '
        '"mechanism": "governed_autonomous_supervisor_cycle", '
        '"observed_at": "2099-01-01T00:00:00+00:00", "expires_at": 4102444800}}',
        encoding="utf-8",
    )
    assert dass_phase._live_runtime_observed() is False
