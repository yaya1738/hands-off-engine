from ai.factory.state_persistence import (
    FactoryStatePersistence,
)


class FakeState:
    def __init__(self):
        self.data = {
            "health": "healthy",
        }

    def snapshot(self):
        return self.data

    def update(self, values):
        self.data.update(values)


class FakePersistence:
    def __init__(self):
        self.saved = None

    def save(self, state):
        self.saved = state

    def load(self):
        return self.saved


def test_save_state():
    state = FakeState()
    storage = FakePersistence()

    bridge = FactoryStatePersistence(
        state,
        storage,
    )

    result = bridge.save_state()

    assert result["health"] == "healthy"
    assert storage.saved["health"] == "healthy"


def test_restore():
    state = FakeState()
    storage = FakePersistence()

    storage.saved = {
        "runtime": "active",
    }

    bridge = FactoryStatePersistence(
        state,
        storage,
    )

    result = bridge.restore()

    assert result["runtime"] == "active"
    assert state.data["runtime"] == "active"


def test_missing_restore():
    state = FakeState()
    storage = FakePersistence()

    bridge = FactoryStatePersistence(
        state,
        storage,
    )

    assert bridge.restore() is None
