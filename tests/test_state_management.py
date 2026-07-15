from ai.factory.state_management import (
    FactoryStateManagement,
)


def build():
    return FactoryStateManagement()


def test_set_state():
    manager = build()

    result = manager.set_state(
        "mode",
        "ACTIVE",
    )

    assert result["set"] is True


def test_get_state():
    manager = build()

    manager.set_state(
        "x",
        1,
    )

    result = manager.get_state(
        "x"
    )

    assert result["found"] is True


def test_update_state():
    manager = build()

    result = manager.update_state(
        {
            "a": 1,
        }
    )

    assert result["updated"] is True


def test_snapshot_state():
    manager = build()

    result = manager.snapshot_state()

    assert result["snapshotted"] is True


def test_history():
    manager = build()

    manager.set_state(
        "x",
        1,
    )

    assert len(manager.history()) == 1
