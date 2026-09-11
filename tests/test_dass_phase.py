import json
from datetime import datetime, timedelta, timezone

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


def _write_liveness(path, *, operating_state: str, observed: datetime, expires: datetime) -> None:
    path.write_text(
        json.dumps(
            {
                "live_system_active": True,
                "operating_state": operating_state,
                "live_attestation": {
                    "active": True,
                    "mechanism": "governed_autonomous_supervisor_cycle",
                    "observed_at": observed.isoformat(),
                    "expires_at": expires.timestamp(),
                },
            }
        ),
        encoding="utf-8",
    )


def test_live_runtime_requires_current_healthy_attestation(tmp_path, monkeypatch):
    path = tmp_path / "autonomy_liveness.json"
    monkeypatch.setattr(dass_phase, "LIVENESS", path)
    assert dass_phase._live_runtime_observed() is False

    now = datetime.now(timezone.utc)
    _write_liveness(
        path,
        operating_state="live_degraded",
        observed=now - timedelta(seconds=10),
        expires=now + timedelta(minutes=5),
    )
    assert dass_phase._live_runtime_observed() is False

    _write_liveness(
        path,
        operating_state="live_steady_state",
        observed=now - timedelta(seconds=10),
        expires=now + timedelta(minutes=5),
    )
    assert dass_phase._live_runtime_observed() is True

    _write_liveness(
        path,
        operating_state="live_steady_state",
        observed=now - timedelta(minutes=30),
        expires=now - timedelta(minutes=15),
    )
    assert dass_phase._live_runtime_observed() is False
