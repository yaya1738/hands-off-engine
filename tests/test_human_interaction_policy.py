from pathlib import Path

from telegram.human_interaction_policy import HumanInteractionPolicy


def test_routine_progress_is_suppressed(tmp_path: Path):
    policy = HumanInteractionPolicy(tmp_path)
    assert not policy.should_notify(
        kind="progress", priority="normal", routine=True
    )


def test_material_decision_is_always_escalated(tmp_path: Path):
    policy = HumanInteractionPolicy(tmp_path)
    assert policy.should_notify(kind="decision", priority="normal")


def test_blocker_with_response_is_escalated(tmp_path: Path):
    policy = HumanInteractionPolicy(tmp_path)
    assert policy.should_notify(
        kind="blocker", priority="normal", requires_response=True
    )


def test_metrics_measure_human_value_without_changing_authority(tmp_path: Path):
    policy = HumanInteractionPolicy(tmp_path)
    policy.record_outcome(
        contacted=True,
        human_response=True,
        autonomous_resolution=False,
        materially_changed=True,
    )
    policy.record_outcome(
        contacted=False,
        autonomous_resolution=True,
    )
    summary = policy.summary()
    assert summary["events"] == 2
    assert summary["contacts"] == 1
    assert summary["autonomous_resolutions"] == 1
    assert summary["human_value_rate"] == 1.0
