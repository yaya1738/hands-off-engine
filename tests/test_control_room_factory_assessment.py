from scripts.control_room_state import build_snapshot


def test_factory_assessment_is_projected_without_reobservation(tmp_path):
    assessment = {
        "health": 0.9,
        "gaps": ["orphaned interaction replies"],
        "objective": "observe",
        "interaction_health": {"available": True, "interaction_orphan_replies": 1},
        "secret": "must-not-leak",
    }
    snapshot = build_snapshot(tmp_path, bus_limit=2, lifecycle_limit=0, factory_assessment=assessment)

    assert snapshot["factory_assessment"] == {
        "available": True,
        "health": 0.9,
        "gaps": ["orphaned interaction replies"],
        "objective": "observe",
        "interaction_health": {"available": True, "interaction_orphan_replies": 1},
    }
    assert "secret" not in snapshot["factory_assessment"]
    assert assessment["gaps"] == ["orphaned interaction replies"]


def test_factory_assessment_fails_closed_when_not_supplied(tmp_path):
    snapshot = build_snapshot(tmp_path, bus_limit=1, lifecycle_limit=0)
    assert snapshot["factory_assessment"] == {"available": False}
