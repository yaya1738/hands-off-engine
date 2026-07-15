from ai.factory.state_manager import (
    FactoryStateManager,
)


def test_set_and_get():
    state = FactoryStateManager()

    state.set(
        "runtime",
        "active",
    )

    assert state.get("runtime") == "active"


def test_default():
    state = FactoryStateManager()

    assert state.get(
        "missing",
        "unknown",
    ) == "unknown"


def test_update():
    state = FactoryStateManager()

    state.update(
        {
            "jobs": 3,
            "health": "healthy",
        }
    )

    snapshot = state.snapshot()

    assert snapshot["jobs"] == 3
    assert snapshot["health"] == "healthy"
